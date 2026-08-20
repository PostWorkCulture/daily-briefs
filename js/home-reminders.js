(() => {
  const DAY = 86400000;
  const BIN_ANCHOR = new Date(2026, 7, 24); // Monday 24 Aug 2026 = recycling

  const startOfDay = (date = new Date()) => {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
  };

  const dayDiff = (from, to) => Math.round((startOfDay(to) - startOfDay(from)) / DAY);
  const fmtDate = d => d.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });

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

  function countdownText(days, noun) {
    if (days === 0) return `${noun} today`;
    if (days === 1) return `${noun} tomorrow`;
    return `${days} days to go`;
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

    const binUrgent = binDays <= 1 ? ' urgent' : '';
    const binHeadline = binDays === 0 ? `${bin.type.toUpperCase()} TODAY` : binDays === 1 ? `${bin.type.toUpperCase()} TOMORROW` : bin.type;

    root.innerHTML = `
      <article class="home-reminder-card bin${binUrgent}">
        <div class="home-reminder-top"><span class="home-reminder-icon">♻</span><span>Bin day</span></div>
        <strong>${binHeadline}</strong>
        <b>${countdownText(binDays, 'Collection')}</b>
        <small>${fmtDate(bin.date)} · ${bin.detail}</small>
      </article>
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
  }

  render();
  window.addEventListener('focus', render);
})();
