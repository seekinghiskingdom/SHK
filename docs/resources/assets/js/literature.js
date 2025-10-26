// This page is /docs/resources/literature/index.html → ../../data points to /docs/data
async function loadIndex(){
  const idxURL = new URL('../../data/v1/lit/literature_index.json', document.baseURI);
  const r = await fetch(idxURL);
  if (!r.ok) throw new Error('Failed to load literature_index.json');
  return r.json();
}
function groupByType(items){
  return items.reduce((a,it)=>{ (a[it.type] ||= []).push(it); return a; },{});
}
function makeItem(it){
  const url = it.type === 'Bible'
    ? `../bible/?version=${encodeURIComponent(it.id)}&ref=John%201`
    : '#';
  return `<li><a href="${url}">${it.title}</a> <span class="muted small">(${(it.lang||'').toUpperCase()||'—'})</span></li>`;
}
(async()=>{
  const root = document.querySelector('#lit-groups');
  try{
    const data = await loadIndex();
    const groups = groupByType(data);
    let html='';
    for(const [type,items] of Object.entries(groups)){
      html += `<div class="group"><h2>${type}</h2><ul class="list">${items.map(makeItem).join('')}</ul></div>`;
    }
    root.innerHTML = html || '<p class="muted">No literature found.</p>';
  }catch(e){
    root.innerHTML = `<p class="muted">Error: ${e.message}</p>`;
  }
})();
