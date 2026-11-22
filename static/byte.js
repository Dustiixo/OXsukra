import {COUNT, MAX_BYTES, PARAMS, patchesOf, splicesOf, positionOf} from '/byte-core.mjs';
const $=id=>document.getElementById(id);
const state={bytes:new Uint8Array(),patches:[],slices:[],digest:'',source:'',view:'3d',yaw:.6,pitch:-.25,zoom:1,selected:0,p:{...PARAMS},pick:[]};
const cv=$('scene'),ctx=cv.getContext('2d',{alpha:false});
function message(s,bad=false){$('message').textContent=s;$('message').style.color=bad?'#f19c9c':'#9bd7bf';}
function save(name,data,type){const url=URL.createObjectURL(new Blob([data],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),500);}
function select(i){state.selected=Math.max(0,Math.min(999,i|0));$('seek').value=state.selected;const s=state.slices[state.selected];if(!s)return;
 $('slice').textContent='SPLICE '+String(s.index).padStart(4,'0');$('address').textContent=`${s.gateRow} / ${s.gateColumn} / ${s.subsplice}`;
 $('range').textContent=`${s.start}..${s.end}`;$('size').textContent=s.length;
 $('entropy').textContent=(s.entropyMilli/1000).toFixed(3)+' bits/byte';$('mean').textContent=(s.meanByteMilli/1000).toFixed(2);
 $('zero').textContent=s.zeroCount;$('printable').textContent=s.printableCount;
 $('hex').textContent=Array.from(state.bytes.subarray(s.start,Math.min(s.start+12,s.end)),b=>b.toString(16).padStart(2,'0')).join(' ')||'(EMPTY)';
 $('cursor').textContent=`${s.index} / 999`;
}
function resizing(){const r=cv.getBoundingClientRect(),w=Math.max(1,Math.floor(r.width)),h=Math.max(1,Math.floor(r.height));if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h;}return [w,h];}
function project(s,w,h){const p=positionOf(s,state.p);if(state.view==='1d')return {x:16+(s.index/999)*(w-32),y:h-22-(s.entropyMilli/8000)*(h-60),z:0};
 if(state.view==='2d')return {x:20+(s.index%100)/99*(w-40),y:20+Math.floor(s.index/100)/9*(h-40),z:0};
 const y=p.y*Math.cos(state.pitch)-p.z*Math.sin(state.pitch),z=p.y*Math.sin(state.pitch)+p.z*Math.cos(state.pitch);
 const x=p.x*Math.cos(state.yaw)-z*Math.sin(state.yaw),z2=p.x*Math.sin(state.yaw)+z*Math.cos(state.yaw);
 const scale=state.zoom*600/(700+z2*.3);return {x:w/2+x*scale,y:h/2+y*scale,z:z2};
}
function draw(){requestAnimationFrame(draw);if(!state.slices.length)return;const [w,h]=resizing();ctx.fillStyle='#050e18';ctx.fillRect(0,0,w,h);
 ctx.strokeStyle='#152b3b';ctx.lineWidth=.6;for(let x=0;x<w;x+=50){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}for(let y=0;y<h;y+=50){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
 let points=state.slices.filter(s=>s.length).map(s=>({...project(s,w,h),s}));if(state.view==='3d')points.sort((a,b)=>b.z-a.z);state.pick=points;
 for(const a of points){const s=a.s,e=s.entropyMilli/8000,hu=((195+state.p.hue+(s.meanByteMilli/1000)*.65)%360+360)%360;
  ctx.fillStyle=`hsl(${hu},85%,${Math.max(25,Math.min(78,30+e*45))}%)`;
  const selected=s.index===state.selected;ctx.beginPath();ctx.arc(a.x,a.y,selected?5:state.view==='2d'?2.5:Math.max(1,1.2+e*2),0,Math.PI*2);ctx.fill();
  if(selected){ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.stroke();}
 }
 ctx.fillStyle='#7fa4b9';ctx.font='11px Consolas,monospace';ctx.fillText(`1000 RECORDS / ${points.length} NONEMPTY / ${state.view.toUpperCase()}`,16,h-15);
}
async function ingest(bytes,name){if(bytes.length>MAX_BYTES)throw Error('16 MiB cap exceeded');state.bytes=bytes;state.source=name;
 state.patches=patchesOf(bytes);state.slices=splicesOf(bytes);
 const hash=await crypto.subtle.digest('SHA-256',bytes);state.digest=Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
 $('source').textContent=name;$('length').textContent=bytes.length.toLocaleString();$('patches').textContent=state.patches.length.toLocaleString();
 $('filled').textContent=state.slices.filter(x=>x.length).length;$('digest').textContent=state.digest;select(0);message('Raw SHA-256 obtained. File never uploaded.');}
function demo(){const enc=new TextEncoder(),words=enc.encode('make the bassline breathe around the kick; preserve the relation; expose the object; '),bytes=new Uint8Array(8192);
 for(let i=0;i<bytes.length;i++){bytes[i]=(i%777<194)?words[i%words.length]:(i%777<299?0:(i*73+(i>>3)*37)&255);}
 return bytes;
}
$('file').onchange=async e=>{const file=e.target.files?.[0];if(!file)return;try{if(file.size>MAX_BYTES)throw Error('16 MiB cap exceeded');await ingest(new Uint8Array(await file.arrayBuffer()),file.name);}catch(err){message(err.message,true);}};
$('demo').onclick=()=>ingest(demo(),'SYNTHETIC / BYTE STUDY').catch(e=>message(e.message,true));
for(const mode of ['3d','2d','1d'])$('view'+mode).onclick=()=>{state.view=mode;$('viewName').textContent=mode.toUpperCase();for(const m of ['3d','2d','1d'])$('view'+m).classList.toggle('active',m===mode);};
for(const name of ['depth','twist','hue'])$(name).oninput=()=>{state.p[name]=Number($(name).value);$('v'+name).textContent=name==='hue'?state.p[name]:state.p[name].toFixed(2);};
$('reset').onclick=()=>{state.p={...PARAMS};for(const name of ['depth','twist','hue']){$(name).value=state.p[name];$('v'+name).textContent=state.p[name];}};
$('fork').onclick=()=>{state.p={...state.p,depth:Math.round((.4+Math.random()*2.4)*10)/10,twist:Math.round((Math.random()*12-6)*10)/10,hue:Math.round(Math.random()*360-180)};for(const n of ['depth','twist','hue']){$(n).value=state.p[n];$('v'+n).textContent=state.p[n];}message('View fork only. Raw bytes unmodified.');};
$('seek').oninput=()=>select(Number($('seek').value));
$('export').onclick=()=>save('ox-byte-browser-preview.json',JSON.stringify({schema:'OX_BROWSER_BYTE_PREVIEW/1',sourceLabel:state.source,sha256:state.digest,byteLength:state.bytes.length,algorithm:'heuristic local entropy; NOT BLT',patches:state.patches,splices:state.slices,mapping:state.p},null,2),'application/json');
$('selfExport').onclick=()=>{const a=[`"Native Self object expression; not executed in browser."`,'(|','  parent* = traits clonable.',`  originDigest = '${state.digest}'.`,`  byteLength = ${state.bytes.length}.`,`  patchCount = ${state.patches.length}.`,`  layerCount = 1000.`,`  depth <- ${state.p.depth}.`,`  twist <- ${state.p.twist}.`,`  hue <- ${state.p.hue}.`,`  threshold <- ${state.p.threshold}.`,`  schema = 'OX_BROWSER_BYTE_PREVIEW/1'.`,'|)'];save('ox-byte-preview.self',a.join('\n'),'text/plain');message('Native Self syntax candidate exported. VM gate still unverified.');};
let drag=null;cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,px:e.clientX,py:e.clientY,moved:false};cv.setPointerCapture(e.pointerId);});
cv.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.px,dy=e.clientY-drag.py;drag.px=e.clientX;drag.py=e.clientY;if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>5)drag.moved=true;if(state.view==='3d'&&drag.moved){state.yaw+=dx*.008;state.pitch=Math.max(-1.5,Math.min(1.5,state.pitch+dy*.008));}});
cv.addEventListener('pointerup',e=>{if(!drag)return;const click=!drag.moved;drag=null;if(click){const r=cv.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let best=null,bestD=400;for(const p of state.pick){const d=(p.x-x)**2+(p.y-y)**2;if(d<bestD){best=p;bestD=d;}}if(best)select(best.s.index);}});
cv.addEventListener('wheel',e=>{if(state.view==='3d'){e.preventDefault();state.zoom=Math.max(.4,Math.min(3,state.zoom*(e.deltaY>0?.92:1.08)));}},{passive:false});
draw();$('demo').click();
