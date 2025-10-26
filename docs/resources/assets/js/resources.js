import { el } from './utils.js';

// This page is /docs/resources/index.html → ../data points to /docs/data
async function loadNav(){
  const navURL = new URL('../data/resources_nav.json', document.baseURI);
  const res = await fetch(navURL);
  if(!res.ok) throw new Error('Failed to load resources_nav.json');
  return res.json();
}

function iconEmoji(kind){
  return { bible:'📖', books:'📚', pin:'📍', feather:'✒️', help:'❓', chat:'💬' }[kind] || '📦';
}

function tileHTML(item){
  const badge = item.comingSoon ? '<span class="badge">Coming soon</span>' : '';
  const cls = 'tile' + (item.comingSoon ? ' disabled' : '');
  const href = item.comingSoon ? '#' : item.href;
  return `<a class="${cls}" href="${href}">
    <h3>${iconEmoji(item.icon)} ${item.title} ${badge}</h3>
    <p>${item.description||''}</p>
  </a>`;
}

(async () => {
  const container = el('#tiles');
  try {
    const nav = await loadNav();
    container.innerHTML = nav.map(tileHTML).join('\n');
  } catch (e) {
    container.innerHTML = `<div class="card">Error: ${e.message}</div>`;
  }
})();
