function tonightTokens(title=''){
  const stop=new Set(['the','a','an','and','or','of','to','for','in','on','at','with','from','is','are','was','were','new','series','show','tv','apple','netflix','bbc','itv','channel','documentary','docuseries','crime','true','murder','scandal','review','trailer','season','episode','episodes','latest','watch','streaming','returns','return','explained']);
  return String(title).toLowerCase().replace(/[^a-z0-9\s]/g,' ').split(/\s+/).filter(x=>x.length>2&&!stop.has(x));
}
function tonightKey(item={}){
  const title=String(item.title||'');
  const low=title.toLowerCase();
  if(low.includes('silo')) return 'show:silo';
  const quoted=title.match(/[“"‘']([^”"’']{3,60})[”"’']/);
  if(quoted) return 'quoted:'+quoted[1].toLowerCase().replace(/\W+/g,'');
  return null;
}
function tonightSimilar(a,b){
  const ka=tonightKey(a),kb=tonightKey(b);
  if(ka&&kb&&ka===kb) return true;
  if(a?.url&&b?.url&&a.url===b.url) return true;
  const A=new Set(tonightTokens(a?.title)),B=new Set(tonightTokens(b?.title));
  if(!A.size||!B.size) return false;
  let overlap=0; A.forEach(x=>{if(B.has(x)) overlap++});
  const containment=overlap/Math.min(A.size,B.size);
  return overlap>=2&&containment>=0.67;
}
function dedupeTonight(items=[]){
  const kept=[];
  for(const item of items){
    if(!item?.title) continue;
    if(kept.some(existing=>tonightSimilar(existing,item))) continue;
    kept.push(item);
  }
  return kept;
}

const originalRenderWatch=typeof renderWatch==='function'?renderWatch:null;
if(originalRenderWatch){
  renderWatch=function(items=[]){originalRenderWatch(dedupeTonight(items).slice(0,5));};
  if(typeof state!=='undefined'&&state.data?.watch) renderWatch(state.data.watch);
}
