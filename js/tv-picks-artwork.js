/* TV Picks hard visual rule: only display picks when the actual programme can be
   identified and paired with genuine programme artwork/stills. Never use page
   screenshots, publisher OG images, logos or generic entertainment imagery. */
(function(){
  const CATALOGUE=[
    {
      match:/\bsilo\b/i,
      programme:'Silo',
      src:'https://images.apple.com/tv-pr/articles/2026/04/apples-globally-acclaimed-drama-silo-starring-and-executive-produced-by-rebecca-ferguson-returns-for-season-three-on-july-3-2026/images/big-image/big-image-01/042126_Silo_Season_Three_Announcement_Big_Image_01_big_image_post.jpg.large.jpg',
      alt:'Rebecca Ferguson in Silo season three',
      pos:'center 42%'
    },
    {
      match:/death of a dog walker|edradynate|david campbell|brian low|aberfeldy/i,
      programme:'Murder Trial: Death of a Dog Walker',
      src:'https://cdn.mos.cms.futurecdn.net/hJKtMGuMpbQEYyukApgHjf.jpg',
      alt:'David Campbell pictured in Murder Trial: Death of a Dog Walker',
      pos:'center 38%'
    },
    {
      match:/spy next door|anna chapman/i,
      programme:'Spy Next Door: The Anna Chapman Story',
      src:'https://www.thesun.co.uk/wp-content/uploads/2026/08/4d156108-529d-4e7d-916d-b649b493fe7e.jpg?quality=90&strip=all&w=1600',
      alt:'Spy Next Door: The Anna Chapman Story',
      pos:'center'
    },
    {
      match:/\bmourinho\b/i,
      programme:'Mourinho',
      src:'https://images.ctfassets.net/4cd45et68cgf/2gNByltwbjhXgVjvI1O1hA/50d3210387f06b2640b80c2ffa901dc9/MOURINHO_n_S1_E1_00_04_42_08.jpg?w=2000',
      alt:'Mourinho documentary series',
      pos:'center 36%'
    },
    {
      match:/charles manson tapes|conversations with a killer.*manson/i,
      programme:'Conversations with a Killer: The Charles Manson Tapes',
      src:'https://image.tmdb.org/t/p/w1280/yRuUGw1zFd3IyayCwHv8gInDVeT.jpg',
      alt:'Conversations with a Killer: The Charles Manson Tapes',
      pos:'center'
    }
  ];

  let scheduled=false;
  function rawTitle(card){return card.dataset.originalTvTitle||(card.querySelector('b')?.textContent||'').trim()}
  function catalogueRule(card){
    const hay=[rawTitle(card),card.getAttribute('href')||'',card.textContent||''].join(' ');
    return CATALOGUE.find(x=>x.match.test(hay))||null;
  }
  function imageOk(src){
    const low=String(src||'').toLowerCase();
    return /^https:\/\//.test(src||'')&&!/image\.thum\.io|screenshot|favicon|placeholder|logo/.test(low);
  }
  function enhance(){
    scheduled=false;
    const box=document.getElementById('watchStrip');
    if(!box)return;
    let shown=0;
    [...box.querySelectorAll('.watch-card')].forEach(card=>{
      if(card.dataset.tvArtEnhanced==='1'){shown++;return}
      if(!card.dataset.originalTvTitle)card.dataset.originalTvTitle=(card.querySelector('b')?.textContent||'').trim();
      const rule=catalogueRule(card);
      if(!rule||!imageOk(rule.src)){
        card.remove();
        return;
      }
      const label=card.querySelector('b');
      if(label&&label.textContent!==rule.programme)label.textContent=rule.programme;
      card.classList.add('artwork');
      card.style.setProperty('--pick-image',`url("${String(rule.src).replace(/"/g,'%22')}")`);
      card.style.setProperty('--pick-pos',rule.pos||'center');
      card.setAttribute('aria-label',rule.alt||rule.programme);
      card.dataset.tvArtEnhanced='1';
      shown++;
    });
    if(!shown&&!box.querySelector('.empty'))box.innerHTML='<div class="empty">No TV pick passed today’s programme-artwork check.</div>';
  }
  function queue(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}

  const base=window.renderWatch;
  if(typeof base==='function')window.renderWatch=function(items){base(items);queue()};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue);else queue();
  new MutationObserver(queue).observe(document.getElementById('watchStrip')||document.body,{childList:true,subtree:true});
})();
