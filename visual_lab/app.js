/* FlowMesh Visual Lab M0.2: LOCAL READ-ONLY trace viewer, no network or engine writes. */
(() => {
'use strict';
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clip = (s,n=180) => {let v=String(s??'');return v.length<=n?v:v.slice(0,n-1)+'…'};
const humanId = id => id==='root'?'Main goal':String(id).toUpperCase();
const sourceName = x => String(x??'').split(/[\\/]/).pop();
const STAGES={
  1:['01 / THE BASE','The machine is running. The screen is cryptic.','A faithful reconstruction of today’s FlowMesh controls and evidence logs. This is the starting point, not a redesigned engine.'],
  2:['02 / MAKE IT TALK','What happened. Why. Proof. Next.','Same recorded work, translated into plain English. No mystery numbers and no pretend AI thoughts.'],
  3:['03 / LIVING MAP','Watch a research idea split into paths.','Branches are visible, shared evidence forms connections, and three timelines stay separate.'],
  4:['04 / OPEN FLOW','Give it room to explore. Keep the receipts.','Everything together: living branches, readable activity, proof, and three cooperative responses when progress stalls.']
};
const BIG_TYPES=['session_created','source_imported','probe_launched','source_excerpt_verified','branch_parked','branch_reactivated','source_gap','prompt_revision','resource_allocation','tick_finished'];
let trace=window.FLOWMESH_DEMO_TRACE, stage=1, cursor=0, selected='root', policyMessage='Try a scenario. These are DESIGN SIMULATIONS, not backend operations.';

function validateTrace(t){
  if(!t||t.schema!=='ixo.flowmesh.visual-trace.v1'||!Array.isArray(t.events)||!t.branches||typeof t.branches!=='object'||!Array.isArray(t.findings)||t.events.length>8000||t.findings.length>1000) throw Error('Not a supported FlowMesh visual trace (or too large).');
  if(t.source_integrity!=='PASS') throw Error('Trace must come from a verified source session.');
  for(let i=0;i<t.events.length;i++) if(!Number.isInteger(t.events[i].seq)||i&&t.events[i].seq<=t.events[i-1].seq) throw Error('Trace has an invalid event sequence.');
  return true;
}
function seenEvents(){return trace.events.slice(0,cursor)}
function current(){const e=seenEvents();return e[e.length-1]||null}
function tick(){return seenEvents().reduce((n,e)=>e.type==='tick_finished'?Math.max(n,Number(e.tick)||0):n,0)}
function visibleBranches(){
  const map={root:{id:'root',parent:null,question:trace.goal||'Research goal',status:'active',parked_reason:null}};
  for(const e of seenEvents()){
    if(e.type==='probe_launched'&&e.branch) map[e.branch]={id:e.branch,parent:e.parent||'root',question:e.question||trace.branches[e.branch]?.question||'Research question',status:'active',parked_reason:null};
    if(e.type==='branch_parked'&&map[e.branch]){map[e.branch].status='parked';map[e.branch].parked_reason=e.reason||'unknown'}
    if(e.type==='branch_reactivated'&&map[e.branch]){map[e.branch].status='active';map[e.branch].parked_reason=null}
  }
  return map;
}
function evidenceSeen(){
  const keys=new Set(seenEvents().filter(x=>x.type==='source_excerpt_verified').map(x=>`${x.branch}/${x.source_id}`));
  return trace.findings.filter(x=>keys.has(`${x.branch}/${x.id}`));
}
function actualEdges(){
  const seen={};const out=[];const used=new Set();
  for(const e of seenEvents()){
    if(e.type!=='source_excerpt_verified'||!e.source_id||!e.branch)continue;
    if(!seen[e.source_id])seen[e.source_id]=[];
    for(const other of seen[e.source_id]){
      if(other===e.branch)continue;
      const id=[other,e.branch].sort().join('|')+'|'+e.source_id;
      if(!used.has(id)){used.add(id);out.push({a:other,b:e.branch,source_id:e.source_id})}
    }
    if(!seen[e.source_id].includes(e.branch))seen[e.source_id].push(e.branch);
  }
  return out;
}
function explain(e){
  if(!e) return {title:'Nothing played yet',what:'Press NEXT RECEIPT to reveal a real event.',why:'You are at the beginning of the session.',proof:'No receipt selected.',next:'Play the next receipt.'};
  const bid=humanId(e.branch||'root');
  switch(e.type){
    case 'session_created': return {title:'Research session started',what:'A research goal was registered.',why:'FlowMesh needs one main question to organize its branches.',proof:'Receipt #'+e.seq,next:'Load some local reference material.'};
    case 'source_imported':return {title:'A document entered the library',what:sourceName(e.name||'Local source')+' was indexed.',why:'Branches can only quote material they can actually read.',proof:'Source SHA-256: '+clip(e.sha256,22),next:'Check whether a branch finds relevant text.'};
    case 'resource_allocation':return {title:'Work time was divided',what:`${e.total_credits??'?'} of ${e.maximum??'?'} scheduling credits assigned.`,why:'Active branches share a limited work budget.',proof:'Allocation receipt #'+e.seq,next:'See whether that work finds new evidence.'};
    case 'probe_launched':return {title:'A new question branched off',what:bid+' is exploring: '+clip(e.question,130),why:'A bounded question can be worked on independently without deleting the parent.',proof:'Branch creation receipt #'+e.seq,next:'Follow the new path or its source evidence.'};
    case 'source_excerpt_verified':return {title:e.novel?'A new source excerpt was recorded':'A familiar passage was revisited',what:`${bid} matched passage ${e.source_id||'unknown'}.`,why:e.novel?'The excerpt was not yet in the recorded findings.':'The same source can be useful to multiple branches without becoming a new discovery.',proof:'SHA-256: '+clip(e.source_sha256||'',24),next:'Open the passage and judge what it actually supports.'};
    case 'branch_parked':return {title:'A branch was parked',what:`${bid} paused. Reason: ${e.reason||'unrecorded'}.`,why:'A stuck path should stop consuming time without losing its history.',proof:'Park receipt #'+e.seq,next:'Continue another branch, or bring in new evidence.'};
    case 'branch_reactivated':return {title:'A parked branch woke up',what:`${bid} resumed.`,why:'New relevant evidence can justify another bounded look.',proof:'Wake receipt #'+e.seq,next:'Check whether it finds something genuinely new.'};
    case 'source_gap':return {title:'No new evidence here',what:`${bid} could not find a fresh relevant excerpt.`,why:'Repeating the same search forever wastes limited work.',proof:'Gap receipt #'+e.seq,next:'Park this path, try a bounded alternative, or ask if access is missing.'};
    case 'prompt_revision':return {title:'The instructions evolved',what:clip(e.text||'A new instruction was recorded.',145),why:'The original prompt remains in history rather than being erased.',proof:'Prompt revision receipt #'+e.seq,next:'Compare old and new directions in the prompt timeline.'};
    case 'tick_finished':return {title:'One research cycle finished',what:'Tick '+e.tick+' is complete.',why:'This is a checkpoint, not necessarily a breakthrough.',proof:'Tick receipt #'+e.seq,next:'Inspect what the cycle actually changed.'};
    case 'snapshot_committed':return {title:'State checkpoint saved',what:'The session wrote a snapshot.',why:'Recorded state makes replay and consistency checks possible.',proof:'Revision '+e.revision,next:'Continue to the next recorded operation.'};
    default:return {title:'Activity recorded',what:'Event: '+e.type,why:'The record is part of the FlowMesh session history.',proof:'Receipt #'+e.seq,next:'Open the detailed event or continue.'};
  }
}
function syncTop(){
  const conf=STAGES[stage];$('stage-number').textContent=conf[0];$('stage-title').textContent=conf[1];$('stage-description').textContent=conf[2];
  document.querySelectorAll('.stage-tab').forEach(x=>{x.classList.toggle('on',Number(x.dataset.stage)===stage); x.setAttribute('aria-pressed',String(Number(x.dataset.stage)===stage))});
  $('seek').max=trace.events.length;$('seek').value=cursor;$('seek-label').textContent=`${cursor} / ${trace.events.length}`;
  $('previous').disabled=cursor===0;$('reset').disabled=cursor===0;$('next').disabled=cursor===trace.events.length;$('next-five').disabled=cursor===trace.events.length;
  $('mode-label').textContent=(trace.source_mode||'unknown').toUpperCase();
  $('data-badge').textContent=trace===window.FLOWMESH_DEMO_TRACE?'VERIFIED SAMPLE · OFFLINE':'LOADED LOCAL TRACE';
}
function syncBranchRail(){
  const b=visibleBranches();const ids=Object.keys(b);if(!b[selected])selected='root';
  $('counts').textContent=`${ids.filter(k=>b[k].status==='active').length} ACTIVE / ${ids.length} TOTAL · TICK ${tick()}`;
  $('branch-list').innerHTML=ids.map(id=>`<button class="branch ${b[id].status==='parked'?'parked':''} ${selected===id?'on':''}" data-bid="${esc(id)}"><span class="bullet"></span><b>${esc(id)}</b><small>${esc(b[id].status.toUpperCase())}</small></button>`).join('');
  $('selected-question').textContent=b[selected].question||'(No question yet)';
  const ev=seenEvents().filter(x=>x.branch===selected);
  const hits=ev.filter(x=>x.type==='source_excerpt_verified').length;
  $('selected-extra').textContent=`STATE: ${b[selected].status.toUpperCase()}\nEVIDENCE MATCHES: ${hits}\nPARENT: ${b[selected].parent||'none'}${b[selected].parked_reason?'\nREASON: '+b[selected].parked_reason:''}`;
  document.querySelectorAll('.branch').forEach(x=>x.onclick=()=>{selected=x.dataset.bid; render()});
}
function syncReceipt(){
  const e=current(), d=explain(e);
  $('event-seq').textContent=e?'#'+String(e.seq).padStart(3,'0'):'#000';
  $('event-title').textContent=d.title;
  $('event-summary').textContent=d.next;
  $('event-what').textContent=d.what;
  $('event-why').textContent=d.why;
  $('event-proof').textContent=d.proof;
  const peek=$('evidence-peek');
  const hit=e?.source_id&&e.type==='source_excerpt_verified'?trace.findings.find(x=>x.id===e.source_id):null;
  peek.hidden=!hit;
  if(hit)peek.innerHTML=`<small>ACTUAL EXCERPT · ${esc(sourceName(hit.file))} · VERIFIED SOURCE BYTES, NOT SCIENTIFIC TRUTH</small>${esc(clip(hit.text,850))}`;
  else peek.textContent='';
}
function section(title,right='REPLAY FROM REAL LOCAL RECEIPTS'){return `<div class="section-head"><strong>${esc(title)}</strong><small>${esc(right)}</small></div>`}
function base(){
  const ev=seenEvents(), docs=ev.filter(x=>x.type==='source_imported'), entries=ev.filter(x=>BIG_TYPES.includes(x.type)).slice(-18);
  const stats=`OFFLINE | TICK ${String(tick()).padStart(3,'0')} | ${Object.values(visibleBranches()).filter(b=>b.status==='active').length} ACTIVE / ${Object.keys(visibleBranches()).length} PATHWAYS | ${evidenceSeen().length} SOURCE EXCERPTS | ${trace.budget_per_tick} WORK CREDITS / TICK`;
  return section('Stage 01 · the current FlowMesh model','FAITHFUL RECONSTRUCTION')+`<div class="base-controls"><span>STEP 1</span><span>STEP 5</span><span>NEW PROBE</span><span>PARK</span><span>WAKE</span><span>FOCUS</span><span>REVISE PROMPT</span><span>IMPORT DOC</span><span>VERIFY</span></div><div class="base-stat">${esc(stats)}</div><div class="base-tabs"><span>FLOW / NETWORK</span><span>3 TIMELINES</span><span>GENERATION BRANCHES</span><span>RECEIPTS / EVENTS</span><span>SOURCE EVIDENCE</span></div><div class="technical-log panel-box">${entries.length?entries.map(e=>`<div><span class="good">#${String(e.seq).padStart(3,'0')} ${esc(e.type.toUpperCase())}</span><br>${esc(clip(JSON.stringify({branch:e.branch,tick:e.tick,reason:e.reason,source_id:e.source_id,question:e.question,sha256:e.sha256}),300))}</div>`).join(''):'<span class="muted">No events yet. Press NEXT RECEIPT.</span>'}</div><div class="callout">Same engine facts, but the screen makes you decode them. That is exactly what the next stage changes.</div>`;
}
function feed(){
  const d=explain(current()), recent=seenEvents().filter(e=>BIG_TYPES.includes(e.type)).slice(-4).reverse();
  return section('Stage 02 · everything becomes explainable','NOT MODEL THOUGHTS · ONLY RECORDED OPERATIONS')+`<div class="feed-grid"><div class="explain-card highlight"><small>WHAT JUST HAPPENED</small><strong>${esc(d.title)}</strong><p>${esc(d.what)}</p></div><div class="explain-card"><small>WHY IT MATTERS</small><strong>${esc(clip(d.why,105))}</strong></div><div class="explain-card proof"><small>SHOW ME THE PROOF</small><strong>${esc(d.proof)}</strong><p>Go to the source. Don't just trust a colored dot.</p></div><div class="explain-card next"><small>WHAT HAPPENS NEXT</small><strong>${esc(d.next)}</strong></div></div><div class="recent"><div class="eyebrow">RECENT REAL EVENTS</div>${recent.length?recent.map(e=>`<div class="recent-row"><b>#${String(e.seq).padStart(3,'0')}</b><span>${esc(explain(e).title)}</span></div>`).join(''):'<p class="muted">Nothing recorded yet.</p>'}</div>`;
}
function graphHTML(){
  const b=visibleBranches(),ids=Object.keys(b),positions={root:[330,155]},others=ids.filter(x=>x!=='root');
  others.forEach((id,i)=>{const ang=-Math.PI/2+(i/(Math.max(1,others.length-1)))*Math.PI;positions[id]=[330+Math.cos(ang)*235,175+Math.sin(ang)*120]});
  const edgeList=[];
  for(const id of others){const parent=b[id].parent;if(positions[parent])edgeList.push(`<line class="graph-edge" x1="${positions[parent][0]}" y1="${positions[parent][1]}" x2="${positions[id][0]}" y2="${positions[id][1]}" />`)}
  for(const link of actualEdges()) if(positions[link.a]&&positions[link.b]) edgeList.push(`<line class="graph-edge source" x1="${positions[link.a][0]}" y1="${positions[link.a][1]}" x2="${positions[link.b][0]}" y2="${positions[link.b][1]}" />`);
  const nodes=ids.map(id=>{const p=positions[id],status=b[id].status,short=clip(b[id].question,35);return `<g class="graph-node ${selected===id?'selected':''} ${status==='parked'?'parked':''}" data-graph-bid="${esc(id)}" transform="translate(${p[0]},${p[1]})" role="button" tabindex="0" aria-label="Select ${esc(id)}"><rect x="-76" y="-25" width="152" height="54" /><text text-anchor="middle" y="-3">${esc(humanId(id))}</text><text class="label-sub" text-anchor="middle" y="16">${status==='parked'?'PARKED':'ACTIVE'} · ${esc(short.slice(0,13))}</text></g>`}).join('');
  return `<svg class="node-graph" viewBox="0 0 660 340" role="img" aria-label="Real research branch tree and shared source links">${edgeList.join('')}${nodes}</svg>`;
}
function lanes(){
  const ev=seenEvents();const groups=[['ENGINE / WORK',e=>e.type==='tick_finished'||e.type==='resource_allocation',''],['PROMPT / EDITS',e=>e.type==='prompt_revision','prompt'],['SOURCE / EVIDENCE',e=>e.type==='source_imported'||e.type==='source_excerpt_verified','source']];
  return `<div class="lane-wrap"><div class="eyebrow">THREE SEPARATE TIMELINES</div>${groups.map(([title,filter,cls])=>`<div class="lane"><span>${title}</span><div class="lane-track" title="${esc(title)}">${ev.filter(filter).slice(-80).map(()=>`<i class="lane-mark ${cls}"></i>`).join('')}</div></div>`).join('')}</div>`;
}
function mapConcept(){
  const ev=seenEvents().filter(e=>e.type==='source_excerpt_verified'&&e.branch===selected),list=ev.slice(-3).reverse();
  return section('Stage 03 · follow the real connections','SOLID = PARENT · DASHED = SHARED EVIDENCE')+`<div class="graph-area">${graphHTML()}<div class="panel-box edge-note"><span class="pill green">● ${actualEdges().length} SHARED SOURCE LINKS</span><p><b>${esc(humanId(selected))}</b> investigates:</p><p>${esc(visibleBranches()[selected]?.question||'')}</p><p>${list.length?'Recent linked excerpts:':'No source excerpts linked to this branch yet.'}</p>${list.map(x=>`<p class="mono">#${esc(x.source_id)}</p><p>${esc(clip((trace.findings.find(f=>f.id===x.source_id)||{}).text||'Existing source match',115))}</p>`).join('')}</div></div>${lanes()}<div class="callout">Click a node. It changes what you inspect, not the actual research records. Lines come from recorded parent relations or genuine shared source IDs.</div>`;
}
function openFlow(){
  const d=explain(current());
  return section('Stage 04 · Open Flow','ALL THREE RESPONSES ENABLED · SIMULATION IS LABELLED')+`<div class="concept-layout"><div class="concept-top"><div><div class="overline">THE COMPLETE FOUNDATION</div><h2>Explore freely. Explain everything.</h2><p>Research can move across branches; user authority stays intact.</p></div><span class="pill green">● ${trace.source_integrity} SOURCE TRACE</span></div><div class="concept-columns"><div>${graphHTML()}${lanes()}</div><div class="policy"><span class="eyebrow">WHEN A BRANCH GETS STUCK</span><h3>Don't make me babysit it.</h3><div class="policy-cards"><div class="policy-row"><span>1</span><div><b>Park the dead end</b><p>Say why, preserve every receipt and release its work budget.</p></div></div><div class="policy-row"><span>2</span><div><b>Try another promising route</b><p>Only bounded read-only research, with attempts capped and user-parked branches respected.</p></div></div><div class="policy-row"><span>3</span><div><b>Ask me if needed</b><p>Only when permission, new input, or a consequential decision is required.</p></div></div></div></div></div><div class="policy"><span class="eyebrow">TRY THE DECISION RULES</span><div class="policy-test"><button data-policy="lead">PROMISING LEAD</button><button data-policy="empty">NO MORE LEADS</button><button data-policy="permission">NEEDS PERMISSION</button><button data-policy="userpark">I PARKED IT</button></div><div id="policy-output" class="policy-output">${esc(policyMessage)}</div></div><div class="callout"><b>Real latest receipt:</b> ${esc(d.title)} · ${esc(clip(d.what,120))}. Concept rules above are <b>not</b> wired to a live autonomous engine.</div></div>`;
}
function connectStage(){
  const m=$('main-stage');
  m.querySelectorAll('[data-graph-bid]').forEach(el=>{const go=()=>{selected=el.dataset.graphBid;render()};el.addEventListener('click',go);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});
  m.querySelectorAll('[data-policy]').forEach(el=>el.addEventListener('click',()=>{
    const key=el.dataset.policy;
    const answer={
      lead:'DESIGN SIMULATION: Park the exhausted path. Preserve receipts. Spawn one bounded read-only alternative, with a retry cap. Report its result; no user interruption necessary.',
      empty:'DESIGN SIMULATION: Park this path and explain the gap. No evidence-backed lead remains, so do NOT fabricate another one. Ask for an optional document or new direction.',
      permission:'DESIGN SIMULATION: Park the blocked operation, keep independent research going elsewhere, and request approval before accessing external or private data.',
      userpark:'DESIGN SIMULATION: The user deliberately parked this branch. Leave it parked. Other authorized research may continue, but do not override the user.'
    };
    policyMessage=answer[key]||policyMessage;
    const out=$('policy-output'); if(out)out.textContent=policyMessage;
  }));
}
function render(){syncTop();syncBranchRail();syncReceipt(); $('main-stage').innerHTML=({1:base,2:feed,3:mapConcept,4:openFlow}[stage])();connectStage()}
function move(n){cursor=Math.max(0,Math.min(trace.events.length,n));render()}
function loadTrace(obj){validateTrace(obj);trace=obj;cursor=0;selected='root';policyMessage='Try a scenario. These are DESIGN SIMULATIONS, not backend operations.';render()}
function bind(){
  document.querySelectorAll('.stage-tab').forEach(btn=>btn.addEventListener('click',()=>{stage=Number(btn.dataset.stage);render()}));
  $('next').addEventListener('click',()=>move(cursor+1));$('next-five').addEventListener('click',()=>move(cursor+5));$('previous').addEventListener('click',()=>move(cursor-1));$('reset').addEventListener('click',()=>move(0));$('seek').addEventListener('input',e=>move(Number(e.target.value)));
  $('how-works').addEventListener('click',()=>$('explainer').classList.remove('hidden'));$('close-explainer').addEventListener('click',()=>$('explainer').classList.add('hidden'));
  $('explainer').addEventListener('click',e=>{if(e.target===$('explainer'))$('explainer').classList.add('hidden')});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')$('explainer').classList.add('hidden')});
  $('load-file').addEventListener('click',()=>$('trace-input').click());
  $('trace-input').addEventListener('change',async e=>{
    const file=e.target.files?.[0];if(!file)return;
    try{if(file.size>5_000_000)throw Error('Trace is over the 5MB local-viewer limit.');loadTrace(JSON.parse(await file.text()));}
    catch(error){alert('Could not load trace: '+error.message)}
    finally{e.target.value=''}
  });
}
validateTrace(trace);bind();render();
})();
