"""Deterministic, reversible bytes -> patches -> 1000-index world.

Not Meta BLT. Patch length follows a reproducible *heuristic* using the
empirical local byte-distribution entropy, not learned next-byte entropy.
No file name, extension, prompt, or decoded text is trusted as byte identity.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from math import log2
from typing import Any
import json
import re

SCHEMA = 'OX_BYTE_WORLD/0.2.0'
MAX_INPUT = 16 * 1024 * 1024
COUNT = 1000
PATCH_MIN = 8
PATCH_MAX = 256


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    return -sum((v / length) * log2(v / length) for v in counts.values())


def _summary(data: bytes, start: int, end: int) -> dict:
    b = data[start:end]
    return {
        'start': start, 'end': end, 'length': len(b),
        'sha256': digest(b),
        'entropyMilli': round(entropy(b) * 1000),
        'zeroCount': b.count(0),
        'printableCount': sum(32 <= v < 127 for v in b),
        'meanByteMilli': round(1000 * sum(b) / len(b)) if b else 0,
    }


def make_patches(data: bytes) -> list[dict]:
    """Partition exactly once. Lower-entropy local windows grow larger patches."""
    result = []
    at = 0
    while at < len(data):
        sample = data[at:at + 64]
        bits = entropy(sample)
        desired = round(PATCH_MAX - min(1.0, bits / 8.0) * (PATCH_MAX - PATCH_MIN))
        size = max(PATCH_MIN, min(PATCH_MAX, desired))
        end = min(len(data), at + size)
        result.append({'index': len(result), **_summary(data, at, end)})
        at = end
    return result


def reconstruct_patches(source: bytes, patches: list[dict]) -> bytes:
    """Refuse overlaps, gaps, reorders or corrupt source; this is not compression."""
    if not isinstance(patches, list):
        raise ValueError('Patches must be a list')
    expected = 0
    parts = []
    for i, patch in enumerate(patches):
        if type(patch.get('index')) is not int or patch['index'] != i:
            raise ValueError('Patch order mismatch')
        start, end = patch.get('start'), patch.get('end')
        if type(start) is not int or type(end) is not int or start != expected or end <= start or end > len(source):
            raise ValueError('Patch gap, overlap or invalid length')
        piece = source[start:end]
        if _summary(source, start, end) != {k: patch[k] for k in _summary(source,start,end)}:
            raise ValueError('Patch measurement mismatch')
        parts.append(piece)
        expected = end
    if expected != len(source):
        raise ValueError('Patches do not cover original bytes')
    return b''.join(parts)


def make_splices(data: bytes) -> list[dict]:
    n = len(data)
    splices = []
    for index in range(COUNT):
        start = index * n // COUNT
        end = (index + 1) * n // COUNT
        splices.append({
            'index': index,
            'gateRow': index // 100,
            'gateColumn': (index % 100) // 10,
            'subsplice': index % 10,
            **_summary(data, start, end),
        })
    return splices


def analyze_bytes(data: bytes, source: str = 'unnamed') -> dict:
    if type(data) is not bytes:
        raise TypeError('Input must be raw bytes')
    if len(data) > MAX_INPUT:
        raise ValueError(f'Input exceeds {MAX_INPUT} byte local safety bound')
    # Keep source label out of the identity fingerprint, and never evaluate it.
    source = source[:120]
    patches, splices = make_patches(data), make_splices(data)
    core = {
        'schema': SCHEMA,
        'input': {'sha256': digest(data), 'byteLength': len(data), 'sourceLabel': source},
        'segmentation': {
            'method': 'OX empirical-local-entropy heuristic / NOT Meta BLT',
            'version': 'OX_PATCH_HEURISTIC/1', 'minLength': PATCH_MIN,
            'maxLength': PATCH_MAX, 'windowBytes': 64,
        },
        'representation': {
            'spliceCount': COUNT, 'addressing': '10 rows x 10 columns x 10 subsplices',
            'semantics': 'byte measurements only; pitch, music and intent are not inferred',
        },
        'patches': patches, 'splices': splices,
    }
    # Content print is independent of filename and of mapping edits.
    core['print'] = digest(canonical({
        'schema':core['schema'],
        'input':{'sha256':core['input']['sha256'],'byteLength':len(data)},
        'segmentation':core['segmentation'],'representation':core['representation'],
        'patches':patches,'splices':splices,
    }))
    return core


def verify_vessel(source: bytes, vessel: dict) -> bool:
    if not isinstance(vessel, dict) or vessel.get('schema') != SCHEMA:
        raise ValueError('Schema mismatch')
    if vessel['input']['byteLength'] != len(source) or vessel['input']['sha256'] != digest(source):
        raise ValueError('Original asset hash/length mismatch')
    reconstructed = reconstruct_patches(source, vessel['patches'])
    if reconstructed != source:
        raise ValueError('Roundtrip changed bytes')
    rebuilt = analyze_bytes(source, vessel['input']['sourceLabel'])
    if rebuilt != vessel:
        raise ValueError('Derived vessel integrity mismatch')
    return True


def render_self_literal(vessel: dict, max_patch_slots: int = 40) -> str:
    """Generate a native Self *object expression* for use in actual Self VM.

    Only SHA hex, numeric literals and static strings are inserted; no raw
    user data enters the Self evaluator. The source is an artifact, NOT an IPC
    connection, and this module does not claim runtime testing.
    """
    if vessel.get('schema') != SCHEMA:
        raise ValueError('Expected byte-world vessel')
    if not isinstance(max_patch_slots,int) or not (0 <= max_patch_slots <= 256):
        raise ValueError('Invalid export limit')
    hash_ = vessel['input']['sha256']; print_ = vessel['print']
    if not all(re.fullmatch(r'[0-9a-f]{64}', x) for x in (hash_,print_)):
        raise ValueError('Invalid digest')
    if type(vessel['input'].get('byteLength')) is not int or not (0 <= vessel['input']['byteLength'] <= MAX_INPUT):
        raise ValueError('Untrusted byte count')
    patches = vessel['patches']
    if not isinstance(patches, list): raise ValueError('Untrusted patch list')
    for index, patch in enumerate(patches[:max_patch_slots]):
        if (type(patch.get('index')) is not int or patch['index'] != index or
            any(type(patch.get(k)) is not int or patch[k] < 0 for k in ('start','end','entropyMilli')) or
            not re.fullmatch(r'[0-9a-f]{64}', str(patch.get('sha256','')))):
            raise ValueError('Untrusted Self source measurement')
    lines = [
        '"OX Spatial Fabric native Self object expression / actual Self interpreter required."',
        '"Evaluating returns a native object. It does not install a new Self module."',
        '(|',
        '  parent* = traits clonable.',
        f"  originDigest = '{hash_}'.",
        f"  representationDigest = '{print_}'.",
        f"  byteLength = {vessel['input']['byteLength']}.",
        f'  patchCount = {len(patches)}.',
        f'  visiblePatchCount = {min(len(patches),max_patch_slots)}.',
        f'  layerCount = {COUNT}.',
        "  schema = 'OX_BYTE_WORLD/0.2.0'.",
        '  depth <- 1.2.', '  twist <- 2.0.', '  hue <- 0.', '  threshold <- 0.18.',
        '  revision <- 0.',
        "  description = 'Original byte asset stays outside Self; object holds verified references'.",
    ]
    for p in patches[:max_patch_slots]:
        lines.extend([
            f'  patch{p["index"]:04} = (|',
            '    parent* = traits clonable.',
            f'    index = {p["index"]}.',
            f'    startByte = {p["start"]}.',
            f'    endByte = {p["end"]}.',
            f'    entropyMilli = {p["entropyMilli"]}.',
            f"    contentDigest = '{p['sha256']}'.",
            '  |).',
        ])
    lines += ['|)', '']
    return '\n'.join(lines)
