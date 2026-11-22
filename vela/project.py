"""Portable .fid (experimental ZIP container) and non-destructive project provenance."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import unicodedata
import uuid
import zipfile
from pathlib import Path
from .audio_core import read_audio, write_audio
from .deepbrew import new_graph, get_graph, audio_object, insert_audio, accept_proposal

SCHEMA = 'vela.fid.experimental/0.1'


def new_event(kind, description, **fields):
    return {'id':uuid.uuid4().hex[:12], 'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'kind':kind, 'description':description, **fields}


class Project:
    def __init__(self, folder=None):
        self.root = Path(folder) if folder else Path(tempfile.mkdtemp(prefix='vela_water_edge_'))
        self.root.mkdir(parents=True,exist_ok=True)
        (self.root/'media').mkdir(exist_ok=True)
        (self.root/'originals').mkdir(exist_ok=True)
        self.manifest = {'schema': SCHEMA, 'name':'Untitled Water’s Edge',
                         'bpm':120.,'bars':8, 'decks':{'a':None,'b':None},
                         'responses':[], 'active_response':None,
                         'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                         'notes':'', 'events':[], 'object_graph':new_graph(), 'limitations':['Audio features are approximations; original audio is kept.']}

    def add_audio(self, label:str, data, original_name:str, save_event=True):
        safe = ''.join(c for c in Path(original_name).stem if c.isalnum() or c in '-_')[:32] or 'audio'
        relative = f'media/{label}_{uuid.uuid4().hex[:8]}_{safe}.wav'
        write_audio(self.root/relative,data)
        digest = hashlib.sha256((self.root/relative).read_bytes()).hexdigest()
        item = {'path':relative,'original_filename':Path(original_name).name,
                'sha256_pcm_wav':digest}
        # Each audio artifact is a durable, content-addressed object. A deck is just a view.
        graph=get_graph(self.manifest)
        from .audio_core import read_audio
        obj=audio_object(relative,(self.root/relative).read_bytes(),read_audio(self.root/relative),
                         kind='source',title=original_name)
        item['object_id']=insert_audio(graph,obj)
        if label in ('a','b'):
            self.manifest['decks'][label]=item
        if save_event:
            self.add_event('input',f'Loaded {Path(original_name).name} on {label}',deck=label,source=item)
        return item

    def _verified_edit_source(self, ref):
        """An undo reference is history data, not authority to read arbitrary paths."""
        path = ref.get('path', '')
        if (not isinstance(path, str) or not path.startswith('media/') or
                '/' in path[6:] or '\\' in path or ':' in path or not path.endswith('.wav')):
            raise ValueError('Unsafe edit media reference')
        graph = get_graph(self.manifest)
        obj = graph['objects'].get(ref.get('object_id'))
        target = self.root / path
        if (not obj or not target.is_file() or target.is_symlink() or
                hashlib.sha256(target.read_bytes()).hexdigest() != obj.get('content_sha256') or
                ref.get('sha256_pcm_wav') != obj.get('content_sha256')):
            raise ValueError('Edit source identity could not be verified')
        original = ref.get('original_binary')
        if original:
            name = original.get('path', '')
            if (not isinstance(name, str) or not name.startswith('originals/') or
                    '/' in name[10:] or '\\' in name or ':' in name):
                raise ValueError('Unsafe original edit reference')
            raw = self.root / name
            if (not raw.is_file() or raw.is_symlink() or
                    hashlib.sha256(raw.read_bytes()).hexdigest() != original.get('sha256')):
                raise ValueError('Original edit source identity could not be verified')
        return read_audio(target)

    def attenuate_bar(self, deck, sample_start, bar_frames):
        return self._edit_bar(deck, sample_start, bar_frames, reverse=False)

    def reverse_bar(self, deck, sample_start, bar_frames):
        return self._edit_bar(deck, sample_start, bar_frames, reverse=True)

    def _edit_bar(self, deck, sample_start, bar_frames, reverse):
        """Human-triggered derived edit; preserve original media."""
        import numpy as np
        from .audio_core import RATE
        if deck not in ('a', 'b') or not self.manifest['decks'].get(deck):
            raise ValueError('Select a loaded deck')
        if type(sample_start) is not int or type(bar_frames) is not int or sample_start < 0 or bar_frames <= 0:
            raise ValueError('Invalid bar selection')
        before = copy.deepcopy(self.manifest['decks'][deck])
        source = self._verified_edit_source(before)
        start = sample_start // bar_frames * bar_frames
        end = min(start + bar_frames, len(source))
        if end <= start:
            raise ValueError('Selected bar is outside the source')
        edited = source.copy()
        fade = min(int(RATE * .005), (end-start)//2)
        if reverse:
            edited[start:end] = source[start:end][::-1]
            if fade:
                weight = np.linspace(0., 1., fade, dtype=np.float32)[:, None]
                edited[start:start+fade] = source[start:start+fade]*(1-weight)+edited[start:start+fade]*weight
                edited[end-fade:end] = source[end-fade:end]*weight+edited[end-fade:end]*(1-weight)
        else:
            gain = np.full(end-start, 10**(-6/20), dtype=np.float32)
            if fade:
                gain[:fade] = np.linspace(1., gain[0], fade, dtype=np.float32)
                gain[-fade:] = np.linspace(gain[-1], 1., fade, dtype=np.float32)
            edited[start:end] *= gain[:, None]
        operation = 'reverse_bar' if reverse else 'attenuate_bar'
        details = {} if reverse else {'gain_db': -6}
        after = self.add_audio(deck, edited, 'Reversed bar.wav' if reverse else 'Attenuated bar.wav', save_event=False)
        graph = get_graph(self.manifest)
        if after['object_id'] != before['object_id']:
            graph['edges'].append({'src':after['object_id'], 'relation':'reversed_from' if reverse else 'attenuated_from',
                                   'dst':before['object_id'], 'source_sample_range':[start,end], **details})
        self.add_event('edit', 'Human reversed selected bar' if reverse else 'Human attenuated selected bar by 6 dB',
                       operation=operation, deck=deck, previous_deck=before,
                       edited_path=after['path'], from_object_id=before['object_id'],
                       to_object_id=after['object_id'], source_sample_start=start,
                       source_sample_end=end, fade_frames=fade, **details)
        return self.deck_audio(deck)

    def audition_bar_edit(self, deck):
        """Return matching pre/post edit bar samples without changing the project."""
        current = self.manifest['decks'].get(deck)
        for event in reversed(self.manifest['events']):
            if event.get('deck') != deck or event.get('operation') not in ('attenuate_bar', 'undo_attenuate_bar', 'reverse_bar', 'undo_reverse_bar'):
                continue
            if (event['operation'] not in ('attenuate_bar', 'reverse_bar') or not current or
                    current.get('path') != event.get('edited_path') or
                    current.get('object_id') != event.get('to_object_id')):
                break
            previous = event['previous_deck']
            if previous.get('object_id') != event.get('from_object_id'):
                raise ValueError('Invalid edit source identity')
            before = self._verified_edit_source(previous)
            after = self._verified_edit_source(current)
            start, end = event['source_sample_start'], event['source_sample_end']
            if (type(start) is not int or type(end) is not int or
                    not 0 <= start < end <= len(before) or len(before) != len(after)):
                raise ValueError('Invalid edit audition range')
            return before[start:end].copy(), after[start:end].copy()
        raise ValueError('No current bar edit to audition on this deck')

    def undo_bar_attenuation(self, deck):
        """Legacy attenuation-only undo entry point."""
        return self.undo_bar_edit(deck, attenuation_only=True)

    def undo_bar_edit(self, deck, attenuation_only=False):
        """Single-step undo, including after FID reopening; refuse stale edits."""
        current = self.manifest['decks'].get(deck)
        for event in reversed(self.manifest['events']):
            if event.get('deck') != deck or event.get('operation') not in ('attenuate_bar', 'undo_attenuate_bar', 'reverse_bar', 'undo_reverse_bar'):
                continue
            if (event['operation'] not in ('attenuate_bar', 'reverse_bar') or not current or
                    current.get('path') != event.get('edited_path') or
                    current.get('object_id') != event.get('to_object_id')):
                break
            if attenuation_only and event['operation'] != 'attenuate_bar':
                break
            previous = copy.deepcopy(event['previous_deck'])
            if previous.get('object_id') != event.get('from_object_id'):
                raise ValueError('Invalid edit source identity')
            audio = self._verified_edit_source(previous)
            self.manifest['decks'][deck] = previous
            self.add_event('revert', 'Human undid selected bar edit',
                           operation='undo_' + event['operation'], deck=deck, edit_event_id=event['id'],
                           restored_object_id=previous['object_id'])
            return audio
        raise ValueError('No current bar edit to undo on this deck')

    def attach_original(self, deck:str, filename:str):
        """Preserve original imported MP3/FLAC/WAV bytes, independent of decoded WAV."""
        source=Path(filename)
        if source.suffix.lower() not in ('.wav','.mp3','.flac','.ogg','.aiff','.aif'):
            raise ValueError('Unsupported source extension')
        if source.stat().st_size > 500*1024*1024:
            raise ValueError('Original audio file is too large for this prototype')
        payload=source.read_bytes()
        digest=hashlib.sha256(payload).hexdigest()
        safe=''.join(x for x in source.stem if x.isalnum() or x in '-_')[:35] or 'audio'
        path=f'originals/{digest[:18]}_{safe}{source.suffix.lower()}'
        target=self.root/path
        if not target.exists():target.write_bytes(payload)
        item=self.manifest['decks'].get(deck)
        if not item:raise ValueError('Deck must contain normalized audio first')
        original={'path':path,'sha256':digest,'original_filename':source.name,'size_bytes':len(payload)}
        item['original_binary']=original
        graph=get_graph(self.manifest)
        graph['objects'][item['object_id']]['original_binary']=original
        self.add_event('evidence','Preserved original imported file bytes',
                       object_id=item['object_id'],original_hash=digest,source=source.name)
        return original

    def add_response(self, response, prompt, iteration, measure, plan, evidence, source_object_id=None):
        id_ = uuid.uuid4().hex[:12]
        path = f'media/response_{iteration:03d}_{id_}.wav'
        write_audio(self.root/path,response)
        item = {'id':id_, 'path':path, 'iteration':iteration, 'prompt':prompt,
                'plan':plan, 'source_evidence':evidence,'evaluation':measure,
                'sha256_pcm_wav':hashlib.sha256((self.root/path).read_bytes()).hexdigest(),
                'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        graph=get_graph(self.manifest)
        obj=audio_object(path,(self.root/path).read_bytes(),read_audio(self.root/path),
                         kind='generated',title=f'Response {iteration}')
        source_deck=self.manifest['decks']['b'] or self.manifest['decks']['a']
        source_id=source_object_id or (source_deck.get('object_id') if source_deck else None)
        item['object_id']=insert_audio(graph,obj,parent=source_id,relation='generated_from')
        self.manifest['responses'].append(item)
        self.add_event('proposal',f"Generated #{iteration}: {plan['mode']}",response_id=id_,
                       parent_response=self.manifest.get('active_response'),
                       evaluation=measure, plan=plan)
        return item

    def add_event(self,kind,description,**fields):
        event = new_event(kind,description,**fields)
        self.manifest['events'].append(event)
        return event

    def apply_response(self, response_id, position_seconds):
        self.manifest['active_response']=response_id
        self.add_event('impact','Generative response entered the music',response_id=response_id,
                       at_music_seconds=round(position_seconds,3))

    def revert_response(self, response_id):
        self.manifest['active_response']=response_id
        self.add_event('revert','Reverted to earlier musical state',response_id=response_id)

    def annotate(self, text, music_seconds, view='water'):
        if not text.strip(): return None
        source=self.manifest['decks']['a'] or self.manifest['decks']['b']
        objid=source.get('object_id') if source else None
        evt=self.add_event('annotation',text.strip(),at_music_seconds=round(music_seconds,3),view=view,
                          source_object_id=objid,active_response=self.manifest.get('active_response'))
        if objid:
            graph=get_graph(self.manifest)
            graph['edges'].append({'src':'evt_'+evt['id'],'relation':'annotates','dst':objid,
                                  'at_music_seconds':round(music_seconds,3)})
        return evt

    def save_fid(self, dest):
        dest = Path(dest)
        if dest.suffix.lower() != '.fid': dest = dest.with_suffix('.fid')
        self.manifest['saved_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        temp = dest.with_name(dest.name+'.tmp')
        try:
            with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                z.writestr('manifest.json',json.dumps(self.manifest,indent=2,ensure_ascii=False))
                for item in sorted((self.root/'media').glob('*.wav')):
                    z.write(item, f'media/{item.name}')
                for item in sorted((self.root/'originals').iterdir()):
                    if item.is_file():z.write(item,f'originals/{item.name}')
            os.replace(temp,dest)
        finally:
            if temp.exists(): temp.unlink()
        return dest

    @classmethod
    def open_fid(cls,filename):
        target = cls()
        with zipfile.ZipFile(filename,'r') as z:
            names = z.namelist()
            if len(names)!=len(set(names)): raise ValueError('Duplicate FID member paths are forbidden')
            # Windows filesystems commonly fold case. Refuse colliding ZIP paths
            # before extraction, even when the raw ZIP names are distinct.
            if len({unicodedata.normalize("NFC", name).casefold() for name in names}) != len(names):
                raise ValueError('FID member paths collide on case-insensitive filesystems after Unicode normalization and casefolding')
            if 'manifest.json' not in names: raise ValueError('No manifest.json in FID')
            # Bound archive metadata before reading/parsing attacker-controlled JSON.
            # All member sizes are checked before any payload is decompressed.
            if len(names) > 4000:
                raise ValueError('FID contains too many entries')
            infos = z.infolist()
            if sum(info.file_size for info in infos) > 2*1024*1024*1024:
                raise ValueError('FID uncompressed size exceeds safe import limit')
            if z.getinfo('manifest.json').file_size > 8*1024*1024:
                raise ValueError('FID manifest exceeds metadata size limit')
            manifest=json.loads(z.read('manifest.json'))
            # Reject malformed metadata before any member is extracted. This is
            # intentionally narrow: legacy valid FIDs retain their existing schema.
            if not isinstance(manifest, dict):
                raise ValueError('FID manifest must be a JSON object')
            if manifest.get('schema') != SCHEMA: raise ValueError('Unsupported FID version')
            if (not isinstance(manifest.get('decks', {}), dict)
                    or not isinstance(manifest.get('responses', []), list)):
                raise ValueError('FID decks/responses metadata has invalid structure')
            if any(value is not None and not isinstance(value, dict)
                   for value in manifest.get('decks', {}).values()):
                raise ValueError('FID deck metadata must be objects or null')
            if any(not isinstance(value, dict) for value in manifest.get('responses', [])):
                raise ValueError('FID response metadata must be objects')
            # Validate the optional audio-object graph's container types before
            # accessing objects or extracting media. Legacy FIDs may omit it.
            if 'object_graph' in manifest:
                graph_meta = get_graph(manifest)
                if (not isinstance(graph_meta.get('objects'), dict)
                        or not isinstance(graph_meta.get('edges'), list)
                        or not isinstance(graph_meta.get('proposals'), list)
                        or not isinstance(graph_meta.get('revisions'), list)
                        or any(not isinstance(obj, dict) for obj in graph_meta['objects'].values())):
                    raise ValueError('FID audio-object graph has invalid structure')
            for info in z.infolist():
                # Reject unsupported ZIP features before extracting any media.
                # This format writes only stored/deflated, unencrypted members.
                if info.flag_bits & 0x1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise ValueError('FID contains encrypted or unsupported-compression members')
            for info in z.infolist():
                # ZIP names use POSIX separators; Windows also treats backslashes,
                # colons, device basenames and trailing spaces/dots specially.
                # Reject ambiguous members before any extraction on either OS.
                leaf = info.filename.rsplit('/', 1)[-1]
                stem = leaf.split('.', 1)[0].upper()
                reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {
                    f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10)
                }
                if (not leaf or any(c in leaf for c in ('\\', ':', '<', '>', '"', '|', '?', '*'))
                        or leaf.endswith((' ', '.')) or stem in reserved
                        or any(ord(c) < 32 for c in leaf)):
                    raise ValueError('FID member filename is unsafe on Windows')
                # Reject Unix symlink entries even when their names resemble safe WAV files.
                # zipfile.extract may materialize them differently across platforms.
                if info.create_system == 3 and stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError('FID symbolic-link members are forbidden')
                if info.file_size > 600*1024*1024: raise ValueError('FID member exceeds limit')
                if not (info.filename=='manifest.json' or
                        (info.filename.startswith('media/') and info.filename.endswith('.wav') and '/' not in info.filename[6:]) or
                        (info.filename.startswith('originals/') and '/' not in info.filename[10:] and
                         Path(info.filename).suffix.lower() in ('.wav','.mp3','.flac','.ogg','.aiff','.aif'))):
                    raise ValueError('Unexpected file path in FID')
            references=[x for x in manifest.get('decks',{}).values() if x]
            references += list(manifest.get('responses',[]))
            graph=get_graph(manifest)
            # Validate optional source-record envelopes before reading their fields.
            # Malformed provenance must fail closed, not raise incidental TypeError.
            for record in references + list(graph['objects'].values()):
                if 'original_binary' in record and record['original_binary'] is not None:
                    original = record['original_binary']
                    if (not isinstance(original, dict)
                            or not isinstance(original.get('path'), str)
                            or not isinstance(original.get('sha256'), str)):
                        raise ValueError('FID original source metadata has invalid structure')
            originals=[v['original_binary'] for v in references if v.get('original_binary')]
            originals += [v['original_binary'] for v in graph['objects'].values() if v.get('original_binary')]
            # One original path must have one declared identity across every
            # reference; a dict overwrite would silently discard conflicts.
            original_hashes = {}
            for original in originals:
                path = original['path']
                digest = original['sha256']
                if path in original_hashes and original_hashes[path] != digest:
                    raise ValueError('FID original source has conflicting provenance checksums')
                original_hashes[path] = digest
            originals={x['path']:x for x in originals}.values()
            for original in originals:
                path=original.get('path','')
                if not (isinstance(path,str) and path.startswith('originals/') and
                        '/' not in path[10:] and path in names):
                    raise ValueError('FID original file reference is unsafe or missing')
                if hashlib.sha256(z.read(path)).hexdigest()!=original.get('sha256'):
                    raise ValueError('FID original file checksum mismatch')
            for ref in references:
                path=ref.get('path','')
                if not (isinstance(path,str) and path.startswith('media/') and
                        path.endswith('.wav') and '/' not in path[6:] and path in names):
                    raise ValueError('FID manifest contains an unsafe or missing media reference')
            # Verify deck WAV provenance even for legacy FIDs without object-graph hashes.
            # A deck hash is written by add_audio and must never silently drift.
            for deck in manifest.get('decks', {}).values():
                if deck and deck.get('sha256_pcm_wav') is not None:
                    if hashlib.sha256(z.read(deck['path'])).hexdigest() != deck['sha256_pcm_wav']:
                        raise ValueError('FID deck audio checksum mismatch')
            # Verify generated response bytes even in legacy FIDs lacking an object graph.
            for response in manifest.get('responses', []):
                if response.get('sha256_pcm_wav') is not None:
                    if hashlib.sha256(z.read(response['path'])).hexdigest() != response['sha256_pcm_wav']:
                        raise ValueError('FID response audio checksum mismatch')
            # No path traversal. Audit checksums BEFORE extracting, so the source identity
            # cannot silently point to different audio bytes after archive modification.
            graph=get_graph(manifest)
            object_refs=list(graph['objects'].values())
            for obj in object_refs:
                path=obj.get('media_path')
                if not isinstance(path,str) or path not in names or not path.startswith('media/') or \
                   '/' in path[6:] or not path.endswith('.wav'):
                    raise ValueError('Object has unsafe or missing audio reference')
                if hashlib.sha256(z.read(path)).hexdigest()!=obj.get('content_sha256'):
                    raise ValueError('Audio object checksum mismatch')
            for name in names:
                if name.startswith('media/') or name.startswith('originals/'):
                    z.extract(name,target.root)
        target.manifest=manifest
        target.upgrade_legacy_objects()
        return target

    def upgrade_legacy_objects(self):
        """In-memory graph migration for earlier valid VELA FIDs, retaining the source."""
        graph=get_graph(self.manifest)
        updated=0
        for ref in self.manifest.get('decks',{}).values():
            if ref and ref.get('object_id') not in graph['objects']:
                path=ref['path']
                item=audio_object(path,(self.root/path).read_bytes(),read_audio(self.root/path),
                                  kind='source',title=ref.get('original_filename','Legacy source'))
                ref['object_id']=insert_audio(graph,item)
                updated+=1
        source=self.manifest.get('decks',{}).get('b') or self.manifest.get('decks',{}).get('a')
        source_id=source.get('object_id') if source else None
        for ref in self.manifest.get('responses',[]):
            if ref.get('object_id') not in graph['objects']:
                path=ref['path']
                item=audio_object(path,(self.root/path).read_bytes(),read_audio(self.root/path),
                                  kind='generated',title='Legacy generated response')
                ref['object_id']=insert_audio(graph,item,parent=source_id,relation='legacy_generated_from')
                updated+=1
        if updated:
            self.add_event('migration','Constructed DeepBrew object view from legacy audio (original FID untouched)',
                           reconstructed_objects=updated,
                           limitation='Provenance links for legacy generated responses are inferred, not verified')
        return updated

    def deck_audio(self, deck):
        data = self.manifest['decks'].get(deck)
        if data:
            return read_audio(self.root/data['path'])
        return None

    def response_audio(self, response_id):
        item = next((x for x in self.manifest['responses'] if x['id']==response_id),None)
        return read_audio(self.root/item['path']) if item else None

    def export_mix(self,dest,transport,seconds=None):
        # Deterministic offline render; do not disturb the playing transport position.
        from .audio_core import Transport, RATE
        with transport.lock:
            temp=Transport(transport.bpm,transport.bars)
            temp.a=transport.a;temp.b=transport.b;temp.active=transport.active
            temp.crossfade=transport.crossfade;temp.volume=transport.volume
            temp.response_gain=transport.response_gain;temp.playing=True
        frames = int(seconds*RATE) if seconds else temp.frames
        audio=[]
        for n in range(0,frames,4096):
            audio.append(temp.render(min(4096,frames-n)))
        import numpy as np
        write_audio(dest,np.concatenate(audio))
        self.add_event('export','Exported mixed WAV',filename=Path(dest).name)
        return dest
