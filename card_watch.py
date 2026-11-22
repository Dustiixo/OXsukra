"""Offline, read-only card catalog matching; no prices or trading actions."""
import csv
import json
from pathlib import Path

GAMES = {'MTG', 'POKEMON', 'YUGIOH'}
MAX_ROWS = 100000
MAX_BYTES = 12_000_000

def load_catalog(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('catalog exceeds 12 MB limit')
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        needed = {'game','name','set_code','collector_number','source'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('catalog requires game,name,set_code,collector_number,source columns')
        result = {}
        for n, row in enumerate(reader):
            if n >= MAX_ROWS: raise ValueError('too many catalog rows')
            game = row['game'].strip().upper()
            if game not in GAMES: raise ValueError('unsupported game')
            key = (game, row['set_code'].strip().casefold(), row['collector_number'].strip().casefold())
            if not all(key) or not row['name'].strip() or not row['source'].strip():
                raise ValueError('incomplete catalog row')
            if key in result: raise ValueError('ambiguous duplicate catalog identity')
            result[key] = {'game':game,'name':row['name'].strip(),'set_code':row['set_code'].strip(),
                           'collector_number':row['collector_number'].strip(),'source':row['source'].strip()}
    return result

def observe(watchlist, catalog):
    """Match only exact identities. No guessed prices, values, or inferred ownership."""
    if len(watchlist) > 1000: raise ValueError('watchlist exceeds 1000 entries')
    output = []
    for entry in watchlist:
        game = str(entry['game']).strip().upper()
        if game not in GAMES: raise ValueError('unsupported watchlist game')
        key = (game,str(entry['set_code']).strip().casefold(),str(entry['collector_number']).strip().casefold())
        match = catalog.get(key)
        output.append({'query':{'game':game,'set_code':entry['set_code'],'collector_number':entry['collector_number']},
                       'status':'matched' if match else 'unmatched', 'card':match})
    return {'mode':'offline_catalog_only','price_data':False,'cards':output}

def from_files(watchlist_path, catalog_path):
    watchlist=json.loads(Path(watchlist_path).read_text(encoding='utf-8'))
    if not isinstance(watchlist,list): raise ValueError('watchlist must be an array')
    return observe(watchlist,load_catalog(catalog_path))
