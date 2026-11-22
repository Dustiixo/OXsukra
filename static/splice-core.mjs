/* OX / RCLL core. Pure math, no network, no arbitrary code execution. */
export const COUNT=1000, FFT_N=2048;
export const NOTE_NAMES=['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
export const DEFAULTS=Object.freeze({depth:1.2,twist:2.0,hue:0,threshold:0.18});
export const SLOT_NAMES=['depth','twist','hue','threshold'];
export function clamp(x,min,max){return Math.min(max,Math.max(min,x));}
export function makeDemo(rate=11025, seconds=12){
 const n=Math.floor(seconds*rate), arr=new Float32Array(n), bpm=155, beat=60/bpm;
 const tune=[55,58,62,65,62,58,53,60];
 for(let i=0;i<n;i++){
   const t=i/rate, bi=Math.floor(t/beat), phase=(t%beat)/beat, midi=tune[Math.floor(bi/2)%tune.length];
   const hz=440*Math.pow(2,(midi-69)/12);
   const note=(Math.sin(2*Math.PI*hz*t)+0.32*Math.sin(2*Math.PI*hz*2*t))*0.28;
   const kick=Math.sin(2*Math.PI*(63-30*Math.min(phase,0.5))*t)*0.60*Math.exp(-phase*13);
   const hat=(Math.sin(2*Math.PI*3217*t)+Math.sin(2*Math.PI*4211*t))*0.035*Math.exp(-(t%(beat/2))/(beat/2)*15);
   arr[i]=clamp(note+kick+hat,-1,1);
 }
 return {samples:arr,sampleRate:rate,duration:seconds,origin:'SYNTHETIC / 155 BPM STUDY'};
}
export function fftMagnitudes(input){
 const n=input.length;
 if(n===0||(n&(n-1))!==0)throw new Error('FFT length must be power of two');
 const re=new Float64Array(n),im=new Float64Array(n);
 for(let i=0;i<n;i++){const w=0.5-0.5*Math.cos(2*Math.PI*i/(n-1));re[i]=input[i]*w;}
 for(let i=1,j=0;i<n;i++){
   let bit=n>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;
   if(i<j){const tmp=re[i];re[i]=re[j];re[j]=tmp;}
 }
 for(let len=2;len<=n;len<<=1){const ang=-2*Math.PI/len, wr=Math.cos(ang),wi=Math.sin(ang);
   for(let i=0;i<n;i+=len){let ar=1,ai=0;
     for(let j=0;j<len/2;j++){
       const u=i+j,v=u+len/2,vr=re[v]*ar-im[v]*ai,vi=re[v]*ai+im[v]*ar;
       re[v]=re[u]-vr;im[v]=im[u]-vi;re[u]+=vr;im[u]+=vi;
       const next=ar*wr-ai*wi;ai=ar*wi+ai*wr;ar=next;
     }
   }
 }
 const out=new Float64Array(n/2);for(let i=0;i<n/2;i++)out[i]=Math.hypot(re[i],im[i]);return out;
}
export function addressOf(i){if(!Number.isInteger(i)||i<0||i>=COUNT)throw new RangeError('Splice address out of bounds');return {gateRow:Math.floor(i/100),gateColumn:Math.floor((i%100)/10),subsplice:i%10};}
export function encodeWord(energy,pitch,onset,timbre){
 const e=clamp(Math.round(energy*255),0,255),p=clamp(Math.round(pitch),0,11),o=clamp(Math.round(onset),0,3),t=clamp(Math.round(timbre),0,3);
 return (e<<8)|(p<<4)|(o<<2)|t;
}
export function decodeWord(word){return {energy8:(word>>8)&255,pitchClass:(word>>4)&15,onset2:(word>>2)&3,timbre2:word&3};}
export function rgb(h,s,l){h=((h%360)+360)%360;s=clamp(s,0,1);l=clamp(l,0,1);
 const a=s*Math.min(l,1-l);const f=n=>{const k=(n+h/30)%12;return Math.round(255*(l-a*Math.max(-1,Math.min(k-3,9-k,1))));};return [f(0),f(8),f(4)];}
export function colourOf(slice,params){return rgb(slice.pitch*30+params.hue,0.72,clamp(0.18+slice.energy*0.54,0.14,0.72));}
export function normalizeParams(candidate={}){
 const p={...DEFAULTS,...candidate};for(const k of SLOT_NAMES){if(typeof p[k]!=='number'||!Number.isFinite(p[k]))throw new Error(`Invalid ${k}`);}
 p.depth=clamp(p.depth,0,3);p.twist=clamp(p.twist,-6,6);p.hue=clamp(p.hue,-180,180);p.threshold=clamp(p.threshold,0,1);return p;
}
export function geometry(slice,params){const p=normalizeParams(params),t=slice.index/999,phi=t*Math.PI*(6+p.twist);
 const radius=80+p.depth*55*(0.5+slice.bass),h=20+slice.energy*130*p.depth;
 return {x:(t-0.5)*740,y:Math.cos(phi)*radius+(slice.pitch-5.5)*7+h*0.3,z:Math.sin(phi)*radius+(slice.centroid-0.5)*100*p.depth,height:h};
}
export function analyzeWindow(samples,sampleRate,index,count=COUNT){
 const n=FFT_N, input=new Float32Array(n),center=Math.floor(((index+0.5)/count)*samples.length),step=Math.max(1,Math.round(sampleRate/11025));
 let sum=0;for(let j=0;j<n;j++){const ix=center+(j-n/2)*step, v=(ix>=0&&ix<samples.length)?samples[ix]:0;input[j]=v;sum+=v*v;}
 const rms=Math.sqrt(sum/n),mag=fftMagnitudes(input),rate=sampleRate/step;
 const chroma=new Float64Array(12);let bass=0,mid=0,treble=0,weight=0,weightedHz=0;
 for(let k=1;k<mag.length;k++){
   const hz=k*rate/n,amp=mag[k];if(hz<30||hz>5000)continue;
   if(hz<180)bass+=amp;else if(hz<1800)mid+=amp;else treble+=amp;
   weight+=amp;weightedHz+=hz*amp;
   if(hz>=65.4&&hz<2100){const midi=Math.round(69+12*Math.log2(hz/440));chroma[((midi%12)+12)%12]+=amp;}
 }
 let pitch=0;for(let k=1;k<12;k++)if(chroma[k]>chroma[pitch])pitch=k;
 const totalChroma=chroma.reduce((a,b)=>a+b,0)||1;
 const total=bass+mid+treble||1;
 return {index,time:Number(((index+0.5)/count)*(samples.length/sampleRate)).toFixed(4),rms,bass:bass/total,mid:mid/total,treble:treble/total,centroid:clamp(weight?weightedHz/weight/3500:0,0,1),chroma:Array.from(chroma,x=>x/totalChroma),pitch};
}
export function finishSlice(s,prevRms=0,normalizer=0.4){
 const energy=clamp(s.rms/Math.max(normalizer,0.001),0,1);
 const silent=s.rms<1e-6;
 const onset=clamp(Math.round(Math.max(0,s.rms-prevRms)*12),0,3);
 const timbre=silent?0:(s.bass>s.mid&&s.bass>s.treble?0:s.treble>s.mid?2:1);
 const word=encodeWord(energy,s.pitch,onset,timbre);const addr=addressOf(s.index);
 return {...s,energy,silent,onset,timbre,word,bitnote:word.toString(2).padStart(16,'0'),...addr};
}
export function analyzeSignal(samples,sampleRate,count=COUNT){
 if(!(samples instanceof Float32Array)||samples.length<64||sampleRate<8000||sampleRate>192000)throw new Error('Invalid PCM input');
 if(count!==COUNT)throw new Error('This experiment uses exactly 1000 micro-splices');
 const raw=[];for(let i=0;i<count;i++)raw.push(analyzeWindow(samples,sampleRate,i,count));
 const sorted=raw.map(s=>s.rms).sort((a,b)=>a-b);const norm=Math.max(sorted[Math.floor(sorted.length*0.94)]*1.4,0.015);
 return raw.map((s,i)=>finishSlice(s,i?raw[i-1].rms:0,norm));
}
export async function analyzeSignalAsync(samples,sampleRate,onProgress){
 if(!(samples instanceof Float32Array)||samples.length<64||sampleRate<8000||sampleRate>192000)throw new Error('Invalid PCM input');
 const raw=[];for(let start=0;start<COUNT;start+=25){for(let i=start;i<Math.min(COUNT,start+25);i++)raw.push(analyzeWindow(samples,sampleRate,i));
   onProgress?.(raw.length/COUNT);await new Promise(resolve=>setTimeout(resolve,0));}
 const sorted=raw.map(s=>s.rms).sort((a,b)=>a-b);const norm=Math.max(sorted[Math.floor(sorted.length*.94)]*1.4,.015);
 return raw.map((s,i)=>finishSlice(s,i?raw[i-1].rms:0,norm));
}
export function parseSlotScript(text){
 if(typeof text!=='string'||text.length>1200)throw Error('Input too long');
 const obj={};for(const raw of text.split('\n')){
  const line=raw.trim();if(!line||line.startsWith('#')||line.startsWith('//'))continue;
  const m=line.match(/^(depth|twist|hue|threshold)\s*:\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*\.?$/);
  if(!m)throw Error('Unsupported slot expression: '+line.slice(0,60));
  if(Object.hasOwn(obj,m[1]))throw Error('Duplicate slot: '+m[1]);obj[m[1]]=Number(m[2]);
 }
 if(Object.keys(obj).length===0)throw Error('No slot assignments');return normalizeParams({...DEFAULTS,...obj});
}
export function slotScript(p){const o=normalizeParams(p);return SLOT_NAMES.map(k=>`${k}: ${o[k]}.`).join('\n');}
export function makePrintPayload(slices){return slices.map(s=>[s.word,...s.chroma.map(x=>Math.round(x*65535))]);}
export function wavBytes(samples,rate){
 const n=samples.length,buf=new ArrayBuffer(44+n*2),dv=new DataView(buf),bytes=new Uint8Array(buf);
 const put=(at,str)=>{for(let i=0;i<str.length;i++)bytes[at+i]=str.charCodeAt(i);};
 put(0,'RIFF');dv.setUint32(4,36+n*2,true);put(8,'WAVE');put(12,'fmt ');dv.setUint32(16,16,true);dv.setUint16(20,1,true);dv.setUint16(22,1,true);dv.setUint32(24,rate,true);dv.setUint32(28,rate*2,true);dv.setUint16(32,2,true);dv.setUint16(34,16,true);put(36,'data');dv.setUint32(40,n*2,true);
 for(let i=0;i<n;i++)dv.setInt16(44+2*i,Math.round(clamp(samples[i],-1,1)*32767),true);return buf;
}
