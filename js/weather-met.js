function weatherIcon(condition,size='large'){
  const text=String(condition||'').toLowerCase();
  const storm=text.includes('thunder');
  const snow=text.includes('snow');
  const rain=!snow&&(text.includes('rain')||text.includes('shower')||text.includes('drizzle'));
  const fog=text.includes('fog')||text.includes('mist');
  const cloudy=text.includes('cloud')||text.includes('overcast')||fog;
  const partly=text.includes('sunny interval')||text.includes('partly cloudy');
  const sunny=!rain&&!snow&&!storm&&(text.includes('sunny')||text.includes('clear'));
  const sun=`<circle cx="32" cy="32" r="10"/><path d="M32 8v8M32 48v8M8 32h8M48 32h8M15 15l6 6M43 43l6 6M49 15l-6 6M21 43l-6 6"/>`;
  const cloud=`<path d="M18 43h29a9 9 0 0 0 1-18 15 15 0 0 0-28-4A11 11 0 0 0 18 43Z"/>`;
  const drops=`<path d="M24 49l-3 7M36 49l-3 7M48 49l-3 7"/>`;
  const flakes=`<path d="M24 50v8M20 54h8M38 50v8M34 54h8M50 50v8M46 54h8"/>`;
  const bolt=`<path d="M34 47l-5 9h7l-3 8 10-12h-7l4-5"/>`;
  let art=cloud;
  if(storm) art=cloud+bolt;
  else if(snow) art=cloud+flakes;
  else if(rain) art=cloud+drops;
  else if(partly) art=sun+cloud;
  else if(sunny) art=sun;
  else if(cloudy) art=cloud;
  return `<svg class="weather-svg ${size}" viewBox="0 0 64 64" aria-hidden="true">${art}</svg>`;
}

function renderWeather(wx={}){
  $('#weatherHeroTemp').textContent=wx.temp||'—';
  $('#weatherHeroSummary').textContent=wx.summary||'Forecast unavailable';
  $('#weatherNowIcon').innerHTML=weatherIcon(wx.condition||wx.summary);
  const out=wx.bestOutdoor||{};
  $('#outdoorTime').textContent=out.label||'—';
  $('#outdoorDetail').textContent=out.detail||'Met Office forecast unavailable';
  $('#outdoorWindow').textContent=wx.source?`${wx.source} · ${wx.location||'KT8 2LE'}`:'';
  const box=$('#forecastStrip');box.innerHTML='';
  (wx.daily||[]).slice(0,7).forEach((d,i)=>{
    const el=document.createElement('article');
    el.className='forecast-day'+(i===0?' today':'');
    const date=new Date(`${d.date}T12:00:00`);
    const rain=d.rainChance==null?'':` · ${d.rainChance}% rain`;
    const low=d.low==null?'':`${d.low}°`;
    el.innerHTML=`<span>${i===0?'Today':date.toLocaleDateString('en-GB',{weekday:'short'})}</span>${weatherIcon(d.condition||d.summary,'small')}<strong>${d.high??'—'}°</strong><small>${low}${rain}</small><em>${d.summary||''}</em>`;
    box.appendChild(el);
  });
}
