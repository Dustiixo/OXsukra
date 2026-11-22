/* IXO / GPU Field M0.4: dependency-free WebGL2 geometry renderer.
   All source-backed changes come from the event projection supplied by field.js.
   Ambient rotation/stars are visual only; they never represent model activity. */
window.IXO_GPU = (() => { 'use strict';
const PI=Math.PI,TAU=2*PI;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const sub=(a,b)=>a.map((v,i)=>v-b[i]);const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{let n=Math.hypot(...a)||1;return a.map(v=>v/n)};
const dot=(a,b)=>a.reduce((n,v,i)=>n+v*b[i],0);
const matmul=(a,b)=>{let o=new Float32Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o};
const perspective=(fovy,aspect,n,f)=>{let t=1/Math.tan(fovy/2);return new Float32Array([t/aspect,0,0,0,0,t,0,0,0,0,(f+n)/(n-f),-1,0,0,2*f*n/(n-f),0])};
const view=(eye,center)=>{let z=norm(sub(eye,center)),x=norm(cross([0,1,0],z)),y=cross(z,x);return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1])};
const model=(p,s=1,r=0)=>{let c=Math.cos(r),n=Math.sin(r);return new Float32Array([c*s,0,-n*s,0,0,s,0,0,n*s,0,c*s,0,p[0],p[1],p[2],1])};
const idMat=model([0,0,0]);
const modelStretch=(p,sx,sy,sz,r=0)=>{let c=Math.cos(r),n=Math.sin(r);return new Float32Array([c*sx,0,-n*sx,0,0,sy,0,0,n*sz,0,c*sz,0,p[0],p[1],p[2],1])};
function seedRand(i){let x=(Math.imul(i+17,747796405)+2891336453)>>>0;x=(Math.imul(x ^ x>>>16,2246822519))>>>0;return (x^x>>>13)>>>0}
function makeCrystal(){const pos=[];
 function tri(a,b,c){const n=norm(cross(sub(b,a),sub(c,a)));for(const p of [a,b,c])pos.push(...p,...n)}
 const count=11, rings=[{y:1.5,r:.015},{y:.72,r:.7},{y:.05,r:.98},{y:-.7,r:.5},{y:-1.62,r:.012}];
 for(let k=0;k<rings.length-1;k++)for(let i=0;i<count;i++){
  let a=i*TAU/count,b=(i+1)*TAU/count;let p=(j,ang)=>[Math.cos(ang)*(rings[j].r)*(1+.09*Math.sin(i*4+j*2)),rings[j].y,Math.sin(ang)*rings[j].r];
  tri(p(k,a),p(k+1,a),p(k,b));tri(p(k,b),p(k+1,a),p(k+1,b));
 }return new Float32Array(pos)
}
// Reusable sculpted, beveled radial geometry. Each part is built once.
function makeVault(){const v=[];const rings=[[.12,-.82],[.7,-.68],[.94,-.35],[.94,.24],[.66,.58],[.48,.83],[.16,.99]];const n=12;
 function tri(a,b,c){const normal=norm(cross(sub(b,a),sub(c,a)));for(const p of [a,b,c])v.push(...p,...normal)}
 const at=(k,i)=>{let [r,y]=rings[k],a=i*TAU/n;return [r*Math.cos(a),y,r*Math.sin(a)]};
 for(let k=0;k<rings.length-1;k++)for(let i=0;i<n;i++){let a=at(k,i),b=at(k,i+1),c=at(k+1,i),d=at(k+1,i+1);tri(a,c,b);tri(b,c,d)}
 for(let i=0;i<n;i++){tri([0,-.82,0],at(0,i),at(0,i+1));tri([0,.99,0],at(rings.length-1,i+1),at(rings.length-1,i))}return new Float32Array(v)}
