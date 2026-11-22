"""Local read-only card observation dashboard; never starts tracker or changes ledger."""
import argparse
import html
import hashlib
import json
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from tracker import ROOT, Tracker
from sold_research import read_sales


def _time(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if ts is not None else 'unknown'


def _cards(observation):
    if not isinstance(observation, dict): return []
    cards = observation.get('cards', [])
    return cards[:200] if isinstance(cards, list) else []


def series_id(key):
    """Stable opaque selector for an exact six-part card/source/currency identity."""
    return hashlib.sha256(json.dumps(key, ensure_ascii=False, separators=(',',':')).encode('utf-8')).hexdigest()[:24]


def render_trends(snapshots, selected=None, search=""):
    """Read-only, source-isolated SVG history. Gaps are not connected."""
    groups = defaultdict(list)
    for snap in snapshots[-500:]:
        try:
            at = float(snap['collected_at'])
            if not 0 <= at < 1e12: continue
        except (KeyError, TypeError, ValueError, OverflowError): continue
        observation = snap.get('observation') or {}
        for card in _cards(observation):
            if not isinstance(card, dict): continue
            identity = tuple(str(card.get(k,'')).strip() for k in ('game','name','set_code','collector_number','currency'))
            source = str(card.get('source',observation.get('source',''))).strip()
            if not all(identity) or not source: continue
            try:
                price = Decimal(str(card.get('unit_price',card.get('price',''))))
                if not price.is_finite() or price < 0: continue
            except (InvalidOperation, TypeError, ValueError): continue
            groups[identity+(source,)].append((at,price))
    def e(x): return html.escape(str(x),quote=True)
    # Search across all observed identities before limiting HTML output.
    # Keep the historical unfiltered 40-series display for compatibility.
    search = search.strip().casefold()
    matching = [key for key in sorted(groups) if search in ' / '.join(key).casefold()]
    keys = matching[:100 if search else 40]
    options = ['<option value="all"'+(' selected' if selected is None else '')+'>All series</option>']
    for i, key in enumerate(keys):
        options.append('<option value="'+series_id(key)+'"'+(' selected' if selected == series_id(key) or selected == i else '')+'>'+html.escape(' / '.join(key),quote=True)+'</option>')
    selector = '<form method="get" action="/"><label for="search">Find card, set, currency or provider</label> <input id="search" name="q" maxlength="100" value="'+e(search)+'" autocomplete="off"> <label for="series">Price series</label> <select id="series" name="series">'+''.join(options)+'</select> <button type="submit">Show</button></form><p class="muted">'+str(len(matching))+' matching series; showing '+str(len(keys))+'. Search to narrow results.</p>'
    blocks=[]
    for index, key in enumerate(keys):
        if selected is not None and selected not in (index, series_id(key)): continue
        readings = groups[key]
        readings.sort(key=lambda x:x[0]); readings=readings[-150:]
        if len(readings)<2: continue
        first,last=readings[0][0],readings[-1][0]
        lo,hi=min(v for _,v in readings),max(v for _,v in readings)
        spread=hi-lo
        def point(at,v):
            x=20+460*(at-first)/(last-first) if last>first else 250
            y=110-90*(float((v-lo)/spread) if spread else .5)
            return f'{x:.1f},{y:.1f}'
        # Missing observations are not interpolated across intervals > 30 min.
        segments=[]; current=[]; gaps=0
        for i,(at,v) in enumerate(readings):
            if i and at-readings[i-1][0]>1800:
                if current: segments.append(current)
                current=[];gaps+=1
            current.append((at,v))
        if current:segments.append(current)
        lines=''.join('<polyline fill="none" stroke="#8fc4ff" stroke-width="2" points="'+e(' '.join(point(t,v) for t,v in segment))+'"/>' for segment in segments if len(segment)>1)
        dots=''.join('<circle cx="'+point(t,v).split(',')[0]+'" cy="'+point(t,v).split(',')[1]+'" r="2.5" fill="#d4e9ff"/>' for segment in segments for t,v in segment)
        label=' / '.join(key)
        blocks.append('<section><h3>'+e(label)+'</h3><p class="muted">'+str(len(readings))+' local observations; '+str(gaps)+' gaps over 30 minutes. Range '+e(lo)+' to '+e(hi)+' '+e(key[4])+'.</p><svg viewBox="0 0 500 130" role="img" aria-label="'+e(label+' indicative price history, '+str(gaps)+' missing-data gaps')+'" style="max-width:100%;height:auto;background:#17212c;border-radius:8px">'+'<title>'+e(label+' indicative price history')+'</title><desc>'+e('UTC collection time '+_time(first)+' to '+_time(last)+'. Indicative price '+str(lo)+' to '+str(hi)+' '+key[4]+'. Gaps not connected.')+'</desc>'+lines+dots+'<text x="20" y="125" fill="#c8d8ed" font-size="9">'+e(_time(first))+'</text><text x="480" y="125" text-anchor="end" fill="#c8d8ed" font-size="9">'+e(_time(last))+'</text><text x="20" y="14" fill="#c8d8ed" font-size="10">'+e(hi)+' '+e(key[4])+'</text><text x="20" y="108" fill="#c8d8ed" font-size="10">'+e(lo)+'</text></svg><p class="muted">Collected '+e(_time(first))+' to '+e(_time(last))+'. Upstream quote freshness unknown unless supplied by provider.</p></section>')
    return selector + (''.join(blocks) if blocks else '<p class="muted">No comparable history yet. Two or more observations of the same card, currency and source are needed.</p>')


def render(status, snapshots=None, selected=None, search="", sales=None):
    observation = status.get('observation') or {}
    cards = _cards(observation)
    def e(x): return html.escape(str(x if x is not None else 'unknown'), quote=True)
    rows = []
    for card in cards:
        if not isinstance(card, dict): continue
        # The upstream quote timestamp is not asserted to be known.
        price = card.get('unit_price', card.get('price', 'unknown'))
        cells = [card.get('game','unknown'), card.get('name','unknown'), card.get('set_code','unknown'),
                 card.get('collector_number','unknown'), price, card.get('currency','unknown'),
                 card.get('source', observation.get('source','unknown')), card.get('source_quoted_at','unknown')]
        rows.append('<tr>'+''.join('<td>'+e(v)+'</td>' for v in cells)+'</tr>')
    # User-imported historical sale claims are displayed distinctly from provider price estimates.
    sale_rows = []
    for sale in (sales or []):
        cells = [sale.get(k,'unknown') for k in ('game','name','set_code','collector_number','sold_at',
                 'price','currency','condition','marketplace','sale_id','verification_status','imported_at','source_url')]
        sale_rows.append('<tr>'+''.join('<td>'+e(v)+'</td>' for v in cells)+'</tr>')
    state = 'STALE' if status.get('stale') else 'CURRENT (local observation only)' 
    age = status.get('observation_age_seconds')
    age_text = 'unknown' if age is None else f'{int(age)} seconds'
    return ('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OX Treasury | Card Watch</title><meta http-equiv="refresh" content="60"><style>body{font:15px system-ui;background:#10151b;color:#e6edf5;margin:2rem}h1{font-size:1.5rem}small,.muted{color:#aebaca}section{border:1px solid #435267;border-radius:12px;padding:1rem;margin:1rem 0}table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}td,th{padding:.7rem;border-bottom:1px solid #435267;text-align:left;white-space:nowrap}th{color:#b6c8e5}code{color:#a8c6ff}</style></head><body><h1>OX Treasury / Card Watch</h1><p class="muted">Read-only local observations. Prices are indicative, not confirmed sold prices. No trading or wagering.</p>'''
        +'<section><strong>'+e(state)+'</strong> | Scheduler '+('enabled' if status.get('enabled') else 'paused')
        +' | Age '+e(age_text)+' | Last collection '+e(_time(status.get('observed_at')))
        +' | Next due '+e(_time(status.get('next_due')))
        +'<p class="muted">Upstream quote time may be unknown. Local collection time does not establish quote freshness.</p></section>'
        +'<section><h2>Observed cards ('+str(len(rows))+')</h2><table><thead><tr>'
        +''.join('<th>'+x+'</th>' for x in ('Game','Card','Set','Number','Indicative price','Currency','Source','Upstream quote time'))
        +'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></section>'
        +'<section><h2>Indicative price history</h2>'+render_trends(snapshots or [], selected, search)+'</section>'
        +'<section><h2>Claimed completed sales ('+str(len(sale_rows))+')</h2><p class="muted">Imported manually from user-supplied CSV. Every row is UNVERIFIED. Never combined with asking-price charts or the financial ledger. Sale claims are not proof of a completed transaction.</p><table><thead><tr>'
        +''.join('<th>'+e(x)+'</th>' for x in ('Game','Card','Set','Number','Sale date','Claimed price','Currency','Condition','Marketplace','Sale ID','Evidence status','Imported at (UTC)','Source URL'))
        +'</tr></thead><tbody>'+''.join(sale_rows)+'</tbody></table></section>'
        +'<p><a href="/history.json" style="color:#a8c6ff">Historical indicative observations (JSON)</a> | <a href="/sales.json" style="color:#a8c6ff">Unverified sale evidence (JSON)</a></p><small>Refreshes every 60 seconds; this page never triggers a provider request.</small></body></html>')


def make_handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path not in ('/', '/status.json', '/history.json', '/sales.json'):
                self.send_error(404); return
            try:
                status = Tracker(db_path).status()
                if path == '/sales.json':
                    query=parse_qs(urlsplit(self.path).query)
                    raw=query.get('limit',['100'])[0]
                    term=query.get('q',[''])[0]
                    if not raw.isdecimal() or len(raw)>3 or not 1 <= int(raw) <= 500 or len(term)>100 or any(ord(c)<32 for c in term):
                        self.send_error(400,'Invalid sale search'); return
                    body=json.dumps({'records':read_sales(db_path,int(raw),term),
                        'verification_status':'unverified',
                        'note':'User-supplied claimed sales; not independently verified or pooled with indicative quotes.'},allow_nan=False).encode('utf-8')
                    kind='application/json; charset=utf-8'
                elif path == '/history.json':
                    query=parse_qs(urlsplit(self.path).query)
                    raw=query.get('limit',['100'])[0]
                    if not raw.isdecimal() or len(raw)>3 or not 1<=int(raw)<=500:
                        self.send_error(400, 'Invalid limit'); return
                    body=json.dumps({'snapshots':Tracker(db_path).recent_observations(int(raw)), 'note':'Collection times are not upstream quote timestamps; prices are indicative, not sold prices.'},allow_nan=False).encode('utf-8'); kind='application/json; charset=utf-8'
                elif path == '/status.json':
                    body = json.dumps(status, allow_nan=False).encode('utf-8'); kind='application/json; charset=utf-8'
                else:
                    query=parse_qs(urlsplit(self.path).query)
                    raw=query.get('series',['all'])[0]
                    if raw != 'all' and not (len(raw)==24 and all(c in '0123456789abcdef' for c in raw)) and (not raw.isdecimal() or len(raw)>2 or int(raw)>39):
                        self.send_error(400, 'Invalid series'); return
                    search=query.get('q',[''])[0]
                    if len(search)>100 or any(ord(c)<32 for c in search):
                        self.send_error(400, 'Invalid search'); return
                    selected=None if raw=='all' else (int(raw) if raw.isdecimal() else raw)
                    body = render(status, Tracker(db_path).recent_observations(500), selected, search, read_sales(db_path,25,search)).encode('utf-8'); kind='text/html; charset=utf-8'
            except (OSError, ValueError, RuntimeError) as exc:
                self.send_error(503, 'Tracker database unavailable'); return
            self.send_response(200)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(body)
        def do_POST(self): self.send_error(405)
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=ROOT/'data'/'tracker.db')
    p.add_argument('--port',type=int,default=8766)
    args=p.parse_args()
    if not 1024 <= args.port <= 65535:p.error('port must be 1024-65535')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(args.db))
    print(f'Read-only dashboard: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
