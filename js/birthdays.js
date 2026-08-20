/* Family birthdays. Ages are calculated from birth dates so they update automatically. */
(function(){
  const birthdays=[
    {name:'Pete',day:7,month:2,year:1983},
    {name:'Sofia',day:28,month:2,year:1985},
    {name:'Adina',day:30,month:11,year:2021},
    {name:'Aurelia',day:18,month:3,year:2013},
    {name:'Isaac',day:27,month:5,year:2014},
    {name:'Oscar',day:7,month:6,year:2021},
    {name:'Arthur',day:4,month:4,year:2024},
    {name:'Trey',day:12,month:12,year:2025},
    {name:"Pete's Mum",day:7,month:5,year:1964},
    {name:"Sofia's Dad",day:25,month:7,year:1948},
    {name:"Sofia's Mum",day:20,month:5,year:1949},
    {name:'Patrick',day:1,month:3,year:1978},
    {name:'Maffi',day:3,month:8,year:1989},
    {name:'Ash & Sophia',day:7,month:11,year:1995}
  ];

  function startOfDay(date=new Date()){
    const d=new Date(date);
    d.setHours(0,0,0,0);
    return d;
  }

  function birthdayInYear(person,year){
    return new Date(year,person.month-1,person.day,12,0,0,0);
  }

  function currentAge(person,today=startOfDay()){
    let age=today.getFullYear()-person.year;
    const thisBirthday=birthdayInYear(person,today.getFullYear());
    if(today<thisBirthday)age-=1;
    return age;
  }

  function nextBirthday(person,today=startOfDay()){
    let next=birthdayInYear(person,today.getFullYear());
    if(next<today)next=birthdayInYear(person,today.getFullYear()+1);
    return next;
  }

  function daysUntil(date,today=startOfDay()){
    const target=startOfDay(date);
    return Math.round((target-today)/86400000);
  }

  function dateLabel(person){
    return birthdayInYear(person,2000).toLocaleDateString('en-GB',{day:'numeric',month:'long'});
  }

  function countdownLabel(days){
    if(days===0)return 'Today';
    if(days===1)return 'Tomorrow';
    return `In ${days} days`;
  }

  function renderBirthdays(){
    const list=document.getElementById('birthdayList');
    const nextCard=document.getElementById('birthdayNextCard');
    const summary=document.getElementById('birthdayNextSummary');
    if(!list||!nextCard||!summary)return;

    const today=startOfDay();
    const ordered=birthdays.map(person=>{
      const next=nextBirthday(person,today);
      const days=daysUntil(next,today);
      const age=currentAge(person,today);
      const nextAge=next.getFullYear()-person.year;
      return {...person,next,days,age,nextAge};
    }).sort((a,b)=>a.days-b.days||a.month-b.month||a.day-b.day||a.name.localeCompare(b.name));

    const upcoming=ordered[0];
    summary.textContent=upcoming.days===0?`${upcoming.name}'s birthday is today.`:`Next up: ${upcoming.name} on ${dateLabel(upcoming)}.`;
    nextCard.innerHTML=`<div class="birthday-next-date"><span>${upcoming.next.toLocaleDateString('en-GB',{month:'short'}).toUpperCase()}</span><strong>${upcoming.day}</strong></div><div class="birthday-next-copy"><small>NEXT BIRTHDAY · ${countdownLabel(upcoming.days).toUpperCase()}</small><h3>${upcoming.name}</h3><p>Turns ${upcoming.nextAge} · ${dateLabel(upcoming)}</p></div>`;

    list.innerHTML=ordered.map(person=>`<article class="birthday-card${person.days===0?' birthday-today':''}"><div class="birthday-date"><span>${person.next.toLocaleDateString('en-GB',{month:'short'}).toUpperCase()}</span><strong>${person.day}</strong></div><div class="birthday-copy"><h3>${person.name}</h3><p>${dateLabel(person)}</p><small>Age ${person.age} · turns ${person.nextAge} ${person.days===0?'today':person.days===1?'tomorrow':`in ${person.days} days`}</small></div></article>`).join('');
  }

  window.familyBirthdays=birthdays;
  window.renderBirthdays=renderBirthdays;
  renderBirthdays();
})();