function makeArc(){const v=[];const n=24;function tri(a,b,c){let normal=norm(cross(sub(b,a),sub(c,a)));for(const p of [a,b,c])v.push(...p,...normal)}
 const at=(i,r,y)=>{let a=-.78+i*1.56/n;return [Math.cos(a)*r,y,Math.sin(a)*r]};
 for(let i=0;i<n;i++){let a=at(i,1.21,-.085),b=at(i+1,1.21,-.085),c=at(i,1.21,.085),d=at(i+1,1.21,.085),e=at(i,1.42,-.055),f=at(i+1,1.42,-.055),g=at(i,1.42,.055),h=at(i+1,1.42,.055);for(const q of [[a,b,d,c],[e,g,h,f],[c,d,h,g],[a,e,f,b]]){tri(q[0],q[1],q[2]);tri(q[0],q[2],q[3])}}return new Float32Array(v)}
function makeLineArray(lines){const o=[];for(let i=0;i<lines.length;i++){const [a,b]=lines[i];o.push(...a,0,1,0,...b,0,1,0)}return new Float32Array(o)}
function makeRings(){const l=[];for(const rad of [1.6,2.1,2.55])for(let i=0;i<120;i++){let a=i*TAU/120,b=(i+1)*TAU/120;const tilt=rad===2.1?1.2:rad===2.55?.4:0;
 const p=ang=>[Math.cos(ang)*rad,Math.sin(ang)*Math.sin(tilt)*rad*.85,Math.sin(ang)*Math.cos(tilt)*rad];l.push([p(a),p(b)]);}return makeLineArray(l)}
function makeFloor(){const lines=[];for(let i=-16;i<=16;i++){let a=i*.9;lines.push([[a,-2.6,-15],[a,-2.6,15]],[[-15,-2.6,a],[15,-2.6,a]])}for(let r=3;r<13;r+=2)for(let i=0;i<100;i++){let a=i*TAU/100,b=(i+1)*TAU/100;lines.push([ [Math.sin(a)*r,-2.55,Math.cos(a)*r],[Math.sin(b)*r,-2.55,Math.cos(b)*r]])}return makeLineArray(lines)}
function makeStars(){const o=[];for(let i=0;i<680;i++){let r=12+seedRand(i*5)%35,theta=seedRand(i*7)%6283/1000,phi=(seedRand(i*13)%3141)/1000;let x=r*Math.sin(phi)*Math.cos(theta),y=r*Math.cos(phi),z=r*Math.sin(phi)*Math.sin(theta);o.push(x,y,z,0,1,0)}return new Float32Array(o)}
function shader(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('GPU shader: '+gl.getShaderInfoLog(s));return s}
function program(gl,v,f){const p=gl.createProgram();gl.attachShader(p,shader(gl,gl.VERTEX_SHADER,v));gl.attachShader(p,shader(gl,gl.FRAGMENT_SHADER,f));gl.bindAttribLocation(p,0,'aP');gl.bindAttribLocation(p,1,'aN');gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error('GPU link: '+gl.getProgramInfoLog(p));return p}
const vSolid=`#version 300 es
layout(location=0) in vec3 aP;layout(location=1) in vec3 aN;
uniform mat4 uVP;uniform mat4 uModel;uniform float uTime;
out vec3 vN;out vec3 vPos;out float vStripe;
void main(){vec4 p=uModel*vec4(aP,1.);vPos=p.xyz;vN=mat3(uModel)*aN;vStripe=aP.y;gl_Position=uVP*p;gl_PointSize=6.;}`;
const fSolid=`#version 300 es
precision highp float;
in vec3 vN;in vec3 vPos;in float vStripe;
uniform vec3 uColor;uniform vec3 uEye;uniform float uTime;uniform float uSelected;uniform float uAlpha;
out vec4 outColor;
void main(){vec3 N=normalize(vN);vec3 L=normalize(vec3(-.5,.7,.4));vec3 V=normalize(uEye-vPos);
 float d=max(dot(N,L),0.);float rim=pow(1.-max(dot(N,V),0.),2.4);
 float band=pow(max(0.,sin(vStripe*23.)),18.)*.19;
 float spec=pow(max(dot(N,normalize(L+V)),0.),22.); vec3 col=uColor*(.17+.62*d)+vec3(.84,.94,1.)*(rim*.28+spec*.5)+uColor*(band+uSelected*.16);
 outColor=vec4(col,uAlpha);}`;
