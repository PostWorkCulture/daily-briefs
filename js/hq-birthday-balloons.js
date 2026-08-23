(() => {
  const palettes = [
    ['#ff5f8f','#ff9f43','#ffd5df','linear-gradient(145deg,#fff5f8,#f8e7ef 58%,#eef6ff)'],
    ['#4a8dff','#42d4ff','#d8f1ff','linear-gradient(145deg,#f7faff,#edf4ff 58%,#e9f9ff)'],
    ['#d64dff','#ff70cc','#f6d7ff','linear-gradient(145deg,#fff7ff,#f5f0ff 58%,#edf4ff)'],
    ['#00d3a7','#6fff73','#d8ffe7','linear-gradient(145deg,#f6fffb,#eef9f5 58%,#edf8ff)'],
    ['#ffd548','#ff9a2f','#fff0be','linear-gradient(145deg,#fffdf4,#fff7e5 58%,#f3f6ff)'],
    ['#8b6dff','#ff66d1','#eadbff','linear-gradient(145deg,#fbf9ff,#f1edff 58%,#fceefa)'],
    ['#00c4ff','#00efd1','#d7fbff','linear-gradient(145deg,#f5fdff,#e9f8fb 58%,#eef9f5)'],
    ['#ff6d6d','#ff4fa3','#ffe0ea','linear-gradient(145deg,#fff7fa,#fae9f0 58%,#f3effa)']
  ];

  const known = {
    'Ash & Sophia':0,'Adina':1,'Trey':2,'Pete':3,'Sofia':4,'Patrick':5,'Aurelia':6,'Arthur':7,
    'Isaac':1,'Oscar':3,"Pete's Mum":5,"Sofia's Dad":6,"Sofia's Mum":4,'Maffi':0
  };

  function hashName(name='') {
    let hash=2166136261;
    for (const ch of name) {
      hash ^= ch.charCodeAt(0);
      hash = Math.imul(hash,16777619) >>> 0;
    }
    return hash >>> 0;
  }

  function paletteFor(name='') {
    if (Object.prototype.hasOwnProperty.call(known,name)) return palettes[known[name] % palettes.length];
    return palettes[hashName(name) % palettes.length];
  }

  function svgKey(name='', compact=false) {
    return `${compact?'c':'f'}${hashName(name).toString(36)}`;
  }

  function balloonSvg(p, name='', compact=false) {
    const [a,b,accent]=p;
    const id=svgKey(name,compact);
    return `<svg class="hq-balloon${compact?' compact':''}" viewBox="0 0 70 86" aria-hidden="true"><defs><linearGradient id="g-${id}" x1="0" x2="1" y1="0" y2="1"><stop offset="0%" stop-color="${a}"/><stop offset="100%" stop-color="${b}"/></linearGradient><filter id="s-${id}" x="-40%" y="-40%" width="180%" height="220%"><feDropShadow dx="0" dy="5" stdDeviation="6" flood-color="rgba(0,0,0,.34)"/></filter></defs><g filter="url(#s-${id})"><ellipse cx="36" cy="31" rx="22" ry="26" fill="url(#g-${id})" stroke="rgba(255,255,255,.18)" stroke-width="1.3"/><ellipse cx="27" cy="21" rx="7" ry="10" fill="rgba(255,255,255,.36)" transform="rotate(-18 27 21)"/><path d="M36 56C34 60 32 62 29 64c4 0 7 2 10 5 2-3 5-5 9-5-4-2-6-4-8-8Z" fill="${accent}"/><path d="M37 68c3 6 5 9 8 15" fill="none" stroke="${accent}" stroke-width="2.3" stroke-linecap="round"/></g></svg>`;
  }

  function ensureStyles() {
    if (document.getElementById('hqBirthdayBalloonStyles')) return;
    const style=document.createElement('style');
    style.id='hqBirthdayBalloonStyles';
    style.textContent=`
      .birthday-avatar.hq-balloon-avatar{width:72px;height:78px;border-radius:0;background:transparent;overflow:visible;display:grid;place-items:center}
      .hq-balloon{width:68px;height:82px;display:block;overflow:visible}.hq-balloon.compact{width:31px;height:39px}
      .birthday-card.hq-colour{border-color:rgba(178,53,111,.18);box-shadow:0 12px 28px rgba(73,79,111,.10)}
      .home-reminder-card.birthday .home-reminder-icon.hq-balloon-home{width:34px;height:42px;background:transparent;overflow:visible}
      @media(max-width:560px){.birthday-avatar.hq-balloon-avatar{width:58px;height:66px}.hq-balloon{width:56px;height:68px}}
    `;
    document.head.appendChild(style);
  }

  function birthdayCards() {
    const groups=[...document.querySelectorAll('.occasion-group')];
    const birthdayGroup=groups.find(group=>/^birthdays$/i.test(group.querySelector('h3')?.textContent?.trim()||''));
    if (birthdayGroup) return [...birthdayGroup.querySelectorAll('.birthday-card')];
    return [...document.querySelectorAll('.birthday-card')].filter(card=>/birthday/i.test(card.querySelector('small')?.textContent||''));
  }

  function enhanceBirthdayCard(card) {
    const name=card.querySelector('strong')?.textContent?.trim()||'';
    if (!name) return;
    const p=paletteFor(name);
    card.classList.add('hq-colour');
    card.style.background=p[3];
    let avatar=card.querySelector('.birthday-avatar');
    if (!avatar) {
      avatar=document.createElement('div');
      avatar.className='birthday-avatar';
      card.prepend(avatar);
    }
    avatar.classList.add('hq-balloon-avatar');
    if (avatar.dataset.hqName!==name || !avatar.querySelector('.hq-balloon')) {
      avatar.innerHTML=balloonSvg(p,name,false);
      avatar.dataset.hqName=name;
    }
  }

  function enhance() {
    ensureStyles();
    birthdayCards().forEach(enhanceBirthdayCard);

    document.querySelectorAll('.home-reminder-card.birthday').forEach(card=>{
      const name=card.querySelector('strong')?.textContent?.trim()||'';
      if (!name) return;
      const p=paletteFor(name);
      card.style.background=p[3];
      const icon=card.querySelector('.home-reminder-icon');
      if(icon && (icon.dataset.hqName!==name || !icon.querySelector('.hq-balloon'))){
        icon.classList.add('hq-balloon-home');
        icon.innerHTML=balloonSvg(p,name,true);
        icon.dataset.hqName=name;
      }
    });
  }

  let queued=false;
  const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance();});};
  enhance();
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
})();
