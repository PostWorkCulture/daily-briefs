const rareWorldFacts=[
  {
    country:'Yemen',
    place:'Socotra · Dragon’s Blood Forests',
    page:'Socotra',
    source:'UNESCO',
    sourceUrl:'https://whc.unesco.org/en/list/1263/',
    image:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Dragon%27s_Blood_Trees%2C_Socotra_Island.jpg?width=2400',
    imagePage:'https://commons.wikimedia.org/wiki/File:Dragon%27s_Blood_Trees,_Socotra_Island.jpg',
    photoCredit:'Rod Waddington · CC BY-SA 2.0',
    fact:'Socotra is so biologically isolated that about 95% of its land-snail species and 90% of its reptile species occur nowhere else on Earth.'
  },
  {
    country:'United States',
    place:'Racetrack Playa · Death Valley',
    page:'Racetrack Playa',
    source:'U.S. National Park Service',
    sourceUrl:'https://www.nps.gov/deva/planyourvisit/the-racetrack.htm',
    image:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Racetrack_Playa-s.png?width=2400',
    imagePage:'https://commons.wikimedia.org/wiki/File:Racetrack_Playa-s.png',
    photoCredit:'Martin D. Adamiker · CC BY-SA 4.0',
    fact:'Some of Death Valley’s “sailing stones” weigh around 320 kg, yet they can move across the playa when thin floating ice is pushed by surprisingly light winds.'
  },
  {
    country:'Brazil',
    place:'Lençóis Maranhenses',
    page:'Lençóis Maranhenses National Park',
    source:'UNESCO',
    sourceUrl:'https://whc.unesco.org/en/list/1611/',
    image:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Parque_Nacional_dos_Len%C3%A7%C3%B3is_Maranhenses_Paulo_Cattelan_%2803%29.jpg?width=2400',
    imagePage:'https://commons.wikimedia.org/wiki/File:Parque_Nacional_dos_Len%C3%A7%C3%B3is_Maranhenses_Paulo_Cattelan_(03).jpg',
    photoCredit:'Paulo Cattelan · CC BY-SA 4.0',
    fact:'Its huge white dune field looks like a desert, but seasonal lagoons form between the dunes from rainwater alone—and some dunes migrate as much as 25 metres a year.'
  },
  {
    country:'Mauritania',
    place:'The Eye of the Sahara',
    page:'Richat Structure',
    source:'NASA Earth Observatory',
    sourceUrl:'https://science.nasa.gov/earth/earth-observatory/eyeing-the-richat-structure/',
    image:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Earth_from_Space-_Eye_of_the_Sahara_ESA515004_-_The_Richat_Structure_in_Mauritania.jpg?width=2400',
    imagePage:'https://commons.wikimedia.org/wiki/File:Earth_from_Space-_Eye_of_the_Sahara_ESA515004_-_The_Richat_Structure_in_Mauritania.jpg',
    photoCredit:'European Space Agency · Attribution',
    fact:'The 40-km-wide “Eye of the Sahara” was once thought to be an impact crater. It is actually the eroded remains of a giant uplifted geologic dome.'
  },
  {
    country:'United States',
    place:'Mono Lake · California',
    page:'Mono Lake',
    source:'U.S. Geological Survey',
    sourceUrl:'https://www.usgs.gov/volcanoes/long-valley-caldera/science/long-valley-caldera-field-guide-mono-lake',
    image:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Mono_Lake_South_Tufa_September_2016_panorama.jpg?width=2400',
    imagePage:'https://commons.wikimedia.org/wiki/File:Mono_Lake_South_Tufa_September_2016_panorama.jpg',
    photoCredit:'King of Hearts · CC BY-SA 4.0',
    fact:'Mono Lake is roughly twice as salty as the ocean, and one of its islands contains lake-bottom mud that was physically pushed upward by magma only a few centuries ago.'
  },
  {
    country:'Yemen',
    place:'Socotra · Dragon’s Blood Tree',
    page:'Dracaena cinnabari',
    source:'UNESCO',
    sourceUrl:'https://www.unesco.org/en/mab/socotra-archipelago',
    image:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Dragon_Blood_Tree%2C_Socotra_Island_%2810098980413%29.jpg?width=2400',
    imagePage:'https://commons.wikimedia.org/wiki/File:Dragon_Blood_Tree,_Socotra_Island_(10098980413).jpg',
    photoCredit:'Rod Waddington · CC BY-SA 2.0',
    fact:'The famous umbrella shape of Socotra’s dragon’s blood tree is not decorative: its dense crown helps shade the roots and reduce water loss in an extremely dry climate.'
  }
];

const MIN_SCENERY_WIDTH=2200;
const MIN_SCENERY_HEIGHT=1000;

function loadHighQualityImage(image,item){
  image.hidden=true;
  image.removeAttribute('src');
  const candidate=new Image();
  candidate.onload=()=>{
    if(candidate.naturalWidth<MIN_SCENERY_WIDTH||candidate.naturalHeight<MIN_SCENERY_HEIGHT){
      image.dataset.quality='rejected';
      return;
    }
    image.src=candidate.src;
    image.hidden=false;
    image.dataset.quality='high';
    image.dataset.sourceWidth=String(candidate.naturalWidth);
    image.dataset.sourceHeight=String(candidate.naturalHeight);
  };
  candidate.onerror=()=>{image.dataset.quality='unavailable'};
  candidate.src=item.image;
}

async function renderRareWorldFact(){
  const start=new Date(new Date().getFullYear(),0,0);
  const day=Math.floor((new Date()-start)/86400000);
  const item=rareWorldFacts[(day-1)%rareWorldFacts.length];
  const image=$('#sceneryImage'),country=$('#sceneryCountry'),place=$('#sceneryPlace'),credit=$('#sceneryCredit'),card=$('#sceneryCard'),fact=$('#sceneryFactText');
  if(country) country.textContent=item.country;
  if(place) place.textContent=item.place;
  if(credit) credit.textContent=`Photo · ${item.photoCredit} · Fact · ${item.source}`;
  if(card) card.href=item.sourceUrl;
  if(fact) fact.textContent=item.fact;
  if(image){
    image.alt=`${item.place}, ${item.country}`;
    loadHighQualityImage(image,item);
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
