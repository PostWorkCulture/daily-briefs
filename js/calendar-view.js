/* Responsive month calendar. Uses only the refreshed events already loaded by app.js. */
(function(){
  const grid=document.getElementById('calendarMonthGrid');
  const monthTitle=document.getElementById('calendarMonthTitle');
  const dayTitle=document.getElementById('calendarDayTitle');
  const agenda=document.getElementById('calendarDayAgenda');
  if(!grid||!monthTitle||!dayTitle||!agenda)return;

  const today=new Date();
  today.setHours(12,0,0,0);
  let visibleMonth=new Date(today.getFullYear(),today.getMonth(),1,12);
  let selectedKey=dateKey(today);
  let calendarItems=[];

  function dateKey(date){
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  }
  function keyDate(key){
    const [year,month,day]=String(key).split('-').map(Number);
    return new Date(year,month-1,day,12);
  }
  function shiftKey(key,days){
    const date=keyDate(key);
    date.setDate(date.getDate()+days);
    return dateKey(date);
  }
  function isoDate(value){
    const match=String(value||'').match(/^\d{4}-\d{2}-\d{2}/);
    return match?match[0]:'';
  }
  function eventSpan(item={}){
    const start=isoDate(item.date)||isoDate(item.start);
    if(!start)return null;
    let end=isoDate(item.end)||start;
    const endsAtMidnight=/T00:00(?::00)?(?:[+-]\d{2}:?\d{2}|Z)?$/.test(String(item.end||''));
    if((item.allDay||endsAtMidnight)&&end>start)end=shiftKey(end,-1);
    if(end<start)end=start;
    return {start,end};
  }
  function eventsOn(key){
    return calendarItems.filter(item=>{
      const span=eventSpan(item);
      return span&&key>=span.start&&key<=span.end;
    }).sort((left,right)=>String(left.start||left.date||'').localeCompare(String(right.start||right.date||'')));
  }
  function eventColour(value){
    return /^#[0-9a-f]{3,8}$/i.test(String(value||''))?value:'#7cf46a';
  }
  function eventTime(item={}){
    return item.time&&item.time!=='All day'?item.time:'All day';
  }
  function renderAgenda(){
    const date=keyDate(selectedKey);
    const items=eventsOn(selectedKey);
    dayTitle.textContent=date.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long'});
    agenda.innerHTML='';
    if(!items.length){
      const empty=document.createElement('div');
      empty.className='calendar-day-empty';
      empty.textContent='No events scheduled.';
      agenda.appendChild(empty);
      return;
    }
    items.forEach(item=>{
      const hasUrl=/^https?:\/\//i.test(String(item.url||''));
      const card=document.createElement(hasUrl?'a':'article');
      card.className='calendar-day-event';
      card.style.setProperty('--month-event-colour',eventColour(item.color));
      if(hasUrl){
        card.href=item.url;
        card.target='_blank';
        card.rel='noopener noreferrer';
      }
      const rail=document.createElement('span');
      rail.className='calendar-day-event-rail';
      rail.setAttribute('aria-hidden','true');
      const copy=document.createElement('span');
      copy.className='calendar-day-event-copy';
      const meta=document.createElement('small');
      meta.textContent=eventTime(item);
      const title=document.createElement('strong');
      title.textContent=item.title||'Untitled event';
      copy.append(meta,title);
      if(item.summary){
        const summary=document.createElement('span');
        summary.className='calendar-day-event-summary';
        summary.textContent=item.summary;
        copy.appendChild(summary);
      }
      card.append(rail,copy);
      agenda.appendChild(card);
    });
  }
  function renderMonth(){
    monthTitle.textContent=visibleMonth.toLocaleDateString('en-GB',{month:'long',year:'numeric'});
    grid.innerHTML='';
    const first=new Date(visibleMonth.getFullYear(),visibleMonth.getMonth(),1,12);
    const offset=(first.getDay()+6)%7;
    const gridStart=new Date(first);
    gridStart.setDate(first.getDate()-offset);
    for(let index=0;index<42;index+=1){
      const date=new Date(gridStart);
      date.setDate(gridStart.getDate()+index);
      const key=dateKey(date);
      const items=eventsOn(key);
      const button=document.createElement('button');
      button.type='button';
      button.className='calendar-month-day';
      button.dataset.calendarDate=key;
      button.setAttribute('role','gridcell');
      button.setAttribute('aria-selected',String(key===selectedKey));
      button.setAttribute('aria-label',`${date.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'})}. ${items.length} ${items.length===1?'event':'events'}.`);
      if(date.getMonth()!==visibleMonth.getMonth())button.classList.add('outside-month');
      if(key===dateKey(today))button.classList.add('today');
      if(key===selectedKey)button.classList.add('selected');
      const number=document.createElement('span');
      number.className='calendar-month-number';
      number.textContent=String(date.getDate());
      const eventList=document.createElement('span');
      eventList.className='calendar-month-events';
      items.slice(0,3).forEach(item=>{
        const chip=document.createElement('span');
        chip.className='calendar-event-chip';
        chip.style.setProperty('--month-event-colour',eventColour(item.color));
        const dot=document.createElement('i');
        dot.setAttribute('aria-hidden','true');
        const label=document.createElement('span');
        label.textContent=item.title||'Untitled event';
        chip.append(dot,label);
        eventList.appendChild(chip);
      });
      if(items.length>3){
        const more=document.createElement('span');
        more.className='calendar-event-more';
        more.textContent=`+${items.length-3}`;
        eventList.appendChild(more);
      }
      button.append(number,eventList);
      button.addEventListener('click',()=>{
        selectedKey=key;
        if(date.getMonth()!==visibleMonth.getMonth()||date.getFullYear()!==visibleMonth.getFullYear())visibleMonth=new Date(date.getFullYear(),date.getMonth(),1,12);
        renderMonth();
      });
      grid.appendChild(button);
    }
    renderAgenda();
  }

  document.querySelectorAll('[data-calendar-month]').forEach(button=>button.addEventListener('click',()=>{
    const action=button.dataset.calendarMonth;
    if(action==='today'){
      visibleMonth=new Date(today.getFullYear(),today.getMonth(),1,12);
      selectedKey=dateKey(today);
    }else{
      visibleMonth=new Date(visibleMonth.getFullYear(),visibleMonth.getMonth()+(action==='next'?1:-1),1,12);
      selectedKey=dateKey(visibleMonth);
    }
    renderMonth();
  }));
  document.querySelector('[data-open-calendar]')?.addEventListener('click',()=>{
    if(window.showBriefView)window.showBriefView('calendar');
    else document.querySelector('[data-view-target="calendar"]')?.click();
  });

  const baseRender=render;
  render=function(data){
    baseRender(data);
    calendarItems=Array.isArray(data.calendar)?data.calendar:[];
    renderMonth();
  };
  window.renderCalendarMonth=renderMonth;
  if(state.data){
    calendarItems=Array.isArray(state.data.calendar)?state.data.calendar:[];
    renderMonth();
  }else renderMonth();
})();
