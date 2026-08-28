/* Profile-aware tab navigation + compact Dida view. Depends on js/app.js. */
(function(){
  const nav=document.getElementById('primaryNav');
  const profileSwitch=document.getElementById('profileSwitch');
  const params=new URLSearchParams(location.search);
  const locked=params.get('locked')==='1';
  if(locked&&profileSwitch)profileSwitch.hidden=true;

  const baseRender=render;
  render=function(data){baseRender(data);renderProfileViews(data,state.profile)};

  function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function sectionIcon(section,index=0){
    const icons={
      ai:[
        '<rect x="5" y="5" width="14" height="14" rx="4"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M19 9h3M2 15h3M19 15h3"/><circle cx="12" cy="12" r="3"/>',
        '<path d="M12 3c.8 4.8 3.2 7.2 7.5 7.5-4.3.3-6.7 2.7-7.5 7.5-.8-4.8-3.2-7.2-7.5-7.5C8.8 10.2 11.2 7.8 12 3Z"/><path d="M19 16v5M16.5 18.5h5"/>',
        '<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="7" r="2.5"/><circle cx="18" cy="17" r="2.5"/><path d="m8.4 10.9 7.2-3M8.4 13.1l7.2 3"/>'
      ],
      career:[
        '<rect x="3" y="7" width="18" height="13" rx="3"/><path d="M8 7V5h8v2M3 12h18M10 12v2h4v-2"/>',
        '<path d="M5 19 19 5M11 5h8v8"/><path d="M5 6v13h13"/>',
        '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2.2 4.8-4.8 2.2 2.2-4.8 4.8-2.2Z"/>'
      ]
    };
    const set=icons[section]||icons.ai;
    return `<svg viewBox="0 0 24 24" aria-hidden="true">${set[index%set.length]}</svg>`;
  }
  function story(item,section='',index=0){
    const tag=item?.url?'a':'article';
    const attrs=item?.url?` href="${esc(item.url)}" target="_blank" rel="noopener noreferrer"`:'';
    const copy=`${item?.meta||item?.source?`<div class="meta">${esc(item.meta||'')}${item.meta&&item.source?' · ':''}${esc(item.source||'')}</div>`:''}<h4>${esc(item?.title||'Untitled')}</h4>${item?.summary?`<p>${esc(item.summary)}</p>`:''}`;
    const icon=section?`<span class="section-story-icon section-story-icon-${section}">${sectionIcon(section,index)}</span>`:'';
    const hierarchy=index===0?' story-lead':index<3?' story-support':' story-stream';
    return `<${tag} class="tab-story${section?' section-story':''}${hierarchy}"${attrs}>${icon}${section?`<div class="section-story-copy">${copy}</div>`:copy}</${tag}>`;
  }
  function group(title,items,section=''){
    const key=String(title||section||'items').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    const heading=title?`<h3>${esc(title)}</h3>`:'';
    return `<section class="tab-group${section?` tab-group-${section}`:''}" data-section-key="${esc(key)}">${heading}<div class="tab-list">${(items||[]).map((item,index)=>story(item,section,index)).join('')||'<div class="empty">Nothing listed today.</div>'}</div></section>`;
  }
  function newestFirst(items){return [...(items||[])].sort((a,b)=>(Date.parse(b.publishedAt||'')||0)-(Date.parse(a.publishedAt||'')||0))}
  function openAIFirst(items){return [...(items||[])].sort((a,b)=>{const score=x=>/openai|chatgpt/i.test(`${x.title||''} ${x.source||''} ${x.url||''}`)?0:1;return score(a)-score(b)})}
  function didaIcon(name){
    const paths={
      star:'<path d="m12 2.8 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9Z"/>',
      puzzle:'<path d="M8 3h4v3.1a2.2 2.2 0 1 0 4 0V3h5v6h-3.1a2.2 2.2 0 1 0 0 4H21v8h-7v-3.1a2.2 2.2 0 1 0-4 0V21H3v-7h3.1a2.2 2.2 0 1 0 0-4H3V3h5Z"/>',
      pencil:'<path d="m4 17.5-.8 3.3 3.3-.8L18.8 7.7l-2.5-2.5L4 17.5Z"/><path d="m14.8 6.7 2.5 2.5M15.8 5.7l1.5-1.5a1.4 1.4 0 0 1 2 0l.5.5a1.4 1.4 0 0 1 0 2l-1.5 1.5"/>',
      book:'<path d="M4 5.5c3.3-.8 5.9-.2 8 1.8v12c-2.1-2-4.7-2.6-8-1.8v-12Zm16 0c-3.3-.8-5.9-.2-8 1.8v12c2.1-2 4.7-2.6 8-1.8v-12Z"/>',
      play:'<path d="M4 8h16v10H4z"/><circle cx="8" cy="13" r="1"/><path d="M16 11v4M14 13h4"/>',
      leaf:'<path d="M20 4C11 4 5 8.5 5 15c0 3 2 5 5 5 6.5 0 10-7 10-16Z"/><path d="M4 21c3-5 7-8 12-11"/>',
      sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/>',
      search:'<circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 5 5"/>',
      sprout:'<path d="M12 21v-9M12 15c-5 0-7-3-7-7 5 0 7 3 7 7Zm0-3c0-5 3-7 7-7 0 5-3 7-7 7Z"/>',
      move:'<path d="M4 16c3-6 6-9 10-9h4"/><path d="m15 4 3 3-3 3M5 16l3 1-1 3"/>',
      sparkle:'<path d="M12 2c.7 5.3 3.4 8 8 8-4.6 0-7.3 2.7-8 8-.7-5.3-3.4-8-8-8 4.6 0 7.3-2.7 8-8Z"/><path d="M19 16v6M16 19h6"/>',
      letters:'<path d="m4 19 4.5-14L13 19M5.5 14h6"/><path d="M15 10h3.5a2.5 2.5 0 0 1 0 5H15m0-5v9h4a2.5 2.5 0 0 0 0-5"/>',
      dice:'<rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="8" cy="8" r="1"/><circle cx="16" cy="8" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="8" cy="16" r="1"/><circle cx="16" cy="16" r="1"/>',
      bolt:'<path d="m13 2-7 11h6l-1 9 7-12h-6l1-8Z"/>'
    };
    return `<svg class="dida-icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name]||paths.sparkle}</svg>`;
  }

  const milestones=[
    ['Social & emotional',['Builds stronger friendships and practises fairness in games','Shows growing independence while still looking for reassurance','Talks about experiences, thoughts and feelings in more detail']],
    ['Language & communication',['Retells a story with a beginning, middle and end','Follows instructions with two or three steps','Uses a wider vocabulary and asks more detailed questions','Reads and writes some familiar words']],
    ['Thinking & learning',['Counts beyond 20 and starts counting backwards from 10','Recognises written numbers and connects them to quantities','Uses objects or drawings for simple adding and taking away','Understands days, routines and before or after','Stays with a chosen activity for longer stretches','Plans, tests and changes an idea when solving a problem']],
    ['Movement & independence',['Skips, hops and balances with more control','Throws and catches a ball more consistently','Uses pencils and scissors with growing control','Manages dressing, shoes, her school bag and simple home jobs with reminders']]
  ];
  const teach=[
    ['Reading power','Read a short page together, then spot one new word on signs, packets or books.'],
    ['Sound detective','Choose one sound or letter blend and hunt for words that use it.'],
    ['Number sense','Count real things beyond 20, compare groups, then add or take away one or two.'],
    ['Story thinking','After a story ask for the beginning, middle, ending and one different ending.'],
    ['Time and plans','Use a simple calendar to talk about yesterday, today, tomorrow and the week ahead.'],
    ['Independence','Let her choose clothes, clear her plate, pair socks and help pack her school bag.']
  ];
  const games=[
    ['Story Builder','Take turns adding a sentence to a ridiculous story. Add a colour, animal or place each turn.'],
    ['Rhyming Hunt','Pick a word and race to invent three rhymes, including silly ones.'],
    ['Number Treasure Hunt','Hide number cards 1–20, find them, order them and make simple pairs that total 10.'],
    ['Hopscotch Missions','Hop to a number, balance on one foot, then solve a tiny adding or taking-away challenge.'],
    ['Mini Shop','Price toys with pretend 1p, 2p, 5p and 10p coins and take turns as shopkeeper and customer.'],
    ['Sock Match Sprint','Match clean socks and sort them by person, colour or size.']
  ];
  const powers=[['Kindness','Notice when someone needs help and think of one thing she can do.'],['Confidence','Order food, ask a shop assistant a question or introduce herself.'],['Problem solving','Before stepping in, ask “What could we try first?”'],['Body confidence','Run, climb, balance, dance, throw, catch and get muddy.'],['Creativity','Keep drawing, building, pretending and making up absurd stories.'],['Family memory','Take one photo or tiny recording each month of a new obsession.']];
  const seasons={
    winter:['Winter missions','Cosy projects + outdoor mini-adventures',['Torch-light treasure hunt','Paper snowflakes and count the points','Build the tallest blanket den','Puddle or frost photo hunt','Make a warm-drink café and practise taking orders']],
    spring:['Spring missions','Growing, noticing and getting outside',['Plant something fast-growing','Six-colour spring scavenger hunt','Build a bug hotel','Draw a map to a playground','Make leaf or flower patterns']],
    summer:['Late-summer missions','Make the most of long, light days',['Garden mini-Olympics: hop, throw, balance, sprint','Picnic alphabet hunt','Trace shadows with chalk and revisit them later','Freeze tiny toys in ice and plan a rescue','Make a six-stop nature treasure map']],
    autumn:['Autumn missions','Leaves, darker evenings and making weather',['Leaf colour hunt','Conker or acorn counting challenge','Torch-lit indoor obstacle course','Design a Halloween creature and invent its story','Bake something simple and count the ingredients']],
    birthday:['Birthday runway · late November','Make turning six feel like an adventure',['Create a “6 things before I’m 6” list','Let Dida design one part of her birthday','Make a handprint “5” now and “6” on her birthday','Record a two-minute favourite-things interview','Build a birthday treasure hunt with six clues']],
    christmas:['Christmas missions','Tiny traditions worth repeating',['Paper-chain countdown in number order','North Pole toy-delivery obstacle course','Invent a silly Christmas story','Do one kindness mission','Wrap an empty box together for folding and tape practice']]
  };
  function currentSeason(){const m=new Date().getMonth()+1;if(m===12||m<=2)return seasons.winter;if(m<=5)return seasons.spring;if(m<=8)return seasons.summer;return seasons.autumn}
  function seasonalBlocks(){const m=new Date().getMonth()+1,out=[currentSeason()];if(m>=8&&m<=11)out.push(seasons.birthday);if(m>=10||m===12)out.push(seasons.christmas);return out}
  function fold(n,icon,title,strap,body){return `<details class="dida-fold"><summary><span class="dida-fold-icon">${didaIcon(icon)}</span><div><h4>${esc(title)}</h4><p>${esc(strap)}</p></div><span class="dida-num">${n}</span><b class="dida-plus" aria-hidden="true">+</b></summary><div class="dida-fold-body">${body}</div></details>`}
  function zoneHead(title){return `<header class="dida-zone-head"><h3>${esc(title)}</h3></header>`}
  function didaHTML(){
    const day=Math.floor(Date.now()/86400000),learn=teach[day%teach.length],play=games[(day+2)%games.length],season=currentSeason(),quick=[['book','LEARN',learn[0],learn[1]],['play','PLAY',play[0],play[1]],['leaf','OUTSIDE / MAKE',season[0],season[2][day%season[2].length]]];
    const seasonal=seasonalBlocks().map(s=>`<section class="dida-season"><div class="dida-season-title"><span>${didaIcon('sun')}</span><div><h4>${esc(s[0])}</h4><p>${esc(s[1])}</p></div></div><div class="dida-season-list">${s[2].map((x,i)=>`<div class="dida-season-item"><span>${didaIcon(['pencil','search','sprout','move','sparkle'][i%5])}</span>${esc(x)}</div>`).join('')}</div></section>`).join('');
    const milestoneBody=`<div class="dida-reference">${milestones.map(m=>`<article class="dida-ref-card"><h5>${esc(m[0])}</h5><ul>${m[1].map(x=>`<li>${esc(x)}</li>`).join('')}</ul></article>`).join('')}</div>`;
    const teachBody=`<div class="dida-reference">${teach.map(x=>`<article class="dida-ref-card"><h5>${esc(x[0])}</h5><p>${esc(x[1])}</p></article>`).join('')}</div>`;
    const gamesBody=`<div class="dida-reference">${games.map(x=>`<article class="dida-ref-card"><h5>${esc(x[0])}</h5><p>${esc(x[1])}</p></article>`).join('')}</div>`;
    const powersBody=`<div class="dida-reference">${powers.map(x=>`<article class="dida-ref-card"><h5>${esc(x[0])}</h5><p>${esc(x[1])}</p></article>`).join('')}</div>`;
    const quickCards=quick.map(x=>`<article class="dida-quick"><span class="dida-quick-icon">${didaIcon(x[0])}</span><div><small>${esc(x[1])}</small><h4>${esc(x[2])}</h4><p>${esc(x[3])}</p></div></article>`).join('');
    const library=[fold('01','star','Age-six development','Grouped development markers for quick scanning.',milestoneBody),fold('02','letters','What to teach her now','Short real-life practice, not formal lessons.',teachBody),fold('03','dice','Games worth playing','Quick games that quietly practise useful skills.',gamesBody),fold('04','bolt','Little superpowers','Useful things to build across the year.',powersBody)].join('');
    return `<section class="dida-zone dida-week-zone" id="dida-week">${zoneHead('This week')}<div class="dida-quick-grid">${quickCards}</div></section><section class="dida-zone dida-seasonal-zone" id="dida-seasonal">${zoneHead('Seasonal missions')}${seasonal}</section><section class="dida-zone dida-library-zone" id="dida-library">${zoneHead('Reference library')}<div class="dida-library">${library}</div><p class="dida-source"><a href="https://stacks.cdc.gov/view/cdc/155268" target="_blank" rel="noopener">CDC ages 6–8 guide</a></p></section>`;
  }

  function renderProfileViews(data,profile){
    if(nav)nav.dataset.profile=profile;
    const news=[];
    if(profile==='sofia'&&data.sections?.Sweden?.length)news.push(['Sweden',data.sections.Sweden]);
    news.push(['Local News',newestFirst(data.sections?.['Local news']||[])],['UK News',data.sections?.['UK news']||[]]);
    document.getElementById('newsTabGroups').innerHTML=news.map(x=>group(x[0],x[1])).join('');
    document.getElementById('aiTabGroups').innerHTML=group('',openAIFirst(data.sections?.AI||[]),'ai');
    document.getElementById('careerTabGroups').innerHTML=group('',data.sections?.Career||[],'career');
    document.getElementById('didaContent').innerHTML=didaHTML();
    if(profile==='sofia'&&document.getElementById('view-arsenal')?.classList.contains('active'))showView('home');
  }
  window.renderProfileViews=renderProfileViews;

  function showView(view){
    if(state.profile==='sofia'&&view==='arsenal')view='home';
    document.querySelectorAll('.brief-view').forEach(v=>v.classList.toggle('active',v.dataset.view===view));
    document.querySelectorAll('[data-view-target]').forEach(b=>{
      const active=b.dataset.viewTarget===view;
      b.classList.toggle('active',active);
      if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');
    });
    const mobile=window.matchMedia('(max-width: 899px)').matches;
    window.scrollTo({top:0,behavior:mobile?'auto':'smooth'});
  }
  window.showBriefView=showView;
  document.querySelectorAll('[data-view-target]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.viewTarget)));

  document.querySelectorAll('[data-profile]').forEach(b=>b.addEventListener('click',()=>{setTimeout(()=>showView('home'),0)}));
  if(state.data)renderProfileViews(state.data,state.profile);
})();
