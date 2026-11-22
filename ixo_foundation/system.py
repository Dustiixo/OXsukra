"""Typed composition and explicit cross-component workflow.

The IXO database owns workspaces, durable facts, proposals and Moon2 traces.
The AIXO database owns learning exercises and evaluations. Research has no
implicit access to either database.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from ixo.runtime import IXORuntime
from ixo.common import SETS, IXOError
from ixo.bridge import capture
from aixo.engine import AIXOEngine, AIXOError
from dsoe.system import DSOESystem
from experience.store import ExperienceStore
from operations import OperationsHub


class Foundation:
    def __init__(self, home: str | Path):
        self.home = Path(home).expanduser().resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.ixo = IXORuntime(self.home / 'ixo.sqlite3')
        try:
            self.aixo = AIXOEngine(self.home / 'aixo.sqlite3')
        except Exception:
            self.ixo.close()
            raise
        try:
            self.dsoe = DSOESystem(self)
        except Exception:
            self.aixo.close()
            self.ixo.close()
            raise
        try:
            self.experience = ExperienceStore(self.home / 'experience.sqlite3')
        except Exception:
            self.dsoe.close()
            self.aixo.close()
            self.ixo.close()
            raise

        try:
            self.operations = OperationsHub(self)
        except Exception:
            self.experience.close()
            self.dsoe.close()
            self.aixo.close()
            self.ixo.close()
            raise

    def close(self) -> None:
        self.operations.close()
        self.experience.close()
        self.dsoe.close()
        self.aixo.close()
        self.ixo.close()

    def __enter__(self) -> Foundation:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def status(self) -> dict[str, Any]:
        """Read-only view; no need to open a browser or instantiate a model."""
        state = self.ixo.status()
        learning = self.aixo.state()
        return {
            'source_id': self.ixo._get('instance_id'),
            'ixo': state,
            'aixo': {
                'source_id': learning['source_id'],
                'course_completed': sum(bool(x['completed_at']) for x in learning['lessons']),
                'course_total': len(learning['lessons']),
                'experiments': len(learning['experiments']),
                'evaluations': len(learning['evaluations']),
                'captured_events': learning['captured_events'],
                'dsoe_evidence_count': learning['dsoe_evidence_count'],
            },
            'research': 'isolated_no_authority',
            'operations': {'available_operations': len(self.operations.list()),
                           'recent_receipts': len(self.operations.receipts(20))},
            'experience': self.experience.report(),
            'dsoe': {'task_count': len(self.dsoe.status()['tasks']),
                     'providers': 3, 'native_connected': 0},
        }

    def capture(self) -> dict[str, Any]:
        inserted = capture(self.ixo, self.aixo)
        exposure = self.experience.capture_ixo(self.ixo)
        return {'ok': True, 'captured_new': inserted, 'ixo_exposures_new': exposure['new_exposures'],
                'total_captured': self.aixo.state()['captured_events'],
                'source_id': self.ixo._get('instance_id')}

    def case(self, *, workspace: str, observation: str, hypothesis: str, question: str) -> dict[str, Any]:
        """Single deterministic research vertical slice.

        This does not autonomously decide, act, or approve facts. Every
        interpretation comes from explicit input; all intermediate writes are
        visible in the IXO event ledger. The operation is sequential, not one
        distributed transaction across two databases.
        """
        if workspace not in SETS:
            raise IXOError('Unknown Habitat set: ' + str(workspace))
        observation = self.ixo._text(observation, 2200)
        hypothesis = self.ixo._text(hypothesis, 2200)
        self.ixo._text('Operator hypothesis: ' + hypothesis, 2200)
        question = AIXOEngine.valid(question, 500)
        # AIXO evidence must not be silently associated with the wrong IXO DB.
        learning_state = self.aixo.state()
        bound = learning_state['source_id']
        if bound is None and learning_state['captured_events']:
            raise AIXOError('Legacy captured events lack source provenance; manual migration required')
        source = self.ixo._get('instance_id')
        if bound is not None and bound != source:
            raise IXOError('AIXO is bound to another IXO source')
        # No durable fact is written until a later explicit Hermes approval.
        workspace_event = self.ixo.activate_set(workspace)
        observation_event = self.ixo.moon('observe', observation)
        interpretation_event = self.ixo.moon('interpret', 'Operator hypothesis: ' + hypothesis)
        proposal = self.ixo.propose(hypothesis, source='user')
        experiment = self.aixo.create_experiment('IXO case: ' + workspace, question)
        evidence = self.capture()
        return {
            'ok': True,
            'workspace': workspace,
            'event_sequences': [workspace_event['seq'], observation_event['seq'], interpretation_event['seq'], proposal['seq']],
            'proposal_id': proposal['id'], 'proposal_status': proposal['status'],
            'experiment_id': experiment['experiment_id'],
            'captured_new': evidence['captured_new'],
            'fact_writes': 0,
            'next': 'Inspect proposal; approve/reject separately. Evaluate experiment against an explicit expected value.',
        }

    @staticmethod
    def probe(text: str) -> dict[str, Any]:
        """Research-only deterministic text probe; no SQLite writes."""
        from frameshift.construct import analyze_text
        if not isinstance(text, str) or not text.strip() or len(text) > 2200:
            raise IXOError('Expected nonempty text of up to 2200 characters')
        return analyze_text(text)
