#!/usr/bin/env python3
"""Build llms.txt and llms/: a plain-text copy of this repository for tools that
read text at a URL rather than cloning (llmstxt.org convention).

    python3 scripts/llms_digest.py           # write llms.txt and llms/
    python3 scripts/llms_digest.py --check   # exit 1 if they don't match the code

.github/workflows/llms-digest.yml runs this on every push to main and commits
the result, so the text always matches the code at the commit it names.
Standard library only.

  llms.txt              index: the README's opening section, then links to everything below
  llms/MAP.md           every tracked file: size, lines, first descriptive line, digest part
  llms/HISTORY.md       commit history, verbatim from git (commits that only regenerate
                        the digest are left out)
  llms/code-N.md        full text of every source and doc file, line-numbered, in parts
                        small enough to fetch whole
  llms/data-samples.md  the first lines of one data file per top-level folder
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PART_CHARS = 120_000
OWN = ("llms.txt", "llms/")  # this script's output: never part of its own input
SKIP_DIRS = {"node_modules", "dist", "build", ".svelte-kit", "__pycache__", ".venv", "venv", ".git", ".next"}
LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock", "Cargo.lock"}
DATA_EXT = {".json", ".jsonl", ".csv", ".tsv", ".parquet", ".npy", ".npz", ".arrow", ".pkl"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf",
              ".zip", ".gz", ".safetensors", ".bin", ".pt", ".onnx", ".mp4", ".mp3", ".wav"}
LANG = {".py": "python", ".ts": "ts", ".js": "js", ".svelte": "svelte", ".tf": "hcl", ".sh": "bash",
        ".md": "markdown", ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".json": "json", ".html": "html",
        ".css": "css", ".txt": "text", ".sql": "sql", ".go": "go", ".rs": "rust"}


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def first_descriptive_line(text: str, ext: str) -> str:
    """A file's own first line of description: a docstring, a leading comment, or a heading."""
    if ext == ".py":
        m = re.search(r'^\s*(?:#![^\n]*\n)?\s*(?:"""|\'\'\')\s*(.+)', text)
        if m:
            return m.group(1).strip().rstrip("\"'")
    for line in text.splitlines()[:15]:
        s = line.strip()
        m = re.match(r"^(?:#{1,6}\s+|//+\s*|#\s*|/\*+\s*|\*\s+|<!--\s*)(.{8,})", s)
        if m and not s.startswith("#!") and not s.startswith("// @ts"):
            return m.group(1).strip().rstrip("*/ -").strip()
    return ""


def classify(path: str, size: int, raw: bytes) -> str:
    name, ext = os.path.basename(path), os.path.splitext(path)[1].lower()
    parts = path.split("/")
    if any(p in SKIP_DIRS for p in parts[:-1]):
        return "skip: generated or vendored directory"
    if name in LOCKFILES:
        return "skip: lockfile"
    if ext in BINARY_EXT or b"\0" in raw[:4096]:
        return "skip: binary"
    if raw.startswith(b"version https://git-lfs"):
        return "skip: Git LFS pointer (content not in the repo)"
    if ext in DATA_EXT and not (len(parts) == 1 and size <= 20_000):  # root configs stay
        return "data: sampled in data-samples.md"
    if size > 200_000:
        return "skip: larger than 200 KB"
    return "include"


def repo_identity(root: Path) -> tuple[str, str, str]:
    """(owner, name, branch) from GitHub Actions, else from the origin remote."""
    full = os.environ.get("GITHUB_REPOSITORY")
    if not full:
        url = git("remote", "get-url", "origin", cwd=root).strip()
        m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
        if not m:
            sys.exit(f"can't tell the GitHub repository from {url!r}; set GITHUB_REPOSITORY=owner/name")
        full = f"{m.group(1)}/{m.group(2)}"
    owner, name = full.split("/", 1)
    branch = os.environ.get("LLMS_BRANCH", "main")
    return owner, name, branch