const vLine=`#version 300 es
layout(location=0) in vec3 aP;uniform mat4 uVP;uniform mat4 uModel;uniform float uTime;out float wave;
void main(){wave=aP.y;gl_Position=uVP*uModel*vec4(aP,1.);gl_PointSize=5.;}`;
const fLine=`#version 300 es
precision highp float;uniform vec3 uColor;uniform float uAlpha;uniform float uTime;in float wave;out vec4 outColor;
void main(){outColor=vec4(uColor*(.65+.35*sin(uTime*.8+wave*1.7)),uAlpha);}`;
const vPoint=`#version 300 es
layout(location=0) in vec3 aP;uniform mat4 uVP;uniform float uTime;uniform float uSize;out float vI;
void main(){vec3 p=aP;p.y+=sin(p.x*.5+uTime*.27)*.16;gl_Position=uVP*vec4(p,1.);float z=max(.3,gl_Position.w);gl_PointSize=clamp(uSize*12./z,1.,22.);vI=fract(aP.x*11.73+aP.z*19.31);}`;
const fPoint=`#version 300 es
precision highp float;in float vI;uniform vec3 uColor;uniform float uAlpha;out vec4 outColor;
void main(){vec2 q=gl_PointCoord-.5;float r=length(q);float a=exp(-r*r*28.)*(.45+vI*.5);outColor=vec4(uColor*a,uAlpha*a);}`;
const vBg=`#version 300 es
layout(location=0) in vec2 aP;void main(){gl_Position=vec4(aP,0.,1.);}`;
const fBg=`#version 300 es
precision highp float;uniform vec2 uResolution;uniform float uTime;out vec4 outColor;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){vec2 uv=gl_FragCoord.xy/uResolution;vec2 p=(uv-.5)*vec2(uResolution.x/uResolution.y,1.);
 float v=1.-smoothstep(.1,1.05,length(p));float center=exp(-pow((uv.x-.56)*2.,2.)-pow((uv.y-.48)*3.,2.));
 vec3 c=vec3(.004,.011,.024)+vec3(.016,.037,.072)*v+vec3(.008,.06,.11)*center*.7;
 vec2 st=floor(uv*uResolution/4.);float star=step(.9971,h(st));float rare=step(.9994,h(st+345.));
 c+=star*vec3(.14,.25,.37)+rare*vec3(.5,.75,.94);c*=1.-smoothstep(.48,.95,length(p))*.55;
 outColor=vec4(c,1.);}`;
