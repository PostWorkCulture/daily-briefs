/* Premium image layer for News / Arsenal / AI / Career.
   Rules: max one image per article, max four image-led cards per tab view,
   never reuse an image, and never invent a fallback. If the daily image map
   has no verified high-quality relevant image, the article stays text-only. */
(function(){
  const IMAGE_LIMIT_PER_VIEW=4;
  let map={};
  let scheduled=false;

  function banned(url){return /image\.thum\.io|screenshot|favicon|placeholder|default[-_]?image/i.test(String(url||''))}
  function imageKey(url){
    try{const u=new URL(url,location.href);['w','width','h','height','q','quality','fit','crop','auto','format','fm','dpr','v','ver','version'].forEach(k=>u.searchParams.delete(k));u.hash='';return (u.host+u.pathname+'?'+u.searchParams.toString()).replace(/\?$/,'').toLowerCase()}catch(_){return String(url||'').replace(/[?#].*$/,'').toLowerCase()}
  }
  function ruleFor(card){
    const url=card.href;if(!url)return null;
    let rule=map[url];
    if(!rule){const key=Object.keys(map).find(k=>url===k||url.startsWith(k));if(key)rule=map[key]}
    if(typeof rule==='string')rule={src:rule};
    if(!rule?.src||banned(rule.src))return null;
    return rule;
  }
  function wrap(card,rule,key){
    if(card.dataset.imageEnhanced==='1'||card.querySelector(':scope > .story-media'))return;
    const copy=document.createElement('div');copy.className='story-copy';
    while(card.firstChild)copy.appendChild(card.firstChild);
    const media=document.createElement('div');media.className='story-media';media.setAttribute('role','img');media.setAttribute('aria-label',rule.alt||('Story image for '+(copy.querySelector('h4,b,h3')?.textContent||'this article')));media.style.backgroundImage=`url("${String(rule.src).replace(/"/g,'%22')}")`;media.style.backgroundPosition=rule.pos||'center';
    if(rule.credit){const credit=document.createElement('span');credit.className='story-credit';credit.textContent=rule.credit;media.appendChild(credit)}
    card.append(copy,media);card.classList.add('has-image');card.dataset.imageEnhanced='1';card.dataset.imageKey=key;
  }
  function enhanceView(view){
    const cards=[...view.querySelectorAll('.tab-story[href],.arsenal-news-item[href]')];
    const used=new Set();let count=0;
    for(const card of cards){
      if(count>=IMAGE_LIMIT_PER_VIEW)break;
      if(card.dataset.imageEnhanced==='1'){
        const key=card.dataset.imageKey;if(key&&!used.has(key)){used.add(key);count++}continue;
      }
      const rule=ruleFor(card);if(!rule?.src)continue;
      const key=imageKey(rule.src);if(!key||used.has(key))continue;
      used.add(key);count++;wrap(card,rule,key);
    }
  }
  function enhance(){scheduled=false;document.querySelectorAll('.brief-view').forEach(enhanceView)}
  function queue(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}

  new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});
  fetch('data/story-images.json?cb='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():{}).then(x=>{map=x||{};queue()}).catch(()=>{});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue);else queue();
})();
