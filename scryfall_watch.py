"""Opt-in, read-only Scryfall exact-printing observations (not completed sales)."""
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler

SOURCE = 'Scryfall'
BASE = 'https://api.scryfall.com/cards/'
USER_AGENT = 'OXTreasury-ReadOnlyWatch/0.6 (personal card research)'
MIN_GAP = 0.25
MAX_ENTRIES = 20
MAX_RESPONSE_BYTES = 256_000
MAX_WATCHLIST_BYTES = 64_000
TIMEOUT = 6

class ProviderUnavailable(RuntimeError): pass
class ProviderRateLimited(ProviderUnavailable):
    def __init__(self, retry_after=3600):
        super().__init__('provider rate limited')
        self.retry_after = max(900, min(14400, int(retry_after)))

def _identity(entry):
    if not isinstance(entry,dict) or str(entry.get('game','')).upper()!='MTG':
        raise ValueError('Scryfall adapter only supports MTG cards')
    set_code=str(entry.get('set_code','')).lower()
    number=str(entry.get('collector_number',''))
    if not re.fullmatch(r'[a-z0-9]{2,12}',set_code):
        raise ValueError('invalid MTG set code')
    if not re.fullmatch(r'[a-zA-Z0-9+*.-]{1,30}',number):
        raise ValueError('invalid collector number')
    return set_code,number

def load_watchlist(path):
    path=Path(path)
    if path.stat().st_size>MAX_WATCHLIST_BYTES:raise ValueError('watchlist exceeds 64KB')
    data=json.loads(path.read_text(encoding='utf-8'))
    _validate(data)
    return data

def _validate(items):
    if not isinstance(items,list) or not 1<=len(items)<=MAX_ENTRIES:
        raise ValueError('Scryfall watchlist must contain 1-20 MTG cards')
    keys=[_identity(x) for x in items]
    if len(set(keys))!=len(keys):raise ValueError('duplicate card identity in watchlist')
    return keys

def _http_get(url,timeout):
    class RejectRedirect(HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            raise ProviderUnavailable('unexpected redirect')
    if not url.startswith(BASE):raise ValueError('provider origin not permitted')
    req=Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/json;q=0.9,*/*;q=0.8'},method='GET')
    try:
        with build_opener(RejectRedirect()).open(req,timeout=timeout) as resp:
            if resp.geturl()!=url:raise ProviderUnavailable('unexpected provider origin')
            body=resp.read(MAX_RESPONSE_BYTES+1)
            if len(body)>MAX_RESPONSE_BYTES:raise ProviderUnavailable('oversized provider response')
            return json.loads(body.decode('utf-8'))
    except HTTPError as e:
        if e.code==404:return None
        if e.code==429:
            try:retry=int(e.headers.get('Retry-After','3600'))
            except (TypeError,ValueError):retry=3600
            raise ProviderRateLimited(retry) from None
        raise ProviderUnavailable(f'provider HTTP {e.code}') from None
    except (URLError,TimeoutError,OSError,UnicodeError,json.JSONDecodeError) as e:
        raise ProviderUnavailable(f'provider {type(e).__name__}') from None

def observe(watchlist,get=_http_get,sleep=time.sleep,monotonic=time.monotonic):
    """Fetch exact card printing snapshots; no sales, portfolio value, or trades inferred."""
    keys=_validate(watchlist)
    records=[]; last=None
    for set_code,number in keys:
        if last is not None:
            wait=MIN_GAP-(monotonic()-last)
            if wait>0:sleep(wait)
        last=monotonic()
        url=BASE+quote(set_code,safe='')+'/'+quote(number,safe='')
        data=get(url,TIMEOUT)
        query={'game':'MTG','set_code':set_code,'collector_number':number}
        if data is None:
            records.append({'query':query,'status':'unmatched','card':None})
            continue
        if not isinstance(data,dict) or data.get('object')!='card' or str(data.get('set','')).lower()!=set_code or str(data.get('collector_number',''))!=number:
            raise ProviderUnavailable('provider returned unexpected card identity')
        prices=data.get('prices') or {}
        if not isinstance(prices,dict):raise ProviderUnavailable('invalid prices object')
        valid_keys={'usd','usd_foil','usd_etched','eur','eur_foil','eur_etched','tix'}
        indicative={k:v for k,v in prices.items() if k in valid_keys and isinstance(v,str) and re.fullmatch(r'[0-9]{1,8}(?:\.[0-9]{1,4})?',v)}
        records.append({'query':query,'status':'matched','card':{
            'game':'MTG','set_code':set_code,'collector_number':number,'name':str(data.get('name',''))[:200],
            'source':SOURCE,'source_url':f'https://scryfall.com/card/{quote(set_code,safe="")}/{quote(number,safe="")}',
            'indicative_prices':indicative,'price_kind':'provider daily estimate; not a completed sale',
            'price_as_of':'not supplied by provider'}})
    return {'mode':'live_read_only_scryfall','source':SOURCE,'source_url':'https://scryfall.com/docs/api',
            'price_data':True,'completed_sales':False,'cards':records}
