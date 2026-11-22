"""Opt-in local engineering worker. No dependency, network, or memory writes."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

class EngineeringWorker:
    def __init__(self, executable='opencode'):
        self.executable = executable

    def status(self):
        path = shutil.which(self.executable)
        return {'installed': bool(path), 'executable': path, 'provider': 'opencode',
                'execution_enabled': False, 'mode': 'explicit-only'}

    def run(self, prompt, workspace, *, approve=False, timeout=120):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt)>6000:
            raise ValueError('A task between 1 and 6000 characters is required')
        directory = Path(workspace).expanduser().resolve(strict=True)
        if not directory.is_dir():
            raise ValueError('Workspace must be a directory')
        if not approve:
            return {'ok': False, 'requires_approval': True, 'workspace': str(directory),
                    'command_preview': ['opencode', 'run', prompt]}
        exe = shutil.which(self.executable)
        if not exe:
            return {'ok': False, 'error': 'OpenCode executable not installed'}
        try:
            p = subprocess.run([exe, 'run', prompt], cwd=directory, capture_output=True,
                               text=True, timeout=max(1,min(int(timeout),600)), check=False)
            return {'ok': p.returncode == 0, 'exit_code': p.returncode,
                    'stdout': p.stdout[-20000:], 'stderr': p.stderr[-5000:],
                    'workspace': str(directory), 'memory_written': False}
        except subprocess.TimeoutExpired:
            return {'ok': False, 'error': 'Worker timed out', 'memory_written': False}
