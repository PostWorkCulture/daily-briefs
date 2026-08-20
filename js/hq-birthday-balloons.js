(() => {
  const palettes = [
    ['#ff5f8f','#ff9f43','#ffd5df','linear-gradient(180deg,rgba(114,33,55,.95),rgba(38,16,23,.97))'],
    ['#4a8dff','#42d4ff','#d8f1ff','linear-gradient(180deg,rgba(25,53,106,.95),rgba(14,23,43,.97))'],
    ['#d64dff','#ff70cc','#f6d7ff','linear-gradient(180deg,rgba(87,31,104,.95),rgba(24,14,40,.97))'],
    ['#00d3a7','#6fff73','#d8ffe7','linear-gradient(180deg,rgba(15,82,71,.95),rgba(13,31,33,.97))'],
    ['#ffd548','#ff9a2f','#fff0be','linear-gradient(180deg,rgba(111,72,14,.95),rgba(43,24,11,.97))'],
    ['#8b6dff','#ff66d1','#eadbff','linear-gradient(180deg,rgba(60,39,110,.95),rgba(24,18,45,.97))'],
    ['#00c4ff','#00efd1','#d7fbff','linear-gradient(180deg,rgba(16,78,100,.95),rgba(11,29,37,.97))'],
    ['#ff6d6d','#ff4fa3','#ffe0ea','linear-gradient(180deg,rgba(109,34,70,.95),rgba(40,15,32,.97))']
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

  function navSvg() {
    return `<svg class="hq-nav-balloons" viewBox="0 0 72 48" aria-hidden="true"><defs><linearGradient id="nb1" x1="0" x2="1"><stop stop-color="#6ed7ff"/><stop offset="1" stop-color="#5484ff"/></linearGradient><linearGradient id="nb2" x1="0" x2="1"><stop stop-color="#ff7cc8"/><stop offset="1" stop-color="#ff5b6e"/></linearGradient><linearGradient id="nb3" x1="0" x2="1"><stop stop-color="#ffd84f"/><stop offset="1" stop-color="#ff9730"/></linearGradient></defs><ellipse cx="18" cy="17" rx="10" ry="12" fill="url(#nb1)"/><ellipse cx="36" cy="14" rx="10" ry="12" fill="url(#nb2)"/><ellipse cx="54" cy="18" rx="10" ry="12" fill="url(#nb3)"/><ellipse cx="14" cy="12" rx="3.2" ry="4.4" fill="rgba(255,255,255,.38)"/><ellipse cx="32" cy="10" rx="3.2" ry="4.4" fill="rgba(255,255,255,.38)"/><ellipse cx="50" cy="14" rx="3.2" ry="4.4" fill="rgba(255,255,255,.38)"/><path d="M18 29c4 6 6 11 8 17M36 26c-1 7-3 12-5 20M54 30c-3 5-5 10-6 16" stroke="rgba(255,255,255,.75)" stroke-width="1.7" fill="none" stroke-linecap="round"/></svg>`;
  }

  function ensureStyles() {
    if (document.getElementById('hqBirthdayBalloonStyles')) return;
    const style=document.createElement('style');
    style.id='hqBirthdayBalloonStyles';
    style.textContent=`
      .hq-nav-balloons{width:28px;height:24px;display:block;margin:0 auto 3px;filter:drop-shadow(0 0 7px rgba(255,107,198,.28))}
      .birthday-avatar.hq-balloon-avatar{width:72px;height:78px;border-radius:0;background:transparent;overflow:visible;display:grid;place-items:center}
      .hq-balloon{width:68px;height:82px;display:block;overflow:visible}.hq-balloon.compact{width:31px;height:39px}
      .birthday-card.hq-colour{border-color:rgba(255,255,255,.13);box-shadow:0 14px 30px rgba(0,0,0,.2)}
      .home-reminder-card.birthday .home-reminder-icon.hq-balloon-home{width:34px;height:42px;background:transparent;overflow:visible}
      #primaryNav[data-profile="sofia"] [data-view-target="home"]{order:1}
      #primaryNav[data-profile="sofia"] [data-view-target="news"]{order:2}
      #primaryNav[data-profile="sofia"] [data-view-target="dida"]{order:3}
      #primaryNav[data-profile="sofia"] [data-view-target="career"]{order:4}
      #primaryNav[data-profile="sofia"] [data-view-target="birthdays"]{order:5}
      #primaryNav[data-profile="sofia"] [data-view-target="ai"]{order:6}
      @media(max-width:899px){
        #primaryNav.bottom-nav{display:flex!important;grid-template-columns:none!important;overflow-x:auto!important;overflow-y:hidden!important;justify-content:flex-start!important;scrollbar-width:none;-webkit-overflow-scrolling:touch;scroll-snap-type:x proximity}
        #primaryNav.bottom-nav::-webkit-scrollbar{display:none}
        #primaryNav.bottom-nav button{flex:0 0 72px!important;min-width:72px!important;scroll-snap-align:center}
      }
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
    const nav=document.querySelector('[data-view-target="birthdays"] b');
    if(nav && nav.dataset.hq!=='1'){nav.innerHTML=navSvg();nav.dataset.hq='1';}

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
