"""Small self-contained, token-reusing UI for the adaptive purpose pilot."""

PURPOSE_PANEL = r'''
<section class="shell" id="purpose-router">
 <h2>HERMES · ADAPTIVE PURPOSE FUNNEL <span class="pill">v1 contract</span></h2>
 <p class="hint">Metadata-based proposals only. No bot-created channels, remote execution, or secret document analysis. Unknown files enter triage.</p>
 <div class="grid">
  <div><label>Filename or item description</label><input id="purpose-name" style="width:100%" value="SyntraBridge.java" maxlength="180">
   <label>Context (optional)</label><textarea id="purpose-context" maxlength="500">Java bridge between independent development systems</textarea>
   <button id="purpose-preview">Preview purpose</button></div>
  <div><label>New purpose request</label><input id="purpose-slug" placeholder="simulation" maxlength="40" style="width:100%">
   <label>Purpose name</label><input id="purpose-title" placeholder="3D Simulation" maxlength="120" style="width:100%">
   <label>Why do we need it?</label><input id="purpose-reason" placeholder="Independent scene/asset experiments" maxlength="500" style="width:100%">
   <label>Keywords (commas, optional)</label><input id="purpose-keywords" placeholder="mesh,scene,rig" maxlength="200" style="width:100%">
   <button id="purpose-request">Request new purpose</button></div>
 </div>
 <div class="row" style="margin-top:14px"><button id="purpose-list">List open reviews</button><button id="purpose-taxonomy">View categories</button></div>
 <div class="grid" style="margin-top:14px"><div><h2>APPROVE A FILE PURPOSE · ADMIN</h2>
  <label>Item ID from the file registry</label><input id="purpose-item-id" placeholder="item ID" maxlength="50" style="width:100%">
  <label>Approved purpose slug</label><input id="purpose-approved-slug" value="development" maxlength="40" style="width:100%">
  <label>Optional term to teach the router</label><input id="purpose-learn-term" placeholder="adapter" maxlength="80" style="width:100%">
  <button id="purpose-correct">Apply reviewed purpose</button></div>
 <div><h2>REVIEW QUEUE</h2><p class="hint">Requests appear below with approve/reject buttons when connected as hub-admin.</p><div id="purpose-reviews" class="hint"></div></div></div>
 <pre id="purpose-output" style="color:#b6cde0;white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto" aria-live="polite"></pre>
 <p class="hint">Human correction: admins use <code>POST /api/v1/items/{id}/purpose</code> to approve a label and optionally teach a new term. A new-purpose approval adds a registry entry—not a Discord category.</p>
</section>
<script>
(function(){
const $=id=>document.getElementById(id);
const output=x=>{$('purpose-output').textContent=typeof x==='string'?x:JSON.stringify(x,null,2)};
async function api(path,method,body){
 const token=sessionStorage.getItem('funnelToken')||'';
 if(!token)throw Error('Connect to the hub first with your member token');
 const res=await fetch(path,{method,headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
 const data=await res.json();
 if(!res.ok)throw Error(data.error||('HTTP '+res.status));
 return data;
}
const wrap=fn=>async()=>{try{output(await fn())}catch(e){output(e.message)}};
$('purpose-preview').onclick=wrap(()=>api('/api/v1/route/preview','POST',{
 name:$('purpose-name').value,description:$('purpose-context').value,project:'shared'}));
$('purpose-request').onclick=wrap(()=>api('/api/v1/purpose-requests','POST',{
 kind:'new_purpose',proposed_slug:$('purpose-slug').value,title:$('purpose-title').value,
 reason:$('purpose-reason').value,keywords:$('purpose-keywords').value.split(',').map(s=>s.trim()).filter(Boolean)}));
$('purpose-correct').onclick=wrap(()=>api('/api/v1/items/'+encodeURIComponent($('purpose-item-id').value)+'/purpose','POST',{
 purpose:$('purpose-approved-slug').value,learn_term:$('purpose-learn-term').value}));
async function reviews(){
 const list=$('purpose-reviews');list.textContent='';
 const [data,status]=await Promise.all([api('/api/v1/purpose-requests','GET'),api('/api/v1/status','GET')]);
 const open=data.requests.filter(x=>x.status==='open');
 if(!open.length){list.textContent='No open requests visible to this token.';output(data);return}
 for(const x of open){
  const block=document.createElement('p');block.className='shell';
  const title=document.createElement('div');title.textContent=x.kind+' · '+x.title+' / '+x.proposed_slug+' / '+x.actor;
  block.append(title);
  const detail=document.createElement('small');detail.textContent=x.reason;block.append(detail);
  if(status.role==='admin')for(const decision of ['approve','reject']){
   const button=document.createElement('button');button.textContent=decision;
   button.onclick=async()=>{try{
    if(!confirm(decision+' purpose request '+x.title+'?'))return;
    output(await api('/api/v1/purpose-requests/'+x.id+'/resolve','POST',{decision}));
    await reviews();
   }catch(e){output(e.message)}};
   block.append(button);
  }
  list.append(block);
 }
 output({open_requests:open.length,role:status.role});
}
$('purpose-list').onclick=wrap(reviews);
$('purpose-taxonomy').onclick=wrap(()=>api('/api/v1/purposes','GET'));
}());
</script>
'''


def extend_ui(html):
    return html.replace('</body>', PURPOSE_PANEL + '</body>')
