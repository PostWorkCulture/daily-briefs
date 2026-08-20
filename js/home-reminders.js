(() => {
  const DAY = 86400000;
  const BIN_ANCHOR = new Date(2026, 7, 24); // Monday 24 Aug 2026 = recycling
  let birthdays = [];

  const startOfDay = (date = new Date()) => {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
  };

  const dayDiff = (from, to) => Math.round((startOfDay(to) - startOfDay(from)) / DAY);
  const fmtDate = d => d.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function nextBinCollection(today = new Date()) {
    const now = startOfDay(today);
    let weeks = 0;
    if (now > BIN_ANCHOR) weeks = Math.ceil(dayDiff(BIN_ANCHOR, now) / 7);
    const date = new Date(BIN_ANCHOR);
    date.setDate(BIN_ANCHOR.getDate() + weeks * 7);
    const recycling = weeks % 2 === 0;
    return {
      date,
      type: recycling ? 'Recycling' : 'General + garden waste',
      detail: recycling ? 'recycling collection' : 'normal rubbish + garden waste collection',
      recycling
    };
  }

  function lastSundayOfOctober(year) {
    const d = new Date(year, 9, 31);
    d.setDate(31 - d.getDay());
    return d;
  }

  function nextClockChange(today = new Date()) {
    const now = startOfDay(today);
    let date = lastSundayOfOctober(now.getFullYear());
    if (date < now) date = lastSundayOfOctober(now.getFullYear() + 1);
    return date;
  }

  function nextChristmas(today = new Date()) {
    const now = startOfDay(today);
    let date = new Date(now.getFullYear(), 11, 25);
    if (date < now) date = new Date(now.getFullYear() + 1, 11, 25);
    return date;
  }

  function nextOccurrence(item, today = new Date()) {
    const now = startOfDay(today);
    const month = Number(item.month);
    const day = Number(item.day);
    if (!month || !day) return null;
    let date = new Date(now.getFullYear(), month - 1, day);
    if (date < now) date = new Date(now.getFullYear() + 1, month - 1, day);
    return date;
  }

  function sortedBirthdays(today = new Date()) {
    return birthdays
      .map(item => ({ ...item, nextDate: nextOccurrence(item, today) }))
      .filter(item => item.name && item.nextDate)
      .sort((a, b) => a.nextDate - b.nextDate || a.name.localeCompare(b.name));
  }

  function countdownText(days, noun) {
    if (days === 0) return `${noun} today`;
    if (days === 1) return `${noun} tomorrow`;
    return `${days} days to go`;
  }

  function ensureBirthdayTab() {
    const nav = document.getElementById('primaryNav');
    if (nav && !nav.querySelector('[data-view-target="birthdays"]')) {
      const button = document.createElement('button');
      button.dataset.viewTarget = 'birthdays';
      button.innerHTML = '<b>🎂</b>Birthdays';
      nav.appendChild(button);
    }

    const shell = document.querySelector('.app-shell');
    if (shell && !document.getElementById('view-birthdays')) {
      const view = document.createElement('div');
      view.className = 'brief-view';
      view.id = 'view-birthdays';
      view.dataset.view = 'birthdays';
      view.innerHTML = '<section class="panel-block tab-panel birthday-panel"><div class="section-head"><h2>Birthdays</h2><span class="section-kicker">Next up first</span></div><div id="birthdayList" class="birthday-list"></div></section>';
      shell.appendChild(view);
    }

    if (!document.getElementById('birthdayStyles')) {
      const style = document.createElement('style');
      style.id = 'birthdayStyles';
      style.textContent = `
        @media(max-width:899px){#primaryNav{grid-template-columns:repeat(7,minmax(0,1fr))}}
        .birthday-list{display:grid;gap:10px}
        .birthday-card{display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center;padding:16px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(180deg,#2d2244,#151c32)}
        .birthday-avatar{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.08);font-size:22px}
        .birthday-card strong{display:block;font-size:16px}.birthday-card small{display:block;color:var(--muted);margin-top:3px}.birthday-card b{color:#ffd983;font-size:14px;text-align:right}
        .birthday-empty{padding:24px;border:1px dashed var(--line);border-radius:20px;color:var(--muted)}
        .home-reminder-card.birthday{background:linear-gradient(145deg,#352247,#1b2035)}
      `;
      document.head.appendChild(style);
    }
  }

  function renderBirthdayTab() {
    const list = document.getElementById('birthdayList');
    if (!list) return;
    const upcoming = sortedBirthdays();
    if (!upcoming.length) {
      list.innerHTML = '<div class="birthday-empty">No birthdays added yet.</div>';
      return;
    }
    list.innerHTML = upcoming.map(item => {
      const days = dayDiff(new Date(), item.nextDate);
      const age = item.year ? item.nextDate.getFullYear() - Number(item.year) : null;
      return `<article class="birthday-card"><div class="birthday-avatar">🎂</div><div><strong>${esc(item.name)}</strong><small>${fmtDate(item.nextDate)}${age ? ` · turning ${age}` : ''}</small></div><b>${days === 0 ? 'Today' : days === 1 ? 'Tomorrow' : `${days} days`}</b></article>`;
    }).join('');
  }

  function render() {
    const root = document.getElementById('homeReminders');
    if (!root) return;

    const today = startOfDay();
    const bin = nextBinCollection(today);
    const binDays = dayDiff(today, bin.date);
    const clocks = nextClockChange(today);
    const clockDays = dayDiff(today, clocks);
    const christmas = nextChristmas(today);
    const christmasDays = dayDiff(today, christmas);
    const nextBirthday = sortedBirthdays(today)[0] || null;

    const binUrgent = binDays <= 1 ? ' urgent' : '';
    const binHeadline = binDays === 0 ? `${bin.type.toUpperCase()} TODAY` : binDays === 1 ? `${bin.type.toUpperCase()} TOMORROW` : bin.type;
    const birthdayCard = nextBirthday ? (() => {
      const days = dayDiff(today, nextBirthday.nextDate);
      const age = nextBirthday.year ? nextBirthday.nextDate.getFullYear() - Number(nextBirthday.year) : null;
      return `<article class="home-reminder-card birthday"><div class="home-reminder-top"><span class="home-reminder-icon">🎂</span><span>Next birthday</span></div><strong>${esc(nextBirthday.name)}</strong><b>${days === 0 ? 'Birthday today' : days === 1 ? 'Birthday tomorrow' : `${days} days to go`}</b><small>${fmtDate(nextBirthday.nextDate)}${age ? ` · turning ${age}` : ''}</small></article>`;
    })() : '';

    root.innerHTML = `
      <article class="home-reminder-card bin${binUrgent}">
        <div class="home-reminder-top"><span class="home-reminder-icon">♻</span><span>Bin day</span></div>
        <strong>${binHeadline}</strong>
        <b>${countdownText(binDays, 'Collection')}</b>
        <small>${fmtDate(bin.date)} · ${bin.detail}</small>
      </article>
      ${birthdayCard}
      <article class="home-reminder-card clocks">
        <div class="home-reminder-top"><span class="home-reminder-icon">◷</span><span>Clocks change</span></div>
        <strong>Clocks go back</strong>
        <b>${clockDays} days</b>
        <small>${fmtDate(clocks)} · back one hour</small>
      </article>
      <article class="home-reminder-card christmas">
        <div class="home-reminder-top"><span class="home-reminder-icon">✦</span><span>Christmas</span></div>
        <strong>${christmasDays} days</strong>
        <b>to Christmas</b>
        <small>${fmtDate(christmas)}</small>
      </article>`;

    renderBirthdayTab();
  }

  async function loadBirthdays() {
    try {
      const res = await fetch(`data/birthdays.json?cb=${Date.now()}`, { cache: 'no-store' });
      birthdays = res.ok ? await res.json() : [];
      if (!Array.isArray(birthdays)) birthdays = [];
    } catch {
      birthdays = [];
    }
    render();
  }

  ensureBirthdayTab();
  render();
  loadBirthdays();
  window.addEventListener('focus', render);
})();
