import {COUNT,NOTE_NAMES,DEFAULTS,SLOT_NAMES,clamp,makeDemo,analyzeSignalAsync,geometry,colourOf,normalizeParams,parseSlotScript,slotScript,makePrintPayload,wavBytes} from '/splice-core.mjs';
const $=id=>document.getElementById(id);
const state={slices:[],params:{...DEFAULTS},origin:'SYNTHETIC',source:'SYNTHETIC / 155 BPM STUDY',duration:12,mode:'3d',selected:0,yaw:.55,pitch:-.33,zoom:1,playing:false,print:'',world:null,pick:[],lastDraw:0,playTime:0,busy:false};
const canvas=$('scene'),ctx=canvas.getContext('2d',{alpha:false});const cc=$('chromagram'),cx=cc.getContext('2d');let audioUrl=null,lastSize=0;
function label(message,error=false){$('slotMessage').textContent=message;$('slotMessage').style.color=error?'#ee8b91':'#8ad8bf';}
function source(message){$('source').textContent=message;$('origin').textContent=state.origin;$('duration').textContent=state.duration.toFixed(2)+'s';$('progress').style.width='100%';}
function slotsToUI(){for(const key of SLOT_NAMES){$(key).value=state.params[key];$('v'+key).textContent=key==='hue'?state.params[key]+'°':state.params[key].toFixed(2);} $('slots').value=slotScript(state.params);updateInspector();}
function setParams(p){state.params=normalizeParams(p);slotsToUI();}
function select(i){state.selected=clamp(Math.round(i),0,COUNT-1);updateInspector();}
function rgbCSS(slice){const [r,g,b]=colourOf(slice,state.params);return `rgb(${r},${g},${b})`;}
function bytesAsHex(n){return '0x'+n.toString(16).padStart(4,'0').toUpperCase();}
function updateInspector(){
 const s=state.slices[state.selected];if(!s)return;
 const [r,g,b]=colourOf(s,state.params),geo=geometry(s,state.params);
 $('sliceName').textContent='SPLICE / '+String(s.index).padStart(4,'0');$('headIndex').textContent=String(s.index).padStart(4,'0');$('rgbbar').style.background=`linear-gradient(90deg,#071421,rgb(${r},${g},${b}),#071421)`;
 $('rgb').textContent=`${r} · ${g} · ${b}`;$('addr').textContent=`${s.gateRow} / ${s.gateColumn} / ${s.subsplice}`;$('time').textContent=s.time.toFixed(3)+'s';$('pitch').textContent=s.silent?'REST':NOTE_NAMES[s.pitch];
 $('energy').textContent=s.energy.toFixed(4);$('centroid').textContent=s.centroid.toFixed(4);$('bands').textContent=[s.bass,s.mid,s.treble].map(v=>v.toFixed(2)).join(' / ');
 $('hex').textContent=bytesAsHex(s.word);$('bits').textContent=s.bitnote.match(/.{4}/g).join(' ');$('active').textContent=s.silent?'REST':s.energy>=state.params.threshold?'ACTIVE':'GATED';
 $('xyz').textContent=[geo.x,geo.y,geo.z].map(v=>v.toFixed(0)).join(' / ');
 const root=$('chroma');root.replaceChildren();for(let i=0;i<12;i++){
   const row=document.createElement('div'),name=document.createElement('span'),bar=document.createElement('i'),value=document.createElement('b');row.className='chromarow';name.textContent=NOTE_NAMES[i];bar.style.width=(Math.max(1,s.chroma[i]*200))+'px';bar.style.background=i===s.pitch?`rgb(${r},${g},${b})`:'#305a71';value.textContent=(100*s.chroma[i]).toFixed(1)+'%';row.append(name,bar,value);root.append(row);
 }drawChromagram();
}
function resize(canvas,ctx){const r=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2),w=Math.max(1,Math.floor(r.width*dpr)),h=Math.max(1,Math.floor(r.height*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}ctx.setTransform(dpr,0,0,dpr,0,0);return [r.width,r.height];}
function proj(pt,w,h){const c=Math.cos(state.yaw),s=Math.sin(state.yaw),cp=Math.cos(state.pitch),sp=Math.sin(state.pitch);const x=pt.x*c-pt.z*s;const z=pt.x*s+pt.z*c;const y=pt.y*cp-z*sp;const zz=pt.y*sp+z*cp;const factor=(920/(920-zz))*state.zoom;return {x:w/2+x*factor*.82,y:h/2-y*factor*.82,z:zz,factor};}
function render3D(w,h,t){
 const data=state.slices,arr=[],cursor=Math.min(COUNT-1,Math.floor((state.playTime/state.duration)*COUNT));
 ctx.strokeStyle='#1b3448';ctx.lineWidth=1;for(let j=-4;j<=4;j++){
  const a=proj({x:-390,y:-120,z:j*75},w,h),b=proj({x:390,y:-120,z:j*75},w,h);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
 }
 for(let i=0;i<data.length;i++){
   const s=data[i],geo=geometry(s,state.params),active=s.energy>=state.params.threshold;
   const near=state.playing?Math.max(0,1-Math.abs(i-cursor)/21):0;
   const bottom=proj({x:geo.x,y:geo.y-geo.height*.28,z:geo.z},w,h);
   const top=proj({x:geo.x,y:geo.y+geo.height*(.58+.3*near),z:geo.z},w,h);
   arr.push({s,x:top.x,y:top.y,bx:bottom.x,by:bottom.y,z:top.z,active,near});
 }
 arr.sort((a,b)=>a.z-b.z);state.pick=[];
 for(const q of arr){const [r,g,b]=colourOf(q.s,state.params);const alpha=q.active?(.43+q.s.energy*.5):.1;
   ctx.strokeStyle=`rgba(${r},${g},${b},${alpha})`;ctx.lineWidth=q.s.index===state.selected?3:q.near>.5?2:1.05;
   ctx.beginPath();ctx.moveTo(q.bx,q.by);ctx.lineTo(q.x,q.y);ctx.stroke();if(q.s.index===state.selected){ctx.strokeStyle='#e6f7ff';ctx.beginPath();ctx.arc(q.x,q.y,5,0,Math.PI*2);ctx.stroke();}
   state.pick.push({x:q.x,y:q.y,index:q.s.index});
 }
 // Continuous spatial connective line highlights the fact that splices belong to one vessel.
 ctx.strokeStyle='rgba(120,195,219,.16)';ctx.lineWidth=1;ctx.beginPath();for(let i=0;i<data.length;i+=4){const g=geometry(data[i],state.params),p=proj(g,w,h);if(i===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);}ctx.stroke();
 const anchor=data[cursor];if(anchor){const g=geometry(anchor,state.params),p=proj({x:g.x,y:g.y+g.height,z:g.z},w,h);ctx.strokeStyle='rgba(228,248,255,.8)';ctx.beginPath();ctx.arc(p.x,p.y,8,0,7);ctx.stroke();}
 $('camera').textContent=`YAW ${state.yaw.toFixed(2)} / PITCH ${state.pitch.toFixed(2)} / ZOOM ${state.zoom.toFixed(2)}`;
}
function render2D(w,h){const cols=40,rows=25,margin=28,cw=(w-2*margin)/cols,ch=(h-2*margin)/rows;state.pick=[];
 for(let i=0;i<COUNT;i++){const s=state.slices[i],x=margin+(i%cols)*cw,y=margin+Math.floor(i/cols)*ch;
 ctx.fillStyle=s.energy>=state.params.threshold?rgbCSS(s):'#192b39';ctx.fillRect(x+1,y+1,Math.max(1,cw-2),Math.max(1,ch-2));state.pick.push({index:i,x:x+cw/2,y:y+ch/2});
 if(i===state.selected){ctx.strokeStyle='#f2ffff';ctx.lineWidth=2;ctx.strokeRect(x,y,cw,ch);}
 }
 ctx.fillStyle='#7796a8';ctx.font='10px monospace';ctx.fillText('40 COLUMNS × 25 ROWS = 1,000 INDEPENDENT MICRO-SPLICES',margin,16);
}
function render1D(w,h){const arr=state.slices,mar=25,dy=h*.5,scale=w/(COUNT+2);state.pick=[];for(let i=0;i<COUNT;i++){
 const s=arr[i],x=mar+(w-2*mar)*i/COUNT,height=(20+s.energy*(h*.37));ctx.strokeStyle=s.energy>=state.params.threshold?rgbCSS(s):'#173144';ctx.lineWidth=1;
 ctx.beginPath();ctx.moveTo(x,dy-height);ctx.lineTo(x,dy+height);ctx.stroke();state.pick.push({index:i,x,y:dy});
 }const x=mar+(w-2*mar)*state.selected/COUNT;ctx.strokeStyle='#f4fbff';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,12);ctx.lineTo(x,h-12);ctx.stroke();
 ctx.fillStyle='#749db0';ctx.font='10px monospace';ctx.fillText('1000 TIME-ORDERED LEDGERS / ENERGY-CODED',mar,16);
}
function draw(){requestAnimationFrame(draw);if(!state.slices.length)return;
 const now=performance.now();if(now-state.lastDraw<28)return;state.lastDraw=now;
 const [w,h]=resize(canvas,ctx);ctx.fillStyle='#050d17';ctx.fillRect(0,0,w,h);
 if(state.mode==='3d')render3D(w,h,now);else if(state.mode==='2d')render2D(w,h);else render1D(w,h);
 $('renderfps').textContent=state.mode.toUpperCase()+' / '+COUNT+' SLICES';
}
function drawChromagram(){if(!state.slices.length)return;const [w,h]=resize(cc,cx),s=state.slices[state.selected],barw=w/12;
 cx.fillStyle='#0a1924';cx.fillRect(0,0,w,h);for(let i=0;i<12;i++){
  const v=s.chroma[i],rgb=colourOf({...s,pitch:i},state.params);cx.fillStyle=`rgb(${rgb.join(',')})`;cx.fillRect(i*barw+3,h-(v*h*6+4),barw-6,v*h*6+4);
  cx.fillStyle='#8ba8b9';cx.font='10px monospace';cx.fillText(NOTE_NAMES[i],i*barw+3,h-2);
 }$('note').textContent=s.silent?'REST':NOTE_NAMES[s.pitch];
}
async function updatePrint(){if(!state.slices.length)return;const p=new TextEncoder().encode(JSON.stringify(makePrintPayload(state.slices)));
 const hash=await crypto.subtle.digest('SHA-256',p);state.print=Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');$('fingerprint').textContent=state.print;
}
async function ingest(samples,rate,name,origin,duration){state.busy=true;state.origin=origin;state.source=name;state.duration=duration;source('ANALYSING / '+name);$('progress').style.width='1%';
 try{state.slices=await analyzeSignalAsync(samples,rate,x=>{$('progress').style.width=(x*100).toFixed(1)+'%';$('source').textContent='MEASURING '+Math.round(x*100)+'% / '+name;});
  state.selected=0;state.playTime=0;source(name);$('scrub').value=0;updateInspector();await updatePrint();label('1000 addresses decoded; no code executed.');
 }catch(e){label('Analysis failed: '+e.message,true);throw e;}finally{state.busy=false;}
}
function asClock(seconds){const m=Math.floor(seconds/60),s=Math.floor(seconds%60);return String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');}
async function loadDemo(){const demo=makeDemo();if(audioUrl)URL.revokeObjectURL(audioUrl);audioUrl=URL.createObjectURL(new Blob([wavBytes(demo.samples,demo.sampleRate)],{type:'audio/wav'}));$('audio').src=audioUrl;
 await ingest(demo.samples,demo.sampleRate,demo.origin,'SYNTHETIC',demo.duration);setParams({...DEFAULTS});$('play').disabled=false;
}
$('demo').onclick=()=>{if(!state.busy){$('audio').pause();loadDemo().catch(e=>label(e.message,true));}};
$('file').onchange=async e=>{const file=e.target.files?.[0];if(!file||state.busy)return;if(file.size>100_000_000){label('Max file size is 100 MB',true);return;}
 const audio=$('audio');audio.pause();state.busy=true;try{
   const bytes=await file.arrayBuffer(),ac=new (window.AudioContext||window.webkitAudioContext)();let buf;
   try{buf=await ac.decodeAudioData(bytes.slice(0));}finally{await ac.close();}
   if(buf.duration>1200)throw Error('20 minute maximum to bound processing time');
   const samples=new Float32Array(buf.length);const channels=Math.min(2,buf.numberOfChannels);for(let c=0;c<channels;c++){
     const ch=buf.getChannelData(c);for(let j=0;j<samples.length;j++)samples[j]+=ch[j]/channels;
   }
   if(audioUrl)URL.revokeObjectURL(audioUrl);audioUrl=URL.createObjectURL(file);audio.src=audioUrl;state.busy=false;
   await ingest(samples,buf.sampleRate,file.name,'UPLOADED / MEASURED',buf.duration);$('play').disabled=false;
 }catch(err){state.busy=false;label('Could not decode audio: '+err.message,true);}}
for(const b of document.querySelectorAll('[data-mode]'))b.onclick=()=>{state.mode=b.dataset.mode;for(const x of document.querySelectorAll('[data-mode]'))x.classList.toggle('active',x===b);$('geom').textContent=state.mode.toUpperCase();};
for(const k of SLOT_NAMES)$(k).oninput=()=>{state.params=normalizeParams({...state.params,[k]:Number($(k).value)});slotsToUI();};
$('apply').onclick=()=>{try{setParams(parseSlotScript($('slots').value));label('Constrained slot changes applied; audio measurements unchanged.');}catch(e){label(e.message,true);}};
$('reset').onclick=()=>{setParams({...DEFAULTS});label('Mapping reset.');};
$('random').onclick=()=>{const p={depth:+(0.7+Math.random()*1.6).toFixed(2),twist:+(-3+Math.random()*6).toFixed(2),hue:Math.round(Math.random()*360-180),threshold:+(0.05+Math.random()*.45).toFixed(2)};setParams(p);label('Experimental mapping fork only; measurements unchanged.');};
$('copySelf').onclick=()=>{const p=state.params;const s=`"OX RCLL numeric experiment / Self object literal, NOT a module. Load by pasting this expression into an actual Self 2024.1 workspace."\n(| parent* = traits clonable.\n   layerCount = 1000.\n   gateCount = 100.\n   depth <- ${p.depth}.\n   twist <- ${p.twist}.\n   hue <- ${p.hue}.\n   threshold <- ${p.threshold}.\n   fingerprint = '${state.print}'.\n|)\n`;
 download('ox-splice-object.self',new Blob([s],{type:'text/plain'}));label('Exported Self source literal; not loaded into Self VM.');};
function download(name,blob){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
$('export').onclick=()=>{if(!state.slices.length)return;const p={format:'RCLL_BITNOTE_VESSEL/0.1',source:{name:state.source,kind:state.origin,duration:state.duration},measurementFingerprint:state.print,mapping:state.params,bitnoteSchema:{bits:'8:energy,4:pitch class,2:onset,2:timbre',pitchClasses:NOTE_NAMES,wordEncoding:'(energy8 << 8) | (pitchClass << 4) | (onset2 << 2) | timbre2',timeIndex:'1000 ordered positions',addressing:'10x10 gates; ten subsplices per gate',units:'time seconds, energy relative quantized'},slices:state.slices.map(s=>({...s,rgb:colourOf(s,state.params),position:geometry(s,state.params)}))};
 download('ox-rcll-bitnote-vessel.json',new Blob([JSON.stringify(p,null,2)],{type:'application/json'}));label('Exported 1000 slice measurements plus derived geometry and mapping.');};
$('audio').ontimeupdate=()=>{if(!state.slices.length)return;state.playTime=$('audio').currentTime;state.playing=!$('audio').paused;const n=clamp(Math.floor(state.playTime/state.duration*999),0,999);$('scrub').value=n;select(n);$('clock').textContent=asClock(state.playTime)+' / '+asClock(state.duration);};
$('audio').onended=()=>{state.playing=false;};$('play').onclick=()=>{$('audio').play().catch(e=>label('Playback blocked: '+e.message,true));};$('pause').onclick=()=>{$('audio').pause();state.playing=false;};
$('scrub').oninput=()=>{const n=Number($('scrub').value);select(n);$('audio').currentTime=(n/999)*state.duration;state.playTime=$('audio').currentTime;};
let drag=null;
canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,oldx:e.clientX,oldy:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.oldx,dy=e.clientY-drag.oldy;if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>5)drag.moved=true;
 if(state.mode==='3d'&&drag.moved){state.yaw+=dx*.008;state.pitch=clamp(state.pitch+dy*.008,-1.5,1.5);}drag.oldx=e.clientX;drag.oldy=e.clientY;});