def build(root: Path, out: Path) -> dict:
    owner, name, branch = repo_identity(root)
    # The last commit that changed anything besides the digest: rebuilding after a
    # digest-only commit then gives identical text, so the workflow never loops.
    code_only = ("--", ".", ":(exclude)llms.txt", ":(exclude)llms")
    sha = git("log", "-1", "--format=%H", *code_only, cwd=root).strip()
    date = git("log", "-1", "--format=%cs", *code_only, cwd=root).strip()
    raw_base = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/"
    files = [f for f in git("ls-files", cwd=root).splitlines() if f and not f.startswith(OWN)]
    stamp = (f"Generated from commit `{sha[:12]}` ({date}) of github.com/{owner}/{name} by "
             f"`scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to "
             f"`{branch}`, so this text matches the code at that commit.")

    rows, included, data_dirs = [], [], {}
    for f in files:
        raw = (root / f).read_bytes()
        verdict = classify(f, len(raw), raw)
        ext = os.path.splitext(f)[1].lower()
        text = "" if verdict == "skip: binary" else raw.decode("utf-8", "replace")
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        desc = first_descriptive_line(text, ext) if verdict == "include" else ""
        rows.append((f, len(raw), lines, desc, verdict))
        if verdict == "include":
            included.append((f, text, ext))
        elif verdict.startswith("data"):
            data_dirs.setdefault(f.split("/")[0] if "/" in f else "(root)", []).append((f, text))

    # Parts: whole files in path order, never split across parts.
    parts, cur, cur_len = [], [], 0
    for f, text, ext in included:
        numbered = "\n".join(f"{i:>5}| {l}" for i, l in enumerate(text.splitlines(), 1))
        block = f"\n## `{f}`\n\n```{LANG.get(ext, '')}\n{numbered}\n```\n"
        if cur and cur_len + len(block) > PART_CHARS:
            parts.append(cur)
            cur, cur_len = [], 0
        cur.append((f, block))
        cur_len += len(block)
    if cur:
        parts.append(cur)

    (out / "llms").mkdir(parents=True, exist_ok=True)
    part_index, file_part = [], {}
    for i, part in enumerate(parts, 1):
        fname = f"llms/code-{i}.md"
        body = "".join(b for _, b in part)
        (out / fname).write_text(
            f"# {name}: source and docs, part {i} of {len(parts)}\n\n{stamp}\nFiles `{part[0][0]}` to "
            f"`{part[-1][0]}`. Lines are numbered as in the repository.\n" + body)
        part_index.append((fname, part[0][0], part[-1][0], len(part), len(body)))
        for f, _ in part:
            file_part[f] = f"code-{i}.md"

    m = [f"# {name}: file map", "", stamp, "",
         f"{len(files)} tracked files. {len(included)} are reproduced in full in the `code-N.md` parts; "
         "the rest are listed with the reason they are not.", "",
         f"Every path below is relative to {raw_base} (append the path to fetch the raw file).", "",
         "| File | Bytes | Lines | Description | In digest |", "|---|---|---|---|---|"]
    for f, size, lines, desc, verdict in rows:
        if not verdict.startswith("data"):
            m.append(f"| `{f}` | {size:,} | {lines:,} | {desc.replace('|', '/')[:100]} | {file_part.get(f, verdict)} |")
    if data_dirs:
        m += ["", "### Data files (not reproduced; one sample per folder in `data-samples.md`)", "",
              "| Folder | Files | Bytes |", "|---|---|---|"]
        sizes = {r[0]: r[1] for r in rows}
        for d, items in sorted(data_dirs.items()):
            m.append(f"| `{d}/` | {len(items)} | {sum(sizes[f] for f, _ in items):,} |")
    (out / "llms" / "MAP.md").write_text("\n".join(m) + "\n")

    if data_dirs:
        ds = [f"# {name}: data samples", "", stamp, "",
              "Data files are not reproduced in full. One sample per top-level folder, first 40 lines:", ""]
        for d, items in sorted(data_dirs.items()):
            f, text = items[0]
            sample = "\n".join(text.splitlines()[:40])
            ds += [f"## `{d}/` ({len(items)} files)", "", f"Sample: `{f}`", "",
                   f"```{LANG.get(os.path.splitext(f)[1].lower(), '')}\n{sample}\n```", ""]
        (out / "llms" / "data-samples.md").write_text("\n".join(ds))

    # Commits that touched anything besides the digest itself, verbatim.
    log = git("log", "--format=%h  %ad  %an  %s", "--date=short", "--", ".", ":(exclude)llms.txt", ":(exclude)llms",
              cwd=root).strip()
    count = len(log.splitlines()) if log else 0
    (out / "llms" / "HISTORY.md").write_text(
        f"# {name}: commit history\n\n{stamp}\n\n{count} commit(s), verbatim from `git log` "
        f"(commits that only regenerate this digest are left out):\n\n```\n{log}\n```\n")

    readme = next((f for f in files if f.lower() == "readme.md"), None)
    total = sum(p[4] for p in part_index)
    idx = [f"# {name}", ""]
    if readme:
        intro = re.split(r"(?m)^##\s", (root / readme).read_text(errors="replace"))[0]
        intro = re.sub(r"(?m)^#\s.*\n", "", intro).strip()
        if intro:
            idx += ["## Summary (the README's opening section, verbatim)", "", intro[:3000], ""]
    idx += [stamp, "", "## Start here", ""]
    if readme:
        idx.append(f"- [README]({raw_base}{readme}): overview")
    idx += [f"- [File map]({raw_base}llms/MAP.md): all {len(files)} files with size, line count, description, "
            "and which digest part holds each one",
            f"- [Commit history]({raw_base}llms/HISTORY.md): {count} commit(s)", ""]
    docs = [r[0] for r in rows if r[0].lower().endswith(".md") and r[0] != readme]
    if docs:
        idx += ["## Documentation", ""] + [f"- [{d}]({raw_base}{d})" for d in docs[:30]] + [""]
    idx += [f"## Full source text ({total:,} characters, about {total // 4:,} tokens, in {len(part_index)} part(s))", ""]
    idx += [f"- [{fn}]({raw_base}{fn}): {n} files, `{a}` to `{b}` ({size:,} characters)"
            for fn, a, b, n, size in part_index]
    if data_dirs:
        idx += ["", "## Data", "", f"- [Data samples]({raw_base}llms/data-samples.md): "
                f"{sum(len(v) for v in data_dirs.values())} data files in {len(data_dirs)} folder(s), one sample each"]
    (out / "llms.txt").write_text("\n".join(idx) + "\n")
    return {"files": len(files), "included": len(included), "parts": len(part_index), "chars": total}


