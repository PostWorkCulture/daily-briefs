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

  function ordinal(n) {
    const s = ['th', 'st', 'nd', 'rd'], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  }

  function birthdayRowText(item) {
    const d = item.nextDate;
    const dayOrdinal = ordinal(d.getDate());
    const monthName = d.toLocaleDateString('en-GB', { month: 'long' });
    const weekday = d.toLocaleDateString('en-GB', { weekday: 'long' });
    const datePart = `${dayOrdinal} ${monthName} - ${weekday}`;

    let milestone = '';
    if (item.year) {
      const age = d.getFullYear() - Number(item.year);
      if (Number.isFinite(age) && age >= 0) {
        if (item.type === 'anniversary') {
          milestone = ` - ${age} YEARS!`;
        } else {
          milestone = ` - TURNS ${age}!`;
        }
      }
    }
    return `${item.name} - ${datePart}${milestone}`;
  }

  const GIRLY_PALETTES = [
    ['#ff4f93','#ff85b6','#ffc2dc'],
    ['#d63384','#ff66c4','#fce4ec'],
    ['#a855f7','#d946ef','#fae8ff'],
    ['#f43f5e','#fb7185','#ffe4e6'],
    ['#ec4899','#f472b6','#fdf2f8'],
    ['#8b5cf6','#c084fc','#f3e8ff']
  ];

  const BOY_PALETTES = [
    ['#0ea5e9','#38bdf8','#e0f2fe'],
    ['#2563eb','#60a5fa','#dbeafe'],
    ['#10b981','#34d399','#ecfdf5'],
    ['#06b6d4','#22d3ee','#cffafe'],
    ['#16a34a','#4ade80','#dcfce7'],
    ['#0284c7','#38bdf8','#e0f2fe']
  ];

  const GIRLS_SET = new Set(['Sofia','Adina','Aurelia',"Pete's Mum","Sofia's Mum",'Ash & Sophia']);
  const BOYS_SET = new Set(['Pete','Trey','Arthur','Isaac','Oscar',"Sofia's Dad",'Patrick','Maffi']);

  function isGirlName(name='') {
    const clean = (name||'').trim();
    if (GIRLS_SET.has(clean)) return true;
    if (BOYS_SET.has(clean)) return false;
    return /\b(mum|mother|grandma|sister|daughter|girl|she|her|sophia|sofia|adina|aurelia|emma|olivia|charlotte|amelia|isabella|mia|harper|evelyn)\b/i.test(clean);
  }

  function hashStr(str='') {
    let hash = 2166136261;
    for (const ch of str) {
      hash ^= ch.charCodeAt(0);
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    return hash >>> 0;
  }

  function paletteForPerson(name='') {
    const pool = isGirlName(name) ? GIRLY_PALETTES : BOY_PALETTES;
    return pool[hashStr(name) % pool.length];
  }

  function balloonSrcFor(name='') {
    const isGirl = isGirlName(name);
    const variant = (hashStr(name) % 3) + 1;
    return isGirl ? `assets/icons/birthday-balloons-girl-${variant}.webp` : `assets/icons/birthday-balloons-boy-${variant}.webp`;
  }

  function renderBalloonSvg(p, name='', compact=false) {
    const src = balloonSrcFor(name);
    return `<img class="hq-balloon${compact ? ' compact' : ''}" src="${src}" alt="" aria-hidden="true" width="${compact ? 28 : 46}" height="${compact ? 35 : 54}">`;
  }

  function milestoneText(item) {
    if (!item.year) return '';
    const number = item.nextDate.getFullYear() - Number(item.year);
    if (!Number.isFinite(number) || number < 0) return '';
    if (item.type === 'anniversary') return `${number} years`;
    return `turning ${number}`;
  }

  function iconFor(item) {
    if (item.type === 'anniversary') return '♥';
    if (item.type === 'occasion') return '★';
    return renderBalloonSvg(paletteForPerson(item.name), item.name, true);
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
        .birthday-panel .section-head h2,.occasion-month h3{color:var(--text,#fff)!important}
        .birthday-list{display:flex;flex-direction:column;gap:18px}
        .occasion-month{display:flex;flex-direction:column;gap:8px}
        .occasion-month h3{margin:0 0 2px;font-size:15px;color:rgba(255,255,255,0.7)!important}
        .birthday-month-grid{display:grid;grid-template-columns:1fr;gap:10px}
        @media(min-width:700px){.birthday-month-grid{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}}
        .birthday-card{display:flex;align-items:center;gap:14px;padding:12px 16px;border:1px solid transparent!important;border-radius:12px;background:#0b0e0c!important;box-shadow:none!important;color:var(--text,#fff)!important;min-height:86px}
        .birthday-card,.home-reminder-card.birthday{transition:border-color .18s,box-shadow .18s;transform:none!important}
        .birthday-card:hover,.birthday-card:focus-visible,.home-reminder-card.birthday:hover,.home-reminder-card.birthday:focus-visible{border-color:rgba(124,244,106,.72)!important;box-shadow:inset 0 0 0 1px rgba(124,244,106,.12),0 0 0 1px rgba(124,244,106,.52),0 0 22px rgba(124,244,106,.18)!important;transform:none!important;outline:none}
        .birthday-avatar{width:46px;height:54px;display:grid;place-items:center;background:transparent!important;border-radius:0;flex-shrink:0}
        .birthday-copy{display:flex;flex-direction:column;gap:3px;flex:1;min-width:0}
        .birthday-name{display:block;font-size:16px;font-weight:700;color:var(--text,#fff)!important;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .birthday-date{display:block;font-size:13px;font-weight:500;color:rgba(255,255,255,0.75)!important;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .birthday-milestone{display:block;font-size:12.5px;font-weight:600;color:#ffd477!important;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .birthday-card small{display:none}
        .birthday-empty{padding:24px;border:1px dashed var(--signal-line,rgba(255,255,255,0.1));border-radius:12px;color:var(--muted,#8b949e)}
        #homeReminders .home-reminder-card.birthday{background:#0b0e0c!important;border-color:var(--signal-line,rgba(255,255,255,0.08))!important;box-shadow:none!important}
        .home-reminder-card.birthday .home-reminder-top{color:var(--text,#fff)}.home-reminder-card.birthday b{color:var(--text,#fff)}
        .hq-balloon{width:44px;height:52px;object-fit:contain;display:block;overflow:visible}.hq-balloon.compact{width:28px;height:35px}
      `;
      document.head.appendChild(style);
    }
  }

  function occasionCard(item) {
    const d = item.nextDate;
    const dayOrdinal = ordinal(d.getDate());
    const monthName = d.toLocaleDateString('en-GB', { month: 'long' });
    const weekday = d.toLocaleDateString('en-GB', { weekday: 'long' });
    const datePart = `${dayOrdinal} ${monthName} - ${weekday}`;

    let milestone = '';
    if (item.year) {
      const age = d.getFullYear() - Number(item.year);
      if (Number.isFinite(age) && age >= 0) {
        milestone = item.type === 'anniversary' ? `${age} years!` : `Turns ${age}!`;
      }
    }
    const p = paletteForPerson(item.name);
    const balloon = renderBalloonSvg(p, item.name, false);
    return `<article class="birthday-card hq-colour" data-person-name="${esc(item.name)}" tabindex="0"><div class="birthday-avatar hq-balloon-avatar" data-hq-name="${esc(item.name)}">${balloon}</div><div class="birthday-copy"><strong class="birthday-name">${esc(item.name)}</strong><span class="birthday-date">${esc(datePart)}</span>${milestone ? `<span class="birthday-milestone">${esc(milestone)}</span>` : ''}</div></article>`;
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
        html: `<article class="home-reminder-card birthday" data-person-name="${esc(nextOccasion.name)}" tabindex="0"><div class="home-reminder-top"><span class="home-reminder-icon hq-balloon-home" data-hq-name="${esc(nextOccasion.name)}">${iconFor(nextOccasion)}</span><span>Next ${typeLabel(nextOccasion).toLowerCase()}</span></div><strong>${esc(nextOccasion.name)}</strong><b>${days === 0 ? `${typeLabel(nextOccasion)} today` : days === 1 ? `${typeLabel(nextOccasion)} tomorrow` : `${days} days to go`}</b><small>${fmtDate(nextOccasion.nextDate)}${milestone ? ` · ${esc(milestone)}` : ''}</small></article>`
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
