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
  function story(item){
    const tag=item?.url?'a':'article';
    const attrs=item?.url?` href="${esc(item.url)}" target="_blank" rel="noopener noreferrer"`:'';
    return `<${tag} class="tab-story"${attrs}>${item?.meta||item?.source?`<div class="meta">${esc(item.meta||'')}${item.meta&&item.source?' · ':''}${esc(item.source||'')}</div>`:''}<h4>${esc(item?.title||'Untitled')}</h4>${item?.summary?`<p>${esc(item.summary)}</p>`:''}</${tag}>`;
  }
  function group(title,items){return `<section class="tab-group"><h3>${esc(title)}</h3><div class="tab-list">${(items||[]).map(story).join('')||'<div class="empty">Nothing listed today.</div>'}</div></section>`}
  function openAIFirst(items){return [...(items||[])].sort((a,b)=>{const score=x=>/openai|chatgpt/i.test(`${x.title||''} ${x.source||''} ${x.url||''}`)?0:1;return score(a)-score(b)})}

  const milestones=[
    ['Social & emotional',['Takes turns and follows simple rules in games','Enjoys singing, dancing or putting on a little performance','Helps with simple home jobs such as matching socks or clearing the table']],
    ['Language & communication',['Tells a short story with connected events','Answers simple questions about a story','Keeps a conversation going for several back-and-forth turns','Recognises or makes simple rhymes']],
    ['Thinking & learning',['Counts to 10','Recognises some written numbers 1–5','Uses time words such as yesterday, tomorrow, morning and night','Stays with an activity for roughly 5–10 minutes','Writes some letters in her name','Recognises some letters']],
    ['Movement & independence',['Buttons some buttons','Hops on one foot','Manages more dressing, tidying and mealtime jobs with less help']]
  ];
  const teach=[
    ['Name power','Practise letters in Dida’s name, then spot them on signs, packets and books.'],
    ['Sound detective','Choose one sound and hunt for things that begin with it.'],
    ['Number sense','Count real things to 10 and beyond, then ask what happens if you add one.'],
    ['Story thinking','After a story ask what happened first, next and what might happen tomorrow.'],
    ['Time words','Use yesterday, today, tomorrow, morning and evening naturally.'],
    ['Independence','Let her choose clothes, clear her plate, pair socks and help pack a small bag.']
  ];
  const games=[
    ['Story Builder','Take turns adding a sentence to a ridiculous story. Add a colour, animal or place each turn.'],
    ['Rhyming Hunt','Pick a word and race to invent three rhymes, including silly ones.'],
    ['Number Treasure Hunt','Hide number cards 1–10, find them, order them and match each with that many objects.'],
    ['Hopscotch Missions','Hop to a number, balance on one foot, then answer a tiny counting challenge.'],
    ['Mini Shop','Price toys with 1–5 pretend coins and take turns as shopkeeper and customer.'],
    ['Sock Match Sprint','Match clean socks and sort them by person, colour or size.']
  ];
  const powers=[['Kindness','Notice when someone needs help and think of one thing she can do.'],['Confidence','Order food, ask a shop assistant a question or introduce herself.'],['Problem solving','Before stepping in, ask “What could we try first?”'],['Body confidence','Run, climb, balance, dance, throw, catch and get muddy.'],['Creativity','Keep drawing, building, pretending and making up absurd stories.'],['Family memory','Take one photo or tiny recording each month of a new obsession.']];
  const seasons={
    winter:['Winter missions','Cosy projects + outdoor mini-adventures',['Torch-light treasure hunt','Paper snowflakes and count the points','Build the tallest blanket den','Puddle or frost photo hunt','Make a warm-drink café and practise taking orders']],
    spring:['Spring missions','Growing, noticing and getting outside',['Plant something fast-growing','Five-colour spring scavenger hunt','Build a bug hotel','Draw a map to a playground','Make leaf or flower patterns']],
    summer:['Late-summer missions','Make the most of long, light days',['Garden mini-Olympics: hop, throw, balance, sprint','Picnic alphabet hunt','Trace shadows with chalk and revisit them later','Freeze tiny toys in ice and plan a rescue','Make a five-stop nature treasure map']],
    autumn:['Autumn missions','Leaves, darker evenings and making weather',['Leaf colour hunt','Conker or acorn counting challenge','Torch-lit indoor obstacle course','Design a Halloween creature and invent its story','Bake something simple and count the ingredients']],
    birthday:['Birthday runway · late November','Make turning five feel like an adventure',['Create a “5 things before I’m 5” list','Let Dida design one part of her birthday','Make a handprint “4” now and “5” on her birthday','Record a two-minute favourite-things interview','Build a birthday treasure hunt with five clues']],
    christmas:['Christmas missions','Tiny traditions worth repeating',['Paper-chain countdown in number order','North Pole toy-delivery obstacle course','Invent a silly Christmas story','Do one kindness mission','Wrap an empty box together for folding and tape practice']]
  };
  function currentSeason(){const m=new Date().getMonth()+1;if(m===12||m<=2)return seasons.winter;if(m<=5)return seasons.spring;if(m<=8)return seasons.summer;return seasons.autumn}
  function seasonalBlocks(){const m=new Date().getMonth()+1,out=[currentSeason()];if(m>=8&&m<=11)out.push(seasons.birthday);if(m>=10||m===12)out.push(seasons.christmas);return out}
  function fold(n,title,strap,body){const desktop=matchMedia('(min-width:761px)').matches;return `<details class="dida-fold"${desktop?' open':''}><summary><span class="dida-num">${n}</span><div><h4>${esc(title)}</h4><p>${esc(strap)}</p></div><b class="dida-plus">+</b></summary><div class="dida-fold-body">${body}</div></details>`}
  function didaHTML(){
    const day=Math.floor(Date.now()/86400000),learn=teach[day%teach.length],play=games[(day+2)%games.length],season=currentSeason(),quick=[['LEARN',learn[0],learn[1]],['PLAY',play[0],play[1]],['OUTSIDE / MAKE',season[0],season[2][day%season[2].length]]];
    const seasonal=seasonalBlocks().map(s=>`<section class="dida-season"><h4>${esc(s[0])}</h4><p>${esc(s[1])}</p><div class="dida-season-list">${s[2].map(x=>`<div class="dida-season-item">${esc(x)}</div>`).join('')}</div></section>`).join('');
    const milestoneBody=`<div class="dida-reference">${milestones.map(m=>`<article class="dida-ref-card"><h5>${esc(m[0])}</h5><ul>${m[1].map(x=>`<li>${esc(x)}</li>`).join('')}</ul></article>`).join('')}</div>`;
    const teachBody=`<div class="dida-reference">${teach.map(x=>`<article class="dida-ref-card"><h5>${esc(x[0])}</h5><p>${esc(x[1])}</p></article>`).join('')}</div>`;
    const gamesBody=`<div class="dida-reference">${games.map(x=>`<article class="dida-ref-card"><h5>${esc(x[0])}</h5><p>${esc(x[1])}</p></article>`).join('')}</div>`;
    const powersBody=`<div class="dida-reference">${powers.map(x=>`<article class="dida-ref-card"><h5>${esc(x[0])}</h5><p>${esc(x[1])}</p></article>`).join('')}</div>`;
    return `<section class="dida-hero"><div class="dida-kicker">DIDA · AGE 5</div><h2>What matters now</h2><p>Confidence, conversation, early literacy and numbers, movement, turn-taking and doing more everyday things independently.</p><div class="dida-source">Milestones are a guide, not a test. <a href="https://www.cdc.gov/act-early/milestones/5-years.html" target="_blank" rel="noopener">CDC age-5 guide</a></div></section><section class="dida-now"><div class="dida-now-head"><div><span>THIS WEEK</span><h3>Three easy wins</h3></div></div><div class="dida-quick-grid">${quick.map(x=>`<article class="dida-quick"><small>${esc(x[0])}</small><h4>${esc(x[1])}</h4><p>${esc(x[2])}</p></article>`).join('')}</div></section><section class="dida-now"><div class="dida-now-head"><div><span>RIGHT NOW</span><h3>Seasonal ideas</h3></div></div>${seasonal}</section>${fold('01','Five-year-old milestones','All the milestones, grouped for quick scanning.',milestoneBody)}${fold('02','What to teach her now','Short real-life practice, not formal lessons.',teachBody)}${fold('03','Games worth playing','Quick games that secretly practise useful skills.',gamesBody)}${fold('04','Little superpowers','Useful things to build across the year.',powersBody)}`;
  }

  function renderProfileViews(data,profile){
    if(nav)nav.dataset.profile=profile;
    const news=[];
    if(profile==='sofia'&&data.sections?.Sweden?.length)news.push(['Sweden',data.sections.Sweden]);
    news.push(['Local News',data.sections?.['Local news']||[]],['UK News',data.sections?.['UK news']||[]]);
    document.getElementById('newsTabGroups').innerHTML=news.map(x=>group(x[0],x[1])).join('');
    document.getElementById('aiTabGroups').innerHTML=group('',openAIFirst(data.sections?.AI||[]));
    document.getElementById('careerTabGroups').innerHTML=group('',data.sections?.Career||[]);
    document.getElementById('didaContent').innerHTML=didaHTML();
    if(profile==='sofia'&&document.getElementById('view-arsenal')?.classList.contains('active'))showView('home');
  }
  window.renderProfileViews=renderProfileViews;

  function showView(view){
    if(state.profile==='sofia'&&view==='arsenal')view='home';
    document.querySelectorAll('.brief-view').forEach(v=>v.classList.toggle('active',v.dataset.view===view));
    document.querySelectorAll('[data-view-target]').forEach(b=>b.classList.toggle('active',b.dataset.viewTarget===view));
    window.scrollTo({top:0,behavior:'smooth'});
  }
  window.showBriefView=showView;
  document.querySelectorAll('[data-view-target]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.viewTarget)));

  document.querySelectorAll('[data-profile]').forEach(b=>b.addEventListener('click',()=>{setTimeout(()=>showView('home'),0)}));
  if(state.data)renderProfileViews(state.data,state.profile);
})();
