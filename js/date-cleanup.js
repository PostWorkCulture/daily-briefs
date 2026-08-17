/* Keep the visible brief date, remove the generated refresh timestamp. */
(function(){
  const tidy=()=>{
    const el=document.getElementById('briefDate');
    if(!el)return;
    const next=String(el.textContent||'').replace(/\s*·\s*refreshed\b.*$/i,'').trim();
    if(next&&next!==el.textContent)el.textContent=next;
  };
  const el=document.getElementById('briefDate');
  if(el)new MutationObserver(tidy).observe(el,{childList:true,subtree:true,characterData:true});
  tidy();
})();
