"use strict";
const $=id=>document.getElementById(id);
const NS="http://www.w3.org/2000/svg";
let nodeSelected=null, graph={nodes:[],edges:[],total:0,dropped:0,pending:0};
let az=0.4, el=0.28, zoom=1.1, dragging=false,px=0,py=0;
const S=$("scene");
const hash=s=>{let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;};
function position(node){
 const h=hash(node.id),k=hash(node.id+"xyz"),z=hash(node.id+"z");
 const r=62+(h%110);
 return [(Math.cos(h*0.000011)*r),(Math.sin(k*0.000013)*r),((z%280)-140)];
}
function project(v){
 const c=Math.cos(az),s=Math.sin(az),ce=Math.cos(el),se=Math.sin(el);
 const x=v[0]*c-v[2]*s, depth=v[0]*s+v[2]*c;
 const y=v[1]*ce-depth*se, zz=v[1]*se+depth*ce;
 const perspective=580/(580+zz*.35);
 return [300+x*zoom*perspective,237+y*zoom*perspective,zz];
}
function element(name,attributes={},parent=S){const el=document.createElementNS(NS,name);for(const[k,v]of Object.entries(attributes))el.setAttribute(k,String(v));parent.append(el);return el;}
function lines(){
 for(let i=-4;i<=4;i++){
  const a=project([i*45,160,-190]),b=project([i*45,160,190]);
  element("line",{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:"#18452c","stroke-width":0.6});
  const c=project([-190,160,i*45]),d=project([190,160,i*45]);
  element("line",{x1:c[0],y1:c[1],x2:d[0],y2:d[1],stroke:"#18452c","stroke-width":0.6});
 }
 for(let radius of [90,157,213]){
  let points=[];for(let a=0;a<=72;a++){const angle=a*Math.PI/36;points.push(project([Math.cos(angle)*radius,0,Math.sin(angle)*radius]).slice(0,2).join(","));}
  element("polyline",{points:points.join(" "),stroke:"#165a31","stroke-dasharray":"2 5","stroke-width":"0.8",fill:"none"});
 }
 const center=project([0,0,0]);
 for(const [v,color,label] of [[[170,0,0],"#45ff7c","X"],[[0,-170,0],"#a2ffd6","Y"],[[0,0,170],"#71bbff","Z"]]){
  const p=project(v);element("line",{x1:center[0],y1:center[1],x2:p[0],y2:p[1],stroke:color,"stroke-width":1.3});
  const t=element("text",{x:p[0]+5,y:p[1]-3,fill:color,"font-size":11});t.textContent=label;
 }
}
function render(){
 S.replaceChildren();lines();
 const pos=new Map(graph.nodes.map(n=>[n.id,project(position(n))]));
 const ordered=[...graph.edges].sort((a,b)=>a.at-b.at);
 for(const e of ordered){
  const a=pos.get(e.from),b=pos.get(e.to);if(!a||!b)continue;
  const color=e.type==="popup"?"#ffc36e":(["link","asset","resource_hint","dom_removed"].includes(e.type)?"#6cb0ff":"#39c96f");
  const edge=element("line",{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:color,"stroke-opacity":e.source==="observed"?".62":".34","stroke-width":Math.min(3,0.5+Math.log2(e.count+1)*.28)});
  const title=element("title",{},edge);title.textContent=`${e.type} / ${e.count} observed or declared`;
 }
 const nodes=[...graph.nodes].sort((a,b)=>position(a)[2]-position(b)[2]);
 for(const n of nodes){
  const p=pos.get(n.id);if(!p)continue;
  const isRoot=graph.nodes.length && n.id===graph.nodes[0].id;
  const chosen=n.id===nodeSelected;
  const g=element("g",{role:"button",tabindex:"0","aria-label":"Select observed node"});
  if(chosen)element("circle",{cx:p[0],cy:p[1],r:12,fill:"none",stroke:"#d7ffac","stroke-width":1},g);
  element("circle",{cx:p[0],cy:p[1],r:isRoot?8:Math.min(6,3+Math.log2(n.hits+1)*.45),fill:isRoot?"#e0ffd8":"#00ff63",stroke:"#0e5f31","stroke-width":1},g);
  if(isRoot||chosen){const txt=element("text",{x:p[0]+9,y:p[1]-7,fill:"#c8ffcb","font-size":9},g);txt.textContent=n.id.length>43?n.id.slice(0,40)+"…":n.id;}
  const t=element("title",{},g);t.textContent=n.id;
  g.addEventListener("click",()=>selectNode(n.id));
  g.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();selectNode(n.id);}});
 }
 $("axis").textContent=`${Math.round(az*180/Math.PI)}° : ${Math.round(el*180/Math.PI)}°`;
 $("count").textContent=`${graph.nodes.length} NODES`;
}
function selectNode(id){nodeSelected=id;const node=graph.nodes.find(n=>n.id===id);const related=graph.edges.filter(e=>e.to===id||e.from===id).slice(-12);
 $("selected").textContent=node?`${node.id}\nTYPE: ${node.type}\nOBSERVATION HITS: ${node.hits}\nCONNECTED EDGES: ${related.length}\n`+related.map(e=>`${e.type.toUpperCase()} · ${e.count} · ${e.source}`).join("\n"):"Select a node";
 render();}
