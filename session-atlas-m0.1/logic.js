/* PARALLAX Session Atlas domain logic. No DOM/network; Node-testable. */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.PX = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const COLORS = ['#7afc93','#68d9ff','#b58bff','#ffbd6d','#ff6e9e','#e0e36c','#74e9cf','#98adff','#ff8580','#a4f5e7'];
  const MAX_TABS = 2000, MAX_SESSIONS = 100, MAX_ISLANDS = 200;
  const uid = () => typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'px-' + Date.now() + '-' + Math.random().toString(36).slice(2,10);
  const str = (v, n=250) => String(v == null ? '' : v).replace(/[\x00-\x1f\x7f]/g,' ').slice(0,n).trim();
  function safeUrl(raw) { try { const u = new URL(raw); return /^https?:$/.test(u.protocol) ? u.href.slice(0,3000) : null; } catch { return null; } }
  function host(url) { try {return new URL(url).hostname.replace(/^www\./,'').toLowerCase();}catch{return 'unknown';} }
  function baseDomain(h) { const p=h.split('.'); return p.length<=2 ? h : p.slice(-2).join('.'); }
  function groupTabs(rawTabs, groupInfo={}) {
    const islands=[], byKey=new Map(), tabs=[];
    for (const original of rawTabs.slice(0,MAX_TABS)) {
      const url=safeUrl(original.url); if (!url) continue;
      const g=Number.isInteger(original.groupId) && original.groupId>=0 ? original.groupId : null;
      const domain=host(url);
      const info=g!=null ? groupInfo[g] : null;
      const key = g!=null ? 'group:'+g : 'site:'+baseDomain(domain);
      let isl=byKey.get(key);
      if(!isl){
        isl={id:uid(),name:str((info && info.title)|| (g!=null?'Tab Group '+g:baseDomain(domain)),80),color:(info&& COLORS.find(c=>c.toLowerCase()===(info.hex||'').toLowerCase()))||COLORS[islands.length%COLORS.length],collapsed:false};
        byKey.set(key,isl);islands.push(isl);
      }
      tabs.push({id:uid(),islandId:isl.id,title:str(original.title||domain,240),url,domain,sourceTabId:Number.isInteger(original.id)?original.id:null,sourceGroupId:g, pinned:!!original.pinned, captured:null});
    }
    return {islands, tabs};
  }
  function newSession(name, rawTabs, groupInfo={}) {
    const grouped=groupTabs(rawTabs,groupInfo);
    return {schema:1,id:uid(),name:str(name||'Untitled research',100)||'Untitled research',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),kind:'real',...grouped,digest:null};
  }
  function normalizeSession(s) {
    if (!s || !Array.isArray(s.tabs) || !Array.isArray(s.islands)) throw new Error('Invalid session schema');
    if(s.tabs.length>MAX_TABS || s.islands.length>MAX_ISLANDS) throw new Error('Session exceeds safety limits');
    const islands=s.islands.map((i,n)=>({id:str(i.id,100)||uid(),name:str(i.name,100)||'Island '+(n+1),color:/^#[\da-fA-F]{6}$/.test(i.color)?i.color:COLORS[n%COLORS.length]}));
    const ids=new Set(islands.map(i=>i.id));
    const tabs=s.tabs.map(t=>({id:str(t.id,100)||uid(),islandId:str(t.islandId,100),title:str(t.title,240)||'Untitled',url:safeUrl(t.url),domain:host(t.url),sourceTabId:null,sourceGroupId:null,pinned:!!t.pinned,captured: t.captured&&typeof t.captured==='object'?{text:str(t.captured.text,2400),at:str(t.captured.at,40),url:str(t.captured.url,3000)}:null})).filter(t=>t.url&&ids.has(t.islandId));
    return {schema:1,id:uid(),name:str(s.name,100)||'Imported session',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),kind:'imported',islands,tabs,digest: typeof s.digest==='object'&&s.digest&&str(s.digest.text,14000)?{text:str(s.digest.text,14000),mode:str(s.digest.mode,40),at:str(s.digest.at,40)}:null};
  }
  function metrics(s){return {islands:s.islands.length,tabs:s.tabs.length,domains:new Set(s.tabs.map(t=>t.domain)).size,evidence:s.tabs.filter(t=>t.captured&&t.captured.text).length};}
  const stopwords=new Set('about after again also another are been before between browser build building click code docs download from have here into just more most next only open over page pages project read research results some source system tabs than that their them then there these this through using what when where which with would your'.split(' '));
  function keywords(tabs,n=8){const count=new Map();for(const t of tabs){const words=String(t.title).toLowerCase().match(/[a-z][a-z0-9-]{3,}/g)||[];for(const w of new Set(words)){if(!stopwords.has(w))count.set(w,(count.get(w)||0)+1);}}return [...count.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,n).map(x=>x[0]);}
  function metadataDigest(s){const m=metrics(s),topDomains=[...new Set(s.tabs.map(t=>t.domain))].slice(0,7);return `Metadata overview (not AI): ${m.tabs} saved tab${m.tabs===1?'':'s'} in ${m.islands} island${m.islands===1?'':'s'}, spanning ${m.domains} domains. ${m.evidence} tabs have explicit page-text evidence. Recurring title terms: ${keywords(s.tabs,7).join(', ')||'insufficient data'}. Sites include ${topDomains.join(', ')||'none'}. This preview is based on saved URLs and titles, not independently verified article content.`;}
  function demoSession(){
    const names=['BYTE-FIRST AI','SELF / MORPHIC','BROWSER ARCHITECTURE','LOCAL MODELS','MUSIC / VELA','GRAPH TOPOLOGY','SECURITY','DESIGN REFERENCES','AUTOMATION','ARCHIVES'];
    const examples=[
      ['https://ai.meta.com/blog/','Meta AI research notes'],['https://github.com/russellallen/self','Self language sources'],['https://learn.microsoft.com/en-us/microsoft-edge/webview2/','WebView2 documentation'],
      ['https://ollama.com/library','Ollama model library'],['https://www.reaper.fm/','REAPER workstation'],['https://en.wikipedia.org/wiki/Graph_theory','Graph topology primer'],
      ['https://owasp.org/www-project-top-ten/','OWASP browser security'],['https://developer.mozilla.org/','MDN web platform'],['https://docs.github.com/','GitHub automation docs'],['https://archive.org/','Internet Archive']
    ];
    const islands=names.map((name,i)=>({id:'demo-island-'+i,name,color:COLORS[i]}));
    const tabs=[];
    for(let i=0;i<300;i++){const x=i%10;tabs.push({id:'demo-tab-'+i,islandId:islands[x].id,title:examples[x][1]+' · reference '+(Math.floor(i/10)+1),url:examples[x][0]+'?sample='+i,domain:host(examples[x][0]),sourceTabId:null,sourceGroupId:null,pinned:false,captured:null});}
    return {schema:1,id:'demo-300',name:'OX / RESEARCH ARCHIPELAGO',createdAt:'2026-11-22T12:00:00.000Z',updatedAt:'2026-11-22T12:00:00.000Z',kind:'demo',islands,tabs,digest:{text:'Illustrative only, not generated by AI. Ten parallel research threads examine byte-first AI, Self/Morphic, browser architecture, local models, audio, topology, security, design, automation and archives. The saved structure helps resume the investigation without reopening all 300 pages. No example page content was fetched.',mode:'demo',at:'2026-11-22T12:00:00.000Z'}};
  }
  return {uid,str,safeUrl,host,groupTabs,newSession,normalizeSession,metrics,keywords,metadataDigest,demoSession,COLORS,MAX_TABS,MAX_SESSIONS};
});
