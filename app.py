"""OX Treasury: run `python app.py` and browse localhost:8765."""
import argparse
import json
import sqlite3
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import core
import imports

ROOT = Path(__file__).resolve().parent

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OX Treasury · v0.3</title>
<style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#e7edf9;background:#0b1120;font-size:14px}*{box-sizing:border-box}body{margin:0}header{background:#10192b;border-bottom:1px solid #2b3850;padding:22px max(20px,calc((100vw - 1240px)/2));display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:0 0 16px;color:#e0eafb}p{margin:4px 0 12px;color:#9fb0ca;line-height:1.5}main{max-width:1280px;margin:auto;padding:24px 20px 80px}.tag{color:#a8f0c5;background:#183a30;border:1px solid #2b6c54;border-radius:999px;font-size:12px;padding:5px 10px}.alert{background:#15273b;color:#bfd5f0;padding:13px 16px;border:1px solid #36516b;border-radius:12px;margin-bottom:20px}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:18px}.metric,.panel{background:#111b2d;border:1px solid #26364e;border-radius:13px;padding:18px}.metric small{color:#9eb1cd;text-transform:uppercase;letter-spacing:.07em;font-weight:700}.metric strong{display:block;font-size:27px;margin-top:8px}.muted{color:#91a1bd}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px}nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}.tab{background:#1b2940;border:1px solid #354865;color:#c9d7ed;padding:9px 14px;border-radius:10px;cursor:pointer}.tab.active{background:#3665a6;color:white}section.view{display:none}section.view.active{display:block}.flex{display:flex;gap:12px;flex-wrap:wrap;align-items:center}input,select{min-width:0;max-width:100%;background:#0a1221;color:#e9f1ff;border:1px solid #40516c;border-radius:8px;padding:10px;width:100%}label{font-weight:650;color:#c9d5ea;display:flex;flex-direction:column;gap:5px}form{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:14px}button{background:#4075bc;border:0;border-radius:8px;padding:11px 14px;color:white;font-weight:750;cursor:pointer}button:hover{filter:brightness(1.12)}button.secondary{background:#243b5a}button.danger{background:#82504b}button:disabled{opacity:.5;cursor:default}table{width:100%;border-collapse:collapse;text-align:left;font-size:13px}th,td{padding:10px 8px;border-bottom:1px solid #29374c;vertical-align:top}th{color:#9fb2d0;font-weight:700}tr:last-child td{border:0}.scroll{overflow:auto}code{color:#a6caff}small{font-size:12px}.pill{color:#bfe5f1;border:1px solid #446681;border-radius:6px;padding:2px 6px;white-space:nowrap}.pos{color:#94e2bc}.neg{color:#ffaba5}#msg{position:fixed;bottom:18px;right:18px;max-width:400px;padding:13px 18px;background:#244063;color:white;border:1px solid #6a91c7;border-radius:10px;display:none;z-index:20}.readonly{background:#182437;border:1px dashed #45617e;padding:12px;border-radius:10px}.one{grid-template-columns:1fr}@media(max-width:850px){.grid{grid-template-columns:1fr}header{padding:18px 20px}.metric strong{font-size:23px}}

