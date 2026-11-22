"""Zero-extra-dependency standard MIDI export for coarse 16th note rhythm sketches."""
from __future__ import annotations
import struct
from pathlib import Path
import numpy as np
from .creative import rhythm_grid


def vlq(n: int) -> bytes:
    if n < 0: raise ValueError('negative variable length')
    out=[n&0x7f]
    while n>>7:
        n >>= 7
        out.insert(0,0x80|(n&0x7f))
    return bytes(out)


def export_rhythm_midi(path, source, bpm: float, bars: int) -> int:
    # 480 ticks/quarter, 120 per 16th; channel 10 percussion (index 9).
    steps=rhythm_grid(source,bpm,bars)
    midi_events=[]
    count=0
    for i,amount in enumerate(steps):
        if amount < .32:continue
        pitch=36 if i%16 in (0,8) else 38 if i%16 in (4,12) else 42
        vel=int(np.clip(45+amount*65,1,127))
        start=i*120
        midi_events.append((start,1,bytes([0x99,pitch,vel])))
        midi_events.append((start+80,0,bytes([0x89,pitch,0])))
        count+=1
    midi_events.sort()
    microseconds=int(60_000_000/float(bpm))
    track=bytearray()
    track+=b'\x00\xff\x51\x03'+microseconds.to_bytes(3,'big')
    track+=b'\x00\xff\x58\x04\x04\x02\x18\x08'
    last=0
    for time,_,message in midi_events:
        track+=vlq(time-last)+message
        last=time
    track+=b'\x00\xff\x2f\x00'
    data=b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(track))+track
    Path(path).write_bytes(data)
    return count
