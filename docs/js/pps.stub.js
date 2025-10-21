// Minimal stub wiring for placeholders; replace with real logic later.
(async function(){
  const cfg = await (await fetch('data/config.json')).json().catch(()=>({}));
  const $ = (s)=>document.querySelector(s);
  const inputs = $('#inputs'), outputs = $('#outputs'), chapter = $('#chapter'), translation = $('#translation');
  const count = $('#count'), results = $('#results'), feedback = $('#feedback'), attribution = $('#attribution');

  // Config
  feedback.href = cfg.feedback_google_form_url || '#';
  translation.innerHTML = (cfg.display_translations||['KJV']).map(t=>`<option>${t}</option>`).join('');
  chapter.innerHTML = `<option value="All">All</option>` + (cfg.chapters||[]).map(c=>`<option>${c}</option>`).join('');

  // Load tags
  const inputTags = await (await fetch('data/pps/input_tags.json')).json().catch(()=>[]);
  const outputTags = await (await fetch('data/pps/output_tags.json')).json().catch(()=>[]);
  inputs.innerHTML = inputTags.map(t=>`<option value="${t.id}">${t.label}</option>`).join('');
  outputs.innerHTML = outputTags.map(t=>`<option value="${t.id}">${t.label}</option>`).join('');

  // Attribution
  const at = cfg.attribution||{};
  attribution.textContent = `KJV: ${at.KJV||'Public domain in the U.S.'} | WEB: ${at.WEB||'Public Domain'}`;

  // Load dataset and show all
  const data = await (await fetch('data/pps/proverbs.json')).json().catch(()=>({data:[]}));
  const verses = data.data||[];

  function render(list){
    count.textContent = `${list.length} result(s)`;
    results.innerHTML = list.map(rec => {
      const text = (translation.value === 'WEB' ? rec.text_WEB || rec.text_KJV : rec.text_KJV) || '';
      const anchors = (rec.pairs||[]).flatMap(p=>p.anchor_phrases||[]).slice(0,2);
      let h = text;
      if(anchors[0]) h = h.replace(anchors[0], `<mark class="input">${anchors[0]}</mark>`);
      if(anchors[1]) h = h.replace(anchors[1], `<mark class="output">${anchors[1]}</mark>`);
      const pills = (rec.pairs||[]).map(p=>`<span class="pill">${p.input_tag}<span class="arrow">→</span>${p.output_tag}</span>`).join('');
      return `<div class="verse"><div class="ref">${rec.ref}</div><div class="text">${h}</div><div class="pills">${pills}</div></div>`;
    }).join('');
  }

  // Initial render (show all)
  render(verses);

  // Wire search button (placeholder: no real filtering yet)
  document.getElementById('btnSearch').addEventListener('click', () => {
    render(verses);
  });
})();