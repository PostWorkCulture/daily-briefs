/* Original activities and device-local favourites. No account or child tracking. */
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const today = () => new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/London', year:'numeric', month:'2-digit', day:'2-digit'}).format(new Date());
  const seasonNow = () => ['winter','winter','spring','spring','spring','summer','summer','summer','autumn','autumn','autumn','winter'][new Date().getMonth()];
  const categories = {learn:'Discover', play:'Imagine', make:'Create', move:'Get moving'};
  let profile, saved, host, reference, oldSeasons;
  const activities = () => window.DIDA_ACTIVITIES || [];
  const key = () => `dailyBriefDida-v1-${profile}`;
  function read() {
    let value = {};
    try { value = JSON.parse(localStorage.getItem(key()) || '{}') || {}; } catch (_) {}
    const ids = new Set(activities().map(a => a.id));
    return {date:value.date, featured:value.featured, season:value.season || seasonNow(),
      favourites:(Array.isArray(value.favourites) ? value.favourites : []).filter(id => ids.has(id)),
      tried:(Array.isArray(value.tried) ? value.tried : []).filter(id => ids.has(id)),
      recent:(Array.isArray(value.recent) ? value.recent : []).filter(id => ids.has(id)).slice(-12)};
  }
  function persist() { try { localStorage.setItem(key(), JSON.stringify(saved)); return true; } catch (_) { return false; } }
  function pick() {
    const pool = activities().filter(a => a.season === 'all' && a.id !== saved.featured);
    const fresh = pool.filter(a => !saved.recent.includes(a.id));
    const choices = fresh.length ? fresh : pool;
    const seed = [...today()].reduce((n,c) => n + c.charCodeAt(0), 0) + saved.recent.length;
    const selected = choices[seed % choices.length];
    if (selected) { saved.featured = selected.id; saved.recent = [...saved.recent.filter(id => id !== selected.id), selected.id].slice(-12); }
    saved.date = today();
  }
  function buttons(a) {
    return `<div class="dida-actions"><button type="button" data-dida-action="save" data-id="${a.id}" aria-pressed="${saved.favourites.includes(a.id)}">${saved.favourites.includes(a.id) ? 'Saved favourite' : 'Save favourite'}</button><button type="button" data-dida-action="tried" data-id="${a.id}" aria-pressed="${saved.tried.includes(a.id)}">${saved.tried.includes(a.id) ? '★ We tried it' : 'We tried it'}</button></div>`;
  }
  function card(a, featured = false) {
    return `<article class="dida-activity${featured ? ' dida-featured' : ''}" data-activity-id="${a.id}"><div class="dida-activity-copy"><span class="dida-kicker">${featured ? 'Today’s little adventure · ' : ''}${categories[a.category] || 'Play'}</span><h4>${esc(a.title)}</h4><div class="dida-meta"><span>${a.minutes} minutes</span><span>${esc(a.setting)}</span></div><dl class="dida-kit"><div><dt>You’ll need</dt><dd>${esc(a.materials)}</dd></div><div><dt>Grown-up role</dt><dd>${esc(a.adultHelp)}</dd></div></dl><ol class="dida-steps">${a.steps.map(step => `<li>${esc(step)}</li>`).join('')}</ol><p class="dida-challenge"><b>Try a twist</b> ${esc(a.challenge)}</p><p class="dida-inspiration">${a.sourceUrl ? `<a href="${esc(a.sourceUrl)}" target="_blank" rel="noopener noreferrer">${esc(a.sourceName)}</a>` : esc(a.sourceName || 'Original family activity')}</p>${buttons(a)}</div></article>`;
  }
  function render(focus) {
    const list = activities(), featured = list.find(a => a.id === saved.featured) || list[0];
    if (!featured) return;
    const others = list.filter(a => a.season === 'all' && a.id !== featured.id);
    const alternatives = [];
    for (const a of [...others.filter(a => a.category !== featured.category && !saved.recent.includes(a.id)), ...others]) {
      if (!alternatives.some(x => x.id === a.id) && (!alternatives.length || alternatives[0].category !== a.category)) alternatives.push(a);
      if (alternatives.length === 2) break;
    }
    const seasonal = list.filter(a => a.season === saved.season);
    const labels = {autumn:'Autumn & Halloween',winter:'Winter',spring:'Spring',summer:'Summer',christmas:'Christmas',birthday:'Birthday'};
    const favourites = list.filter(a => saved.favourites.includes(a.id));
    host.innerHTML = `<section class="dida-zone dida-play-zone" id="dida-play"><header class="dida-zone-head"><h3>Play together</h3></header><p class="dida-intro">A little time together. A big idea to try.</p><div class="dida-feature-layout"><img class="dida-scene" src="assets/dida/play-together.webp" alt="A colourful cardboard rocket and friendly clay creature in a miniature invention workshop" width="1536" height="1024">${card(featured,true)}</div><div class="dida-swap-row"><button type="button" class="dida-primary" data-dida-action="pick">Pick another adventure</button><p class="dida-stickers">${saved.tried.length ? `★ ${saved.tried.length} adventure${saved.tried.length === 1 ? '' : 's'} tried together` : 'Your first adventure sticker is waiting.'}</p></div><h4 class="dida-subhead">Two more ways to play</h4><div class="dida-activity-grid">${alternatives.map(a => card(a)).join('')}</div><details class="dida-favourites"><summary>Saved favourites <span>${favourites.length}</span></summary>${favourites.length ? `<div class="dida-activity-grid">${favourites.map(a => card(a)).join('')}</div>` : '<p>Save an idea you’d like to come back to.</p>'}</details><p class="dida-device-note">Favourites and stickers stay on this device, separately for each profile.</p></section><section class="dida-zone dida-seasonal-zone" id="dida-seasonal"><header class="dida-zone-head"><h3>Explore this season</h3></header><div class="dida-season-banner"><img class="dida-scene" src="assets/dida/explore-this-season.webp" alt="An autumn discovery trail with colourful leaves, a magnifying glass and a friendly clay squirrel" width="1536" height="1024" loading="lazy"><div><p class="dida-intro">Small discoveries, seasonal makes and things to celebrate.</p><label class="dida-season-label" for="dida-season-choice">Choose an adventure season</label><select id="dida-season-choice">${Object.entries(labels).map(([id,label]) => `<option value="${id}"${saved.season === id ? ' selected' : ''}>${label}</option>`).join('')}</select></div></div><div class="dida-activity-grid">${seasonal.map(a => card(a)).join('')}</div><details class="dida-season-inspiration"><summary>More seasonal inspiration</summary>${oldSeasons}</details></section><section class="dida-zone dida-library-zone" id="dida-library"><header class="dida-zone-head"><h3>Parent guide</h3></header><div class="dida-parent-banner"><img class="dida-scene" src="assets/dida/parent-guide.webp" alt="A warm reading lamp, open book and emerald toolbox in a miniature storybook scene" width="1536" height="1024" loading="lazy"><p class="dida-intro">A little background when you need it. Open any guide below.</p></div>${reference}</section><p id="dida-feedback" class="dida-feedback" role="status" aria-live="polite"></p>`;
    if (focus) host.querySelector(focus)?.focus({preventScroll:true});
  }
  window.mountDidaActivities = (nextProfile, referenceHTML, seasonalHTML) => {
    const nextHost = document.getElementById('didaContent');
    if (host === nextHost && profile === nextProfile && saved.date === today() && host.querySelector('.dida-activity')) return;
    host = nextHost; profile = nextProfile; reference = referenceHTML; oldSeasons = seasonalHTML; saved = read();
    if (saved.date !== today() || !activities().some(a => a.id === saved.featured)) { pick(); persist(); }
    render();
    if (host.dataset.didaBound) return;
    host.dataset.didaBound = 'true';
    host.addEventListener('change', event => {
      if (event.target.id !== 'dida-season-choice') return;
      const open = [...host.querySelectorAll('details')].map(el => el.open);
      saved.season = event.target.value; persist(); render('#dida-season-choice');
      host.querySelectorAll('details').forEach((el,index) => { el.open = Boolean(open[index]); });
    });
    host.addEventListener('click', event => {
      const button = event.target.closest('[data-dida-action]');
      if (!button) return;
      const {didaAction:action,id} = button.dataset;
      const open = [...host.querySelectorAll('details')].map(el => el.open);
      let message;
      if (action === 'pick') { pick(); message = 'A fresh adventure is ready.'; }
      else {
        const field = action === 'save' ? 'favourites' : 'tried';
        const exists = saved[field].includes(id);
        saved[field] = exists ? saved[field].filter(x => x !== id) : [...saved[field], id];
        message = action === 'save' ? (exists ? 'Removed from favourites.' : 'Saved for another day.') : (exists ? 'Adventure sticker removed.' : 'Adventure sticker earned. Lovely teamwork!');
      }
      const stored = persist();
      render();
      host.querySelectorAll('details').forEach((el,index) => { el.open = Boolean(open[index]); });
      (host.querySelector(`[data-dida-action="${action}"]${id ? `[data-id="${id}"]` : ''}`) || host.querySelector('.dida-favourites summary')).focus({preventScroll:true});
      host.querySelector('#dida-feedback').textContent = message + (stored ? '' : ' Storage is unavailable, so this will last only while the page is open.');
      const status = host.querySelector('#dida-feedback');
      setTimeout(() => { if (status.isConnected) status.textContent = ''; }, 5500);
    });
  };
})();
