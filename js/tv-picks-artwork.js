/* Restore programme/story artwork for Tonight. Exact known programme art wins;
   otherwise use the same verified unique-image map as story cards. */
(function(){
  const KNOWN={
    'Conversations with a Killer: The Charles Manson Tapes':'https://image.tmdb.org/t/p/w1280/yRuUGw1zFd3IyayCwHv8gInDVeT.jpg',
    'Spy Next Door: The Anna Chapman Story':'https://www.thesun.co.uk/wp-content/uploads/2026/08/4d156108-529d-4e7d-916d-b649b493fe7e.jpg?quality=90&strip=all&w=1024',
    'Mourinho':'https://images.ctfassets.net/4cd45et68cgf/2gNByltwbjhXgVjvI1O1hA/50d3210387f06b2640b80c2ffa901dc9/MOURINHO_n_S1_E1_00_04_42_08.jpg?w=2000'
  };
  let map={};
  function titleOf(card){return (card.querySelector('b')?.textContent||'').trim()}
  function ruleFor(card){
    const title=titleOf(card);
    if(KNOWN[title])return {src:KNOWN[title],alt:title};
    const url=card.href||'';
    let rule=map[url];
    if(!rule&&url){const key=Object.keys(map).find(k=>url===k||url.startsWith(k));if(key)rule=map[key]}
    return typeof rule==='string'?{src:rule,alt:title}:rule;
  }
  function enhance(){
    const used=new Set();
    document.querySelectorAll('#watchStrip .watch-card').forEach((card,i)=>{
      if(i>=4)return;
      const rule=ruleFor(card);if(!rule?.src)return;
      const key=String(rule.src).replace(/[?#].*$/,'').toLowerCase();if(used.has(key))return;used.add(key);
      card.classList.add('artwork');
      card.style.setProperty('--pick-image',`url("${String(rule.src).replace(/"/g,'%22')}")`);
      card.setAttribute('aria-label',(rule.alt||titleOf(card)||'Tonight pick')+' artwork');
    });
  }
  const base=window.renderWatch;
  if(typeof base==='function')window.renderWatch=function(items){base(items);enhance()};
  fetch('data/story-images.json?cb='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():{}).then(x=>{map=x||{};enhance()}).catch(enhance);
  new MutationObserver(enhance).observe(document.body,{childList:true,subtree:true});
})();
