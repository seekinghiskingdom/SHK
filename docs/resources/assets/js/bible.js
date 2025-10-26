import { parseRef } from './ref.js';

// Page lives at /docs/resources/bible/index.html
// We read the index from ../../data/literature_index.json
async function loadIndex() {
  const idxURL = new URL('../../data/literature_index.json', document.baseURI);
  const res = await fetch(idxURL);
  if (!res.ok) throw new Error('Failed to load literature_index.json');
  const list = await res.json();
  return { idxURL, list };
}

function buildBibleCatalog(idxURL, list) {
  const bibles = list.filter(x => (x.type || '').toLowerCase() === 'bible');
  const map = new Map();
  for (const it of bibles) {
    const label = (it.meta?.abbr || it.title || it.id || 'Bible').toString();
    // Single-file format (legacy): { data_path }
    if (it.data_path) {
      const dataURL = new URL(it.data_path, idxURL);
      map.set(it.id, { id: it.id, label, title: it.title, kind: 'single', dataURL });
    }
    // Per-book format (v1): { per_book:true, base_url, book_index }
    else if (it.per_book && it.base_url) {
      const baseURL = new URL(it.base_url, idxURL);
      const bookIndexURL = new URL(it.book_index || './v1/lit/bible/books.json', idxURL);
      map.set(it.id, { id: it.id, label, title: it.title, kind: 'per_book', baseURL, bookIndexURL });
    }
  }
  return map;
}

async function loadSingleFile(entry) {
  const res = await fetch(entry.dataURL);
  if (!res.ok) throw new Error(`Failed to load Bible data for ${entry.id}`);
  const data = await res.json(); // expects { abbr, books:[{name,chapters:[[]]}] }
  return {
    label: data.abbr || entry.label,
    mode: 'single',
    getBookByName: (name) => data.books.find(b => b.name.toLowerCase() === name.toLowerCase()) || null,
    renderChapter: (book, chapter) => {
      const cIdx = chapter - 1;
      const lines = book.chapters[cIdx] || [];
      return lines.map((txt, i) => `<p class="verse"><span class="n">${i+1}</span>${txt}</p>`).join('\n');
    },
    renderRange: (book, chapter, vStart, vEnd) => {
      const cIdx = chapter - 1;
      const lines = book.chapters[cIdx] || [];
      const a = Math.max(1, vStart), b = Math.min(lines.length, vEnd);
      let out = '';
      for (let v=a; v<=b; v++) out += `<p class="verse"><span class="n">${v}</span>${lines[v-1]}</p>`;
      return out || '<p class="muted">No verses in range.</p>';
    }
  };
}

async function loadPerBook(entry) {
  // load books.json once
  let bookMapPromise = null;
  const getBookMap = async () => {
    if (!bookMapPromise) {
      const r = await fetch(entry.bookIndexURL);
      if (!r.ok) throw new Error('Failed to load books.json');
      const m = await r.json(); // { order:[], names:{'GEN':'Genesis', ...} }
      const rev = new Map(Object.entries(m.names).map(([code, full]) => [full.toLowerCase(), code]));
      bookMapPromise = Promise.resolve({ reverse: rev });
    }
    return bookMapPromise;
  };

  const fetchBookFile = async (code) => {
    const url = new URL(`${code}.json`, entry.baseURL);
    const r = await fetch(url);
    if (!r.ok) throw new Error(`Failed to load book file ${code}.json`);
    return r.json(); // { book:'Genesis', chapters: { '1': {'1':'text', ...}, ... } }
  };

  return {
    label: entry.label,
    mode: 'per_book',
    getBookByName: async (name) => {
      const { reverse } = await getBookMap();
      const code = reverse.get(name.toLowerCase());
      if (!code) return null;
      const data = await fetchBookFile(code);
      data.__code = code;
      return data;
    },
    renderChapter: (bookData, chapter) => {
      const ch = (bookData.chapters || {})[String(chapter)] || {};
      const verses = Object.keys(ch).map(n => [parseInt(n,10), ch[n]]).sort((a,b)=>a[0]-b[0]);
      return verses.map(([n,txt]) => `<p class="verse"><span class="n">${n}</span>${txt}</p>`).join('\n') || '<p class="muted">No verses in this chapter.</p>';
    },
    renderRange: (bookData, chapter, vStart, vEnd) => {
      const ch = (bookData.chapters || {})[String(chapter)] || {};
      const verses = Object.keys(ch).map(n => [parseInt(n,10), ch[n]]).sort((a,b)=>a[0]-b[0]);
      let out = '';
      for (const [n, txt] of verses) if (n>=vStart && n<=vEnd) out += `<p class="verse"><span class="n">${n}</span>${txt}</p>`;
      return out || '<p class="muted">No verses in range.</p>';
    }
  };
}

