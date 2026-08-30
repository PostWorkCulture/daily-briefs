const MIN_SCENERY_WIDTH=2200;
const MIN_SCENERY_HEIGHT=1000;

function loadHighQualityImage(image,item){
  image.hidden=true;
  image.removeAttribute('src');
  image.dataset.quality='checking';
  if(!item.image){
    image.dataset.quality='unavailable';
    return;
  }
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

function renderWorldFact(item={}){
  const image=$('#sceneryImage');
  const country=$('#sceneryCountry');
  const place=$('#sceneryPlace');
  const credit=$('#sceneryCredit');
  const imageCard=$('#sceneryCard');
  const factCard=$('#sceneryFact');
  const factLabel=$('#sceneryFactLabel');
  const factText=$('#sceneryFactText');
  const factSource=$('#sceneryFactSource');
  if(!item.id){
    if(factText) factText.textContent='Today’s verified fact is unavailable.';
    if(image) image.hidden=true;
    return;
  }
  if(country) country.textContent=item.locationContext||item.country||'Explore';
  if(place) place.textContent=item.place||'Somewhere remarkable';
  if(credit) credit.textContent=`Photo · ${item.photoCredit||'verified source'}`;
  if(imageCard) imageCard.href=item.sourceUrl;
  if(factCard) factCard.href=item.sourceUrl;
  if(factLabel) factLabel.textContent=`Insane fact of the day · ${item.category||'Wild place'}`;
  if(factText) factText.textContent=item.fact;
  if(factSource) factSource.textContent=`Fact source · ${item.source}`;
  if(image){
    image.alt=`${item.place}, ${item.locationContext||item.country}`;
    loadHighQualityImage(image,item);
  }
}

window.renderWorldFact=renderWorldFact;
if(typeof state!=='undefined'&&state.data?.worldFact)renderWorldFact(state.data.worldFact);
