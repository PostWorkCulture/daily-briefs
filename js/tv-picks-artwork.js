/* TV Picks artwork guard. Cards may only use exact programme artwork supplied
   by the current schedule enrichment. Generic images and old title allowlists
   are deliberately rejected. */
(function(){
  const allowed=/^https:\/\/static\.tvmaze\.com\/uploads\/images\/original_untouched\//;
  function valid(src){return allowed.test(String(src||''))&&!/logo|placeholder|favicon|screenshot/i.test(src||'')}
  function verify(){
    const box=document.getElementById('watchStrip');
    if(!box)return;
    let shown=0;
    [...box.querySelectorAll('.watch-card')].forEach(card=>{
      const src=card.dataset.artwork||'';
      if(!valid(src)){card.remove();return}
      card.classList.add('artwork');
      card.style.setProperty('--pick-image',`url("${src.replace(/"/g,'%22')}")`);
      shown++;
    });
    if(!shown&&!box.querySelector('.empty'))box.innerHTML='<div class="empty">No current TV pick passed today’s programme-artwork check.</div>';
  }
  const base=window.renderWatch;
  if(typeof base==='function')window.renderWatch=function(items){base(items);verify()};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',verify);else verify();
})();
