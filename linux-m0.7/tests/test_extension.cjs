const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const P=require('../extension/core.js');
const base='https://demo.example.org/';
assert.equal(P.cleanUrl('https://demo.example.org/home?token=abc#secret'),'https://demo.example.org/home');
assert.equal(P.cleanUrl('javascript:alert(1)'),null);
assert.equal(P.cleanUrl('file:///etc/passwd'),null);
assert.equal(P.cleanUrl('https://demo.example.org/checkout'),null);
assert.equal(P.cleanUrl('https://demo.example.org/verylongsegmentttttttttttttttttttttttt'),'https://demo.example.org/[redacted-path]');
assert.equal(P.cleanUrl('http://localhost:8000/foo'),null);
assert.equal(P.cleanUrl('https://admin:password@demo.example.org/'),null);
const v=P.safeEvent({type:'request',from:base,to:'https://cdn.example.net/a.js?api_key=SECRET',status:200},base);
assert.equal(v.to,'https://cdn.example.net/a.js');
const cookie=P.safeEvent({type:'cookie_meta',from:base,name:'session',value:'PRIVATE',cookieDomain:'.demo.example.org',secure:true},base);
assert.ok(!Object.hasOwn(cookie,'value'));assert.equal(cookie.secure,true);
const feed=new P.BoundedFeed(80,25,30);
for(let i=0;i<1500;i++)feed.add(P.safeEvent({type:'request',from:base,to:`https://cdn${i}.example.net/x.js`},base));
assert.equal(feed.snapshot().nodes.length,25); assert.equal(feed.snapshot().edges.length,24);
assert.equal(feed.snapshot().pending,80);assert.ok(feed.snapshot().dropped>0);
const calls={};const register=name=>({addListener:fn=>{calls[name]=fn}});
const state={activeTab:{id:4,url:'https://demo.example.org/hello?x=1',incognito:false}};
const fakeBrowser={
 webRequest:{onBeforeRequest:register('request'),onCompleted:register('complete'),onErrorOccurred:register('error'),onBeforeRedirect:register('redirect')},
 webNavigation:{onCommitted:register('committed'),onHistoryStateUpdated:register('history'),onCreatedNavigationTarget:register('popup'),onCompleted:register('navigateDone')},
 tabs:{onRemoved:register('removed'),get:async()=>state.activeTab,reload:async()=>{},executeScript:async()=>{},sendMessage:async()=>{},update:async()=>{}},
 runtime:{onMessage:register('msg'),connectNative:()=>{throw Error('No host');}},
 browserAction:{onClicked:register('clicked')},sidebarAction:{open:async()=>{}},
 permissions:{contains:async()=>true}
};
const context={ParallaxCore:P,browser:fakeBrowser,crypto:{randomUUID:()=> '00112233-4455-4677-8899-aabbccddeeff'},setInterval:()=>{},setTimeout,clearTimeout,URL,console};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension/background.js'),'utf8'),context);
(async()=>{
 const arm=await calls.msg({action:'arm',tabId:4},{});assert.equal(arm.ok,true);
 calls.request({tabId:4,type:'script',url:'https://cdn.example.net/dynamic.js?token=private'});
 calls.complete({tabId:4,type:'script',url:'https://cdn.example.net/dynamic.js?token=private',statusCode:200});
 calls.popup({sourceTabId:4,tabId:5,url:'https://new.example.net/page#private'});
 await calls.msg({action:'observation',type:'dom_assets',targets:[{tag:'a',url:'https://other.example.net/link?secret=1'}]}, {tab:{id:4},url:'https://demo.example.org/hello'});
 const snap=await calls.msg({action:'state'},{});
 assert.equal(snap.graph.total,4);
 assert.ok(snap.graph.edges.some(e=>e.type==='request'));
 assert.ok(snap.graph.edges.some(e=>e.type==='link'));
 assert.ok(snap.graph.edges.some(e=>e.type==='popup'));
 assert.ok(!JSON.stringify(snap).includes('private'));
 // Unexpected cross-origin change disarms to protect accidental bleed.
 calls.committed({tabId:4,frameId:0,url:'https://another.example.net/'});
 await new Promise(r=>setTimeout(r,0));
 assert.equal((await calls.msg({action:'state'},{})).armed,false);
 console.log('PASS: URL hygiene, bounded influx, popup semantics, opt-in enforcement, nav disarm, no query/cookie value leak.');
})().catch(e=>{console.error(e);process.exitCode=1});
