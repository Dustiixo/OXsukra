'use strict';
// Provenance-labelled experience client; Python owns all records and gates.
function switchExperience(){
  ['panel-ixo','panel-aixo','panel-dsoe'].forEach(id=>$(id).hidden=true);
  $('panel-experience').hidden=false;
  ['tab-ixo','tab-aixo','tab-dsoe'].forEach(id=>$(id).className='');
  $('tab-experience').className='active';
  refreshExperience();
}
function xpItem(parent,text){const node=el('div',text);node.className='item';parent.appendChild(node);}
async function refreshExperience(){
  try {
    const response=await fetch('/api/experience',{headers:{'X-IXO-Token':token},cache:'no-store'});
    const state=await response.json();
    if(!response.ok)throw Error(state.error||'Service offline');
    const r=state.report, s=state.general;
    const pct=n=>n===null?'NO OBSERVATIONS':(100*n).toFixed(1)+'%';
    $('exp-stats').textContent=`${r.observed_exposures} observed exposures · ${r.total_records} distinct records · IXO share of exposures ${pct(r.ixo_exposure_share)} · non-IXO learning domains ${r.non_ixo_learning_domains.length} · non-IXO held-out tasks ${r.non_ixo_heldout_task_cases}`;
    const warn=$('exp-warnings');warn.replaceChildren();
    if(!r.warnings.length)xpItem(warn,'Exposure metrics satisfy configured coverage checks; this is not proof of intelligence.');
    r.warnings.forEach(x=>xpItem(warn,'CHECK / '+x));
    const man=$('exp-manifest');man.replaceChildren();
    xpItem(man,`${s.selected} eligible items · ${s.by_origin.ixo_development||0} IXO · ${(s.by_origin.independent_project||0)+(s.by_origin.external_reference||0)} independent · no model training performed`);
    s.records.slice(0,16).forEach(x=>xpItem(man,`${x.project} / ${x.domain} / ${x.kind} / ${x.source_ref}`));
    if(s.records.length>16)xpItem(man,`+ ${s.records.length-16} more; inspect full manifest using the CLI`);
  }catch(err){$('exp-stats').textContent='EXPERIENCE ERROR: '+err.message}
}
async function experienceAction(data){
  try{
    const response=await fetch('/api/experience/action',{method:'POST',headers:{'X-IXO-Token':token,'Content-Type':'application/json'},body:JSON.stringify(data)});
    const result=await response.json();
    output(result.error||JSON.stringify(result));
    await refreshExperience();
    return result;
  }catch(err){output('EXPERIENCE ERROR: '+err.message)}
}
$('exp-sync').onclick=()=>experienceAction({action:'sync-ixo'});
$('exp-form').onsubmit=async event=>{
  event.preventDefault();
  const result=await experienceAction({action:'add',project:$('exp-project').value,
    domain:$('exp-domain').value,origin:$('exp-origin').value,
    source_ref:$('exp-source').value,content:$('exp-content').value});
  if(result?.ok)$('exp-content').value='';
};