def snapshot(d: Path) -> dict[str, str]:
    out = {}
    if (d / "llms.txt").exists():
        out["llms.txt"] = (d / "llms.txt").read_text()
    for p in sorted((d / "llms").glob("*")) if (d / "llms").is_dir() else []:
        out[f"llms/{p.name}"] = p.read_text()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if llms.txt and llms/ don't match the code")
    args = ap.parse_args()
    root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
    tmp = Path(tempfile.mkdtemp(prefix="llms-digest-"))
    try:
        stats = build(root, tmp)
        fresh = snapshot(tmp)
        if args.check:
            # The stamp names a commit; compare everything else.
            norm = lambda d: {k: re.sub(r"commit `[0-9a-f]{12}` \(\d{4}-\d\d-\d\d\)", "commit", v) for k, v in d.items()}
            if norm(fresh) != norm(snapshot(root)):
                sys.exit("llms.txt / llms/ don't match the code. Run: python3 scripts/llms_digest.py")
            print("llms.txt and llms/ match the code.")
            return
        shutil.rmtree(root / "llms", ignore_errors=True)
        (root / "llms").mkdir()
        for rel, text in fresh.items():
            (root / rel).write_text(text)
        print(f"{stats['included']} of {stats['files']} files in {stats['parts']} part(s), {stats['chars']:,} characters.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
