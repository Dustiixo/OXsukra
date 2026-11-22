const assert=require('node:assert/strict');
const test=require('node:test');
const p=require('../logic.js');
test('300 real tabs grouped into ten existing Chrome groups',()=>{
  const tabs=Array.from({length:300},(_,i)=>({id:i+1,title:'Source '+i,url:'https://docs.example.org/page/'+i,groupId:i%10}));
  const s=p.newSession('Large research',tabs,Object.fromEntries(Array.from({length:10},(_,i)=>[i,{title:'Island '+i}])));
  assert.equal(s.tabs.length,300);assert.equal(s.islands.length,10);assert.equal(p.metrics(s).tabs,300);
  assert.equal(s.tabs.filter(t=>t.islandId===s.islands[0].id).length,30);
});
test('dedicated domain islands for ungrouped tabs',()=>{
 const s=p.newSession('test',[{url:'https://learn.microsoft.com/en-us/'},{url:'https://learn.microsoft.com/en-us/edge'},{url:'https://github.com/owner/repo'}]);
 assert.equal(s.tabs.length,3);assert.equal(s.islands.length,2);
});
test('safe URL scheme rejects local, javascript, extension and file URLs',()=>{
 for(const url of ['javascript:alert(1)','file:///etc/passwd','chrome://settings','data:text/html,a','http://'])assert.equal(p.safeUrl(url),null);
 assert.equal(p.safeUrl('https://example.com/a'),'https://example.com/a');
});
test('import removes external source identifiers and rejects bad URL',()=>{
 const s=p.normalizeSession({name:'Imported',islands:[{id:'a',name:'one',color:'#00ff00'}],tabs:[{islandId:'a',title:'X',url:'https://example.com',sourceTabId:777},{islandId:'a',url:'file:///tmp/x'}]});
 assert.equal(s.tabs.length,1);assert.equal(s.tabs[0].sourceTabId,null);
});
test('bounded session rejects oversize',()=>{
 assert.throws(()=>p.normalizeSession({islands:[{id:'x'}],tabs:Array.from({length:2001},()=>({}))}),/safety/);
});
test('metadata overview never presents itself as AI or verified content',()=>{
 const d=p.metadataDigest(p.demoSession());assert.match(d,/not AI/i);assert.match(d,/not independently verified/i);
});
test('demo is 300 URL records across exactly 10 synthetic islands',()=>{
 const s=p.demoSession();assert.equal(s.tabs.length,300);assert.equal(s.islands.length,10);assert.equal(s.kind,'demo');
});
