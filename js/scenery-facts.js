const rareWorldFacts=[
  {
    country:'Yemen',
    place:'Socotra · Dragon’s Blood Forests',
    page:'Socotra',
    source:'UNESCO',
    sourceUrl:'https://whc.unesco.org/en/list/1263/',
    fact:'Socotra is so biologically isolated that about 95% of its land-snail species and 90% of its reptile species occur nowhere else on Earth.'
  },
  {
    country:'United States',
    place:'Racetrack Playa · Death Valley',
    page:'Racetrack Playa',
    source:'U.S. National Park Service',
    sourceUrl:'https://www.nps.gov/deva/planyourvisit/the-racetrack.htm',
    fact:'Some of Death Valley’s “sailing stones” weigh around 320 kg, yet they can move across the playa when thin floating ice is pushed by surprisingly light winds.'
  },
  {
    country:'Brazil',
    place:'Lençóis Maranhenses',
    page:'Lençóis Maranhenses National Park',
    source:'UNESCO',
    sourceUrl:'https://whc.unesco.org/en/list/1611/',
    fact:'Its huge white dune field looks like a desert, but seasonal lagoons form between the dunes from rainwater alone—and some dunes migrate as much as 25 metres a year.'
  },
  {
    country:'Mauritania',
    place:'The Eye of the Sahara',
    page:'Richat Structure',
    source:'NASA Earth Observatory',
    sourceUrl:'https://science.nasa.gov/earth/earth-observatory/eyeing-the-richat-structure/',
    fact:'The 40-km-wide “Eye of the Sahara” was once thought to be an impact crater. It is actually the eroded remains of a giant uplifted geologic dome.'
  },
  {
    country:'United States',
    place:'Mono Lake · California',
    page:'Mono Lake',
    source:'U.S. Geological Survey',
    sourceUrl:'https://www.usgs.gov/volcanoes/long-valley-caldera/science/long-valley-caldera-field-guide-mono-lake',
    fact:'Mono Lake is roughly twice as salty as the ocean, and one of its islands contains lake-bottom mud that was physically pushed upward by magma only a few centuries ago.'
  },
  {
    country:'Yemen',
    place:'Socotra · Dragon’s Blood Tree',
    page:'Dracaena cinnabari',
    source:'UNESCO',
    sourceUrl:'https://www.unesco.org/en/mab/socotra-archipelago',
    fact:'The famous umbrella shape of Socotra’s dragon’s blood tree is not decorative: its dense crown helps shade the roots and reduce water loss in an extremely dry climate.'
  }
];

async function wikipediaImage(page){
  try{
    const url=`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(page)}`;
    const r=await fetch(url,{headers:{Accept:'application/json'}});
    if(!r.ok) return null;
    const d=await r.json();
    return d.originalimage?.source||d.thumbnail?.source||null;
  }catch(e){return null;}
}

async function renderRareWorldFact(){
  const start=new Date(new Date().getFullYear(),0,0);
  const day=Math.floor((new Date()-start)/86400000);
  const item=rareWorldFacts[(day-1)%rareWorldFacts.length];
  const image=$('#sceneryImage'),country=$('#sceneryCountry'),place=$('#sceneryPlace'),credit=$('#sceneryCredit'),card=$('#sceneryCard'),fact=$('#sceneryFactText');
  if(country) country.textContent=item.country;
  if(place) place.textContent=item.place;
  if(credit) credit.textContent=`Fact source · ${item.source}`;
  if(card) card.href=item.sourceUrl;
  if(fact) fact.textContent=item.fact;
  if(image){
    image.alt=`${item.place}, ${item.country}`;
    const src=await wikipediaImage(item.page);
    if(src) image.src=src;
  }
}

const originalRenderScenery=typeof renderScenery==='function'?renderScenery:null;
if(originalRenderScenery){
  renderScenery=function(){
    originalRenderScenery();
    renderRareWorldFact();
  };
  renderRareWorldFact();
}
