/* IXO / Spatial Chamber M0.3 - rendered geometry is an artistic projection of a verified FlowMesh trace. */
(() => {'use strict';
const $ = id => document.getElementById(id);
const c=$('field'), g=c.getContext('2d',{alpha:false});
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const short=(s,n=110)=>{s=String(s??'');return s.length>n?s.slice(0,n-1)+'…':s};
const goodType=new Set(['source_excerpt_verified','source_imported','branch_reactivated']);
const redType=new Set(['branch_parked','source_gap']);
const branchType=new Set(['probe_launched','branch_parked','branch_reactivated']);
const allowedSchema='ixo.flowmesh.visual-trace.v1';
let trace=window.FLOWMESH_TRACE;
let cursor=0, selected='root', present={}, visible={}, branches={}, selectedEvent=null;
let playing=false, playTimer=null, view={yaw:-.52,pitch:.2,zoom:1.16,targetX:0,targetY:0,targetZ:0}, desired={...view};
let W=0,H=0,dpr=1,drag=false,dragMoved=false,dragStart=null,lastPointer=null;
let hitPoints=[],flashUntil=0,flashBranch='root',simTime=0, toastTimer=0;
let reduced=window.matchMedia('(prefers-reduced-motion:reduce)').matches;
let live=false, liveDataVersion=-1;
function hash(s){s=String(s);let h=2166136261;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),16777619)}return h>>>0}
function rnd(seed){return (Math.sin(seed*127.1+78.233)*43758.5453123)%1}
function pseudo(n){let x=hash('seed:'+n);x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967295}
const stars=Array.from({length:225},(_,i)=>({x:(pseudo(i*3)-.5)*1900,y:(pseudo(i*3+1)-.5)*1100,z:(pseudo(i*3+2)-.5)*1600,r:.4+pseudo(i+800)*1.2}));
function validate(t){
 if(!t||t.schema!==allowedSchema||t.source_integrity!=='PASS'||!Array.isArray(t.events)||!Array.isArray(t.findings)||typeof t.branches!=='object'||!t.branches||Array.isArray(t.branches))throw Error('Unsupported or unverified FlowMesh visual trace.');
 if(t.events.length>12000||t.findings.length>1500||Object.keys(t.branches).length>180) throw Error('Trace exceeds the local viewer limits.');
 let prev=0;for(const e of t.events){if(!e||!Number.isInteger(e.seq)||e.seq<=prev||typeof e.type!=='string')throw Error('The receipt sequence is invalid.');prev=e.seq}
 for(const k of Object.keys(t.branches)){if(k.length>80)throw Error('Branch identifier too long.')}return true;
}
function worldPos(id){if(id==='root')return {x:0,y:6,z:0};const ids=Object.keys(trace.branches||{}).filter(x=>x!=='root').sort();let i=Math.max(0,ids.indexOf(id));let a=i*2.399963229728653 + .62, r=280+Math.floor(i/6)*80;return {x:Math.cos(a)*r,y:Math.sin(i*1.65)*90+20,z:Math.sin(a)*r};}
function at(n){return trace.events.slice(0,n)}
function buildProjection(){
 let events=at(cursor), bs={root:{id:'root',parent:null,question:trace.goal||'Research goal',status:'active',created_tick:0}}, sourceUse=new Map(), links=[], findings=[];
 for(const e of events){
  if(e.type==='probe_launched'&&e.branch){bs[e.branch]={id:e.branch,parent:e.parent||'root',question:e.question||trace.branches[e.branch]?.question||'Research path',status:'active',created_tick:e.tick||1}}
  if(e.type==='branch_parked'&&bs[e.branch])bs[e.branch].status='parked';
  if(e.type==='branch_reactivated'&&bs[e.branch])bs[e.branch].status='active';
  if(e.type==='source_excerpt_verified'&&bs[e.branch]&&e.source_id){
   findings.push(e);
   const prev=sourceUse.get(e.source_id)||new Set();for(const other of prev){if(other!==e.branch){let key=[e.branch,other].sort().join('|')+'|'+e.source_id;links.push({key,a:other,b:e.branch,source:e.source_id})}}
   prev.add(e.branch);sourceUse.set(e.source_id,prev);
  }
 }
 return {bs,findings,links};
}
function currentEvent(){return cursor>0?trace.events[cursor-1]:null}
function sourceText(e){return trace.findings.find(f=>f.id===e.source_id&&f.branch===e.branch)?.text || trace.findings.find(f=>f.id===e.source_id)?.text || ''}
function explain(e){if(!e)return {kind:'READY',title:'The field is ready.',description:'Start playback, scrub the timeline, or pick a branch to inspect recorded research.',why:'No event has been selected yet.',proof:'No recorded event selected.',digest:'LOCAL / READ-ONLY'};
 const bid=String(e.branch||'root').toUpperCase();let base={kind:String(e.type).replaceAll('_',' ').toUpperCase(),title:'An operation was recorded.',description:`Recorded ${e.type} at receipt ${e.seq}.`,why:'This event is preserved in the FlowMesh receipt sequence.',proof:`Event #${e.seq}`,digest:'SOURCE VERIFIED / EXPORTER'};
 switch(e.type){
  case 'session_created':return {...base,title:'A new investigation began.',description:'The research session was created in '+String(e.mode||trace.source_mode||'offline')+' mode.',why:'Everything else in the chamber branches from this starting point.',proof:'Receipt #'+e.seq+' · session_created'};
  case 'source_imported':return {...base,title:'A document entered the field.',description:short(e.name,170),why:'A local source is now available to investigate. Importing is not a discovery.',proof:'Recorded source SHA-256',digest:short(e.sha256,64)};
  case 'probe_launched':return {...base,title:'A new route split from the original.',description:short(e.question,180),why:'FlowMesh opened a separate research question instead of overwriting the parent branch.',proof:`${bid} · parent ${e.parent||'root'} · ${e.reason||'recorded launch'}`};
  case 'source_excerpt_verified':return {...base,kind:'SOURCE / VERIFIED',title:e.novel?'New evidence was attached.':'A known source was revisited.',description:short(sourceText(e)||'A recorded source passage was linked to a research path.',210),why:e.novel?'This excerpt adds a new source link to the recorded history.':'This source was used again. Reuse is not a new discovery.',proof:`${bid} · ${e.source_id} · relevance ${Number(e.relevance||0).toFixed(3)}`,digest:short(e.source_sha256,64)};
  case 'branch_parked':return {...base,kind:'PATH / STOPPED',title:'This route was parked.',description:`${bid} stopped receiving work.`,why:'A parked branch remains in the history. It is not deleted.',proof:`Reason: ${e.reason||'not specified'}`};
  case 'branch_reactivated':return {...base,kind:'PATH / REACTIVATED',title:'A dormant route reopened.',description:`${bid} became active again.`,why:'New evidence or an allowed action can restore a previously parked investigation.',proof:`Recorded reactivation, receipt #${e.seq}`};
  case 'resource_allocation':return {...base,kind:'ENGINE / ALLOCATION',title:'Work was distributed.',description:Object.entries(e.credits||{}).map(([k,v])=>`${k}: ${v}`).join(' / ')+' work credits',why:'These are scheduler units, not CPU/GPU utilization or model intelligence.',proof:`Tick ${e.tick||'?'} · ${e.total_credits||'?'} / ${e.maximum||'?'} credits`};
  case 'prompt_revision':return {...base,kind:'HUMAN / DIRECTION',title:'The research instructions changed.',description:short(e.text,210),why:'The revision belongs to the prompt timeline; it does not rewrite old events.',proof:`Receipt #${e.seq} · prompt revision`};
  case 'source_gap':return {...base,kind:'SOURCE / GAP',title:'This question hit a dead end.',description:`${bid} could not find additional source evidence.`,why:'No evidence is a limit, not permission to invent an answer.',proof:`Gap recorded: ${e.reason||'no further source match'}`};
  case 'tick_finished':return {...base,kind:'ENGINE / TICK',title:'One research cycle finished.',description:`Tick ${e.tick} completed.`,why:'A completed cycle is not necessarily a discovery.',proof:`Scheduler receipt #${e.seq}`};
  case 'snapshot_committed':return {...base,kind:'HISTORY / SNAPSHOT',title:'The history was checkpointed.',description:`Revision ${e.revision} was recorded.`,why:'The system preserves state so previous decisions remain inspectable.',proof:`Checkpoint receipt #${e.seq}`};
  default:return base;
 }
}
function setText(id,val){$(id).textContent=String(val??'')}
function statusTick(){let n=0;for(const e of at(cursor))if(e.type==='tick_finished')n=Math.max(n,e.tick||0);return n}
function renderUI(){
 const state=buildProjection();branches=state.bs;visible=state;selectedEvent=currentEvent();
 if(!branches[selected])selected='root';
 const d=explain(selectedEvent);const color=selectedEvent&&redType.has(selectedEvent.type)?'red':selectedEvent&&goodType.has(selectedEvent.type)?'green':'blue';
 setText('receipt-num','#'+String(selectedEvent?.seq||0).padStart(3,'0'));setText('event-kind',d.kind);$('event-kind').dataset.color=color;
 setText('event-title',d.title);setText('event-description',d.description);setText('event-why',d.why);setText('proof',d.proof);setText('proof-digest',d.digest);
 setText('selected-label',selected==='root'?'ROOT / MAIN GOAL':selected.toUpperCase()+' / RESEARCH PATH');setText('selected-question',branches[selected].question);setText('selected-meta','STATUS / '+branches[selected].status.toUpperCase());
 setText('goal',short(trace.goal,160));setText('path-count',`${String(Object.values(branches).filter(x=>x.status==='active').length).padStart(2,'0')} / ${String(Object.keys(branches).length).padStart(2,'0')}`);
 setText('current-index',String(cursor).padStart(3,'0'));setText('total-index',String(trace.events.length).padStart(3,'0'));setText('last-event-time','TICK '+String(statusTick()).padStart(3,'0'));
 const list=$('paths');list.replaceChildren();for(const b of Object.values(branches)){
  const btn=document.createElement('button');btn.className='path'+(selected===b.id?' active':'')+(b.status==='parked'?' parked':'');btn.dataset.branch=b.id;btn.type='button';btn.setAttribute('aria-label','Focus path '+b.id);btn.setAttribute('aria-pressed',selected===b.id?'true':'false');
  const dot=document.createElement('span');dot.className='state-dot';const body=document.createElement('span');body.className='path-copy';const name=document.createElement('strong');name.textContent=b.id==='root'?'ROOT / ORIGIN':b.id.toUpperCase();const desc=document.createElement('small');desc.textContent=short(b.question,57);body.append(name,desc);const num=document.createElement('span');num.className='path-number';num.textContent=b.status==='parked'?'//':'›';btn.append(dot,body,num);btn.addEventListener('click',()=>selectBranch(b.id,true));list.append(btn);
 }
 $('seek').max=String(trace.events.length);$('seek').value=String(cursor);
 for(const [lane,filter] of [['engine',e=>['tick_finished','resource_allocation','snapshot_committed'].includes(e.type)],['prompt',e=>e.type==='prompt_revision'],['evidence',e=>['source_excerpt_verified','source_imported','source_gap'].includes(e.type)]]){
  const p=$('lane-'+lane);p.replaceChildren();for(let i=0;i<trace.events.length;i++)if(filter(trace.events[i])){const tick=document.createElement('i');tick.className='lane-mark '+(lane==='prompt'?'prompt':lane==='evidence'?'evidence':'')+(i<cursor?' on':' future');tick.style.left=`${((i+.5)/Math.max(1,trace.events.length))*100}%`;tick.title=`#${trace.events[i].seq} ${trace.events[i].type}`;p.append(tick)}
 }
}
function selectBranch(id,focus=false){if(!branches[id])return;selected=id;if(focus)focusBranch(id);renderUI();showToast(`${id.toUpperCase()} / ${branches[id].status.toUpperCase()} · ${short(branches[id].question,75)}`)}
function seek(n,flash=false){cursor=clamp(Math.round(n),0,trace.events.length);const e=currentEvent();if(flash&&e){flashUntil=performance.now()+1050;flashBranch=e.branch||'root'}renderUI()}
function setPlaying(b){playing=b;setText('play',playing?'❚❚':'▶');$('play').setAttribute('aria-label',playing?'Pause replay':'Play recorded events');if(playTimer)clearInterval(playTimer);playTimer=null;if(playing){if(cursor>=trace.events.length)seek(0);playTimer=setInterval(()=>{if(cursor>=trace.events.length){setPlaying(false);return}seek(cursor+1,true)},560)}}
function load(t,opts={}){validate(t);const keep=!!opts.keep;if(keep&&cursor!==trace.events.length){}else{cursor=t.events.length}trace=t;selected='root';renderUI();showToast(opts.live?'LIVE SOURCE / VERIFIED RECEIPT CHAIN':'LOCAL TRACE / LOADED');}
function showToast(s){let t=$('toast');t.textContent=s;t.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),2200)}
function resize(){const r=c.getBoundingClientRect();W=r.width;H=r.height;dpr=Math.min(2,window.devicePixelRatio||1);c.width=Math.max(1,Math.round(W*dpr));c.height=Math.max(1,Math.round(H*dpr));g.setTransform(dpr,0,0,dpr,0,0)}
function project(pt){let x=pt.x-view.targetX,y=pt.y-view.targetY,z=pt.z-view.targetZ;let yy=view.yaw,pi=view.pitch;let rx=x*Math.cos(yy)-z*Math.sin(yy),rz=x*Math.sin(yy)+z*Math.cos(yy);let ry=y*Math.cos(pi)-rz*Math.sin(pi),dz=y*Math.sin(pi)+rz*Math.cos(pi);let factor=1000/(1000+dz*.72);return {x:W*.525+rx*factor*view.zoom,y:H*.49-ry*factor*view.zoom,z:dz,scale:factor*view.zoom}}
function line3(a,b,color,width=1,alpha=1){const A=project(a),B=project(b);g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.beginPath();g.moveTo(A.x,A.y);g.lineTo(B.x,B.y);g.stroke();g.globalAlpha=1}
function drawGrid(){
 const horizon=H*.79,grad=g.createRadialGradient(W*.525,H*.45,0,W*.525,H*.5,W*.64);grad.addColorStop(0,'#111d2b');grad.addColorStop(.45,'#070e19');grad.addColorStop(1,'#02050a');g.fillStyle=grad;g.fillRect(0,0,W,H);
 const glow=g.createRadialGradient(W*.49,H*.51,40,W*.49,H*.51,W*.43);glow.addColorStop(0,'rgba(57,109,154,.115)');glow.addColorStop(.65,'rgba(25,48,67,.05)');glow.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=glow;g.fillRect(0,0,W,H);
 for(let i=-13;i<=13;i++){let alpha=i===0?.16:.045;let p={x:i*75,y:-280,z:0};line3({x:i*75,y:-280,z:-1200},{x:i*75,y:-280,z:1200},'#7da7d4',i===0?.9:.5,alpha)}
 for(let j=-16;j<=16;j++){line3({x:-1200,y:-280,z:j*75},{x:1200,y:-280,z:j*75},'#7da7d4',.55,j%5===0?.14:.055)}
 // Suspended depth slices: guide geometry, not computation.
 for(let a=0;a<4;a++){let level=-190+a*95;let col=a===1?'#6589b6':'#304b6a';for(let t=-5;t<=5;t++){line3({x:-710,y:level,z:t*165},{x:710,y:level,z:t*165},col,.55,.055)}}
 for(let i=0;i<stars.length;i++){let s=stars[i],p=project(s);if(p.x<0||p.x>W||p.y<0||p.y>H)continue;g.fillStyle=i%11===0?'rgba(182,223,245,.55)':'rgba(136,169,198,.22)';g.fillRect(p.x,p.y,s.r,s.r)}
 g.strokeStyle='rgba(126,163,191,.1)';g.lineWidth=1;for(let i=0;i<5;i++){let r=100+i*63;g.beginPath();g.ellipse(W*.525,H*.49,r*view.zoom,r*.38*view.zoom,-.12,0,Math.PI*2);g.stroke()}
 // cinematic sidebars, without obscuring activity
 let left=g.createLinearGradient(0,0,W*.28,0);left.addColorStop(0,'rgba(1,3,8,.8)');left.addColorStop(1,'rgba(1,3,8,0)');g.fillStyle=left;g.fillRect(0,100,W*.33,H-270);
 let right=g.createLinearGradient(W*.74,0,W,0);right.addColorStop(0,'rgba(1,3,8,0)');right.addColorStop(1,'rgba(1,3,8,.85)');g.fillStyle=right;g.fillRect(W*.71,100,W*.29,H-270);
}
function drawPath(points,color,width=1.1,opacity=1){g.globalAlpha=opacity;g.strokeStyle=color;g.lineWidth=width;g.beginPath();points.forEach((p,i)=>{const k=project(p);if(i===0)g.moveTo(k.x,k.y);else g.lineTo(k.x,k.y)});g.stroke();g.globalAlpha=1}
function drawConnections(){
 const b=branches;
 for(const [id,n] of Object.entries(b)){if(id==='root'||!b[n.parent])continue;let A=worldPos(n.parent),B=worldPos(id),distance=Math.hypot(A.x-B.x,A.y-B.y,A.z-B.z);
 const pts=Array.from({length:26},(_,i)=>{const t=i/25;return {x:lerp(A.x,B.x,t),y:lerp(A.y,B.y,t)+Math.sin(Math.PI*t)*(-28-.09*distance),z:lerp(A.z,B.z,t)}});
 drawPath(pts,'#a8cbe8',1.5,n.status==='parked'?.26:.51);drawPath(pts,'#e5f3ff',.3,n.status==='parked'?.14:.31);
 }
 let links=visible.links||[];const used=new Set();for(const l of links){if(!b[l.a]||!b[l.b])continue;let unique=[l.a,l.b].sort().join('|');if(used.has(unique))continue;used.add(unique);
 let A=worldPos(l.a),B=worldPos(l.b),pts=Array.from({length:30},(_,i)=>{let t=i/29;return {x:lerp(A.x,B.x,t),y:lerp(A.y,B.y,t)+70*Math.sin(Math.PI*t),z:lerp(A.z,B.z,t)+95*Math.sin(Math.PI*t)}});
 g.setLineDash([3,9]);drawPath(pts,'#77ffd0',1,Math.min(.46,.12+links.filter(x=>[x.a,x.b].sort().join('|')===unique).length*.045));g.setLineDash([]);
 }
}
function ring(center,radius,axis,color,alpha,time,thickness=1){let pts=[];for(let i=0;i<=80;i++){let a=i*Math.PI*2/80+time;let xx=Math.cos(a)*radius,zz=Math.sin(a)*radius;
 pts.push(axis===0?{x:center.x+xx,y:center.y+zz*.27,z:center.z+zz}:axis===1?{x:center.x+xx*.2,y:center.y+Math.sin(a)*radius*.85,z:center.z+Math.cos(a)*radius}: {x:center.x+xx,y:center.y+Math.sin(a)*radius*.6,z:center.z+Math.sin(a)*radius*.28})}
 drawPath(pts,color,thickness,alpha)
}
function polygon(vertices,color,opacity,lineWidth=1){const pts=vertices.map(project);g.globalAlpha=opacity;g.strokeStyle=color;g.lineWidth=lineWidth;g.beginPath();pts.forEach((p,i)=>i?g.lineTo(p.x,p.y):g.moveTo(p.x,p.y));g.closePath();g.stroke();g.globalAlpha=1}
function drawNode(id,node,time){let p=worldPos(id),p2=project(p),root=id==='root',sel=id===selected,park=node.status==='parked';let rad=(root?73:51),color=park?'#ff615c':sel?'#e9f5ff':'#79bbff';let pulse=simTime<flashUntil&&flashBranch===id?Math.max(0,(flashUntil-simTime)/1050):0;
 // activity marker corresponds to a selected receipt. Persistent ring oscillations are decorative.
 let glowRad=(root?117:89)*p2.scale*(1+pulse*.22);
 let glow=g.createRadialGradient(p2.x,p2.y,1,p2.x,p2.y,glowRad);glow.addColorStop(0,park?'rgba(255,70,67,.23)':sel?'rgba(179,219,255,.29)':'rgba(55,124,186,.18)');glow.addColorStop(.45,park?'rgba(255,70,67,.09)':'rgba(52,120,184,.09)');glow.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=glow;g.beginPath();g.arc(p2.x,p2.y,glowRad,0,Math.PI*2);g.fill();
 let spin=reduced?0:time*.08,detail=rad;
 ring(p,rad*1.5,0,park?'#f36f71':'#88c4ff',sel?.48:.25,spin,sel?1.4:.85);
 ring(p,rad*1.88,1,park?'#e85258':'#809dce',sel?.24:.13,-spin*.45,.8);
 ring(p,rad*1.28,2,sel?'#d2e6f3':'#a0c2df',sel?.38:.2,spin*.7,.65);
 const faces=[];const steps=8;for(let i=0;i<steps;i++){let a=2*Math.PI*i/steps+spin, b=2*Math.PI*(i+1)/steps+spin;
 let va={x:p.x+Math.cos(a)*detail,y:p.y+Math.sin(a)*detail*.52,z:p.z+Math.sin(a)*detail*.7},vb={x:p.x+Math.cos(b)*detail,y:p.y+Math.sin(b)*detail*.52,z:p.z+Math.sin(b)*detail*.7};faces.push([va,vb,{x:p.x,y:p.y+detail*.82,z:p.z}]);faces.push([va,vb,{x:p.x,y:p.y-detail*.82,z:p.z}]);}
 for(let i=0;i<faces.length;i++)polygon(faces[i],color,sel?.48:.27,.6);
 const pp={x:p.x,y:p.y+detail*.82,z:p.z},pn={x:p.x,y:p.y-detail*.82,z:p.z};line3(pp,pn,color,1.3,sel?.56:.28);
 // center point
 g.beginPath();g.arc(p2.x,p2.y,root?4.1*p2.scale:3.2*p2.scale,0,Math.PI*2);g.fillStyle=park?'#ff6b66':sel?'#ecfaff':'#8ac2ec';g.fill();
 // focus accents
 if(sel){let r=78*p2.scale;g.strokeStyle='rgba(220,240,255,.75)';g.lineWidth=1.2;for(let k=0;k<4;k++){let a=k*Math.PI/2+.22;g.beginPath();g.arc(p2.x,p2.y,r,a,a+.3);g.stroke()}}
 // labels: always grounded in a known branch, anchored in 3D space
 let label=id==='root'?'ORIGIN / ROOT':id.toUpperCase();let anchorY=p2.y-((root?86:74)*p2.scale);
 g.textAlign='center';g.fillStyle='#f2f4f3';g.font=`${sel?'bold 13px':'11px'} Consolas,monospace`;g.fillText(label,p2.x,anchorY);g.fillStyle=park?'#ff6d69':sel?'#9dffe3':'#83adcb';g.font='9px Consolas,monospace';g.fillText(park?'PARKED':root?'MAIN OBJECTIVE':'RESEARCH / ACTIVE',p2.x,anchorY+17);g.textAlign='start';
 hitPoints.push({id,x:p2.x,y:p2.y,r:Math.max(28,detail*p2.scale*1.3),z:p2.z});
 if(pulse){g.strokeStyle=park?'rgba(255,115,110,.8)':'rgba(139,250,211,.8)';g.lineWidth=1.5;g.globalAlpha=pulse;g.beginPath();g.arc(p2.x,p2.y,(1.9+(1-pulse)*2.4)*rad*p2.scale,0,Math.PI*2);g.stroke();g.globalAlpha=1}
}
function drawEvidence(time){let e=currentEvent();if(!e||e.type!=='source_excerpt_verified'||!branches[e.branch])return;const p=worldPos(e.branch),v=project(p);let phase=clamp((flashUntil-time)/1050,0,1);if(phase<=0)return;
 // this burst is tied only to a real source excerpt receipt
 for(let i=0;i<14;i++){let a=i*2.399,dist=(1-phase)*150+16;let px=v.x+Math.cos(a)*dist,py=v.y+Math.sin(a)*dist*.65;g.strokeStyle='rgba(124,255,212,'+(phase*.8)+')';g.lineWidth=.9;g.beginPath();g.moveTo(px,py);g.lineTo(px+Math.cos(a)*16*phase,py+Math.sin(a)*15*phase);g.stroke()}
}
function drawVignette(){const vg=g.createRadialGradient(W*.52,H*.5,W*.22,W*.52,H*.5,W*.68);vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,'rgba(0,0,0,.6)');g.fillStyle=vg;g.fillRect(0,0,W,H);
 // targeting reticle, subtle pixel-thin marks
 g.strokeStyle='rgba(172,207,236,.20)';g.lineWidth=.8;const x=W*.525,y=H*.49;for(const s of [-1,1]){g.beginPath();g.moveTo(x+s*182,y);g.lineTo(x+s*198,y);g.moveTo(x,y+s*168);g.lineTo(x,y+s*183);g.stroke()}
}
function renderFrame(t){simTime=t;if(W!==c.clientWidth||H!==c.clientHeight)resize();for(const k of ['yaw','pitch','zoom','targetX','targetY','targetZ'])view[k]+= (desired[k]-view[k])*.09;
 hitPoints=[];drawGrid();drawConnections();
 // Sort by projected depth, so nearer branches render above distant branches.
 const entries=Object.entries(branches).sort((a,b)=>project(worldPos(a[0])).z-project(worldPos(b[0])).z);
 for(const [id,n] of entries)drawNode(id,n,t/1000);
 drawEvidence(t);drawVignette();requestAnimationFrame(renderFrame)}
