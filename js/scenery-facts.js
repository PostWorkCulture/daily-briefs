const sceneryFacts={
  Norway:'Norway has more than 1,000 fjords, carved by glaciers over millions of years; Sognefjord is the country’s longest and deepest.',
  Japan:'Mount Fuji is Japan’s highest mountain at 3,776 metres and is actually an active stratovolcano, with its last eruption occurring in 1707.',
  Iceland:'Skógafoss drops about 60 metres, and on sunny days its spray often creates a vivid single or double rainbow in front of the falls.',
  Italy:'The Cinque Terre villages are linked by steep coastal paths and centuries-old terraces that were carved into the cliffs for vineyards and olive groves.'
};

function renderSceneryFact(){
  const country=$('#sceneryCountry')?.textContent?.trim();
  const fact=$('#sceneryFactText');
  if(!fact) return;
  fact.textContent=sceneryFacts[country]||'A remarkable place with a story worth discovering.';
}

const originalRenderScenery=typeof renderScenery==='function'?renderScenery:null;
if(originalRenderScenery){
  renderScenery=function(){originalRenderScenery();renderSceneryFact()};
  renderSceneryFact();
}
