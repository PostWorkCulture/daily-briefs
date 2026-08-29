/* Exact publisher image layer for News / Arsenal. AI uses company marks or code-native fallback icons; Career uses code-native icons.
   Rules: max one image per article, max five image-led cards per tab view,
   never reuse an image, and reject every generic or inferred fallback. */
(function(){
  const IMAGE_LIMIT_PER_VIEW=5;
  let map={};
  let scheduled=false;
  const imageChecks=new Map();
  const viewRuns=new WeakMap();

  function banned(url){return /image\.thum\.io|screenshot|favicon|placeholder|default[-_]?image/i.test(String(url||''))}
  function imageKey(url){
    try{const u=new URL(url,location.href);['w','width','h','height','q','quality','fit','crop','auto','format','fm','dpr','v','ver','version'].forEach(k=>u.searchParams.delete(k));u.hash='';return (u.host+u.pathname+'?'+u.searchParams.toString()).replace(/\?$/,'').toLowerCase()}catch(_){return String(url||'').replace(/[?#].*$/,'').toLowerCase()}
  }
  function ruleFor(card){
    const url=card.href;if(!url)return null;
    let rule=map[url];
    if(!rule){const key=Object.keys(map).find(k=>url===k||url.startsWith(k));if(key)rule=map[key]}
    if(typeof rule==='string')rule={src:rule};
    if(!rule?.src||rule.provenance!=='publisher'||!rule.matchedPageTitle||banned(rule.src))return null;
    return rule;
  }
  function loadable(rule){
    const src=String(rule?.src||'');
    if(!src)return Promise.resolve(null);
    if(imageChecks.has(src))return imageChecks.get(src);
    const check=new Promise(resolve=>{
      const image=new Image();
      let settled=false;
      const finish=result=>{if(settled)return;settled=true;clearTimeout(timer);resolve(result)};
      const timer=setTimeout(()=>finish(null),8000);
      image.decoding='async';
      image.onload=async()=>{
        try{await image.decode()}catch(_){}
        finish(image.naturalWidth>=1200&&image.naturalHeight>=675?{width:image.naturalWidth,height:image.naturalHeight}:null);
      };
      image.onerror=()=>finish(null);
      image.src=src;
    });
    imageChecks.set(src,check);
    return check;
  }
  function wrap(card,rule,key,loaded){
    if(card.dataset.imageEnhanced==='1'||card.querySelector(':scope > .story-media'))return;
    const copy=document.createElement('div');copy.className='story-copy';
    while(card.firstChild)copy.appendChild(card.firstChild);
    const media=document.createElement('div');media.className='story-media';media.dataset.imageReady='1';media.dataset.imageWidth=String(loaded.width);media.dataset.imageHeight=String(loaded.height);media.setAttribute('role','img');media.setAttribute('aria-label',rule.alt||('Story image for '+(copy.querySelector('h4,b,h3')?.textContent||'this article')));media.style.backgroundImage=`url("${String(rule.src).replace(/"/g,'%22')}")`;media.style.backgroundPosition=rule.pos||'center';
    if(rule.credit){const credit=document.createElement('span');credit.className='story-credit';credit.textContent=rule.credit;media.appendChild(credit)}
    card.append(copy,media);card.classList.add('has-image');card.dataset.imageEnhanced='1';card.dataset.imageKey=key;
  }
  async function enhanceView(view){
    if(view.matches('#view-ai,#view-career'))return;
    const run=(viewRuns.get(view)||0)+1;viewRuns.set(view,run);
    const cards=[...view.querySelectorAll('.tab-story[href],.arsenal-news-item[href]')];
    const used=new Set();let count=0;
    for(const card of cards){
      if(card.dataset.imageEnhanced==='1'){
        const key=card.dataset.imageKey;if(key&&!used.has(key)){used.add(key);count++}continue;
      }
    }
    const candidates=[];
    for(const card of cards){
      if(card.dataset.imageEnhanced==='1')continue;
      const rule=ruleFor(card);if(!rule?.src)continue;
      const key=imageKey(rule.src);if(!key||used.has(key))continue;
      used.add(key);candidates.push({card,rule,key});
      if(candidates.length>=IMAGE_LIMIT_PER_VIEW*2)break;
    }
    const checked=await Promise.all(candidates.map(async candidate=>({...candidate,loaded:await loadable(candidate.rule)})));
    if(viewRuns.get(view)!==run)return;
    for(const candidate of checked){
      if(count>=IMAGE_LIMIT_PER_VIEW)break;
      if(!candidate.loaded||!candidate.card.isConnected||!view.contains(candidate.card))continue;
      wrap(candidate.card,candidate.rule,candidate.key,candidate.loaded);count++;
    }
  }
  function enhance(){scheduled=false;Promise.all([...document.querySelectorAll('.brief-view')].map(enhanceView)).catch(()=>{})}
  function queue(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}

  new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});
  fetch('data/story-images.json?cb='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():{}).then(x=>{map=x||{};queue()}).catch(()=>{});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue);else queue();
})();