function gpu(canvas){const opts={antialias:true,alpha:false,depth:true,stencil:false,preserveDrawingBuffer:false,powerPreference:'high-performance'};
 const gl=canvas.getContext('webgl2',opts)||canvas.getContext('webgl',opts);if(!gl)throw Error('WebGL is unavailable.');
 const webgl2=typeof gl.createVertexArray==='function';const ext=webgl2?null:gl.getExtension('OES_vertex_array_object');if(!webgl2&&!ext)throw Error('VAO support unavailable.');
 const createVAO=()=>webgl2?gl.createVertexArray():ext.createVertexArrayOES();const bindVAO=x=>webgl2?gl.bindVertexArray(x):ext.bindVertexArrayOES(x);
 const legacy=(source,isFrag=false)=>{if(webgl2)return source;return source.replace('#version 300 es','').replace(/layout\(location=0\) in/g,'attribute').replace(/layout\(location=1\) in/g,'attribute').replace(/\bin vec3\b/g,isFrag?'varying vec3':'attribute vec3').replace(/\bin float\b/g,isFrag?'varying float':'attribute float').replace(/\bout vec3\b/g,isFrag?'':'varying vec3').replace(/\bout float\b/g,isFrag?'':'varying float').replace(/\bout vec4 outColor;/g,'').replaceAll('outColor=','gl_FragColor=')};
 const progs={solid:program(gl,legacy(vSolid),legacy(fSolid,true)),line:program(gl,legacy(vLine),legacy(fLine,true)),point:program(gl,legacy(vPoint),legacy(fPoint,true)),bg:program(gl,legacy(vBg),legacy(fBg,true))};
 const bgBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,bgBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
 const geom=(arr)=>{const vao=createVAO(),vbo=gl.createBuffer();bindVAO(vao);gl.bindBuffer(gl.ARRAY_BUFFER,vbo);gl.bufferData(gl.ARRAY_BUFFER,arr,gl.STATIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,3,gl.FLOAT,false,24,12);bindVAO(null);return{vao,vbo,count:arr.length/6}};
 const crystal=geom(makeCrystal()),vault=geom(makeVault()),arc=geom(makeArc()),ring=geom(makeRings()),floor=geom(makeFloor()),stars=geom(makeStars());
 const dynamic=gl.createBuffer(),dynamicVAO=createVAO();bindVAO(dynamicVAO);gl.bindBuffer(gl.ARRAY_BUFFER,dynamic);gl.bufferData(gl.ARRAY_BUFFER,100000,gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,3,gl.FLOAT,false,24,12);bindVAO(null);
 const location=(prog,key)=>gl.getUniformLocation(prog,key);
 const set=(p,kind,VP,mdl,col,alpha,time,eye,selected=0)=>{gl.useProgram(p);let x=location(p,'uVP');if(x!==null)gl.uniformMatrix4fv(x,false,VP);x=location(p,'uModel');if(x!==null)gl.uniformMatrix4fv(x,false,mdl);x=location(p,'uColor');if(x!==null)gl.uniform3fv(x,col);x=location(p,'uAlpha');if(x!==null)gl.uniform1f(x,alpha);x=location(p,'uTime');if(x!==null)gl.uniform1f(x,time);x=location(p,'uEye');if(x!==null)gl.uniform3fv(x,eye);x=location(p,'uSelected');if(x!==null)gl.uniform1f(x,selected)};
 const draw=(pg,geo,mode)=>{bindVAO(geo.vao);gl.drawArrays(mode,0,geo.count);bindVAO(null)};
 const dyn=(lines)=>{if(!lines.length)return;const a=makeLineArray(lines);bindVAO(dynamicVAO);gl.bindBuffer(gl.ARRAY_BUFFER,dynamic);gl.bufferData(gl.ARRAY_BUFFER,a,gl.DYNAMIC_DRAW);gl.drawArrays(gl.LINES,0,a.length/6);bindVAO(null)};
 const colors={root:[.73,.82,.93],active:[.22,.60,.94],parked:[.83,.15,.19],selected:[.94,.97,1],evidence:[.35,1,.72]};
 let quality='medium',dpr=1,W=0,H=0,VP,eye=[0,0,12],zoomDist=12,lastPositions=[];
 function setQuality(q){quality=['low','medium','high'].includes(q)?q:'medium'}
 function resize(){let factor=quality==='high'?1.5:quality==='medium'?1.1:.73;dpr=Math.min(window.devicePixelRatio||1,factor);let w=Math.max(2,Math.floor(canvas.clientWidth*dpr)),h=Math.max(2,Math.floor(canvas.clientHeight*dpr));if(w!==W||h!==H){W=canvas.width=w;H=canvas.height=h;gl.viewport(0,0,W,H)}}
 function position(i,n=6){if(i===0)return [0,.1,0];let t=(i-1)*2.399963229728653+1.07;let r=3.4+Math.floor((i-1)/6)*1.0;return [Math.cos(t)*r,Math.sin(i*1.63)*1.0,Math.sin(t)*r*.85]}
 function project(pos){const x=pos[0],y=pos[1],z=pos[2],v=[x,y,z,1],o=[];for(let r=0;r<4;r++)o.push(VP[r]*v[0]+VP[4+r]*v[1]+VP[8+r]*v[2]+VP[12+r]*v[3]);if(o[3]<=0)return null;return {x:(o[0]/o[3]*.5+.5)*canvas.clientWidth,y:(1-(o[1]/o[3]*.5+.5))*canvas.clientHeight,depth:o[3],scale:8/o[3]}}
 function render(state,time,cam){resize();let t=time*.001,aspect=W/H;let yaw=cam.yaw,pitch=cam.pitch,d=cam.dist;zoomDist=d;const center=cam.target||[0,0,0];eye=[center[0]+d*Math.sin(yaw)*Math.cos(pitch),center[1]+d*Math.sin(pitch),center[2]+d*Math.cos(yaw)*Math.cos(pitch)];VP=matmul(perspective(PI/3,aspect,.12,130),view(eye,center));
 gl.depthMask(true);gl.clearDepth(1);gl.clear(gl.DEPTH_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);gl.disable(gl.BLEND);gl.useProgram(progs.bg);gl.uniform2f(location(progs.bg,'uResolution'),W,H);gl.uniform1f(location(progs.bg,'uTime'),t);gl.bindBuffer(gl.ARRAY_BUFFER,bgBuffer);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);gl.drawArrays(gl.TRIANGLES,0,3);gl.disableVertexAttribArray(0);
 gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 set(progs.line,'line',VP,idMat,[.12,.36,.65],.17,t,eye);draw(progs.line,floor,gl.LINES);
 gl.depthMask(false);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);set(progs.point,'point',VP,idMat,[.45,.7,1],.55,t,eye);gl.uniform1f(location(progs.point,'uSize'),5);draw(progs.point,stars,gl.POINTS);gl.depthMask(true);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 const ids=Object.keys(state.branches||{}).sort((a,b)=>a==='root'?-1:b==='root'?1:a.localeCompare(b));const positions={};ids.forEach((id,i)=>positions[id]=position(i));
 const edges=[];for(const [id,b] of Object.entries(state.branches||{})){if(id==='root')continue;let a=positions[b.parent]||positions.root,z=positions[id];const p=(v,k)=>[v[0],v[1],v[2]];
 for(let j=0;j<20;j++){let u=j/20,v=(j+1)/20;let interp=q=>[a[0]*(1-q)+z[0]*q,a[1]*(1-q)+z[1]*q+Math.sin(q*PI)*.62,a[2]*(1-q)+z[2]*q];edges.push([interp(u),interp(v)])}}
 gl.depthMask(false);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);set(progs.line,'line',VP,idMat,[.27,.58,.94],.32,t,eye);dyn(edges);gl.depthMask(true);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 // Source-backed shared-evidence edges only; never synthesize relationships.
 const evidenceEdges=[];for(const link of state.links||[]){let a=positions[link.a],b=positions[link.b];if(!a||!b)continue;for(let j=0;j<20;j++){let u=j/20,v=(j+1)/20;let f=q=>[a[0]*(1-q)+b[0]*q,(a[1]*(1-q)+b[1]*q)+Math.sin(q*PI)*1.2,a[2]*(1-q)+b[2]*q];evidenceEdges.push([f(u),f(v)])}}
 if(evidenceEdges.length){gl.depthMask(false);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);set(progs.line,'line',VP,idMat,colors.evidence,.73,t,eye);dyn(evidenceEdges);gl.depthMask(true);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA)}
 // Genuine faceted meshes, not canvas-projected polygons. Depth test and normal lighting are GPU driven.
 for(const id of ids){const b=state.branches[id],p=positions[id];let root=id==='root',selected=id===state.selected,parked=b.status==='parked';let size=root?1.22:.63;let color=parked?colors.parked:selected?colors.selected:root?colors.root:colors.active;
 let spin=(window.matchMedia('(prefers-reduced-motion:reduce)').matches?0:t*.09)+(id==='root'?0:ids.indexOf(id)*.8);
 set(progs.solid,'solid',VP,model(p,size,spin),color,root?.97:.93,t,eye,selected?1:0);draw(progs.solid,vault,gl.TRIANGLES);
 // Segmented armor: root has four gates, active paths three, parked paths two.
 // Shape, not just color, encodes a recorded state. Geometry itself is decorative.
 const segmentCount=root?4:parked?2:3;
 for(let k=0;k<segmentCount;k++){let a=k*TAU/segmentCount+spin;let col=parked?[.65,.13,.17]:[.26,.32,.40];set(progs.solid,'solid',VP,model(p,size*1.13,a),col,1,t,eye,selected?1:0);draw(progs.solid,arc,gl.TRIANGLES);}
 // Four eccentric metallic fins lend each vessel a recognizable silhouette.
 for(let k=0;k<4;k++){let a=k*TAU/4+spin*.75,offset=(root?1.12:.58),fin=[p[0]+Math.cos(a)*offset,p[1]+Math.sin(a*1.6)*.37,p[2]+Math.sin(a)*offset];
  set(progs.solid,'solid',VP,modelStretch(fin,root?.13:.085,root?.64:.38,root?.19:.12,a),parked?[.49,.12,.16]:[.09,.24,.37],.85,t,eye,0);draw(progs.solid,crystal,gl.TRIANGLES)}
 gl.depthMask(false);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
 const ringScale=root?1.15:.6;set(progs.line,'line',VP,model(p,ringScale,spin*.7),selected?[.75,.91,1]:parked?[1,.25,.32]:[.27,.65,1],selected?.66:.34,t,eye);draw(progs.line,ring,gl.LINES);
 if(selected){set(progs.line,'line',VP,model(p,ringScale*1.18,-spin*.4),[.75,.95,1],.43,t,eye);draw(progs.line,ring,gl.LINES)}
 // Satellite source vessels are present only for recorded verified excerpts.
 // Their count grows/shrinks when replay crosses actual source receipts.
 let evidence=Math.min(10,Math.max(0,(state.counts||{})[id]||0));
 for(let k=0;k<evidence;k++){
  let a=k*2.399963229728653+spin*.34, r=1.18+(k%3)*.24;
  const vessel=[p[0]+Math.cos(a)*r*size,p[1]+Math.sin(a*1.7)*.72*size,p[2]+Math.sin(a)*r*size];
  gl.depthMask(true);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
  set(progs.solid,'solid',VP,modelStretch(vessel,.10,.30+(k%3)*.045,.14,a),[.20,.78,.57],.85,t,eye,0);draw(progs.solid,crystal,gl.TRIANGLES);
  set(progs.line,'line',VP,idMat,colors.evidence,.38,t,eye);dyn([[p,vessel]]);
  gl.depthMask(false);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
 }
 gl.depthMask(false);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
 if(state.flashId===id && state.flash>0){let ss=(1+(.95-state.flash)*.9)*ringScale;set(progs.line,'line',VP,model(p,ss,spin),state.flashType==='source_excerpt_verified'?colors.evidence:colors.selected,state.flash*.9,t,eye);draw(progs.line,ring,gl.LINES)}
 gl.depthMask(true);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 }
 lastPositions=ids.map(id=>({id,world:positions[id],screen:project(positions[id]),state:state.branches[id]}));return lastPositions;
 }
 return {gl,render,backend:webgl2?'webgl2':'webgl1',setQuality,getQuality:()=>quality,project,getPositions:()=>lastPositions,getCanvas:()=>canvas};
}
return {create:gpu};
})();