let lastState=null;
async function call(action,extra={}){
 try{const r=await browser.runtime.sendMessage({action,...extra});if(!r||!r.ok)throw new Error(r?.error||"Request failed");return r;}
 catch(e){$("vaultStatus").textContent=e.message;$("vaultStatus").classList.add("error");throw e;}
}
async function refresh(){
 try{const r=await browser.runtime.sendMessage({action:"state"});if(!r||!r.ok)return;
  lastState=r;graph=r.graph;
  $("total").textContent=graph.total.toLocaleString();$("edges").textContent=graph.edges.length.toLocaleString();$("dropped").textContent=graph.dropped.toLocaleString();
  $("captureState").textContent=r.armed?"CAPTURING":"STANDBY";$("captureState").classList.toggle("on",r.armed);
  $("vaultStatus").textContent=r.vaultMessage;
  if(nodeSelected && !graph.nodes.some(n=>n.id===nodeSelected))nodeSelected=null;
  render();
 }catch(_){/* sidebar temporarily disconnected */}
}
$("arm").addEventListener("click",async()=>{
 try{
  const [tab]=await browser.tabs.query({currentWindow:true,active:true});
  if(!tab || !tab.url || !/^https:\/\//i.test(tab.url))throw new Error("Open a public HTTPS website first.");
  const u=new URL(tab.url);
  const allowed=await browser.permissions.request({origins:[u.origin+"/*"]});
  if(!allowed)throw new Error("Firefox site permission was declined.");
  await call("arm",{tabId:tab.id});await refresh();
 }catch(e){$("selected").textContent=e.message;}
});
$("stop").addEventListener("click",async()=>{try{await call("stop");await refresh();}catch(_){}});
$("focus").addEventListener("click",()=>call("focus").catch(()=>{}));
$("connect").addEventListener("click",()=>call("connect").then(refresh).catch(()=>{}));
$("save").addEventListener("click",async()=>{
 const pw=$("passphrase").value; $("passphrase").value="";
 try{await call("vault-create",{passphrase:pw});await refresh();}catch(_){}
});
$("list").addEventListener("click",async()=>{
 try{const r=await call("vault-list");$("archives").replaceChildren();
  if(!r.captures || !r.captures.length){$("archives").textContent="No saved encrypted captures.";return;}
  for(const item of r.captures.slice(0,40)){
   const btn=document.createElement("button");btn.className="linkButton alt";btn.textContent="OPEN "+item.sessionId.slice(0,13)+"…";
   btn.addEventListener("click",async()=>{
     const pw=$("passphrase").value;$("passphrase").value="";
     try{const out=await call("vault-open",{sessionId:item.sessionId,passphrase:pw});
       $("archives").textContent=`Decrypted ${out.events.length} recent events / ${out.total} stored\n`+out.events.slice(-8).map(e=>`${e.type}: ${e.to||e.from}`).join("\n");
     }catch(_){}
   });$("archives").append(btn);
  }
 }catch(_){}
});
$("explain").addEventListener("click",async()=>{
 if(!nodeSelected){$("synopsis").textContent="Select an actual node in the spatial view.";return;}
 $("synopsis").textContent="Requesting local synopsis…";
 try{const r=await call("summarize",{nodeId:nodeSelected,model:$("model").value.trim()});$("synopsis").textContent=r.summary;}
 catch(e){$("synopsis").textContent=`Local AI unavailable: ${e.message}`;}
});
$("cookies").addEventListener("click",async()=>{
 try{
  if(!lastState || !lastState.origin)throw new Error("Arm a site first.");
  const granted=await browser.permissions.request({permissions:["cookies"]});
  if(!granted)throw new Error("Cookie permission declined.");
  const r=await call("cookie-metadata");$("selected").textContent=`Inspected ${r.count} cookie metadata records. Cookie values were not captured.`;
 }catch(e){$("selected").textContent=e.message;}
});
S.addEventListener("pointerdown",e=>{dragging=true;px=e.clientX;py=e.clientY;S.setPointerCapture(e.pointerId);});
S.addEventListener("pointerup",()=>dragging=false);
S.addEventListener("pointercancel",()=>dragging=false);
S.addEventListener("pointermove",e=>{if(!dragging)return;az+=(e.clientX-px)*.008;el=Math.max(-1.4,Math.min(1.4,el+(e.clientY-py)*.008));px=e.clientX;py=e.clientY;render();});
S.addEventListener("wheel",e=>{e.preventDefault();zoom=Math.max(.45,Math.min(2.8,zoom+(e.deltaY>0?-.08:.08)));render();},{passive:false});
document.addEventListener("keydown",e=>{
 if(["INPUT","TEXTAREA"].includes(document.activeElement?.tagName))return;
 if(e.key==="ArrowLeft")az-=.1;
 else if(e.key==="ArrowRight")az+=.1;
 else if(e.key==="ArrowUp")el=Math.max(-1.4,el-.1);
 else if(e.key==="ArrowDown")el=Math.min(1.4,el+.1);
 else return;
 e.preventDefault();render();
});
setInterval(refresh,900);
refresh();
