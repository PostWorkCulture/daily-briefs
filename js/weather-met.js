function weatherIcon(condition,size='large'){
  const text=String(condition||'').toLowerCase();
  const storm=text.includes('thunder');
  const snow=text.includes('snow')||text.includes('sleet');
  const rain=!snow&&(text.includes('rain')||text.includes('shower')||text.includes('drizzle'));
  const fog=text.includes('fog')||text.includes('mist');
  const partly=text.includes('sunny interval')||text.includes('partly cloudy')||text.includes('light cloud')||text.includes('cloud with sun');
  const overcast=text.includes('overcast');
  const cloudy=!partly&&(text.includes('cloud')||overcast||fog);
  const sunny=!rain&&!snow&&!storm&&!partly&&(text.includes('sunny')||text.includes('clear'));

  const sun=`<g class="wx-sun" stroke="#ffd35a"><circle cx="22" cy="22" r="8"/><path d="M22 5v6M22 33v6M5 22h6M33 22h6M10 10l4 4M30 30l4 4M34 10l-4 4M14 30l-4 4"/></g>`;
  const bigSun=`<g class="wx-sun" stroke="#ffd35a"><circle cx="32" cy="32" r="10"/><path d="M32 8v8M32 48v8M8 32h8M48 32h8M15 15l6 6M43 43l6 6M49 15l-6 6M21 43l-6 6"/></g>`;
  const cloud=`<g class="wx-cloud" stroke="#f6fbff"><path d="M18 43h29a9 9 0 0 0 1-18 15 15 0 0 0-28-4A11 11 0 0 0 18 43Z"/></g>`;
  const greyCloud=`<g class="wx-cloud" stroke="#c8d2dc"><path d="M18 43h29a9 9 0 0 0 1-18 15 15 0 0 0-28-4A11 11 0 0 0 18 43Z"/></g>`;
  const drops=`<g class="wx-rain" stroke="#7dd7ff"><path d="M24 49l-3 7M36 49l-3 7M48 49l-3 7"/></g>`;
  const flakes=`<g class="wx-snow" stroke="#dff6ff"><path d="M24 50v8M20 54h8M38 50v8M34 54h8M50 50v8M46 54h8"/></g>`;
  const bolt=`<g class="wx-storm" stroke="#ffd35a"><path d="M34 47l-5 9h7l-3 8 10-12h-7l4-5"/></g>`;

  let art=greyCloud;
  if(storm) art=greyCloud+bolt;
  else if(snow) art=greyCloud+flakes;
  else if(rain) art=greyCloud+drops;
  else if(partly) art=sun+cloud;
  else if(sunny) art=bigSun;
  else if(cloudy) art=greyCloud;

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

// app.js starts loading profile data before this override is evaluated. If the
// data has already landed, immediately redraw weather with the Met Office icon map.
if(typeof state!=='undefined'&&state.data?.weather){renderWeather(state.data.weather)}
