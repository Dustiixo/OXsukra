/* OX Byte World *projection* core, zero packages; Python's bytebridge is the verified artifact writer.
   This is empirical local byte entropy, NOT learned Meta BLT patching. */
export const COUNT=1000, MAX_BYTES=16*1024*1024;
export const PARAMS=Object.freeze({depth:1.2, twist:2, hue:0, threshold:0.18});
export function entropy(bytes) {
 if(!bytes.length) return 0;
 const counts=new Uint32Array(256);for(const v of bytes)counts[v]++;
 let h=0;for(const n of counts)if(n){const p=n/bytes.length;h-=p*Math.log2(p);}return h;
}
export function patchesOf(bytes) {
 if(!(bytes instanceof Uint8Array)||bytes.length>MAX_BYTES)throw Error('Requires bounded Uint8Array');
 let at=0;const result=[];
 while(at<bytes.length){const bits=entropy(bytes.subarray(at,at+64));const length=Math.max(8,Math.min(256,Math.round(256-Math.min(1,bits/8)*248)));
  const end=Math.min(bytes.length,at+length);result.push({index:result.length,start:at,end,length:end-at,entropyMilli:Math.round(entropy(bytes.subarray(at,end))*1000)});at=end;
 }
 return result;
}
export function splicesOf(bytes) {
 if(!(bytes instanceof Uint8Array)||bytes.length>MAX_BYTES)throw Error('Requires bounded Uint8Array');
 const result=[],n=bytes.length;
 for(let i=0;i<COUNT;i++){const start=Math.floor(i*n/COUNT),end=Math.floor((i+1)*n/COUNT),b=bytes.subarray(start,end),h=entropy(b);
  let sum=0,zero=0,printable=0;for(const v of b){sum+=v;if(v===0)zero++;if(v>=32&&v<127)printable++;}
  result.push({index:i,gateRow:Math.floor(i/100),gateColumn:Math.floor((i%100)/10),subsplice:i%10,
    start,end,length:b.length,entropyMilli:Math.round(h*1000),meanByteMilli:b.length?Math.round(1000*sum/b.length):0,zeroCount:zero,printableCount:printable});
 }
 return result;
}
export function positionOf(s,p=PARAMS){const t=s.index/999,e=s.entropyMilli/8000, v=s.length? s.meanByteMilli/255000:0;
 const angle=t*Math.PI*(8+p.twist),r=(30+p.depth*100)*(0.35+e);
 return {x:(t-.5)*780,y:Math.sin(angle)*r+(v-.5)*200,z:Math.cos(angle)*r+(e-.5)*120};}
