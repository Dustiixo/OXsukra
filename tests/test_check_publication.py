import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_publication import audit_repo


class PublicationTests(unittest.TestCase):
    def test_public_source_missing_from_default_branch(self):
        def fetch(url):
            if url.endswith("/OXsukra"):
                return {"private": False, "default_branch": "main"}
            if "/contents?" in url:
                return [{"name": "LICENSE"}]
            raise HTTPError(url, 404, "Not Found", {}, None)
        result = audit_repo("Dustiixo", {"name": "OXsukra", "source_paths": ["governance_router/core.py"]}, fetch)
        self.assertEqual(result["state"], "MISSING_EXPECTED_SOURCE")

    def test_placeholder_not_claimed_complete(self):
        def fetch(url):
            if url.endswith("/HermesXO"):
                return {"private": False, "default_branch": "main"}
            return [{"name": "README.md"}]
        result = audit_repo("Dustiixo", {"name": "HermesXO", "source_paths": []}, fetch)
        self.assertEqual(result["state"], "PLACEHOLDER_ONLY")

    def test_private_repo_never_inspected(self):
        calls = []
        def fetch(url):
            calls.append(url)
            return {"private": True, "default_branch": "main"}
        result = audit_repo("Dustiixo", {"name": "secret"}, fetch)
        self.assertEqual(result["state"], "NOT_CONFIRMED_PUBLIC")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
