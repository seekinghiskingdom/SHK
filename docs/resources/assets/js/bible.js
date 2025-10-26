import { parseRef } from './ref.js';

// NOTE: this page lives at /docs/resources/bible/index.html
// so ../../data points to /docs/data
async function loadBible(version){
  const idxURL = new URL('../../data/v1/lit/literature_index.json', document.baseURI);

  const idxRes = await fetch(idxURL);
  if (!idxRes.ok) throw new Error('Failed to load literature_index.json');
  const idx = await idxRes.json();

  const meta = idx.find(x => x.id === version);
  if (!meta) throw new Error('Version not found: ' + version);

  // Resolve data_path relative to the index file's directory (robust for relative/absolute)
  const dataURL = new URL(meta.data_path, idxURL);
  const res = await fetch(dataURL);
  if (!res.ok) throw new Error('Failed to load bible data');
  const data = await res.json();
  return { meta, data };
}

function findBook(data, name){
  const i = data.books.findIndex(b => b.name.toLowerCase() === name.toLowerCase());
  return i >= 0 ? { book:data.books[i], index:i } : null;
}

function renderChapter(book, chapter){
  const cIdx = chapter - 1;
  const lines = book.chapters[cIdx] || [];
  return lines.map((txt, i) => `<p class="verse"><span class="n">${i+1}</span>${txt}</p>`).join('\n');
}

function renderRange(book, chapter, vStart, vEnd){
  const cIdx = chapter - 1;
  const lines = book.chapters[cIdx] || [];
  const a = Math.max(1, vStart), b = Math.min(lines.length, vEnd);
  let out = '';
  for (let v=a; v<=b; v++) out += `<p class="verse"><span class="n">${v}</span>${lines[v-1]}</p>`;
  return out || '<p class="muted">No verses in range.</p>';
}

function buildExternalLinks(refStr){
  const enc = encodeURIComponent(refStr);
  const blb = `https://www.blueletterbible.org/search/preSearch.cfm?Criteria=${enc}`;
  const bg = `https://www.biblegateway.com/passage/?search=${enc}`;
  return `<a target="_blank" rel="noopener" href="${blb}">Open in BLB</a> · <a target="_blank" rel="noopener" href="${bg}">Open in BG</a>`;
}

function getParam(name){
  const u = new URL(location.href);
  return u.searchParams.get(name);
}

(async () => {
  const refInput = document.getElementById('ref-input');
  const form = document.getElementById('ref-form');
  const passage = document.getElementById('passage');
  const metaBox = document.getElementById('passage-meta');
  const links = document.getElementById('external-links');
  const versionSel = document.getElementById('version');

  const initialVersion = getParam('version') || 'bible_kjv';
  versionSel.value = initialVersion;
  const initialRef = getParam('ref') || 'John 1';
  refInput.value = initialRef;

  let loaded = await loadBible(initialVersion);

  async function refresh(){
    const ref = parseRef(refInput.value);
    if (!ref) { passage.innerHTML = '<p class="muted">Invalid reference.</p>'; return; }
    const { book, chapter, verses } = ref;

    const found = findBook(loaded.data, book);
    if (!found) { passage.innerHTML = '<p class="muted">Book not found.</p>'; return; }

    let html = '';
    if (!verses) html = renderChapter(found.book, chapter);
    else html = renderRange(found.book, chapter, verses[0], verses[1]);

    passage.innerHTML = html;
    const refStr = verses ? `${book} ${chapter}:${verses[0]}${verses[1]!==verses[0]?`-${verses[1]}`:''}` : `${book} ${chapter}`;
    metaBox.textContent = `${loaded.data.abbr} · ${refStr}`;
    links.innerHTML = buildExternalLinks(refStr);

    const u = new URL(location.href);
    u.searchParams.set('version', versionSel.value);
    u.searchParams.set('ref', refStr.replace(/\s+/g,' '));
    history.replaceState({}, '', u.toString());
  }

  form.addEventListener('submit', (e) => { e.preventDefault(); refresh(); });

  versionSel.addEventListener('change', async () => {
    loaded = await loadBible(versionSel.value);
    refresh();
  });

  await refresh();
})();
