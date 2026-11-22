'use strict';
// Thin client. DSOE Python store is the sole authority for all transitions.
let dsoeState = null;
function switchDSOE() {
  $('panel-ixo').hidden = true;
  $('panel-aixo').hidden = true;
  $('panel-dsoe').hidden = false;
  $('panel-experience').hidden = true;
  $('tab-experience').className = '';
  $('tab-ixo').className = '';
  $('tab-aixo').className = '';
  $('tab-dsoe').className = 'active';
  refreshDSOE();
}
async function dsoeAction(payload) {
  try {
    const response = await fetch('/api/dsoe/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-IXO-Token': token},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    output(data.error || JSON.stringify(data, null, 2));
    await refreshDSOE();
    await refresh();
    return data;
  } catch (error) {
    output('DSOE ERROR: ' + error.message);
  }
}
function dsoeButton(text, handler) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = text;
  button.onclick = handler;
  return button;
}
async function dsoeDetail(taskID) {
  try {
    const response = await fetch('/api/dsoe/task?id=' + encodeURIComponent(taskID), {cache:'no-store'});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || 'Could not load task');
    const tasks = $('dsoe-tasks');
    const previous = tasks.querySelector('.dsoe-detail');
    if (previous) previous.remove();
    const wrapper = document.createElement('div');
    wrapper.className = 'item dsoe-detail';
    wrapper.appendChild(el('strong', 'TASK ' + taskID));
    result.jobs.forEach(job => {
      const child = el('div', `${job.stage} / ${job.provider} / ${job.state} / ${job.id}`);
      child.className = 'item';
      if (job.state === 'DISPATCHED') {
        child.appendChild(dsoeButton('COPY JOB ID', () => navigator.clipboard?.writeText(job.id)));
        child.appendChild(dsoeButton('COPY HANDOFF', async () => {
          const h = await fetch('/api/dsoe/handoff?job=' + encodeURIComponent(job.id), {headers:{'X-IXO-Token':token}});
          if (h.ok) {const payload = await h.json(); navigator.clipboard?.writeText(JSON.stringify(payload, null, 2));}
        }));
      }
      if (job.state === 'REPORTED') {
        child.appendChild(dsoeButton('ACCEPT (REVIEW)', () => reviewDSOE(job.id, 'accept')));
        child.appendChild(dsoeButton('REJECT', () => reviewDSOE(job.id, 'reject')));
      }
      if (job.state === 'ACCEPTED') {
        child.appendChild(dsoeButton('RECORD IN AIXO', () => dsoeAction({action:'evidence', job_id:job.id})));
      }
      wrapper.appendChild(child);
    });
    tasks.prepend(wrapper);
  } catch (error) {output('DSOE ERROR: ' + error.message);}
}
async function reviewDSOE(jobID, decision) {
  const reason = prompt(`Why do you ${decision} this external result?`);
  if (!reason?.trim()) return;
  await dsoeAction({action:'review', job_id: jobID, decision, reason});
}
async function refreshDSOE() {
  try {
    const response = await fetch('/api/dsoe', {cache:'no-store'});
    if (!response.ok) throw Error('DSOE offline');
    dsoeState = await response.json();
    const registry = $('dsoe-providers');
    registry.replaceChildren();
    dsoeState.providers.forEach(p => {
      const card = document.createElement('div');
      card.className = 'item';
      card.appendChild(el('strong', p.key || p.name || 'PANTHEON'));
      card.appendChild(el('div', (p.stage || '') + ' / external runtime not connected'));
      registry.appendChild(card);
    });
    const tasks = $('dsoe-tasks');
    tasks.replaceChildren();
    if (!dsoeState.status.tasks.length) tasks.appendChild(el('div', 'No tasks. Create one above.'));
    dsoeState.status.tasks.forEach(t => {
      const card = document.createElement('div');
      card.className = 'item';
      card.appendChild(el('strong', t.state + ' / ' + t.workspace));
      card.appendChild(el('div', t.objective));
      card.appendChild(el('small', 'ID ' + t.id));
      card.appendChild(dsoeButton('DETAIL', () => dsoeDetail(t.id)));
      if (t.state === 'DRAFT') card.appendChild(dsoeButton('APPROVE', () => dsoeAction({action:'approve', task_id:t.id})));
      if (t.state === 'APPROVED') card.appendChild(dsoeButton('DISPATCH NEXT', () => dsoeAction({action:'dispatch', task_id:t.id})));
      tasks.appendChild(card);
    });
    lines('dsoe-events', dsoeState.status.events, e => `${e.seq} ${e.action} / ${e.task_id}`);
  } catch (error) {output('DSOE ERROR: ' + error.message);}
}
$('dsoe-plan').onsubmit = async event => {
  event.preventDefault();
  const objective = $('dsoe-objective').value.trim();
  if (objective) await dsoeAction({action:'plan', objective});
};
$('dsoe-report').onsubmit = async event => {
  event.preventDefault();
  let result;
  try { result = JSON.parse($('dsoe-json').value); }
  catch (error) { output('DSOE ERROR: Invalid JSON'); return; }
  if (!result || Array.isArray(result) || typeof result !== 'object') {
    output('DSOE ERROR: Result must be a JSON object'); return;
  }
  await dsoeAction({action:'report', job_id:$('dsoe-jobid').value.trim(), result});
};
