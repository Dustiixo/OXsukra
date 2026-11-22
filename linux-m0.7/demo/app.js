(() => {
let phase=0;
const target=document.querySelector('#dynamic');
document.querySelector('#step').addEventListener('click',()=>{
  phase++;
  // A real History API navigation event and a real DOM link replacement.
  history.pushState({phase},'',`/phase/${phase}`);
  const a=document.createElement('a');a.href=`/phase/${phase}/detail`;a.textContent=`Generated link ${phase}`;
  target.replaceChildren(a);
  document.querySelector('#count').textContent=`Phase ${phase}: live DOM changed`;
});
document.querySelector('#popup').addEventListener('click',()=>window.open('/popup','_blank','noopener'));
document.querySelector('#burst').addEventListener('click',async()=>{
  const jobs=Array.from({length:35},(_,i)=>fetch(`sample.json?request=${i}-${Date.now()}`,{cache:'no-store'}).catch(()=>null));
  await Promise.all(jobs);
  document.querySelector('#count').textContent='35 browser resource requests attempted';
});
})();
