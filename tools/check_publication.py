#!/usr/bin/env python3
"""Read-only verifier of OXsukra's public GitHub default-branch publication.

Not a code completeness audit. No tokens, repository writes, or private API calls.
"""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com/repos"


def get_json(url):
    request = Request(url, headers={"User-Agent": "ox-publication-auditor/1", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=12) as reply:
        return json.load(reply)


def audit_repo(owner, record, fetch=get_json):
    name = record["name"]
    base = f"{API}/{quote(owner, safe='')}/{quote(name, safe='')}"
    try:
        repo = fetch(base)
        if repo.get("private") is not False:
            return {"name": name, "state": "NOT_CONFIRMED_PUBLIC"}
        branch = repo["default_branch"]
        contents = fetch(base + "/contents?ref=" + quote(branch, safe=""))
        if not isinstance(contents, list):
            return {"name": name, "state": "UNKNOWN_LAYOUT", "branch": branch}
        filenames = {item["name"] for item in contents}
        expected = record.get("source_paths", [])
        missing = []
        for path in expected:
            try:
                fetch(base + "/contents/" + "/".join(quote(part, safe="") for part in path.split("/")) + "?ref=" + quote(branch, safe=""))
            except HTTPError as exc:
                if exc.code == 404:
                    missing.append(path)
                else:
                    raise
        placeholders = {"README.md", "LICENSE", "LICENSE.md", ".gitignore", "CHECKPOINT_M0_1.md"}
        state = "MISSING_EXPECTED_SOURCE" if missing else (
            "PLACEHOLDER_ONLY" if filenames.issubset(placeholders) else "HAS_OTHER_FILES_UNVERIFIED")
        return {"name": name, "state": state, "branch": branch,
                "missing_source_paths": missing, "root_entries": sorted(filenames)}
    except HTTPError as exc:
        return {"name": name, "state": "HTTP_ERROR", "http_status": exc.code}
    except (URLError, TimeoutError, KeyError, ValueError) as exc:
        return {"name": name, "state": "CHECK_ERROR", "error_type": type(exc).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "PUBLICATION_MANIFEST.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = {"schema": manifest["schema"], "owner": manifest["owner"],
              "scope": "public default branches; metadata only",
              "repositories": [audit_repo(manifest["owner"], item) for item in manifest["repositories"]],
              "unpublished_targets_not_checked": manifest.get("separate_repository_backlog", [])}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
