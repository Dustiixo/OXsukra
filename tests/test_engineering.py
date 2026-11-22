import tempfile
import unittest
from ixo.engineering import EngineeringWorker

class WorkerTests(unittest.TestCase):
    def test_no_implicit_execution(self):
        with tempfile.TemporaryDirectory() as d:
            result = EngineeringWorker().run('inspect code', d)
            self.assertTrue(result['requires_approval'])
    def test_bad_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                EngineeringWorker().run('', d)
    def test_missing_binary(self):
        with tempfile.TemporaryDirectory() as d:
            result=EngineeringWorker('nonexistent-ixo-worker-239').run('inspect',d,approve=True)
            self.assertFalse(result['ok'])
