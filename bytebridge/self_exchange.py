"""Strict byte-identity-preserving source bridge for a native Self handoff.

This is NOT a Self interpreter or proof that Morphic ran. It accepts only one
numeric edit in an exact, generated Self object expression. No Self text is
executed, and no arbitrary file-out/Transporter source is accepted.
"""
from __future__ import annotations
import re
from decimal import Decimal
from .core import render_self_literal, digest
from .ledger import BOUNDS, validate_slot, verify

METHOD = 'CONTROLLED_LITERAL_EDIT/1'
SLOTS = tuple(BOUNDS)
NUMBER = r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?'
MAX_SOURCE_BYTES = 65536


def _number(value):
    """Format bounded numeric slots without exponential or executable syntax."""
    # Decimal(str()) avoids exponent syntax while keeping float round-trip
    # precision, including tiny nonzero values from prior ledger revisions.
    s = format(Decimal(str(value)), 'f')
    if '.' in s:s=s.rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


def source_for_revision(vessel: dict, world: dict) -> bytes:
    """Revision-bound Self expression; byte-source unchanged and not executed."""
    verify(world, vessel['input']['sha256'])
    result = render_self_literal(vessel)
    for slot in SLOTS:
        value = world['mapping'][slot]
        validate_slot(slot, value)
        marker = f'  {slot} <- '
        matches = re.findall(r'^' + re.escape(marker) + r'.*$', result, flags=re.MULTILINE)
        if len(matches) != 1:
            raise ValueError('Unstable Self source template')
        result = result.replace(matches[0], f'{marker}{_number(value)}.')
    result = result.replace('  revision <- 0.\n',
        f"  baseHead = '{world['head']}'.\n  revision <- {world['revision']}.\n")
    if not result.endswith('\n'):
        raise ValueError('Self source must end in a newline')
    encoded = result.encode('ascii')
    if len(encoded)>MAX_SOURCE_BYTES:
        raise ValueError('Self baseline exceeds handoff bound')
    return encoded


def one_slot_literal_edit(baseline: bytes, candidate: bytes) -> tuple[str, float, float]:
    """Check that *only* one numeric slot has changed, with all other bytes exact.

    Restricted syntax intentionally rejects arbitrary Self file-out/reformatting,
    methods, slot injection, reordered slots, added comments or code.
    """
    if type(baseline) is not bytes or type(candidate) is not bytes:
        raise TypeError('Self literal inputs must be exact bytes')
    if not 0<len(baseline)<=MAX_SOURCE_BYTES or not 0<len(candidate)<=MAX_SOURCE_BYTES:
        raise ValueError('Self literal size bound')
    if baseline == candidate:
        raise ValueError('No Self slot changed')
    try:
        current = candidate.decode('ascii')
        original = baseline.decode('ascii')
    except UnicodeDecodeError as e:
        raise ValueError('Self handoff must be ASCII') from e
    deltas = []
    for slot in SLOTS:
        regex = re.compile(r'(?m)^  '+re.escape(slot)+r' <- ('+NUMBER+r')\.$')
        a, b = list(regex.finditer(original)), list(regex.finditer(current))
        if len(a)!=1 or len(b)!=1:
            raise ValueError('Expected exactly one numeric slot definition')
        before, after = float(a[0].group(1)), float(b[0].group(1))
        validate_slot(slot, after)
        if before != after:
            deltas.append((slot, before, after, b[0]))
    if len(deltas)!=1:
        raise ValueError('Exactly one substantive Self slot edit required')
    slot, before, after, match = deltas[0]
    # Replace the *single* changed numeric literal back to its exact original
    # token. Anything else altered is a structural or foreign-source change.
    base_token = re.search(r'(?m)^  '+re.escape(slot)+r' <- ('+NUMBER+r')\.$',original).group(1)
    reconstructed = current[:match.start(1)] + base_token + current[match.end(1):]
    if reconstructed != original:
        raise ValueError('Self source differs outside one numeric slot')
    return slot, before, after


def validate_source_evidence(observation: dict, vessel: dict, world: dict, candidate: bytes):
    baseline=source_for_revision(vessel,world)
    if observation['baselineSourceSha256']!=digest(baseline):
        raise ValueError('Self baseline source hash mismatch')
    if observation['objectSourceSha256']!=digest(candidate):
        raise ValueError('Self candidate source hash mismatch')
    slot, before, value = one_slot_literal_edit(baseline,candidate)
    if (slot != observation['slot'] or before != observation['before'] or value != observation['value']):
        raise ValueError('Signed observation disagrees with Self literal edit')
    return True
