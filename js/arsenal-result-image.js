/* Add the approved last-match image without changing core Arsenal rendering. */
(function(){
  function enhance(a){
    const card=document.getElementById('lastResultCard'),last=a?.lastResult;
    if(!card||!last?.image)return;
    let media=card.querySelector('.match-result-photo');
    if(!media){media=document.createElement('div');media.className='match-result-photo';card.prepend(media)}
    media.style.backgroundImage=`url("${String(last.image).replace(/"/g,'%22')}")`;
    media.setAttribute('role','img');media.setAttribute('aria-label',last.imageAlt||'Latest Arsenal match');
    card.classList.add('has-match-image');
  }
  const base=window.renderArsenal;
  if(typeof base==='function')window.renderArsenal=function(a){base(a);enhance(a)};
  new MutationObserver(()=>{if(window.state?.data?.arsenal)enhance(window.state.data.arsenal)}).observe(document.body,{childList:true,subtree:true});
  if(window.state?.data?.arsenal)enhance(window.state.data.arsenal);
})();
