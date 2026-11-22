"""Local, immutable-at-the-time-of-use excerpt search. Never executes source files."""
from __future__ import annotations
import hashlib
import re
import shutil
from pathlib import Path

ALLOWED = {".md", ".txt"}
STOP = {"what", "does", "how", "there", "with", "which", "that", "this", "into", "from", "their", "about", "could", "would", "also", "when", "then", "while", "were", "have", "your", "they", "over", "need", "goal", "investigate", "between", "while", "through", "working", "computer"}


def tokens(text):
    return {v for v in re.findall(r"[a-z0-9_]+", text.lower()) if (len(v) >= 3 or v.isdigit()) and v not in STOP}


def source_root(root: Path):
    original = Path(root) / "sources"
    if original.is_symlink():
        raise ValueError("Sources directory must not be a symlink")
    p = original.resolve()
    if not p.is_dir():
        raise FileNotFoundError("Missing sources folder")
    return p


def import_source(root: Path, path: Path):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.suffix.lower() not in ALLOWED:
        raise ValueError("Only regular .md or .txt sources are accepted")
    if path.stat().st_size > 256 * 1024:
        raise ValueError("Source exceeds 256 KiB limit")
    source = path.read_bytes()
    try:
        source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Source is not valid UTF-8. Save the .md or .txt file as UTF-8 and try importing it again."
        ) from exc
    dstroot = source_root(root)
    h = hashlib.sha256(source).hexdigest()
    target = dstroot / f"{h[:16]}_{path.name}"
    if target.exists():
        if target.read_bytes() != source:
            raise ValueError("Existing source name conflicts with content")
        return {"name": target.name, "sha256": h, "already_present": True}
    target.write_bytes(source)
    return {"name": target.name, "sha256": h, "already_present": False}


def excerpts(root: Path):
    results = []
    for path in sorted(source_root(root).iterdir())[:128]:
        if path.suffix.lower() not in ALLOWED or not path.is_file() or path.is_symlink():
            continue
        raw = path.read_bytes()
        if len(raw) > 256 * 1024:
            continue
        sha = hashlib.sha256(raw).hexdigest()
        try:
            contents = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"Workspace source {path.name} is not valid UTF-8. Restore a valid source and verify the session."
            ) from exc
        paragraphs = re.split(r"\n\s*\n", contents)
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph or len(paragraph) > 2800:
                continue
            results.append({"id": f"{sha[:16]}:{i}", "file": path.name, "source_sha256": sha,
                            "excerpt_sha256": hashlib.sha256(paragraph.encode("utf-8")).hexdigest(),
                            "text": paragraph, "terms": sorted(tokens(paragraph))})
    return results


def retrieve(root: Path, query: str, already_seen: set[str], limit=3):
    query_tokens = tokens(query)
    scored = []
    for e in excerpts(root):
        if e["id"] in already_seen:
            continue
        common = query_tokens & set(e["terms"])
        if not common:
            continue
        score = len(common) / max(len(query_tokens), 1)
        scored.append((score, len(common), e["id"], e))
    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return [dict(x[3], relevance=round(x[0], 3)) for x in scored[:limit]]


def confirm_excerpt(root: Path, reference: dict):
    # Filename is never trusted as a path. It must match an enumerated local source.
    entries = {e["id"]: e for e in excerpts(root)}
    found = entries.get(reference.get("id"))
    return bool(found and all(found[k] == reference.get(k) for k in ("file", "source_sha256", "excerpt_sha256", "text")))
