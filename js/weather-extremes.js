/* Render Met Office 'Yesterday in England' hottest/coldest cards. */
(function(){
  function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function card(kind,item,dateLabel){
    if(!item)return'';
    const photo=item.photo||null;
    const cls='uk-extreme '+kind+(photo?.src?'':' no-photo');
    const photoStyle=photo?.src?` style="background-image:url('${esc(photo.src)}')"`:'';
    const credit=photo?.src?`<div class="uk-extreme-photo-credit">${photo.page?`<a href="${esc(photo.page)}" target="_blank" rel="noopener">${esc(photo.credit||'Exact-place photo')}</a>`:esc(photo.credit||'Exact-place photo')}</div>`:'<div class="uk-extreme-photo-credit">Exact-place photo unavailable</div>';
    const kicker=kind==='hot'?'Hottest place':'Coldest place';
    const line=kind==='hot'?'highest UK maximum':'lowest UK minimum';
    return `<article class="${cls}"><div class="uk-extreme-photo" role="img" aria-label="${esc(photo?.alt||item.displayLocation||item.location||kicker)}"${photoStyle}></div>${credit}<div class="uk-extreme-copy"><div class="uk-extreme-kicker">${kicker}</div><h3>${esc(item.displayLocation||item.location||'—')} · ${esc(item.value||'—')}</h3><p>${esc(dateLabel||'Yesterday')}’s ${line}.</p><p>Official Met Office observed extreme.</p></div></article>`;
  }
  function render(wx){
    const root=document.getElementById('yesterdayExtremes');if(!root)return;
    const data=wx?.yesterdayExtremes;
    if(!data||data.error||(!data.hot&&!data.cold)){root.hidden=true;root.innerHTML='';return}
    root.hidden=false;
    root.innerHTML=`<div class="uk-yesterday-title"><strong>Yesterday in England</strong><span>${esc(data.dateLabel||'Met Office observations')}</span></div><div class="uk-extremes">${card('hot',data.hot,data.dateLabel)}${card('cold',data.cold,data.dateLabel)}</div>`;
  }
  const base=window.renderWeather;
  if(typeof base==='function')window.renderWeather=function(wx){base(wx);render(wx)};
  window.renderYesterdayExtremes=render;
  if(window.state?.data?.weather)render(window.state.data.weather);
})();