function focusBranch(id){let p=worldPos(id);desired.targetX=p.x*.8;desired.targetY=p.y*.75;desired.targetZ=p.z*.8;desired.zoom=Math.max(.95,desired.zoom)}
function resetCamera(){desired={yaw:-.52,pitch:.2,zoom:1.16,targetX:0,targetY:0,targetZ:0};showToast('VIEW / RECENTERED')}
function bindCanvas(){
 c.addEventListener('pointerdown',e=>{drag=true;dragMoved=false;dragStart={x:e.clientX,y:e.clientY};lastPointer={x:e.clientX,y:e.clientY};c.setPointerCapture(e.pointerId)});
 c.addEventListener('pointermove',e=>{if(!drag)return;let dx=e.clientX-lastPointer.x,dy=e.clientY-lastPointer.y;dragMoved=dragMoved||Math.hypot(e.clientX-dragStart.x,e.clientY-dragStart.y)>5;desired.yaw+=dx*.005;desired.pitch=clamp(desired.pitch-dy*.004,-.75,.9);lastPointer={x:e.clientX,y:e.clientY}});
 c.addEventListener('pointerup',e=>{if(!drag)return;drag=false;if(dragMoved)return;const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let closest=null,dist=Infinity;for(const k of hitPoints){const d=Math.hypot(k.x-x,k.y-y);if(d<k.r&&d<dist){closest=k;dist=d}}if(closest)selectBranch(closest.id,true)});
 c.addEventListener('pointercancel',()=>drag=false);
 c.addEventListener('wheel',e=>{e.preventDefault();desired.zoom=clamp(desired.zoom*Math.exp(-e.deltaY*.00075),.48,2.3)},{passive:false});
}
function bindControls(){
 $('first').addEventListener('click',()=>{setPlaying(false);seek(0,true)});$('previous').addEventListener('click',()=>{setPlaying(false);seek(cursor-1,true)});$('play').addEventListener('click',()=>setPlaying(!playing));$('next').addEventListener('click',()=>{setPlaying(false);seek(cursor+1,true)});$('last').addEventListener('click',()=>{setPlaying(false);seek(trace.events.length,true)});$('seek').addEventListener('input',e=>{setPlaying(false);seek(Number(e.target.value),true)});
 $('inspect').addEventListener('click',()=>{const on=document.body.classList.toggle('inspect-open');$('inspect').setAttribute('aria-expanded',on?'true':'false')});$('reset-view').addEventListener('click',resetCamera);$('focus').addEventListener('click',()=>{focusBranch(selected);showToast('FOCUS / '+selected.toUpperCase())});
 $('load-trace').addEventListener('click',()=>$('trace-file').click());$('trace-file').addEventListener('change',async e=>{const f=e.target.files?.[0];if(!f)return;try{if(f.size>8_000_000)throw Error('Trace exceeds 8MB.');load(JSON.parse(await f.text()));setPlaying(false);setText('mode','PRIVATE TRACE / LOCAL FILE')}catch(err){showToast('LOAD REJECTED / '+err.message)}finally{e.target.value=''}});
 $('help').addEventListener('click',()=>$('about').classList.remove('hidden'));$('close-about').addEventListener('click',()=>$('about').classList.add('hidden'));$('about').addEventListener('click',e=>{if(e.target===$('about'))$('about').classList.add('hidden')});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('about').classList.add('hidden');return}if(['INPUT','TEXTAREA'].includes(document.activeElement?.tagName))return;if(e.key==='ArrowRight'){setPlaying(false);seek(cursor+1,true)}else if(e.key==='ArrowLeft'){setPlaying(false);seek(cursor-1,true)}else if(e.code==='Space'){e.preventDefault();setPlaying(!playing)}else if(e.key==='r'||e.key==='R')resetCamera()});
}
async function poll(){if(!live)return;try{let key=new URLSearchParams(location.search).get('key')||'';if(!key)throw Error('No authorized local bridge token');let res=await fetch('/api/trace?key='+encodeURIComponent(key),{cache:'no-store',credentials:'same-origin'});if(!res.ok)throw Error('Integrity verification blocked live export');let obj=await res.json();validate(obj);let newHash=hash(JSON.stringify(obj.events.map(e=>e.seq)));if(liveDataVersion!==newHash){let wasEnd=cursor===trace.events.length,oldSelected=selected;trace=obj;if(wasEnd)cursor=obj.events.length;else cursor=clamp(cursor,0,obj.events.length);renderUI();if(branches[oldSelected])selected=oldSelected;renderUI();liveDataVersion=newHash}}catch(err){setText('mode','LIVE LINK / BLOCKED');console.warn('FlowMesh local live bridge:',err.message)}}
function start(){validate(trace);cursor=trace.events.length;renderUI();resize();bindCanvas();bindControls();requestAnimationFrame(renderFrame);window.addEventListener('resize',resize);
 // Only talks to an explicit local 127.0.0.1 server, never to external hosts.
 if(['127.0.0.1','localhost'].includes(location.hostname)&&location.protocol==='http:'&&new URLSearchParams(location.search).has('key')){live=true;setText('mode','LOCAL LIVE BRIDGE / READ-ONLY');poll();setInterval(poll,4500)}
 // For reproducible browser smoke tests. Does not grant mutation capabilities.
 window.__IXO_TEST__={getState:()=>({cursor,total:trace.events.length,selected,branchCount:Object.keys(branches).length,sourceCount:visible.findings.length,edgeCount:visible.links.length,playing,live}),step:()=>seek(cursor+1,true),load:(t)=>load(t),project:(id)=>project(worldPos(id))};
}
try{start()}catch(err){console.error(err);setText('event-title','TRACE COULD NOT BE VERIFIED');setText('event-description',err.message);setText('mode','BLOCKED / INVALID TRACE')}
})();
