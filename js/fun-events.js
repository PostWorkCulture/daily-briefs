/* Calendar-month window uses the household's London date, including year rollover. */
(function(root){
  function funEventInWindow(item,today){
    today=today||new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/London',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    const valid=value=>typeof value==='string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10)===value;
    if(!valid(today)||!valid(item.startDate)||!valid(item.endDate))return false;
    const [year,month]=today.split('-').map(Number);
    const cutoff=new Date(Date.UTC(year,month+1,1)).toISOString().slice(0,10);
    return item.startDate<=item.endDate && item.endDate>=today && item.startDate<cutoff;
  }
  root.funEventInWindow=funEventInWindow;
  if(typeof module!=='undefined')module.exports=funEventInWindow;
})(globalThis);
