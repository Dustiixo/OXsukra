HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OX Funnel / HERMES</title><style>
:root{color-scheme:dark;font-family:ui-monospace,Consolas,monospace;background:#0a0e13;color:#e3eaf2}*{box-sizing:border-box}body{margin:0;max-width:1120px;padding:24px 18px 80px;margin-inline:auto}h1{font-size:26px;letter-spacing:-1px}h1 span{color:#e24d59}h2{font-size:15px;letter-spacing:.08em;margin:0 0 12px}small,.muted{color:#96a8b8}p{line-height:1.55}.shell{border:1px solid #314256;border-radius:11px;padding:18px;margin:16px 0;background:#101824}.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:15px}input,textarea,button,select{background:#0d121b;color:#f1f5f8;border:1px solid #395066;padding:10px;border-radius:7px;font:inherit}input{min-width:230px}button{cursor:pointer;border-color:#5a7187}button:hover{background:#26384d}button.primary{background:#17364a;border-color:#61b9d9}label{display:block;color:#aac6dc;font-size:12px;margin-bottom:6px}table{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}th{text-align:left;color:#8ea6bb}td,th{padding:9px 5px;border-bottom:1px solid #293747;overflow-wrap:anywhere}.pill{padding:3px 8px;border:1px solid #3d5a71;border-radius:20px;font-size:11px}#message{white-space:pre-wrap;color:#d1e8ba;font-size:12px}.hint{font-size:12px;color:#9bacbd}code{color:#89d6dc}a{color:#96d9ef}textarea{width:100%;height:100px}::placeholder{color:#74879b}</style></head><body>
<header class="row" style="justify-content:space-between"><div><h1><span>OX</span> FUNNEL <small>/ HERMES BRIDGE</small></h1><div class="muted">Local-first intake • private by default • approved team exchange</div></div><span class="pill">v0.5 · editable pilot</span></header>
<section class="shell"><h2>ACCESS</h2><div class="row"><input id="token" type="password" placeholder="Paste your member token" autocomplete="off"><button id="connect" class="primary">Connect</button><button id="clear">Clear token</button><span id="who" class="muted"></span></div><p class="hint">The token stays in this browser tab's session storage. This interface requires the same token as the local funnel sender. Use a private VPN or HTTPS for access from other machines.</p><div id="message"></div></section>
<div class="grid"><section class="shell"><h2>HUB STATUS</h2><div id="status" class="muted">Connect to load status.</div><button id="refresh" style="margin-top:12px">Refresh all</button></section>
<section class="shell"><h2>KNOWLEDGE SEARCH</h2><div class="row"><input id="query" placeholder="Find files, references, notes"><button id="search">Search</button></div><div id="results" style="margin-top:12px" class="hint"></div></section></div>
<section class="shell"><h2>SUBMIT A FILE · PRIVATE BY DEFAULT</h2><p class="hint">Choose a file deliberately. Browser uploads are limited to 32 MiB; the desktop Funnel handles large files with resumable chunks. Nothing is sent to Discord, Drive or another member until authorized.</p><div class="row"><input type="file" id="file-select"><input id="file-project" value="shared" maxlength="40" placeholder="Project slug"><button id="file-upload" class="primary">Submit privately</button></div><p id="file-progress" class="hint" aria-live="polite">Waiting for a selected file.</p></section>
<section class="shell"><h2>HERMES ROUTER · SAFE PREVIEW</h2><p class="hint">Preview possible event routes before anything happens. v0.2 only records explicit metadata-only events; it does not send commands to other bots, launch compute jobs, stream media, or copy files. Read the disclosure and obtain member agreement before deploying.</p><div class="grid"><div><label>Event type</label><select id="event-type"><option value="artifact.received">Artifact received</option><option value="music.requested">Music requested</option><option value="session.planned">Session planned</option><option value="experiment.proposed">Experiment proposed</option><option value="business.idea_submitted">Business idea submitted</option><option value="release.proposed">Release proposed</option><option value="home.alert">Home alert</option></select><label style="margin-top:10px">Project</label><input id="event-project" value="shared" style="width:100%"></div><div><label>Short summary (no secrets or personal records)</label><textarea id="event-summary" maxlength="300" placeholder="An explicit, metadata-only event description"></textarea></div></div><div class="row"><button id="event-preview">Preview routing</button><button id="event-record" class="primary">Record event (no execution)</button></div><label style="margin-top:12px"><input id="disclosure-ack" type="checkbox" style="min-width:unset"> I have read the disclosure and intend only to record metadata</label><pre id="event-result" style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;color:#b6cde0"></pre></section>
<div class="grid"><section class="shell"><h2>INTEGRATION REGISTRY</h2><p class="hint">Capabilities and statuses; a listed third-party service is NOT automatically installed, trusted, or controllable.</p><div id="integration-summary" class="hint">Connect to browse modules.</div><button id="integration-list">Inspect integrations</button></section><section class="shell"><h2>DISCLOSURE & DATA ACCESS</h2><div id="disclosure-summary" class="hint">Read full disclosure before sharing real content. Group retention, deletion and ACL controls still need setup.</div><button id="disclosure-open">Inspect current disclosure</button></section></div>
<section class="shell"><h2>PROCESSING QUEUE</h2><div style="overflow-x:auto"><table><thead><tr><th>File</th><th>Project</th><th>Job</th><th>Status</th><th>Mirror</th></tr></thead><tbody id="jobs"><tr><td colspan="5">No data yet.</td></tr></tbody></table></div></section>
<section class="shell"><h2>FILES I CAN ACCESS</h2><p class="hint">Uploads start private. Owners can explicitly share a file with the team; mirroring externally needs a separate authorization. Shared categories are labels, not permissions.</p><div style="overflow-x:auto"><table><thead><tr><th>Name</th><th>Project</th><th>Owner</th><th>Visibility</th><th>Actions</th></tr></thead><tbody id="items"><tr><td colspan="5">No data yet.</td></tr></tbody></table></div></section>
<div class="grid"><section class="shell"><h2>ADD A KNOWLEDGE POINT</h2><label>Title</label><input id="note-title" style="width:100%" placeholder="Proposed discovery"><label>Project</label><input id="note-project" value="shared" style="width:100%"><label>Text / evidence</label><textarea id="note-body" placeholder="Claim, reference, next verification..."></textarea><button id="add-note" class="primary">Create proposed note</button><p class="hint">New notes are proposed, not automatically verified. Uploaded files and AI annotations do not become approved facts.</p></section>
<section class="shell"><h2>DOCUMENTED API</h2><p class="hint">Obsidian export includes approved notes only: <code>python -m funnel export-obsidian team-notes.zip</code>.</p><p class="hint">Clickable endpoints, accessed with authenticated requests through this dashboard.</p><div id="api-links" class="row"></div><pre id="api-preview" style="white-space:pre-wrap;font-size:12px;color:#b6cde0"></pre><p class="hint">Programmatic access: <code>Authorization: Bearer TOKEN</code>. Refer to README for uploads and resumable chunks.</p></section></div>
<section class="shell"><h2>KNOWLEDGE REVIEW</h2><p class="hint">Authors submit proposed notes for review. Admins can approve or reject; approved team notes become searchable and exportable. No automatic promotion of AI claims.</p><div id="note-list" class="hint">Connect to view knowledge points.</div></section>
<script>
const $=id=>document.getElementById(id);
let token=sessionStorage.getItem('funnelToken')||'';$('token').value=token;
function msg(s){$('message').textContent=s}
async function api(route,opt={}){const r=await fetch(route,{...opt,headers:{'Authorization':'Bearer '+token,...(opt.body?{'Content-Type':'application/json'}:{}),...(opt.headers||{})}});let v=await r.json().catch(()=>({error:'Invalid response'}));if(!r.ok)throw Error(v.error||r.status);return v}
function td(text){let e=document.createElement('td');e.textContent=String(text??'');return e}
function replaceRows(id,rows,render){const e=$(id);e.textContent='';if(!rows.length){let tr=document.createElement('tr');let cell=td('No records');cell.colSpan=5;tr.append(cell);e.append(tr);return}for(const row of rows){let tr=document.createElement('tr');render(tr,row);e.append(tr)}}
async function refresh(){if(!token){msg('Enter an access token.');return}try{const [s,j,i]=await Promise.all([api('/api/v1/status'),api('/api/v1/jobs'),api('/api/v1/items')]);$('who').textContent='Authenticated: '+s.actor;$('status').textContent=`${s.items} items · ${s.notes} knowledge points\nJobs: ${JSON.stringify(s.jobs)}\nDrive mirror configured: ${s.mirror_enabled?'YES':'NO'}`;replaceRows('jobs',j.jobs,(tr,x)=>{[x.name,x.project,x.id.slice(0,10),x.status,x.mirror||x.error||'—'].forEach(t=>tr.append(td(t)))});replaceRows('items',i.items,(tr,x)=>{[x.name,x.project,x.actor,x.sha256.slice(0,14)+'…'].forEach(t=>tr.append(td(t)));let c=document.createElement('td'),b=document.createElement('button');b.textContent='Download';b.onclick=()=>download(x.id,x.name);c.append(b);tr.append(c)});msg('Connected.')}catch(e){msg('Connection error: '+e.message)}}
async function download(id,name){try{const r=await fetch('/api/v1/items/'+encodeURIComponent(id)+'/download',{headers:{Authorization:'Bearer '+token}});if(!r.ok)throw Error('Download failed: '+r.status);const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),15000)}catch(e){msg(e.message)}}
async function search(){try{let v=await api('/api/v1/search?q='+encodeURIComponent($('query').value));$('results').textContent='';for(let i of v.items){let p=document.createElement('p');p.textContent='FILE · '+i.project+' / '+i.name;$('results').append(p)}for(let n of v.notes){let p=document.createElement('p');p.textContent='NOTE · '+n.project+' / '+n.title+' ['+n.state+']';$('results').append(p)}if(!v.items.length&&!v.notes.length)$('results').textContent='No matches.'}catch(e){msg(e.message)}}
$('connect').onclick=()=>{token=$('token').value.trim();sessionStorage.setItem('funnelToken',token);refresh()};$('clear').onclick=()=>{token='';sessionStorage.removeItem('funnelToken');$('token').value='';$('who').textContent='';msg('Token cleared from tab')};$('refresh').onclick=refresh;$('search').onclick=search;$('query').onkeydown=e=>{if(e.key==='Enter')search()};
$('event-preview').onclick=async()=>{try{const out=await api('/api/v1/automation/preview',{method:'POST',body:JSON.stringify({event_type:$('event-type').value})});$('event-result').textContent=JSON.stringify(out,null,2)}catch(e){msg(e.message)}};
$('event-record').onclick=async()=>{try{const request={event_type:$('event-type').value,project:$('event-project').value,summary:$('event-summary').value,disclosure_version:'HERMES-DISCLOSURE-0.2',acknowledged:$('disclosure-ack').checked};const out=await api('/api/v1/automation/events',{method:'POST',body:JSON.stringify(request)});$('event-result').textContent='RECORDED ONLY: '+out.event_id+'\n'+JSON.stringify(out.preview,null,2);msg('Event recorded. NO AUTOMATION EXECUTED.')}catch(e){msg(e.message)}};
$('integration-list').onclick=async()=>{try{let out=await api('/api/v1/integrations');$('integration-summary').textContent=out.capabilities.map(x=>x.name+' ['+x.state+'] - '+x.restriction).join('\n\n');$('integration-summary').style.whiteSpace='pre-wrap'}catch(e){msg(e.message)}};
$('disclosure-open').onclick=async()=>{try{let out=await api('/api/v1/disclosure');$('disclosure-summary').textContent=Object.entries(out).map(([k,v])=>k.toUpperCase()+'\n'+v).join('\n\n');$('disclosure-summary').style.whiteSpace='pre-wrap'}catch(e){msg(e.message)}};
$('add-note').onclick=async()=>{try{const r=await api('/api/v1/notes',{method:'POST',body:JSON.stringify({title:$('note-title').value,body:$('note-body').value,project:$('note-project').value})});msg('Created proposed knowledge point: '+r.note_id);$('note-body').value='';refresh()}catch(e){msg(e.message)}};
for(const [label,route] of [['Hub status','/api/v1/status'],['Queue','/api/v1/jobs'],['Items','/api/v1/items'],['Knowledge','/api/v1/notes'],['Search example','/api/v1/search?q=IXO'],['Modules','/api/v1/integrations'],['Disclosure','/api/v1/disclosure'],['Event types','/api/v1/automation/types'],['Automation events','/api/v1/automation/events']]){let b=document.createElement('button');b.textContent=label;b.onclick=async()=>{try{$('api-preview').textContent=JSON.stringify(await api(route),null,2).slice(0,8000)}catch(e){msg(e.message)}};$('api-links').append(b)};
// v0.5 interaction layer: the original API widgets remain; privacy/review and
// deliberate browser intake are added without requiring an external JS build.
async function sendFile(){
 try{
  if(!token)throw Error('Connect with your member token first');
  const file=$('file-select').files[0];if(!file)throw Error('Select a file first');
  if(file.size>32*1024*1024)throw Error('Browser limit is 32 MiB. Use the desktop Funnel for larger files.');
  if(!crypto.subtle)throw Error('Browser hashing requires localhost or HTTPS');
  $('file-upload').disabled=true;
  $('file-progress').textContent='Computing SHA-256 locally...';
  const hash=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
  const digest=Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
  const created=await api('/api/v1/uploads',{method:'POST',body:JSON.stringify({name:file.name,size:file.size,sha256:digest,project:$('file-project').value})});
  let offset=0;
  while(offset<file.size){
   const end=Math.min(offset+created.max_chunk,file.size);
   const resp=await fetch('/api/v1/uploads/'+created.upload_id+'/chunk?offset='+offset,{method:'PATCH',headers:{Authorization:'Bearer '+token},body:file.slice(offset,end)});
   const detail=await resp.json();if(!resp.ok)throw Error(detail.error||('Chunk failed '+resp.status));
   offset=detail.offset;
   $('file-progress').textContent='Uploading: '+Math.round(offset/file.size*100)+'%';
  }
  const complete=await api('/api/v1/uploads/'+created.upload_id+'/complete',{method:'POST',body:'{}'});
  $('file-progress').textContent='PRIVATE upload verified. Item '+complete.item_id+' · '+complete.purpose+' ('+complete.route_state+')';
  msg('File received, queued and hashed. Choose Share explicitly if you want others to see it.');
  await refreshV05();
 }catch(e){$('file-progress').textContent='Not completed: '+e.message;msg(e.message)}
 finally{$('file-upload').disabled=false}
}
async function shareFile(x,desired){
 if(!confirm(desired==='team'?'Share '+x.name+' with all four members?':'Make '+x.name+' private again?'))return;
 try{
  const res=await api('/api/v1/items/'+x.id+'/share',{method:'POST',body:JSON.stringify({visibility:desired,acknowledged:true})});
  msg('Item '+res.item_id+' is now '+res.visibility);await refreshV05();
 }catch(e){msg(e.message)}
}
async function mirrorFile(x){
 if(!confirm('Authorize optional EXTERNAL storage mirroring for '+x.name+'? Remote copies cannot be automatically recalled.'))return;
 try{await api('/api/v1/items/'+x.id+'/authorize-mirror',{method:'POST',body:JSON.stringify({acknowledged:true})});msg('Mirror authorized. Worker runs only if a remote is configured.');await refreshV05()}catch(e){msg(e.message)}
}
function action(label,callback){const b=document.createElement('button');b.textContent=label;b.onclick=callback;return b}
function renderNotes(notes,actor,role){
 const list=$('note-list');list.textContent='';
 if(!notes.length){list.textContent='No visible knowledge notes.';return}
 for(const n of notes){
  const row=document.createElement('p');row.className='shell';
  const description=document.createElement('div');description.textContent=n.title+' / '+n.project+' / '+n.author+' / '+n.state+' / '+n.visibility;
  row.append(description);
  if(n.author===actor&&['proposed','rejected'].includes(n.state))row.append(action('Submit for review',async()=>{
   if(!confirm('Authorize this note for admin review and possible team publication?'))return;
   try{await api('/api/v1/notes/'+n.id+'/submit',{method:'POST',body:JSON.stringify({acknowledged:true})});await refreshV05()}catch(e){msg(e.message)}
  }));
  if(n.author===actor&&['submitted','approved'].includes(n.state))row.append(action('Withdraw',async()=>{
   if(!confirm('Withdraw note from team access? Previously exported copies cannot be recalled.'))return;
   try{await api('/api/v1/notes/'+n.id+'/withdraw',{method:'POST',body:'{}'});await refreshV05()}catch(e){msg(e.message)}
  }));
  if(role==='admin'&&n.state==='submitted')for(const choice of ['approve','reject'])row.append(action(choice,async()=>{
   try{await api('/api/v1/notes/'+n.id+'/review',{method:'POST',body:JSON.stringify({decision:choice})});await refreshV05()}catch(e){msg(e.message)}
  }));
  list.append(row);
 }
}
async function refreshV05(){
 if(!token){msg('Enter an access token.');return}
 try{
  const [s,j,i,n]=await Promise.all([api('/api/v1/status'),api('/api/v1/jobs'),api('/api/v1/items'),api('/api/v1/notes')]);
  $('who').textContent='Authenticated: '+s.actor+' ['+s.role+']';
  $('status').textContent=s.items+' visible items · '+s.notes+' visible notes\nJobs: '+JSON.stringify(s.jobs)+'\nRemote mirror configured: '+(s.mirror_enabled?'YES (per-file authorization still required)':'NO');
  replaceRows('jobs',j.jobs,(tr,x)=>{[x.name,x.project,x.id.slice(0,10),x.status,x.mirror||x.error||'—'].forEach(t=>tr.append(td(t)))});
  replaceRows('items',i.items,(tr,x)=>{
   [x.name,x.project,x.actor,x.visibility].forEach(t=>tr.append(td(t)));
   const c=document.createElement('td');c.append(action('Download',()=>download(x.id,x.name)));
   if(x.actor===s.actor){
    c.append(action(x.visibility==='private'?'Share':'Unshare',()=>shareFile(x,x.visibility==='private'?'team':'private')));
    if(x.visibility==='team')c.append(action('Mirror opt-in',()=>mirrorFile(x)));
   }
   tr.append(c);
  });
  renderNotes(n.notes,s.actor,s.role);msg('Connected — private content is visible only to its owner or operator.');
 }catch(e){msg('Connection error: '+e.message)}
}
refresh=refreshV05;
$('refresh').onclick=refreshV05;
$('file-upload').onclick=sendFile;
if(token)refreshV05();
</script></body></html>'''
