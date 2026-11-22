/* Synthetic browser content integration: SPA-style additions/removals and resource hints. */
const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const assert=require('node:assert/strict');
let elements=[{tagName:'A',href:'https://demo.example.org/start'}];
const sent=[];let mutationCallback=null,performanceCallback=null,timerCallback=null,stopped=false;
class MutationObserverMock{constructor(fn){mutationCallback=fn;}observe(){}disconnect(){stopped=true;}}
class PerformanceObserverMock{constructor(fn){performanceCallback=fn;}observe(){}disconnect(){}}
const context={
 window:{addEventListener(){}},
 document:{querySelectorAll(){return elements;}},
 browser:{runtime:{sendMessage:async msg=>{sent.push(msg);},onMessage:{addListener(){}}}},
 MutationObserver:MutationObserverMock,PerformanceObserver:PerformanceObserverMock,
 setTimeout:fn=>{timerCallback=fn;return 1;},clearTimeout:()=>{},console
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension/content.js'),'utf8'),context);
assert.ok(sent.some(e=>e.type==='dom_assets'));
elements=[{tagName:'A',href:'https://demo.example.org/replaced'}, {tagName:'SCRIPT',src:'https://cdn.example.net/client.js?api=secret'}];
mutationCallback([{type:'childList',addedNodes:[{}],removedNodes:[{}]},{type:'attributes',addedNodes:[],removedNodes:[]}]);
assert.equal(typeof timerCallback,'function');timerCallback();
assert.ok(sent.some(e=>e.type==='dom_removed'));
assert.ok(sent.some(e=>e.type==='mutation' && e.kind==='added'));
assert.ok(sent.some(e=>e.type==='mutation' && e.kind==='removed'));
assert.ok(sent.some(e=>e.type==='mutation' && e.kind==='attributes'));
performanceCallback({getEntries:()=>[{name:'https://static.example.net/resource.css?auth=SECRET'}]});
assert.ok(sent.some(e=>e.type==='resource_hints'));
assert.ok(!stopped);
assert.ok(!JSON.stringify(sent).includes('innerHTML'));
console.log('PASS: SPA additions/removals, mutation coalescing, resource timing hints.');