canvas.addEventListener('pointerup',e=>{if(!drag)return;const click=!drag.moved;drag=null;if(click&&state.pick.length){const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let best=null,bestDist=Infinity;for(const p of state.pick){const d=(p.x-x)**2+(p.y-y)**2;if(d<bestDist){bestDist=d;best=p;}}if(best)select(best.index);}});
canvas.addEventListener('wheel',e=>{if(state.mode!=='3d')return;e.preventDefault();state.zoom=clamp(state.zoom*(e.deltaY>0?.92:1.08),.5,2.5);},{passive:false});
async function refreshWorld(){try{const chosenId=$('target').value;const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error('World state unavailable');state.world=await r.json();const items=Object.values(state.world.objects);$('target').replaceChildren();for(const o of items){const op=document.createElement('option');op.value=o.id;op.textContent=o.name;$('target').append(op);}if(chosenId&&items.some(o=>o.id===chosenId))$('target').value=chosenId;
 $('morphStatus').textContent=`WORLD VERIFIED · REV ${state.world.revision} · ${items.length} OBJECTS`;
 }catch(e){$('morphStatus').textContent='World link failed: '+e.message;}}
$('load').onclick=async()=>{await refreshWorld();const id=$('target').value,obj=state.world?.objects[id];if(!obj)return;const p={...state.params};for(const k of SLOT_NAMES){const v=obj.resolved['rcll'+k[0].toUpperCase()+k.slice(1)]?.value;if(typeof v==='number')p[k]=v;}setParams(p);$('morphStatus').textContent='Loaded numeric slots from '+obj.name;};
$('save').onclick=async()=>{const w=state.world,id=$('target').value;if(!w?.objects[id])return;const current=w.objects[id];const ok=window.confirm(`Append mapping changes to ${current.name} in your local OX Morph history? This does not modify the audio or protected IXO.`);if(!ok)return;
 try{for(const k of SLOT_NAMES){const key='rcll'+k[0].toUpperCase()+k.slice(1);const body={op:'set_slot',object_id:id,slot_name:key,slot:{kind:'value',value:state.params[k]},reason:'RCLL spatial mapping preset / explicit human commit',expected_revision:state.world.revision};const r=await fetch('/api/mutate',{method:'POST',headers:{'Content-Type':'application/json','X-OX-Token':state.world.csrf_token},body:JSON.stringify(body)});const out=await r.json();if(!r.ok)throw Error(out.error||'Save error');state.world={...out.world,csrf_token:state.world.csrf_token};}
 $('morphStatus').textContent=`COMMITTED / WORLD REV ${state.world.revision} / 4 HISTORY EVENTS`;
 }catch(e){$('morphStatus').textContent='Save stopped: '+e.message+'; inspect history for partial commit';}
};
window.addEventListener('resize',updateInspector);slotsToUI();draw();loadDemo().catch(e=>label(e.message,true));refreshWorld();