.note{background:#1d2a3b;border-left:3px solid #a3bddf;padding:12px;margin:9px 0 18px}
#mappingGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:12px 0}
#mappingGrid label{font-size:12px}.actions{display:flex;gap:5px;flex-wrap:wrap}.actions button{padding:6px 8px;font-size:11px;white-space:nowrap}
#batchTable tbody tr,#importRows tbody tr{border-top:1px solid #2d3b52}
#filePreview,#importSummary{white-space:normal}.hidden{display:none!important}
</style></head><body>
<header><div><h1>OX TREASURY <small class="muted">/ v0.3</small></h1><p>Personal capital ledger · Canada / NZ / Australia · local-first</p></div><span class="tag">LOCAL CSV IMPORT · NO REAL MONEY MOVEMENT</span></header>
<main>
<div class="alert"><b>Evidence boundary:</b> Account labels are placeholders until you verify the providers. CSV imports are user-supplied, not independently verified. This program does not log in to providers, place bets, trade, move funds, or fetch live rates. Your database stays on this PC.</div>
<div class="metrics" id="metrics"></div>
<nav><button class="tab active" data-tab="overview">Overview</button><button class="tab" data-tab="accounts">Accounts</button><button class="tab" data-tab="transactions">Money movements</button><button class="tab" data-tab="buffers">Buffers</button><button class="tab" data-tab="bets">Wagers</button><button class="tab" data-tab="holdings">Holdings</button><button class="tab" data-tab="weights">Pool weights</button><button class="tab" data-tab="imports">CSV imports &amp; review</button></nav>
<section class="view active" id="overview">
 <div class="grid"><div class="panel"><h2>Capital flow</h2><p>Sportsbook balances &rarr; confirmed withdrawals &rarr; wallet / bank &rarr; five virtual buckets: shares, crypto, reserve, fun money and optional wager budget.</p><p>No cross-currency amount is combined without an observed FX conversion.</p><div class="readonly" id="flow"></div></div><div class="panel"><h2>Evidence rules</h2><p>Account verification is separate from transaction evidence. An account claimed to be legitimate is not automatically independently verified.</p><p>A deposit is not profit. The pool is capped by both wallet liquidity and cumulative settled betting P&amp;L in that same currency. Open wagers reduce available cash.</p></div></div>
 <div class="panel"><h2>Latest movements</h2><div id="latest" class="scroll"></div></div>
</section>
<section class="view" id="accounts"><div class="panel"><h2>Add account</h2><form id="accountForm"><label>Label<input name="name" required placeholder="My AU broker"></label><label>Type<select name="kind"><option value="wallet">Wallet</option><option value="bank">Bank</option><option value="sportsbook">Sportsbook</option><option value="crypto">Crypto exchange</option><option value="broker">Stock broker</option><option value="skins">Game item account</option></select></label><label>Country<select name="country"><option value="CA">Canada</option><option value="NZ">New Zealand</option><option value="AU">Australia</option><option value="US">US</option></select></label><label>Currency<select name="currency"><option>CAD</option><option>NZD</option><option>AUD</option><option>USD</option></select></label><label>Status<select name="status"><option value="active">Active</option><option value="planned">Planned</option><option value="archived">Archived</option></select></label><button type="submit">Add account</button></form></div><div class="panel"><h2>Account register</h2><div id="accountTable" class="scroll"></div></div></section>
<section class="view" id="transactions"><div class="panel"><h2>Record confirmed movement</h2><p>Record real activity after it happens. Cross-currency moves require both sent and received amounts.</p><form id="eventForm"><label>Movement<select name="kind"><option value="cash_in">External cash in</option><option value="cash_out">External cash out</option><option value="transfer">Same-currency transfer</option><option value="fx_transfer">FX conversion / transfer</option><option value="fee">Fee</option><option value="profit_sweep">Confirmed sportsbook profit sweep</option></select></label><label>Source<select name="source" class="accts optional"></select></label><label>Destination<select name="target" class="accts optional"></select></label><label>Sent amount<input name="amount" type="number" min="0.01" step="0.01" required></label><label>Received amount (FX only)<input name="target_amount" type="number" min="0.01" step="0.01" placeholder="Needed for FX"></label><label>Evidence<select name="evidence"><option value="user_recorded">User recorded</option><option value="statement_matched">Statement matched</option><option value="unverified">Unverified</option></select></label><label>External reference<input name="reference" placeholder="Optional unique ID"></label><label>Notes<input name="memo" placeholder="Withdrawal, deposit, etc"></label><button type="submit">Record movement</button></form></div><div class="panel"><h2>Ledger</h2><div id="eventTable" class="scroll"></div></div></section>
<section class="view" id="buffers">
<div class="grid"><div class="panel"><h2>Hold or release recorded funds</h2><p>Holding reserves cash within its current wallet or bank account. Releasing makes it unheld again. Neither action sends money to a betting site or exchange.</p>
<form id="bufferForm"><label>Wallet / bank<select name="account" class="accts cash"></select></label>
<label>Purpose<select name="purpose"><option value="betting">Optional gambling budget</option><option value="investing">General investment staging (legacy)</option><option value="shares">Shares / ETFs</option><option value="crypto">Crypto</option><option value="reserve">Protected savings</option><option value="fun">Fun money</option></select></label>
<label>Action<select name="action"><option value="hold">Hold</option><option value="release">Release</option></select></label>
<label>Amount<input type="number" name="amount" min="0.01" step="0.01" required></label>
<label>Note<input name="memo" placeholder="Why it is held / released"></label><button type="submit">Record buffer action</button></form>
<p>A separate confirmed money movement must still be recorded when funds actually leave the account. Buffer money is excluded from allocation proposals and outgoing transfers.</p></div>
<div class="panel"><h2>Current held amounts</h2><div id="bufferTable" class="scroll"></div></div></div>
<div class="panel"><h2>Buffer audit history</h2><div id="bufferHistory" class="scroll"></div></div></section>
<section class="view" id="bets"><div class="panel"><h2>Log a wager already placed</h2><p>This does not place a bet. Stake is removed from recorded sportsbook cash until settlement.</p><form id="betForm"><label>Sportsbook<select name="account" class="accts sports"></select></label><label>Category<select name="category"><option>Basketball</option><option>Horse racing</option><option>Greyhound racing</option><option>Football</option><option>Casino</option><option>Other</option></select></label><label>Stake<input type="number" name="stake" min="0.01" step="0.01" required></label><label>Reference<input name="reference" placeholder="Optional bet ID"></label><label>Notes<input name="memo"></label><button type="submit">Log existing wager</button></form></div><div class="panel"><h2>Settle an existing wager</h2><form id="settleForm"><label>Open bet<select name="id" id="openBets"></select></label><label>Gross payout (0 for loss)<input type="number" name="payout" min="0" step="0.01" required></label><button type="submit">Record settlement</button></form></div><div class="panel"><h2>Wager record</h2><div id="betTable" class="scroll"></div></div></section>
<section class="view" id="holdings"><div class="panel"><h2>Record asset snapshot</h2><p>Market values are manually entered snapshots, not verified quotes. Brokerage cash is tracked separately; avoid counting the same capital twice.</p><form id="positionForm"><label>Account<select name="account" class="accts invest"></select></label><label>Asset symbol<input name="symbol" required placeholder="BTC / VOO / CS2 item"></label><label>Asset type<select name="asset_type"><option>crypto</option><option>stock</option><option>ETF</option><option>game item</option><option>other</option></select></label><label>Quantity<input name="quantity" type="number" min="0" step="any" required></label><label>Observed unit price<input name="unit_price" type="number" min="0" step="any" required></label><label>Price currency<select name="quote_currency"><option>CAD</option><option>NZD</option><option>AUD</option><option>USD</option></select></label><button type="submit">Save snapshot</button></form></div><div class="panel"><h2>Current snapshots</h2><div id="positionTable" class="scroll"></div></div></section>
<section class="view" id="weights"><div class="grid"><div class="panel"><h2>Funding allocation proposal</h2><div class="readonly" id="pool"></div><p>Informational only. No transfer, reinvestment or leverage is executed. The proposal must be re-reviewed when data is incomplete or funds are not withdrawable.</p></div><div class="panel"><h2>Edit rules</h2><form id="settingForm"><label>Funding wallet / bank<select name="pool_source" class="accts cash"></select></label><label>Protected cash floor<input name="cash_floor" type="number" min="0" step="0.01" required></label><label>Shares / ETFs %<input name="weight_stocks" type="number" min="0" max="100" required></label><label>Crypto %<input name="weight_crypto" type="number" min="0" max="100" required></label><label>Reserve %<input name="weight_reserve" type="number" min="0" max="100" required></label><label>Fun money %<input name="weight_fun" type="number" min="0" max="100" required></label><label>Auto-wager brokerage budget %<input name="weight_wager" type="number" min="0" max="100" required></label><button type="submit">Update weighting rule</button></form><p>Weights must equal 100%. Share-focused default: 50 / 15 / 20 / 10 / 5. A wager allocation is only held in a buffer; the app never places bets. Release holdings deliberately after checking that costs, obligations, and your Australia fund remain protected.</p></div></div><div class="panel"><h2>Play ceiling and eligible profit sweep</h2>
<p>This is a local monitoring threshold, not a licensed sportsbook's enforceable loss/deposit limit. Only settled net gains above your ceiling can qualify for a recorded profit sweep.</p>
<form id="playRuleForm"><label>Sportsbook<select name="account" class="accts sports"></select></label><label>Target play balance<input name="ceiling" type="number" min="0.01" step="0.01" required></label><label>Monitoring<select name="enabled"><option value="1">Enabled</option><option value="0">Suspended</option></select></label><button type="submit">Save play ceiling</button></form>
<div id="rulesTable" class="scroll"></div>
<p>To record a completed eligible withdrawal, select <b>Confirmed sportsbook profit sweep</b> on the Money movements tab. This program does not itself initiate withdrawals, investments or wagers.</p></div>
<div class="panel"><h2>Recorded allocation commitments</h2><div id="commits" class="scroll"></div></div></section>
<div class="flex"><button class="secondary" id="export">Export complete JSON ledger</button><span class="muted">Local database: <code>data/treasury.db</code> (demo uses data/demo.db)</span></div>

<section class="view" id="imports">
 <div class="panel">
  <h2>Phase 2: Import an account statement</h2>
  <p>Choose a <b>CSV file exported from your own account</b>. No account login or internet upload: the browser sends it only to this app on 127.0.0.1. It stages new rows for review before changing ledger cash or holdings.</p>
  <div class="note">Generic formats for bank/PayPal cash movements, sportsbook bet records, crypto/broker holdings. This is <b>not</b> a verified native PayPal, brokerage, gambling or exchange connector. Exports may contain internal transfers, refunds, trades, gross amounts, pending activity or repeated positions. Map <b>signed NET cash amount</b> for cash exports; do not count internal transfers as new income. Review each row before posting.</div>
  <form id="importForm">
    <label>Source account<select id="importAccount" name="account" class="accts" required></select></label>
    <label>Export category<select id="importProfile" name="profile"><option value="cash">Wallet / bank / exchange cash movements</option><option value="bets">Sportsbook placed / settled bets</option><option value="holdings">Stocks / crypto / skins holding snapshots</option></select></label>
    <label>CSV file (UTF-8, max 2 MB / 5,000 rows)<input id="importFile" type="file" accept=".csv,text/csv" required></label>
    <button type="submit">1. Preview file and detect columns</button>
  </form>
  <div id="previewBox" class="hidden">
    <h2>Map statement columns</h2>
    <div id="filePreview" class="readonly"></div>
    <div id="mappingGrid"></div>
    <div class="flex"><button id="stageImport">2. Stage rows (no ledger changes)</button><button class="secondary" id="cancelPreview">Cancel</button></div>
    <div id="sampleTable" class="scroll" style="margin-top:14px"></div>
  </div>
 </div>
 <div class="panel" style="margin-top:16px"><h2>Statement import batches and reconciliation</h2><p>Counts, reported cash flows and settled bet net P&amp;L are limited to each import batch. They do not prove a complete account history or create spendable profit.</p><div id="importSummary" class="readonly"></div><div id="batchTable" class="scroll"></div></div>
 <div class="panel" style="margin-top:16px"><h2>Review staged rows</h2><p>Only an explicit action records a movement, wager or holding snapshot. <b>Match by reference</b> links an exact pre-existing ledger record instead of double-posting it. For internal transfers, use the existing Money Movements page to record a single paired transfer, then match its reference here.</p><div id="importRows" class="scroll"></div></div>
 <div class="panel" style="margin-top:16px"><h2>Rejected rows and reference conflicts</h2><div id="importIssues" class="scroll"></div></div>
</section>
</main><div id="msg" role="status"></div>
<script>
const $=id=>document.getElementById(id);const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let data={};
function alertMsg(msg){const t=$('msg');t.textContent=msg;t.style.display='block';clearTimeout(t._timer);t._timer=setTimeout(()=>t.style.display='none',6500)}
function tbl(headers,rows){if(!rows.length)return '<p>No records yet.</p>';return '<table><thead><tr>'+headers.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}
function acct(id){return (data.accounts||[]).find(a=>a.id===id)?.name||id||'External'}
function currency(c,v){return (c||'')+' '+v}
function fillSelects(){document.querySelectorAll('select.accts').forEach(el=>{let old=el.value;let list=data.accounts.filter(a=>{
if(el.classList.contains('sports'))return a.kind==='sportsbook'&&a.status==='active';
if(el.classList.contains('invest'))return ['crypto','broker','skins'].includes(a.kind);
if(el.classList.contains('cash'))return ['wallet','bank'].includes(a.kind)&&a.status==='active';
return a.status==='active';});
el.innerHTML=(el.classList.contains('optional')?'<option value="">External / none</option>':'')+list.map(a=>`<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.currency)})</option>`).join('');if(list.some(a=>a.id===old))el.value=old;});}
function render(){fillSelects();const accounts=data.accounts,events=data.events,bets=data.bets,positions=data.positions,p=data.pool;
$('metrics').innerHTML=[['Active accounts',accounts.filter(a=>a.status==='active').length],['Settled betting P&L (CAD)',currency('CAD',data.pnl.CAD)],['Open stake (CAD)',currency('CAD',data.open_risk.CAD)],['Proposed pool ('+p.currency+')',currency(p.currency,p.proposed_max)]].map(([a,b])=>`<div class="metric"><small>${esc(a)}</small><strong>${esc(b)}</strong></div>`).join('');
$('flow').innerHTML=`<b>Funding source:</b> ${esc(acct(p.source))}<br><b>Recorded cash:</b> ${esc(currency(p.currency,p.balance))}<br><b>Held buffer:</b> ${esc(currency(p.currency,p.buffer_held))}<br><b>Unheld cash:</b> ${esc(currency(p.currency,p.available))}<br><b>Protected cash floor:</b> ${esc(currency(p.currency,p.protected_floor))}<br><b>Proposed maximum:</b> ${esc(currency(p.currency,p.proposed_max))}`;
let erows=events.map(e=>[e.at.slice(0,16).replace('T',' '),e.kind,acct(e.source),acct(e.target),currency(e.source_currency||e.target_currency,e.source?e.source_amount:e.target_amount),e.target&&e.source?currency(e.target_currency,e.target_amount):'',e.evidence,e.reference||'']);
$('latest').innerHTML=tbl(['UTC','Type','From','To','Sent / Amount','Received','Evidence','Reference'],erows.slice(0,8));$('eventTable').innerHTML=tbl(['UTC','Type','From','To','Sent / Amount','Received','Evidence','Reference'],erows);
$('accountTable').innerHTML=tbl(['Account','Type','Country','Currency','Recorded cash','Held buffer','Unheld cash','Status','Provider evidence'],accounts.map(a=>[a.name,a.kind,a.country,a.currency,a.balance,a.held,a.available,a.status,a.verified]));
$('bufferTable').innerHTML=tbl(['Wallet / bank','Purpose','Held'],(data.buffers||[]).map(x=>[acct(x.account),x.purpose,currency(accounts.find(a=>a.id===x.account)?.currency,x.held)]));
$('bufferHistory').innerHTML=tbl(['UTC','Account','Purpose','Action','Amount','Note'],(data.buffer_actions||[]).map(x=>[x.at.slice(0,16).replace('T',' '),acct(x.account),x.purpose,x.action,currency(accounts.find(a=>a.id===x.account)?.currency,x.amount),x.memo]));
$('betTable').innerHTML=tbl(['ID','Book','Category','Stake','Gross payout','Net P&L','Status','Evidence'],bets.map(b=>['#'+b.id,acct(b.account),b.category,currency(b.currency,b.stake),b.payout===null?'open':currency(b.currency,b.payout),b.pnl===null?'—':currency(b.currency,b.pnl),b.payout===null?'open':'settled',b.evidence]));
$('openBets').innerHTML=bets.filter(b=>b.payout===null).map(b=>`<option value="${b.id}">#${b.id} ${esc(acct(b.account))} ${esc(b.currency)} ${esc(b.stake)}</option>`).join('');
$('positionTable').innerHTML=tbl(['Account','Asset','Type','Qty','Unit quote','Market value','Observed UTC','Source'],positions.map(x=>[acct(x.account),x.symbol,x.asset_type,x.quantity,currency(x.quote_currency,x.unit_price),currency(x.quote_currency,x.market_value),x.observed_at.slice(0,16).replace('T',' '),x.source]));
$('pool').innerHTML=`<b>Proposed maximum:</b> ${esc(currency(p.currency,p.proposed_max))}<hr>${Object.entries(p.allocations).map(([k,v])=>`<p><b>${esc(k)}:</b> ${esc(currency(p.currency,v))}</p>`).join('')}<small class="muted">${esc(p.warning)}</small>`;
$('rulesTable').innerHTML=tbl(['Sportsbook','Ceiling','Balance','Settled net P&L','Already swept','Eligible sweep','Enabled'],(data.play_rules||[]).map(x=>[acct(x.account),x.ceiling,x.balance,x.settled_net_pnl,x.already_swept,x.suggested_sweep,x.enabled?'Yes':'No']));
$('commits').innerHTML=tbl(['UTC','Account','Total','Shares','Crypto','Reserve','Fun','Wager'],(data.allocation_commits||[]).map(x=>[x.at.slice(0,16).replace('T',' '),acct(x.account),x.amount,x.stocks,x.crypto,x.reserve,x.fun,x.wager]));
const s=$('settingForm');for(const key of ['cash_floor','weight_reserve','weight_stocks','weight_crypto','weight_fun','weight_wager','pool_source']){if(s.elements[key])s.elements[key].value=data.settings[key]}}
async function refresh(){let r=await fetch('/api/dashboard');if(!r.ok)throw new Error('Cannot read ledger');data=await r.json();render()}
function values(f){return Object.fromEntries(new FormData(f).entries())}
function hook(id,url,transform=x=>x){$(id).addEventListener('submit',async e=>{e.preventDefault();const f=e.currentTarget;const body=transform(values(f));try{let r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let obj=await r.json();if(!r.ok)throw new Error(obj.error||'Could not save');await refresh();alertMsg('Recorded successfully');if(id!=='settingForm')f.reset()}catch(err){alertMsg('Not saved: '+err.message)}})}
hook('accountForm','/api/account');hook('eventForm','/api/event',d=>{if(!d.target_amount)delete d.target_amount;return d});hook('betForm','/api/bet');hook('settleForm','/api/settle');hook('positionForm','/api/position');hook('bufferForm','/api/buffer');hook('settingForm','/api/settings');hook('playRuleForm','/api/play-rule');
document.querySelectorAll('.tab').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.tab,.view').forEach(x=>x.classList.remove('active'));button.classList.add('active');$(button.dataset.tab).classList.add('active')}));

// CSV input is local only. Export data remains in local SQLite after staging.
let importPreview=null, importCsvText='', importFileName='';
let importReport={batches:[],records:[],issues:[]};
async function apiPost(url,body){const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const o=await res.json();if(!res.ok)throw new Error(o.error||'Request failed');return o}
function rowActions(r){
 if(r.review_state==='applied'||r.review_state==='matched')return '<small>'+esc(r.review_state)+' #'+esc(r.ledger_id)+'</small>';
 const acts=[];
 if(r.review_state==='ignored'){acts.push(['restore','Restore']);return actionsHtml(acts,r.id)}
 if(r.profile==='cash'){
   if(r.data.amount_cents>0)acts.push(['cash_in','Post cash in']);
   if(r.data.amount_cents<0){acts.push(['cash_out','Post cash out']);acts.push(['fee','Post fee'])}
   if(r.data.reference)acts.push(['match','Match reference']);
 }else if(r.profile==='bets'){
   acts.push(['record_bet','Record bet']);if(r.data.reference)acts.push(['match','Match reference']);
 }else if(r.profile==='holdings')acts.push(['update_holding','Update holding']);
 acts.push(['ignore','Ignore']);return actionsHtml(acts,r.id)
}
function actionsHtml(a,id){return '<div class="actions">'+a.map(([act,label])=>'<button class="secondary" type="button" data-review="'+esc(act)+'" data-id="'+id+'">'+esc(label)+'</button>').join('')+'</div>'}
function renderImportReport(){
 const r=importReport; $('importSummary').textContent=r.notice||'No imported statements yet.';
 $('batchTable').innerHTML=tbl(['Batch','Imported (UTC)','Account','Format','File','Rows','New','Dupes','Rejected','Review','Reported totals (not verified)'],
 (r.batches||[]).map(b=>['#'+b.id,b.imported_at.slice(0,16),b.account_name,b.profile,b.filename,b.total_rows,b.new_rows,b.duplicate_rows,b.rejected_rows,
 'Staged '+b.summary.staged+' · Applied '+b.summary.applied+' · Matched '+b.summary.matched+' · Ignored '+b.summary.ignored,
 b.profile==='cash'?'In '+b.account_currency+' '+b.summary.in_cents+' | Out '+b.account_currency+' '+b.summary.out_cents:
 b.profile==='bets'?'Stakes '+b.account_currency+' '+b.summary.stakes_cents+' | Payout '+b.summary.payout_cents+' | net settled '+b.summary.settled_pnl_cents+' | open '+b.summary.open_bets:
 'Latest symbol snapshots: '+b.summary.holding_symbols+' | '+Object.entries(b.summary.holdings_by_currency).map(([k,v])=>k+' '+v).join(' | ')]));
 const records=(r.records||[]);
 if(!records.length){$('importRows').innerHTML='<p>Nothing imported yet.</p>'}else{
  $('importRows').innerHTML='<table><thead><tr><th>Import</th><th>Account</th><th>Reference / description</th><th>Amount / asset</th><th>Status</th><th>Review</th></tr></thead><tbody>'+records.map(x=>{
    const d=x.data, label=x.profile==='cash'?((d.amount_cents/100).toFixed(2)+' '+d.currency):x.profile==='bets'?('Stake '+(d.stake_cents/100).toFixed(2)+' / payout '+(d.payout_cents===null?'open':(d.payout_cents/100).toFixed(2))+' '+d.currency):(d.quantity+' '+d.symbol+' @ '+d.unit_price+' '+d.currency);
    return '<tr><td>#'+x.id+' · '+esc(x.profile)+'<br><small>Batch '+x.batch_id+'</small></td><td>'+esc(x.account_name)+'</td><td>'+esc(d.reference||d.symbol||d.description||'No ID')+'<br><small>'+esc(d.date||'Date unavailable')+'</small></td><td>'+esc(label)+'</td><td>'+esc(d.status||x.review_state)+'</td><td>'+rowActions(x)+'</td></tr>';
  }).join('')+'</tbody></table>';
 }
 $('importIssues').innerHTML=tbl(['Batch','CSV row','Type','Reason'],(r.issues||[]).map(i=>['#'+i.batch_id,i.csv_row,i.severity,i.message]));
}
async function refreshImports(){const r=await fetch('/api/import/report');if(!r.ok)throw new Error('Failed to retrieve CSV import report');importReport=await r.json();renderImportReport()}
$('importForm').addEventListener('submit',async e=>{
 e.preventDefault();try{
 const file=$('importFile').files[0];if(!file)throw new Error('Choose a CSV file');if(file.size>2*1024*1024)throw new Error('File exceeds 2 MB');
 importCsvText=await file.text();importFileName=file.name;
 importPreview=await apiPost('/api/import/preview',{csv_text:importCsvText,profile:$('importProfile').value});
 const p=importPreview;$('previewBox').classList.remove('hidden');$('filePreview').textContent=`${p.rows} data rows · ${p.headers.length} columns. ${p.warning}`;
 $('mappingGrid').innerHTML=p.fields.map(field=>'<label>'+esc(field)+(p.required.includes(field)?' *':'')+'<select data-map="'+esc(field)+'"><option value="">(not included)</option>'+p.headers.map(h=>'<option value="'+esc(h)+'"'+(p.mapping[field]===h?' selected':'')+'>'+esc(h)+'</option>').join('')+'</select></label>').join('');
 $('sampleTable').innerHTML=tbl(p.headers,p.sample.map(row=>p.headers.map(h=>row[h])));
 }catch(ex){alertMsg('Preview: '+ex.message)}
});
$('stageImport').addEventListener('click',async e=>{e.preventDefault();if(!importPreview)return;
 const mapping={};document.querySelectorAll('#mappingGrid select').forEach(el=>{if(el.value)mapping[el.dataset.map]=el.value});
 try{
 const response=await apiPost('/api/import/stage',{account:$('importAccount').value,profile:$('importProfile').value,filename:importFileName,csv_text:importCsvText,mapping});
 $('previewBox').classList.add('hidden');importCsvText='';importPreview=null;$('importFile').value='';
 await refreshImports();alertMsg(`Staged ${response.new_rows} new, ${response.duplicate_rows} duplicate, ${response.rejected_rows} rejected. Review below.`);
 }catch(ex){alertMsg('Not imported: '+ex.message)}
});
$('cancelPreview').addEventListener('click',e=>{e.preventDefault();$('previewBox').classList.add('hidden');importCsvText='';importPreview=null});
$('importRows').addEventListener('click',async e=>{
 const b=e.target.closest('button[data-review]');if(!b)return;
 const id=Number(b.dataset.id),action=b.dataset.review;
 const r=importReport.records.find(v=>v.id===id);if(!r)return;
 const risky=['cash_in','cash_out','fee','record_bet','update_holding'].includes(action);
 if(risky && !window.confirm(`Confirm ${action} for imported row #${id}? This changes your local ledger, NOT real accounts. Verify original statement and avoid double-counting transfers/trades.`))return;
 try{b.disabled=true;const result=await apiPost('/api/import/review',{id,action});await refresh();await refreshImports();alertMsg('Row '+id+' marked '+result.state)}catch(ex){b.disabled=false;alertMsg('Review rejected: '+ex.message)}
});

$('export').addEventListener('click',()=>location.href='/api/export');refresh().then(()=>refreshImports()).catch(err=>alertMsg(err.message));
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    database = None
    def log_message(self, fmt, *args):
        if not self.path.startswith('/api/dashboard'):
            super().log_message(fmt,*args)

    def send(self, code, content, mime='application/json', extra=None):
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', mime+'; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        for k,v in (extra or {}).items(): self.send_header(k,v)
        self.send_header('Content-Length',str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def allowed_host(self):
        host = self.headers.get('Host','')
        return host in {'localhost:8765','127.0.0.1:8765'}

    def do_GET(self):
        if not self.allowed_host(): return self.send(403,'{"error":"Invalid host"}')
        path=urlsplit(self.path).path
        if path=='/': return self.send(200,PAGE,'text/html')
        cx=core.db_open(self.database)
        try:
            if path=='/api/import/report':
                return self.send(200,json.dumps(imports.report(cx)))
            if path=='/api/dashboard':
                return self.send(200,json.dumps(core.dashboard(cx)))
            if path=='/api/export':
                dump={
                    'accounts':core.rows(cx,'SELECT * FROM accounts'),
                    'events':core.rows(cx,'SELECT * FROM events'),
                    'bets':core.rows(cx,'SELECT * FROM bets'),
                    'positions':core.rows(cx,'SELECT * FROM positions'),
                    'buffer_actions':core.rows(cx,'SELECT * FROM buffer_actions'),
                    'allocation_commits':core.rows(cx,'SELECT * FROM allocation_commits'),
                    'play_rules':core.rows(cx,'SELECT * FROM play_rules'),
                    'settings':core.rows(cx,'SELECT * FROM settings'),
                    'import_batches':core.rows(cx,'SELECT * FROM import_batches'),
                    'import_records':core.rows(cx,'SELECT * FROM import_records'),
                    'import_issues':core.rows(cx,'SELECT * FROM import_issues'),
                    'exported_utc':core.now(), 'schema':'OX_TREASURY_V0_3'
                }
                return self.send(200,json.dumps(dump,indent=2),'application/json',
                         {'Content-Disposition':'attachment; filename="ox_treasury_export.json"'})
            return self.send(404,'{"error":"Not found"}')
        finally:cx.close()

    def do_POST(self):
        if not self.allowed_host(): return self.send(403,'{"error":"Invalid host"}')
        # Block cross-origin requests to the locally bound service.
        origin=self.headers.get('Origin','')
        if origin and origin not in {'http://127.0.0.1:8765','http://localhost:8765'}:
            return self.send(403,'{"error":"Invalid origin"}')
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            return self.send(415,'{"error":"JSON required"}')
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>2*1024*1024+100000: return self.send(413,'{"error":"Invalid request size"}')
            payload=json.loads(self.rfile.read(n).decode('utf8'))
            if not isinstance(payload,dict):raise ValueError('Request must be object')
            cx=core.db_open(self.database)
            try:
                path=urlsplit(self.path).path
                if path=='/api/import/preview': result=imports.preview(payload.get('csv_text'),payload.get('profile'))
                elif path=='/api/import/stage': result=imports.stage(cx,payload)
                elif path=='/api/import/review': result=imports.review(cx,int(payload['id']),payload['action'])
                elif path=='/api/account': result={'id':core.add_account(cx,payload)}
                elif path=='/api/event':core.add_event(cx,payload);result={'ok':True}
                elif path=='/api/bet':result={'id':core.add_bet(cx,payload)}
                elif path=='/api/settle':core.settle_bet(cx,int(payload['id']),payload['payout']);result={'ok':True}
                elif path=='/api/position':core.add_position(cx,payload);result={'ok':True}
                elif path=='/api/buffer':core.buffer_action(cx,payload);result={'ok':True}
                elif path=='/api/settings':core.update_settings(cx,payload);result={'ok':True}
                elif path=='/api/play-rule':core.set_play_rule(cx,payload);result={'ok':True}
                else:return self.send(404,'{"error":"Not found"}')
                return self.send(200,json.dumps(result))
            finally:cx.close()
        except (ValueError,KeyError,sqlite3.IntegrityError,TypeError) as e:
            return self.send(400,json.dumps({'error':str(e)}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--demo',action='store_true',help='Use a separate database with fictional transactions')
    p.add_argument('--no-browser',action='store_true')
    args=p.parse_args()
    file=ROOT/'data'/('demo.db' if args.demo else 'treasury.db')
    cx=core.db_open(file)
    imports.ensure_schema(cx)
    if args.demo:core.seed_demo(cx)
    cx.close()
    Handler.database=file
    print(f'OX Treasury running at http://127.0.0.1:8765  | DB: {file}',flush=True)
    if not args.no_browser: webbrowser.open('http://127.0.0.1:8765')
    try:ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
    except KeyboardInterrupt:print('\nStopped.')
