(() => {
  const DAY = 86400000;
  const BIN_ANCHOR = new Date(2026, 7, 24); // Monday 24 Aug 2026 = recycling
  const REMINDER_ART = {
    clocks: 'assets/icons/clocks-card.webp',
    halloween: 'assets/icons/halloween-card.webp',
    normalBins: 'assets/icons/normal-bins-card.webp',
    recycling: 'assets/icons/recycling-card.webp',
    christmas: 'assets/icons/xmas-card.webp'
  };
  let occasions = [];

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
      type: recycling ? 'Recycling' : 'General & garden waste',
      detail: recycling ? 'Recycling collection' : 'Put out both bins',
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

  function midsummerEve(year) {
    const d = new Date(year, 5, 19);
    d.setDate(19 + ((5 - d.getDay() + 7) % 7)); // Friday between 19 and 25 June
    return d;
  }

  function festiveDatesForYear(year) {
    return [
      { name: "New Year's Day", date: new Date(year, 0, 1), icon: '✦', detail: 'New year', theme: 'new-year' },
      { name: 'Swedish Midsummer', date: midsummerEve(year), icon: '☀', detail: 'Midsummer Eve', theme: 'midsummer' },
      { name: 'Halloween', date: new Date(year, 9, 31), icon: '◐', detail: 'Halloween', theme: 'halloween' },
      { name: 'Bonfire Night', date: new Date(year, 10, 5), icon: '✹', detail: 'Guy Fawkes Night', theme: 'bonfire' },
      { name: 'Christmas Day', date: new Date(year, 11, 25), icon: '✦', detail: 'Christmas', theme: 'christmas' }
    ];
  }

  function nextFestiveDate(today = new Date()) {
    const now = startOfDay(today);
    return [
      ...festiveDatesForYear(now.getFullYear()),
      ...festiveDatesForYear(now.getFullYear() + 1)
    ].filter(item => item.date >= now).sort((a, b) => a.date - b.date)[0];
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

  function normaliseType(item) {
    const type = String(item.type || 'birthday').toLowerCase();
    return ['birthday', 'anniversary', 'occasion'].includes(type) ? type : 'occasion';
  }

  function sortedOccasions(today = new Date()) {
    const seen = new Set();
    return occasions
      .map(item => ({ ...item, type: normaliseType(item), nextDate: nextOccurrence(item, today) }))
      .filter(item => item.name && item.nextDate)
      .filter(item => {
        const key = `${item.type}|${item.name.trim().toLowerCase()}|${item.month}|${item.day}|${item.year || ''}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((a, b) => a.nextDate - b.nextDate || a.name.localeCompare(b.name));
  }

  function milestoneText(item) {
    if (!item.year) return '';
    const number = item.nextDate.getFullYear() - Number(item.year);
    if (!Number.isFinite(number) || number < 0) return '';
    if (item.type === 'birthday') return `turning ${number}`;
    if (item.type === 'anniversary') return `${number} years`;
    return `${number} years`;
  }

  function iconFor(item) {
    if (item.type === 'anniversary') return '♥';
    if (item.type === 'occasion') return '★';
    return '🎂';
  }

  function typeLabel(item) {
    if (item.type === 'anniversary') return 'Anniversary';
    if (item.type === 'occasion') return item.label || 'Occasion';
    return 'Birthday';
  }

  function countdownText(days, noun) {
    if (days === 0) return `${noun} today`;
    if (days === 1) return `${noun} tomorrow`;
    return `${days} days to go`;
  }

  function reminderArtwork(src) {
    return src
      ? `<img class="home-reminder-art" src="${src}" alt="" aria-hidden="true" decoding="async">`
      : '';
  }

  function reminderCopy(content) {
    return `<div class="home-reminder-copy">${content}</div>`;
  }

  function ensureBirthdayTab() {
    const nav = document.getElementById('primaryNav');
    if (nav && !nav.querySelector('[data-view-target="birthdays"]')) {
      const button = document.createElement('button');
      button.dataset.viewTarget = 'birthdays';
      button.innerHTML = '<b class="birthday-nav-mark" aria-hidden="true"><svg class="nav-balloon" viewBox="0 0 24 28"><path d="M12 2C7.6 2 4 5.7 4 10.3c0 5.8 5.2 10.2 8 11.7 2.8-1.5 8-5.9 8-11.7C20 5.7 16.4 2 12 2Z"/><path d="m10.2 22 1.8 2 1.8-2M12 24c2 1.1 2.5 2.4 1.2 3"/></svg></b>Birthday';
      nav.appendChild(button);
    }

    const shell = document.querySelector('.app-shell');
    if (shell && !document.getElementById('view-birthdays')) {
      const view = document.createElement('div');
      view.className = 'brief-view';
      view.id = 'view-birthdays';
      view.dataset.view = 'birthdays';
      view.innerHTML = '<section class="panel-block tab-panel birthday-panel"><div class="section-head"><h2>Birthday</h2></div><div id="birthdayList" class="birthday-list"></div></section>';
      shell.appendChild(view);
    }

    if (!document.getElementById('birthdayStyles')) {
      const style = document.createElement('style');
      style.id = 'birthdayStyles';
      style.textContent = `
        @media(max-width:899px){#primaryNav{grid-template-columns:repeat(7,minmax(0,1fr))}}
        .birthday-panel .section-head h2,.occasion-month h3{color:#142a3d!important}.birthday-list{display:grid;gap:22px}.occasion-month{display:grid;gap:10px}.occasion-month h3{margin:0 0 2px;font-size:15px}.birthday-month-grid{display:grid;grid-template-columns:1fr;gap:10px}
        .birthday-card{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:14px;align-items:center;padding:16px;border:1px solid rgba(217,0,119,.48);border-radius:20px;background:#fff!important;box-shadow:0 12px 28px rgba(73,79,111,.10)}
        .birthday-card,.home-reminder-card.birthday{transition:border-color .18s,box-shadow .18s;transform:none!important}
        .birthday-card:hover,.birthday-card:focus-visible,.home-reminder-card.birthday:hover,.home-reminder-card.birthday:focus-visible{border-color:rgba(0,124,184,.88)!important;box-shadow:inset 0 0 0 2px rgba(39,147,199,.16),0 0 0 3px rgba(255,255,255,.45),0 0 20px rgba(23,128,183,.40),0 0 38px rgba(57,135,255,.22)!important;transform:none!important;outline:none}
        .birthday-avatar{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;background:rgba(217,0,119,.08);font-size:22px}
        .birthday-card strong{display:block;font-size:16px}.birthday-card small{display:block;color:#142a3d;margin-top:3px}.birthday-card b{color:#8f004f;font-size:14px;text-align:right}
        .birthday-empty{padding:24px;border:1px dashed var(--line);border-radius:20px;color:var(--muted)}
        #homeReminders .home-reminder-card.birthday{background:#ffc1dc!important;border-color:rgba(217,0,119,.48);box-shadow:0 12px 28px rgba(73,79,111,.10)}
        .home-reminder-card.birthday .home-reminder-top,.home-reminder-card.birthday small{color:#142a3d}.home-reminder-card.birthday b{color:#142a3d}
        @media(min-width:700px){.birthday-month-grid{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}}
      `;
      document.head.appendChild(style);
    }
  }

  function occasionCard(item) {
    const days = dayDiff(new Date(), item.nextDate);
    const milestone = milestoneText(item);
    return `<article class="birthday-card" tabindex="0"><div class="birthday-avatar">${iconFor(item)}</div><div><strong>${esc(item.name)}</strong><small>${typeLabel(item)} · ${fmtDate(item.nextDate)}${milestone ? ` · ${esc(milestone)}` : ''}</small></div><b>${days === 0 ? 'Today' : days === 1 ? 'Tomorrow' : `${days} days`}</b></article>`;
  }

  function renderBirthdayTab() {
    const list = document.getElementById('birthdayList');
    if (!list) return;
    const upcoming = sortedOccasions();
    if (!upcoming.length) {
      list.innerHTML = '<div class="birthday-empty">No birthdays or anniversaries added yet.</div>';
      return;
    }
    const months = new Map();
    upcoming.forEach(item => {
      const key = `${item.nextDate.getFullYear()}-${item.nextDate.getMonth()}`;
      if (!months.has(key)) months.set(key, []);
      months.get(key).push(item);
    });
    list.innerHTML = [...months.values()].map(items => {
      const first = items[0].nextDate;
      const month = first.toLocaleDateString('en-GB', { month: 'long' });
      return `<section class="occasion-group occasion-month"><h3>${esc(month)}</h3><div class="birthday-month-grid">${items.map(occasionCard).join('')}</div></section>`;
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
    const festive = nextFestiveDate(today);
    const festiveDays = dayDiff(today, festive.date);
    const nextOccasion = sortedOccasions(today)[0] || null;

    const binUrgent = binDays <= 1 ? ' urgent' : '';
    const binHeadline = binDays === 0 ? `${bin.type.toUpperCase()} TODAY` : binDays === 1 ? `${bin.type.toUpperCase()} TOMORROW` : bin.type;
    const binArt = bin.recycling ? REMINDER_ART.recycling : REMINDER_ART.normalBins;
    const festiveArt = REMINDER_ART[festive.theme] || '';

    const cards = [
      {
        date: bin.date,
        html: `<article class="home-reminder-card bin has-art${binUrgent}">${reminderArtwork(binArt)}${reminderCopy(`<div class="home-reminder-top"><span class="home-reminder-icon">♻</span><span>Bin day</span></div><strong>${binHeadline}</strong><b>${countdownText(binDays, 'Collection')}</b><small>${fmtDate(bin.date)} · ${bin.detail}</small>`)}</article>`
      },
      {
        date: clocks,
        html: `<article class="home-reminder-card clocks has-art">${reminderArtwork(REMINDER_ART.clocks)}${reminderCopy(`<div class="home-reminder-top"><span class="home-reminder-icon">◷</span><span>Clocks change</span></div><strong>Clocks go back</strong><b>${clockDays === 0 ? 'Today' : clockDays === 1 ? 'Tomorrow' : `${clockDays} days to go`}</b><small>${fmtDate(clocks)} · back one hour</small>`)}</article>`
      },
      {
        date: festive.date,
        html: `<article class="home-reminder-card festive ${festive.theme}${festiveArt ? ' has-art' : ''}">${reminderArtwork(festiveArt)}${reminderCopy(`<div class="home-reminder-top"><span class="home-reminder-icon">${festive.icon}</span><span>Festive</span></div><strong>${festive.name}</strong><b>${festiveDays === 0 ? 'Today' : festiveDays === 1 ? 'Tomorrow' : `${festiveDays} days to go`}</b><small>${fmtDate(festive.date)} · ${festive.detail}</small>`)}</article>`
      }
    ];

    if (nextOccasion) {
      const days = dayDiff(today, nextOccasion.nextDate);
      const milestone = milestoneText(nextOccasion);
      cards.push({
        date: nextOccasion.nextDate,
        html: `<article class="home-reminder-card birthday" tabindex="0"><div class="home-reminder-top"><span class="home-reminder-icon">${iconFor(nextOccasion)}</span><span>Next ${typeLabel(nextOccasion).toLowerCase()}</span></div><strong>${esc(nextOccasion.name)}</strong><b>${days === 0 ? `${typeLabel(nextOccasion)} today` : days === 1 ? `${typeLabel(nextOccasion)} tomorrow` : `${days} days to go`}</b><small>${fmtDate(nextOccasion.nextDate)}${milestone ? ` · ${esc(milestone)}` : ''}</small></article>`
      });
    }

    root.innerHTML = cards.sort((a, b) => a.date - b.date).map(card => card.html).join('');
    renderBirthdayTab();
  }

  async function loadOccasions() {
    try {
      const res = await fetch(`data/occasions.json?cb=${Date.now()}`, { cache: 'no-store' });
      occasions = res.ok ? await res.json() : [];
      if (!Array.isArray(occasions)) occasions = [];
    } catch {
      occasions = [];
    }
    render();
  }

  ensureBirthdayTab();
  render();
  loadOccasions();
  window.addEventListener('focus', render);
})();
