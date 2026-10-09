(() => {
  const girlyPalettes = [
    ['#ff4f93','#ff85b6','#ffc2dc'], // Soft hot pink
    ['#d63384','#ff66c4','#fce4ec'], // Magenta / rose
    ['#a855f7','#d946ef','#fae8ff'], // Purple / violet
    ['#f43f5e','#fb7185','#ffe4e6'], // Blush rose
    ['#ec4899','#f472b6','#fdf2f8'], // Candy pink
    ['#8b5cf6','#c084fc','#f3e8ff']  // Lavender
  ];

  const boyPalettes = [
    ['#0ea5e9','#38bdf8','#e0f2fe'], // Sky blue
    ['#2563eb','#60a5fa','#dbeafe'], // Royal blue
    ['#10b981','#34d399','#ecfdf5'], // Emerald green
    ['#06b6d4','#22d3ee','#cffafe'], // Cyan / turquoise
    ['#16a34a','#4ade80','#dcfce7'], // Bright leaf green
    ['#0284c7','#38bdf8','#e0f2fe']  // Deep azure
  ];

  const GIRLS = new Set([
    'Sofia',
    'Adina',
    'Aurelia',
    "Pete's Mum",
    "Sofia's Mum",
    'Ash & Sophia'
  ]);

  const BOYS = new Set([
    'Pete',
    'Trey',
    'Arthur',
    'Isaac',
    'Oscar',
    "Sofia's Dad",
    'Patrick',
    'Maffi'
  ]);

  function isGirl(name='') {
    const clean = (name||'').trim();
    if (GIRLS.has(clean)) return true;
    if (BOYS.has(clean)) return false;
    return /\b(mum|mother|grandma|sister|daughter|girl|she|her|sophia|sofia|adina|aurelia|emma|olivia|charlotte|amelia|isabella|mia|harper|evelyn)\b/i.test(clean);
  }

  function hashName(name='') {
    let hash=2166136261;
    for (const ch of name) {
      hash ^= ch.charCodeAt(0);
      hash = Math.imul(hash,16777619) >>> 0;
    }
    return hash >>> 0;
  }

  function paletteFor(name='') {
    const pool = isGirl(name) ? girlyPalettes : boyPalettes;
    return pool[hashName(name) % pool.length];
  }

  function svgKey(name='', compact=false) {
    return `${compact?'c':'f'}${hashName(name).toString(36)}`;
  }

  function balloonSrcFor(name='') {
    const isGirlUser = isGirl(name);
    const variant = (hashName(name) % 3) + 1;
    return isGirlUser ? `assets/icons/birthday-balloons-girl-${variant}.webp` : `assets/icons/birthday-balloons-boy-${variant}.webp`;
  }

  function balloonSvg(p, name='', compact=false) {
    const src = balloonSrcFor(name);
    return `<img class="hq-balloon${compact?' compact':''}" src="${src}" alt="" aria-hidden="true" width="${compact?28:46}" height="${compact?35:54}">`;
  }

  function ensureStyles() {
    if (document.getElementById('hqBirthdayBalloonStyles')) return;
    const style=document.createElement('style');
    style.id='hqBirthdayBalloonStyles';
    style.textContent=`
      .birthday-avatar.hq-balloon-avatar{width:46px;height:54px;border-radius:0;background:transparent!important;overflow:visible;display:grid;place-items:center;flex-shrink:0}
      .hq-balloon{width:44px;height:52px;object-fit:contain;display:block;overflow:visible}.hq-balloon.compact{width:28px;height:35px}
      .home-reminder-card.birthday .home-reminder-icon.hq-balloon-home{width:30px;height:36px;background:transparent!important;overflow:visible;display:grid;place-items:center}
    `;
    document.head.appendChild(style);
  }

  function extractName(card) {
    if (card.dataset.personName) return card.dataset.personName;
    const strongText = card.querySelector('strong')?.textContent?.trim() || '';
    if (strongText) return strongText.split(/\s*-\s*/)[0].trim();
    return '';
  }

  function birthdayCards() {
    return [...document.querySelectorAll('.birthday-card')];
  }

  function enhanceBirthdayCard(card) {
    const name = extractName(card);
    if (!name) return;
    const p = paletteFor(name);
    card.classList.add('hq-colour');
    let avatar = card.querySelector('.birthday-avatar');
    if (!avatar) {
      avatar = document.createElement('div');
      avatar.className = 'birthday-avatar';
      card.prepend(avatar);
    }
    avatar.classList.add('hq-balloon-avatar');
    if (avatar.dataset.hqName !== name || !avatar.querySelector('.hq-balloon')) {
      avatar.innerHTML = balloonSvg(p, name, false);
      avatar.dataset.hqName = name;
    }
  }

  function enhance() {
    ensureStyles();
    birthdayCards().forEach(enhanceBirthdayCard);

    document.querySelectorAll('.home-reminder-card.birthday').forEach(card=>{
      const name = extractName(card);
      if (!name) return;
      const p = paletteFor(name);
      const icon = card.querySelector('.home-reminder-icon');
      if (icon && (icon.dataset.hqName !== name || !icon.querySelector('.hq-balloon'))) {
        icon.classList.add('hq-balloon-home');
        icon.innerHTML = balloonSvg(p, name, true);
        icon.dataset.hqName = name;
      }
    });
  }

  window.birthdayBalloonSvg = balloonSvg;
  window.birthdayPaletteFor = paletteFor;

  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      enhance();
    });
  };
  enhance();
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
