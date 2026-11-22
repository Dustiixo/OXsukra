/* Explicitly injected. Reads only URL-bearing attributes + change counts; no fields/text/bodies. */
(() => {
 "use strict";
 if (window.__oxParallaxObserver) return;
 const state={alive:true,dirty:true,present:new Map(),mutation:{added:0,removed:0,attributes:0},timed:new Set()};
 window.__oxParallaxObserver=state;
 const VALID=new Set(["a","script","link","iframe","img","video","audio","source"]);
 const send=(type,targets=[],count=1,kind="")=>{
   if(!state.alive)return;
   browser.runtime.sendMessage({action:"observation",type,targets,count,kind}).catch(()=>{});
 };
 function scan(){
   if(!state.alive||!state.dirty)return;
   state.dirty=false;
   const fresh=[],removed=[],now=new Map();
   let freshTotal=0;
   const elements=document.querySelectorAll("a[href],script[src],link[href],iframe[src],img[src],video[src],audio[src],source[src]");
   const complete=elements.length<=900;
   for(let i=0;i<Math.min(elements.length,900);i++){
     const e=elements[i],tag=e.tagName.toLowerCase();if(!VALID.has(tag))continue;
     const url=e.href||e.src;if(typeof url!=="string"||!/^https?:/i.test(url))continue;
     const key=tag+"|"+url;
     now.set(key,{tag,url});
     if(!state.present.has(key)){freshTotal++;if(fresh.length<90)fresh.push({tag,url});}
   }
   // In truncated/huge pages, missing elements are not proof that links disappeared.
   if(complete)for(const [key,entry] of state.present){if(!now.has(key)&&removed.length<60)removed.push(entry);}
   state.present=now;
   if(fresh.length)send("dom_assets",fresh);
   if(freshTotal>90)send("overflow",[],freshTotal-90,"dom-urls");
   if(elements.length>900)send("overflow",[],elements.length-900,"dom-limit");
   if(removed.length)send("dom_removed",removed);
   for(const [kind,count] of Object.entries(state.mutation))if(count)send("mutation",[],count,kind);
   state.mutation={added:0,removed:0,attributes:0};
 }
 let debounce=null;
 const observer=new MutationObserver(records=>{
   if(!state.alive)return;
   if(records.length>400)send("overflow",[],records.length-400,"mutation-limit");
   for(const record of records.slice(0,400)){
     if(record.type==="attributes")state.mutation.attributes=Math.min(1000000,state.mutation.attributes+1);
     if(record.type==="childList"){
       state.mutation.added=Math.min(1000000,state.mutation.added+record.addedNodes.length);
       state.mutation.removed=Math.min(1000000,state.mutation.removed+record.removedNodes.length);
     }
   }
   state.dirty=true;
   if(!debounce)debounce=setTimeout(()=>{debounce=null;scan();},600);
 });
 observer.observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:["href","src"]});
 scan();
 // Resource Timing can reveal completed/cached resources not delivered through webRequest;
 // these are marked "timed hint", never mislabeled as observed HTTP requests.
 let performanceObserver=null;
 try{
   performanceObserver=new PerformanceObserver(list=>{
     if(!state.alive)return;
     const hints=[];
     const entries=list.getEntries();
     if(entries.length>80)send("overflow",[],entries.length-80,"performance-limit");
     for(const entry of entries.slice(0,80)){
       if(typeof entry.name==="string" && /^https?:/i.test(entry.name) && !state.timed.has(entry.name)){
         if(state.timed.size<1500)state.timed.add(entry.name);
         hints.push({url:entry.name,tag:"timed"});
       }
     }
     if(hints.length)send("resource_hints",hints);
   });
   performanceObserver.observe({type:"resource",buffered:true});
 }catch(_){ /* optional API; no change to network observer */ }
 function stop(){state.alive=false;observer.disconnect();if(performanceObserver)performanceObserver.disconnect();if(debounce)clearTimeout(debounce);state.present.clear();state.timed.clear();}
 browser.runtime.onMessage.addListener(msg=>{if(msg&&msg.action==="parallax-stop")stop();});
 window.addEventListener("pagehide",stop,{once:true});
})();
