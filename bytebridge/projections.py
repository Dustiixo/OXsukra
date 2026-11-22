"""Deterministic, deliberately non-semantic sonic and 3D views of one byte world.

The WAV is not a reversible audio codec. Exact source bytes live in original.bin.
"""
from __future__ import annotations
import io, math, struct, wave
from .core import COUNT
from .ledger import validate_slot, BOUNDS


def obj_projection(vessel:dict, mapping:dict) -> bytes:
    for key in BOUNDS: validate_slot(key,mapping[key])
    rows=[f'# OX_BYTE_PATH/1 ORIGINAL_SHA256 {vessel["input"]["sha256"]}',
          f'# VIEW_ENTROPY_HEURISTIC; MAP: depth={mapping["depth"]}, twist={mapping["twist"]}, hue={mapping["hue"]}, threshold={mapping["threshold"]}',
          'o OX_Byte_World']
    prev=0;vertex=0
    for s in vessel['splices']:
        if s['length']==0: continue
        t=s['index']/(COUNT-1);e=s['entropyMilli']/8000.;v=s['meanByteMilli']/255000.
        phi=t*math.pi*(8+mapping['twist']);radius=(30+mapping['depth']*100)*(.35+e)
        x=(t-.5)*780.;y=math.sin(phi)*radius+(v-.5)*200.;z=math.cos(phi)*radius+(e-.5)*120.
        rows.append(f'v {x:.6f} {y:.6f} {z:.6f}')
        vertex+=1
        if prev:rows.append(f'l {prev} {vertex}')
        prev=vertex
    return ('\n'.join(rows)+'\n').encode('ascii')


def sonify(vessel:dict, sample_rate:int=16000, frames_per_splice:int=160) -> bytes:
    """Ten-second illustrative modulation. Pitch ~ mean byte; volume ~ entropy.

    All PCM values are bounded and attack/release shaped; no pitch or intent
    inference. Output is a standard 16-bit mono WAV file.
    """
    if sample_rate != 16000 or frames_per_splice != 160: raise ValueError('Pinned sonification configuration')
    buf=io.BytesIO()
    with wave.open(buf,'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(sample_rate)
        phase=0.;data=bytearray()
        for s in vessel['splices']:
            valid=s['length']>0
            e=s['entropyMilli']/8000.;mean=s['meanByteMilli']/255000.
            hz=70+720*mean
            volume=.24*e if valid else 0.
            for j in range(frames_per_splice):
                phase+=2*math.pi*hz/sample_rate
                # Window endpoints at zero prevent discontinuities across windows.
                fade=math.sin(math.pi*j/(frames_per_splice-1))**2
                sample=round(32767*volume*fade*math.sin(phase))
                data.extend(struct.pack('<h',max(-32768,min(32767,sample))))
        audio.writeframes(bytes(data))
    return buf.getvalue()
