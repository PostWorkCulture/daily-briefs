/* TV feedback is private to this browser and profile; programme rules stay strict. */
(() => {
  const base = window.renderWatch;
  let current = [], hidden = {}, activePick, profile;
  const key = () => `dailyBriefTV-v1-${profile}`;
  const identity = item => String(item.showId || item.title?.toLocaleLowerCase() || '');
  function read() { try { return JSON.parse(localStorage.getItem(key()) || '{}') || {}; } catch (_) { return {}; } }
  function save() { try { localStorage.setItem(key(),JSON.stringify(hidden)); return true; } catch (_) { return false; } }
  function controls() {
    let box = document.getElementById('tvPreferences');
    if (!box) {
      box = document.createElement('div'); box.id = 'tvPreferences';
      document.getElementById('watchStrip').after(box);
      box.innerHTML = '<details><summary>Hidden TV picks <span></span></summary><p>These choices stay on this device for this profile. New picks must still pass your interests and freshness rules.</p><div class="tv-hidden-list"></div></details><p class="tv-feedback-status" role="status"></p>';
      box.addEventListener('click', event => {
        const button = event.target.closest('[data-restore-tv]');
        if (!button) return;
        delete hidden[button.dataset.restoreTv]; save(); draw();
        box.querySelector('summary').focus();
        box.querySelector('.tv-feedback-status').textContent = 'Preference removed. This programme can appear again when it is current.';
      });
    }
    return box;
  }
  function dialog() {
    let el = document.getElementById('tvFeedbackDialog');
    if (el) return el;
    el = document.createElement('dialog'); el.id = 'tvFeedbackDialog'; el.setAttribute('aria-labelledby','tvFeedbackTitle');
    el.innerHTML = '<form method="dialog"><h3 id="tvFeedbackTitle"></h3><p class="tv-programme-summary"></p><p>Hide this programme from your future picks on this device.</p><button type="button" data-tv-reason="Already watched">Already watched</button><button type="button" data-tv-reason="Not interested">Not interested</button><button value="cancel">Keep this pick</button></form>';
    document.body.append(el);
    el.addEventListener('click', event => {
      const button = event.target.closest('[data-tv-reason]');
      if (!button || !activePick) return;
      hidden[identity(activePick)] = {title:activePick.title,reason:button.dataset.tvReason,date:new Date().toISOString()};
      const stored = save(); el.close(); draw();
      const box = controls(); box.querySelector('summary').focus({preventScroll:true});
      box.querySelector('.tv-feedback-status').textContent = stored ? 'Preference saved. Hidden picks are replaced when another qualifying programme is available.' : 'Hidden for this visit. Browser storage is unavailable.';
    });
    return el;
  }
  function draw() {
    const seen = new Set();
    const visible = [...current, ...(state.data?.watchAlternatives || [])].filter(item => {
      const id = identity(item);
      if (hidden[id] || seen.has(id)) return false;
      seen.add(id); return true;
    }).slice(0,5);
    base(visible);
    document.querySelectorAll('#watchStrip .watch-card').forEach(card => {
      const item = visible.find(pick => pick.title === card.querySelector('b')?.textContent);
      if (!item) return;
      const article = document.createElement('article');
      for (const attr of card.attributes) if (!['href','target','rel'].includes(attr.name)) article.setAttribute(attr.name,attr.value);
      const link = document.createElement('a'); link.className = 'watch-destination'; link.href = item.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      while (card.firstChild) link.append(card.firstChild);
      const button = document.createElement('button'); button.type = 'button'; button.className = 'watch-feedback-toggle'; button.textContent = 'Hide'; button.setAttribute('aria-label',`Hide ${item.title}`);
      button.addEventListener('click',() => { activePick=item; const modal=dialog(); modal.querySelector('h3').textContent=item.title; modal.querySelector('.tv-programme-summary').textContent=item.summary || ''; modal.showModal(); });
      article.append(link,button); card.replaceWith(article);
    });
    if (!visible.length) document.getElementById('watchStrip').innerHTML = '<p class="empty">You’ve hidden today’s qualifying picks. Restore one below or check the next edition.</p>';
    const box = controls(), list = box.querySelector('.tv-hidden-list'); list.replaceChildren();
    box.querySelector('summary span').textContent = `(${Object.keys(hidden).length})`;
    for (const [id,value] of Object.entries(hidden)) {
      const row = document.createElement('div'), label = document.createElement('span'), button = document.createElement('button');
      label.textContent = `${value.title} · ${value.reason}`; button.textContent = 'Restore'; button.dataset.restoreTv=id; button.type='button'; button.setAttribute('aria-label',`Restore ${value.title}`); row.append(label,button); list.append(row);
    }
  }
  window.renderWatch = items => { document.getElementById('tvFeedbackDialog')?.close(); profile=state.profile; current=items || []; hidden=read(); draw(); };
  if (state.data) window.renderWatch(state.data.watch);
})();
