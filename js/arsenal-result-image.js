/* Add the approved last-match image and enforce the six-field next-fixture card. */
(function(){
  function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function resultImage(a){
    const card=document.getElementById('lastResultCard'),last=a?.lastResult;
    if(!card||!last?.image)return;
    let media=card.querySelector('.match-result-photo');
    if(!media){media=document.createElement('div');media.className='match-result-photo';card.prepend(media)}
    media.style.backgroundImage=`url("${String(last.image).replace(/"/g,'%22')}")`;
    media.setAttribute('role','img');media.setAttribute('aria-label',last.imageAlt||'Latest Arsenal match');
    card.classList.add('has-match-image');
  }
  function row(label,value,sub=''){
    return `<div class="fixture-fact"><span>${esc(label)}</span><b>${esc(value||'TBC')}</b>${sub?`<small>${esc(sub)}</small>`:''}</div>`
  }
  function fixtureDetails(a){
    const card=document.getElementById('nextFixtureCard'),next=a?.nextFixture;
    if(!card||!next)return;
    const previous=next.previousMeeting||{};
    const kick=[next.dateLabel,next.kickoff].filter(Boolean).join(' · ');
    const previousSub=[previous.date,previous.competition].filter(Boolean).join(' · ');
    card.innerHTML=`<span>Next fixture</span><strong>${esc(next.opponent||'Opponent TBC')}</strong><div class="fixture-facts">${row('Stadium',next.stadium)}${row('Actual kick-off',kick||'TBC')}${row('Competition',next.competition)}${row('TV channel',next.tvChannel)}${row('Score last time they played',previous.score||'No previous meeting found',previousSub)}</div>`;
    card.classList.add('fixture-detail-card');
  }
  function enhance(a){resultImage(a);fixtureDetails(a)}
  const base=window.renderArsenal;
  if(typeof base==='function')window.renderArsenal=function(a){base(a);enhance(a)};
})();