function buildExternalLinks(refStr){
  const enc = encodeURIComponent(refStr);
  const blb = `https://www.blueletterbible.org/search/preSearch.cfm?Criteria=${enc}`;
  const bg  = `https://www.biblegateway.com/passage/?search=${enc}`;
  return `<a target="_blank" rel="noopener" href="${blb}">Open in BLB</a> · <a target="_blank" rel="noopener" href="${bg}">Open in BG</a>`;
}

function getParam(name){ return new URL(location.href).searchParams.get(name); }

(async () => {
  const refInput   = document.getElementById('ref-input');
  const form       = document.getElementById('ref-form');
  const passage    = document.getElementById('passage');
  const metaBox    = document.getElementById('passage-meta');
  const links      = document.getElementById('external-links');
  const versionSel = document.getElementById('version');

  const { idxURL, list } = await loadIndex();
  const catalog = buildBibleCatalog(idxURL, list);
  if (catalog.size === 0) { passage.innerHTML = '<p class="muted">No Bibles in index.</p>'; return; }

  // populate versions
  versionSel.innerHTML = '';
  for (const entry of catalog.values()) {
    const opt = document.createElement('option');
    opt.value = entry.id;
    opt.textContent = entry.label;
    versionSel.appendChild(opt);
  }

  const urlVersion = getParam('version');
  const defaultVersion = urlVersion && catalog.has(urlVersion) ? urlVersion : [...catalog.keys()][0];
  versionSel.value = defaultVersion;
  refInput.value = getParam('ref') || 'John 1';

  async function makeRenderer(entry) {
    return entry.kind === 'single' ? loadSingleFile(entry) : loadPerBook(entry);
  }

  let entry = catalog.get(versionSel.value);
  let renderer = await makeRenderer(entry);

  async function refresh(){
    const parsed = parseRef(refInput.value);
    if (!parsed) { passage.innerHTML = '<p class="muted">Invalid reference.</p>'; return; }
    const { book, chapter, verses } = parsed;

    const bookData = renderer.mode === 'single' ? renderer.getBookByName(book) : await renderer.getBookByName(book);
    if (!bookData) { passage.innerHTML = '<p class="muted">Book not found in this version.</p>'; return; }

    passage.innerHTML = verses
      ? renderer.renderRange(bookData, chapter, verses[0], verses[1])
      : renderer.renderChapter(bookData, chapter);

    const refStr = verses
      ? `${book} ${chapter}:${verses[0]}${verses[1]!==verses[0]?`-${verses[1]}`:''}`
      : `${book} ${chapter}`;

    const label = renderer.label || entry.label;
    metaBox.textContent = `${label} · ${refStr}`;
    links.innerHTML = buildExternalLinks(refStr);

    const u = new URL(location.href);
    u.searchParams.set('version', entry.id);
    u.searchParams.set('ref', refStr.replace(/\s+/g,' '));
    history.replaceState({}, '', u.toString());
  }

  form.addEventListener('submit', (e) => { e.preventDefault(); refresh(); });
  versionSel.addEventListener('change', async () => {
    entry = catalog.get(versionSel.value);
    renderer = await makeRenderer(entry);
    refresh();
  });

  await refresh();
})();
