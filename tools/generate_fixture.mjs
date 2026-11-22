import fs from 'node:fs';
import crypto from 'node:crypto';
import {makeDemo,analyzeSignal,makePrintPayload,DEFAULTS,geometry,colourOf} from '../static/splice-core.mjs';
const demo=makeDemo(),slices=analyzeSignal(demo.samples,demo.sampleRate),print=crypto.createHash('sha256').update(JSON.stringify(makePrintPayload(slices))).digest('hex');
const artifact={format:'RCLL_BITNOTE_VESSEL/0.1',source:{kind:'SYNTHETIC',name:demo.origin,duration:demo.duration},measurementFingerprint:print,mapping:DEFAULTS,bitnoteSchema:{bits:'8:energy,4:pitch,2:onset,2:timbre'},slices:slices.map(s=>({...s,rgb:colourOf(s,DEFAULTS),position:geometry(s,DEFAULTS)}))};
fs.writeFileSync(new URL('../demo_vessel.json',import.meta.url),JSON.stringify(artifact,null,2)+'\n');
console.log('fixture',slices.length, 'print',print);
