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

  const sunOnly=`
    <g aria-hidden="true">
      <circle cx="32" cy="32" r="11" fill="#FFD84D" stroke="#FFD84D"/>
      <g stroke="#FFD84D" stroke-width="3" stroke-linecap="round">
        <path d="M32 8v7M32 49v7M8 32h7M49 32h7M15 15l5 5M44 44l5 5M49 15l-5 5M20 44l-5 5"/>
      </g>
    </g>`;

  const partlyCloudy=`
    <g aria-hidden="true">
      <circle cx="24" cy="22" r="10" fill="#FFD84D" stroke="#FFD84D"/>
      <g stroke="#FFD84D" stroke-width="2.8" stroke-linecap="round">
        <path d="M24 5v6M24 33v6M7 22h6M35 22h6M12 10l4 4M34 32l4 4M38 10l-4 4M16 32l-4 4"/>
      </g>
      <path d="M18 47h29.5a9.5 9.5 0 0 0 .7-19 14.5 14.5 0 0 0-27.1-3.2A11.5 11.5 0 0 0 18 47Z"
            fill="#F5F8FB" stroke="#DCE5EC" stroke-width="2.4"/>
    </g>`;

  const cloud=`<path d="M18 45h29a9 9 0 0 0 1-18 15 15 0 0 0-28-4A11 11 0 0 0 18 45Z" fill="#C9D3DC" stroke="#E7EEF3" stroke-width="2.4"/>`;
  const drops=`<g stroke="#62BFF4" stroke-width="3" stroke-linecap="round"><path d="M24 51l-3 7M36 51l-3 7M48 51l-3 7"/></g>`;
  const flakes=`<g stroke="#DFF6FF" stroke-width="2.4" stroke-linecap="round"><path d="M24 51v8M20 55h8M38 51v8M34 55h8M50 51v8M46 55h8"/></g>`;
  const bolt=`<path d="M34 48l-5 9h7l-3 7 10-12h-7l4-4" fill="#FFD84D" stroke="#FFD84D"/>`;

  let art=cloud;
  if(storm) art=cloud+bolt;
  else if(snow) art=cloud+flakes;
  else if(rain) art=cloud+drops;
  else if(partly) art=partlyCloudy;
  else if(sunny) art=sunOnly;
  else if(cloudy) art=cloud;

  return `<svg class="weather-svg ${size}" viewBox="0 0 64 64" aria-hidden="true">${art}</svg>`;
}

function renderWeather(wx={}){
  const box=$('#forecastStrip');
  if(!box) return;
  box.innerHTML='';
  (wx.daily||[]).slice(0,7).forEach((d,i)=>{
    const el=document.createElement('article');
    el.className='forecast-day'+(i===0?' today':'');
    const date=new Date(`${d.date}T12:00:00`);
    const low=d.low==null?'':`<small>${d.low}° low</small>`;
    el.innerHTML=`<span>${i===0?'Today':date.toLocaleDateString('en-GB',{weekday:'short'})}</span>${weatherIcon(d.condition||d.summary,'small')}<strong>${d.high??'—'}°</strong>${low}<em>${d.summary||''}</em>`;
    box.appendChild(el);
  });
}

if(typeof state!=='undefined'&&state.data?.weather){renderWeather(state.data.weather)}
