# simulacra-americana: source and docs, part 6 of 17

Generated from commit `6f14dc41b9fa` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `scripts/llms_digest.py` to `simharness/__init__.py`. Lines are numbered as in the repository.

## `scripts/llms_digest.py`

```python
    1| #!/usr/bin/env python3
    2| """Build llms.txt and llms/: a plain-text copy of this repository for tools that
    3| read text at a URL rather than cloning (llmstxt.org convention).
    4| 
    5|     python3 scripts/llms_digest.py           # write llms.txt and llms/
    6|     python3 scripts/llms_digest.py --check   # exit 1 if they don't match the code
    7| 
    8| .github/workflows/llms-digest.yml runs this on every push to main and commits
    9| the result, so the text always matches the code at the commit it names.
   10| Standard library only.
   11| 
   12|   llms.txt              index: the README's opening section, then links to everything below
   13|   llms/MAP.md           every tracked file: size, lines, first descriptive line, digest part
   14|   llms/HISTORY.md       commit history, verbatim from git (commits that only regenerate
   15|                         the digest are left out)
   16|   llms/code-N.md        full text of every source and doc file, line-numbered, in parts
   17|                         small enough to fetch whole
   18|   llms/data-samples.md  the first lines of one data file per top-level folder
   19| """
   20| from __future__ import annotations
   21| 
   22| import argparse
   23| import os
   24| import re
   25| import shutil
   26| import subprocess
   27| import sys
   28| import tempfile
   29| from pathlib import Path
   30| 
   31| PART_CHARS = 120_000
   32| OWN = ("llms.txt", "llms/")  # this script's output: never part of its own input
   33| SKIP_DIRS = {"node_modules", "dist", "build", ".svelte-kit", "__pycache__", ".venv", "venv", ".git", ".next"}
   34| LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock", "Cargo.lock"}
   35| DATA_EXT = {".json", ".jsonl", ".csv", ".tsv", ".parquet", ".npy", ".npz", ".arrow", ".pkl"}
   36| BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf",
   37|               ".zip", ".gz", ".safetensors", ".bin", ".pt", ".onnx", ".mp4", ".mp3", ".wav"}
   38| LANG = {".py": "python", ".ts": "ts", ".js": "js", ".svelte": "svelte", ".tf": "hcl", ".sh": "bash",
   39|         ".md": "markdown", ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".json": "json", ".html": "html",
   40|         ".css": "css", ".txt": "text", ".sql": "sql", ".go": "go", ".rs": "rust"}
   41| 
   42| 
   43| def git(*args: str, cwd: Path) -> str:
   44|     return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout
   45| 
   46| 
   47| def first_descriptive_line(text: str, ext: str) -> str:
   48|     """A file's own first line of description: a docstring, a leading comment, or a heading."""
   49|     if ext == ".py":
   50|         m = re.search(r'^\s*(?:#![^\n]*\n)?\s*(?:"""|\'\'\')\s*(.+)', text)
   51|         if m:
   52|             return m.group(1).strip().rstrip("\"'")
   53|     for line in text.splitlines()[:15]:
   54|         s = line.strip()
   55|         m = re.match(r"^(?:#{1,6}\s+|//+\s*|#\s*|/\*+\s*|\*\s+|<!--\s*)(.{8,})", s)
   56|         if m and not s.startswith("#!") and not s.startswith("// @ts"):
   57|             return m.group(1).strip().rstrip("*/ -").strip()
   58|     return ""
   59| 
   60| 
   61| def classify(path: str, size: int, raw: bytes) -> str:
   62|     name, ext = os.path.basename(path), os.path.splitext(path)[1].lower()
   63|     parts = path.split("/")
   64|     if any(p in SKIP_DIRS for p in parts[:-1]):
   65|         return "skip: generated or vendored directory"
   66|     if name in LOCKFILES:
   67|         return "skip: lockfile"
   68|     if ext in BINARY_EXT or b"\0" in raw[:4096]:
   69|         return "skip: binary"
   70|     if raw.startswith(b"version https://git-lfs"):
   71|         return "skip: Git LFS pointer (content not in the repo)"
   72|     if ext in DATA_EXT and not (len(parts) == 1 and size <= 20_000):  # root configs stay
   73|         return "data: sampled in data-samples.md"
   74|     if size > 200_000:
   75|         return "skip: larger than 200 KB"
   76|     return "include"
   77| 
   78| 
   79| def repo_identity(root: Path) -> tuple[str, str, str]:
   80|     """(owner, name, branch) from GitHub Actions, else from the origin remote."""
   81|     full = os.environ.get("GITHUB_REPOSITORY")
   82|     if not full:
   83|         url = git("remote", "get-url", "origin", cwd=root).strip()
   84|         m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
   85|         if not m:
   86|             sys.exit(f"can't tell the GitHub repository from {url!r}; set GITHUB_REPOSITORY=owner/name")
   87|         full = f"{m.group(1)}/{m.group(2)}"
   88|     owner, name = full.split("/", 1)
   89|     branch = os.environ.get("LLMS_BRANCH", "main")
   90|     return owner, name, branch
   91| 
   92| 
   93| def build(root: Path, out: Path) -> dict:
   94|     owner, name, branch = repo_identity(root)
   95|     # The last commit that changed anything besides the digest: rebuilding after a
   96|     # digest-only commit then gives identical text, so the workflow never loops.
   97|     code_only = ("--", ".", ":(exclude)llms.txt", ":(exclude)llms")
   98|     sha = git("log", "-1", "--format=%H", *code_only, cwd=root).strip()
   99|     date = git("log", "-1", "--format=%cs", *code_only, cwd=root).strip()
  100|     raw_base = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/"
  101|     files = [f for f in git("ls-files", cwd=root).splitlines() if f and not f.startswith(OWN)]
  102|     stamp = (f"Generated from commit `{sha[:12]}` ({date}) of github.com/{owner}/{name} by "
  103|              f"`scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to "
  104|              f"`{branch}`, so this text matches the code at that commit.")
  105| 
  106|     rows, included, data_dirs = [], [], {}
  107|     for f in files:
  108|         raw = (root / f).read_bytes()
  109|         verdict = classify(f, len(raw), raw)
  110|         ext = os.path.splitext(f)[1].lower()
  111|         text = "" if verdict == "skip: binary" else raw.decode("utf-8", "replace")
  112|         lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
  113|         desc = first_descriptive_line(text, ext) if verdict == "include" else ""
  114|         rows.append((f, len(raw), lines, desc, verdict))
  115|         if verdict == "include":
  116|             included.append((f, text, ext))
  117|         elif verdict.startswith("data"):
  118|             data_dirs.setdefault(f.split("/")[0] if "/" in f else "(root)", []).append((f, text))
  119| 
  120|     # Parts: whole files in path order, never split across parts.
  121|     parts, cur, cur_len = [], [], 0
  122|     for f, text, ext in included:
  123|         numbered = "\n".join(f"{i:>5}| {l}" for i, l in enumerate(text.splitlines(), 1))
  124|         block = f"\n## `{f}`\n\n```{LANG.get(ext, '')}\n{numbered}\n```\n"
  125|         if cur and cur_len + len(block) > PART_CHARS:
  126|             parts.append(cur)
  127|             cur, cur_len = [], 0
  128|         cur.append((f, block))
  129|         cur_len += len(block)
  130|     if cur:
  131|         parts.append(cur)
  132| 
  133|     (out / "llms").mkdir(parents=True, exist_ok=True)
  134|     part_index, file_part = [], {}
  135|     for i, part in enumerate(parts, 1):
  136|         fname = f"llms/code-{i}.md"
  137|         body = "".join(b for _, b in part)
  138|         (out / fname).write_text(
  139|             f"# {name}: source and docs, part {i} of {len(parts)}\n\n{stamp}\nFiles `{part[0][0]}` to "
  140|             f"`{part[-1][0]}`. Lines are numbered as in the repository.\n" + body)
  141|         part_index.append((fname, part[0][0], part[-1][0], len(part), len(body)))
  142|         for f, _ in part:
  143|             file_part[f] = f"code-{i}.md"
  144| 
  145|     m = [f"# {name}: file map", "", stamp, "",
  146|          f"{len(files)} tracked files. {len(included)} are reproduced in full in the `code-N.md` parts; "
  147|          "the rest are listed with the reason they are not.", "",
  148|          f"Every path below is relative to {raw_base} (append the path to fetch the raw file).", "",
  149|          "| File | Bytes | Lines | Description | In digest |", "|---|---|---|---|---|"]
  150|     for f, size, lines, desc, verdict in rows:
  151|         if not verdict.startswith("data"):
  152|             m.append(f"| `{f}` | {size:,} | {lines:,} | {desc.replace('|', '/')[:100]} | {file_part.get(f, verdict)} |")
  153|     if data_dirs:
  154|         m += ["", "### Data files (not reproduced; one sample per folder in `data-samples.md`)", "",
  155|               "| Folder | Files | Bytes |", "|---|---|---|"]
  156|         sizes = {r[0]: r[1] for r in rows}
  157|         for d, items in sorted(data_dirs.items()):
  158|             m.append(f"| `{d}/` | {len(items)} | {sum(sizes[f] for f, _ in items):,} |")
  159|     (out / "llms" / "MAP.md").write_text("\n".join(m) + "\n")
  160| 
  161|     if data_dirs:
  162|         ds = [f"# {name}: data samples", "", stamp, "",
  163|               "Data files are not reproduced in full. One sample per top-level folder, first 40 lines:", ""]
  164|         for d, items in sorted(data_dirs.items()):
  165|             f, text = items[0]
  166|             sample = "\n".join(text.splitlines()[:40])
  167|             ds += [f"## `{d}/` ({len(items)} files)", "", f"Sample: `{f}`", "",
  168|                    f"```{LANG.get(os.path.splitext(f)[1].lower(), '')}\n{sample}\n```", ""]
  169|         (out / "llms" / "data-samples.md").write_text("\n".join(ds))
  170| 
  171|     # Commits that touched anything besides the digest itself, verbatim.
  172|     log = git("log", "--format=%h  %ad  %an  %s", "--date=short", "--", ".", ":(exclude)llms.txt", ":(exclude)llms",
  173|               cwd=root).strip()
  174|     count = len(log.splitlines()) if log else 0
  175|     (out / "llms" / "HISTORY.md").write_text(
  176|         f"# {name}: commit history\n\n{stamp}\n\n{count} commit(s), verbatim from `git log` "
  177|         f"(commits that only regenerate this digest are left out):\n\n```\n{log}\n```\n")
  178| 
  179|     readme = next((f for f in files if f.lower() == "readme.md"), None)
  180|     total = sum(p[4] for p in part_index)
  181|     idx = [f"# {name}", ""]
  182|     if readme:
  183|         intro = re.split(r"(?m)^##\s", (root / readme).read_text(errors="replace"))[0]
  184|         intro = re.sub(r"(?m)^#\s.*\n", "", intro).strip()
  185|         if intro:
  186|             idx += ["## Summary (the README's opening section, verbatim)", "", intro[:3000], ""]
  187|     idx += [stamp, "", "## Start here", ""]
  188|     if readme:
  189|         idx.append(f"- [README]({raw_base}{readme}): overview")
  190|     idx += [f"- [File map]({raw_base}llms/MAP.md): all {len(files)} files with size, line count, description, "
  191|             "and which digest part holds each one",
  192|             f"- [Commit history]({raw_base}llms/HISTORY.md): {count} commit(s)", ""]
  193|     docs = [r[0] for r in rows if r[0].lower().endswith(".md") and r[0] != readme]
  194|     if docs:
  195|         idx += ["## Documentation", ""] + [f"- [{d}]({raw_base}{d})" for d in docs[:30]] + [""]
  196|     idx += [f"## Full source text ({total:,} characters, about {total // 4:,} tokens, in {len(part_index)} part(s))", ""]
  197|     idx += [f"- [{fn}]({raw_base}{fn}): {n} files, `{a}` to `{b}` ({size:,} characters)"
  198|             for fn, a, b, n, size in part_index]
  199|     if data_dirs:
  200|         idx += ["", "## Data", "", f"- [Data samples]({raw_base}llms/data-samples.md): "
  201|                 f"{sum(len(v) for v in data_dirs.values())} data files in {len(data_dirs)} folder(s), one sample each"]
  202|     (out / "llms.txt").write_text("\n".join(idx) + "\n")
  203|     return {"files": len(files), "included": len(included), "parts": len(part_index), "chars": total}
  204| 
  205| 
  206| def snapshot(d: Path) -> dict[str, str]:
  207|     out = {}
  208|     if (d / "llms.txt").exists():
  209|         out["llms.txt"] = (d / "llms.txt").read_text()
  210|     for p in sorted((d / "llms").glob("*")) if (d / "llms").is_dir() else []:
  211|         out[f"llms/{p.name}"] = p.read_text()
  212|     return out
  213| 
  214| 
  215| def main() -> None:
  216|     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  217|     ap.add_argument("--check", action="store_true", help="exit 1 if llms.txt and llms/ don't match the code")
  218|     args = ap.parse_args()
  219|     root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
  220|     tmp = Path(tempfile.mkdtemp(prefix="llms-digest-"))
  221|     try:
  222|         stats = build(root, tmp)
  223|         fresh = snapshot(tmp)
  224|         if args.check:
  225|             # The stamp names a commit; compare everything else.
  226|             norm = lambda d: {k: re.sub(r"commit `[0-9a-f]{12}` \(\d{4}-\d\d-\d\d\)", "commit", v) for k, v in d.items()}
  227|             if norm(fresh) != norm(snapshot(root)):
  228|                 sys.exit("llms.txt / llms/ don't match the code. Run: python3 scripts/llms_digest.py")
  229|             print("llms.txt and llms/ match the code.")
  230|             return
  231|         shutil.rmtree(root / "llms", ignore_errors=True)
  232|         (root / "llms").mkdir()
  233|         for rel, text in fresh.items():
  234|             (root / rel).write_text(text)
  235|         print(f"{stats['included']} of {stats['files']} files in {stats['parts']} part(s), {stats['chars']:,} characters.")
  236|     finally:
  237|         shutil.rmtree(tmp, ignore_errors=True)
  238| 
  239| 
  240| if __name__ == "__main__":
  241|     main()
```

## `scripts/mirror-portraits.py`

```python
    1| #!/usr/bin/env python3
    2| """Mirror the candidates' Wikimedia Commons portraits for the assets bucket.
    3| 
    4| For every person in src/lib/simulacra/history.ts (PEOPLE), resolve the Commons
    5| file through the Commons API (prop=imageinfo, iiprop=url|extmetadata), download
    6| its 330px thumbnail to <out>/portraits/<id>.jpg, and write
    7| <out>/portraits/credits.json with the file page, author, licence name and
    8| licence URL exactly as the API gives them (never guessed).
    9| 
   10| The output stays out of git; scripts/publish-assets.sh uploads it.
   11| Re-runnable: existing images are kept unless --force.
   12| 
   13|   python3 scripts/mirror-portraits.py --out ../simulacra-assets
   14| """
   15| from __future__ import annotations
   16| 
   17| import argparse
   18| import html
   19| import json
   20| import re
   21| import sys
   22| import time
   23| import urllib.parse
   24| import urllib.request
   25| from pathlib import Path
   26| 
   27| ROOT = Path(__file__).resolve().parent.parent
   28| HISTORY = ROOT / 'src/lib/simulacra/history.ts'
   29| API = 'https://commons.wikimedia.org/w/api.php'
   30| # Wikimedia's User-Agent policy: identify the tool and a contact.
   31| UA = 'SimulacraAmericana-portrait-mirror/1.0 (https://simulacraamericana.com; cam@partyhat.ai)'
   32| WIDTH = 330
   33| 
   34| # `  id: ["Full Name", "Surname", "x/xy/File.jpg/330px-File.jpg"],` inside PEOPLE.
   35| ROW = re.compile(r'^\s*(\w+):\s*\["([^"]+)",\s*"[^"]*",\s*"([^"]+)"\]', re.M)
   36| 
   37| 
   38| def people() -> list[tuple[str, str, str]]:
   39|     src = HISTORY.read_text()
   40|     block = src[src.index('const PEOPLE = {'):]
   41|     block = block[:block.index('\n}')]
   42|     rows = []
   43|     for pid, name, path in ROW.findall(block):
   44|         # "b/b6/<File>/330px-<File>": the Commons file name is the third segment.
   45|         rows.append((pid, name, urllib.parse.unquote(path.split('/')[2])))
   46|     if not rows:
   47|         sys.exit(f'no PEOPLE rows parsed from {HISTORY}')
   48|     return rows
   49| 
   50| 
   51| def get(url: str) -> bytes:
   52|     req = urllib.request.Request(url, headers={'User-Agent': UA})
   53|     for attempt in range(4):
   54|         try:
   55|             with urllib.request.urlopen(req, timeout=30) as r:
   56|                 return r.read()
   57|         except urllib.error.HTTPError as e:
   58|             if e.code in (429, 503) and attempt < 3:
   59|                 time.sleep(2 ** attempt * 2)
   60|                 continue
   61|             raise
   62|     raise RuntimeError('unreachable')
   63| 
   64| 
   65| def plain(value: str | None) -> str | None:
   66|     """extmetadata values are HTML fragments; keep their text."""
   67|     if not value:
   68|         return None
   69|     return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', value))).strip() or None
   70| 
   71| 
   72| def imageinfo(titles: list[str]) -> dict[str, dict]:
   73|     q = urllib.parse.urlencode({
   74|         'action': 'query', 'format': 'json', 'formatversion': '2', 'prop': 'imageinfo',
   75|         'iiprop': 'url|extmetadata', 'iiurlwidth': WIDTH, 'titles': '|'.join(f'File:{t}' for t in titles),
   76|     })
   77|     data = json.loads(get(f'{API}?{q}'))
   78|     # The API normalises titles (underscores -> spaces); map back.
   79|     norm = {n['to']: n['from'] for n in data['query'].get('normalized', [])}
   80|     out = {}
   81|     for page in data['query']['pages']:
   82|         asked = norm.get(page['title'], page['title'])
   83|         out[asked.removeprefix('File:')] = page
   84|     return out
   85| 
   86| 
   87| def main() -> None:
   88|     ap = argparse.ArgumentParser()
   89|     ap.add_argument('--out', type=Path, required=True, help='assets staging folder (outside the repo)')
   90|     ap.add_argument('--force', action='store_true', help='re-download images that already exist')
   91|     args = ap.parse_args()
   92|     dest = args.out / 'portraits'
   93|     dest.mkdir(parents=True, exist_ok=True)
   94| 
   95|     rows = people()
   96|     pages: dict[str, dict] = {}
   97|     files = sorted({f for _, _, f in rows})
   98|     for i in range(0, len(files), 40):  # the API takes 50 titles per query
   99|         pages.update(imageinfo(files[i:i + 40]))
  100| 
  101|     credits, problems = {}, []
  102|     for pid, name, file in rows:
  103|         page = pages.get(file)
  104|         info = (page or {}).get('imageinfo', [None])[0]
  105|         if not info:
  106|             problems.append(f'{pid}: {file} not found on Commons')
  107|             continue
  108|         meta = info.get('extmetadata', {})
  109|         val = lambda k: plain(meta.get(k, {}).get('value'))  # noqa: E731
  110|         target = dest / f'{pid}.jpg'
  111|         if args.force or not target.exists():
  112|             target.write_bytes(get(info['thumburl']))
  113|             time.sleep(0.2)
  114|         credits[pid] = {
  115|             'name': name,
  116|             'file': f'File:{file}',
  117|             'filePage': info['descriptionurl'],
  118|             'author': val('Artist'),
  119|             'credit': val('Credit'),
  120|             'license': val('LicenseShortName'),
  121|             'licenseUrl': val('LicenseUrl'),
  122|             'attributionRequired': val('AttributionRequired') == 'true',
  123|             'usageTerms': val('UsageTerms'),
  124|         }
  125|         lic = credits[pid]['license'] or ''
  126|         if credits[pid]['attributionRequired'] and not credits[pid]['author']:
  127|             problems.append(f'{pid}: {lic} requires attribution but the API gives no author')
  128| 
  129|     (dest / 'credits.json').write_text(json.dumps(credits, indent=2, ensure_ascii=False) + '\n')
  130|     needs = sorted(p for p, c in credits.items() if c['attributionRequired'])
  131|     print(f'{len(credits)}/{len(rows)} portraits mirrored to {dest}')
  132|     print(f'{len(needs)} need attribution: {", ".join(needs) or "none"}')
  133|     for p in problems:
  134|         print('PROBLEM', p, file=sys.stderr)
  135|     sys.exit(1 if problems else 0)
  136| 
  137| 
  138| if __name__ == '__main__':
  139|     main()
```

## `scripts/model-check.ts`

```ts
    1| // Prints the sample model's outcome for every what-if of every story
    2| // election (src/lib/simulacra/stories.ts), to check the model outside the
    3| // page: history's electoral vote, then each what-if's.
    4| //   pnpm tsx scripts/model-check.ts
    5| import { electionOf } from '../src/lib/simulacra/history';
    6| import { _model } from '../src/lib/simulacra/sample';
    7| import { STORIES } from '../src/lib/simulacra/stories';
    8| 
    9| const ev = (r: { ev: { A: number; B: number; O: number } }) => `${r.ev.A}–${r.ev.B}${r.ev.O ? `–${r.ev.O}` : ''}`;
   10| 
   11| for (const year of Object.keys(STORIES).map(Number)) {
   12|   const e = electionOf(year);
   13|   const history = _model.rerun(year);
   14|   if (!e || !history) continue;
   15|   const [a, b] = e.candidates;
   16|   console.log(`\n${year}  ${a.short} over ${b?.short ?? 'no one'}: ${ev(history)} as it happened`);
   17|   for (const w of _model.whatIfsFor(year)) {
   18|     const r = _model.rerun(year, [w.key]);
   19|     if (!r) continue;
   20|     const flips = r.states.filter((s) => s.flipped).length;
   21|     const winner = r.winner ? (e.candidates.find((c) => c.key === r.winner)?.short ?? 'Others') : 'no majority';
   22|     console.log(`  ${w.key.padEnd(14)} ${ev(r).padEnd(12)} ${winner.padEnd(12)} ${String(flips).padStart(2)} flipped  (${r.confidence})`);
   23|   }
   24| }
```

## `scripts/publish-assets.sh`

```bash
    1| #!/usr/bin/env bash
    2| # Publish the robot assets and mirrored portraits to s3://simulacra-americana-assets
    3| # (served by CloudFront at assets.simulacraamericana.com) and invalidate.
    4| # Re-runnable. The assets themselves are never in git.
    5| #
    6| #   scripts/publish-assets.sh [assets-dir]     default ../simulacra-assets
    7| #
    8| # Robot: COPIED (never moved) from the shared Partyhat bucket, only what the
    9| # page loads (src/lib/robot: models/atlas-09-americana.glb and its rerun paint
   10| # set). Portraits: from scripts/mirror-portraits.py's output.
   11| set -euo pipefail
   12| 
   13| SRC="s3://${SOURCE_ASSETS_BUCKET:?set SOURCE_ASSETS_BUCKET to the bucket holding the source harness assets}/harness-assets"
   14| DST=s3://simulacra-americana-assets
   15| ASSETS=${1:-$(cd "$(dirname "$0")/.." && pwd)/../simulacra-assets}
   16| LONG='public, max-age=31536000, immutable'
   17| test "$(aws sts get-caller-identity --query Account --output text)" = "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID to the target AWS account}"
   18| 
   19| # Robot model and paint set (object-to-object copy, same account).
   20| aws s3 cp "$SRC/models/atlas-09-americana.glb" "$DST/models/atlas-09-americana.glb" \
   21|   --metadata-directive REPLACE --content-type model/gltf-binary --cache-control "$LONG" --only-show-errors
   22| aws s3 cp "$SRC/models/atlas-09-americana-rerun/" "$DST/models/atlas-09-americana-rerun/" --recursive \
   23|   --metadata-directive REPLACE --cache-control "$LONG" --only-show-errors
   24| # --metadata-directive REPLACE drops the source content types; restore them.
   25| for k in $(aws s3api list-objects-v2 --bucket simulacra-americana-assets --prefix models/atlas-09-americana-rerun/ \
   26|              --query 'Contents[].Key' --output text); do
   27|   case "$k" in
   28|     *.json) ct=application/json ;; *.png) ct=image/png ;; *.jpg|*.jpeg) ct=image/jpeg ;;
   29|     *.webp) ct=image/webp ;; *.ktx2) ct=image/ktx2 ;; *) continue ;;
   30|   esac
   31|   aws s3 cp "$DST/$k" "$DST/$k" --metadata-directive REPLACE --content-type "$ct" \
   32|     --cache-control "$LONG" --only-show-errors
   33| done
   34| 
   35| # Portraits and their credits (credits change when a portrait does: short cache).
   36| if [ -d "$ASSETS/portraits" ]; then
   37|   aws s3 sync "$ASSETS/portraits/" "$DST/portraits/" --exclude '*' --include '*.jpg' \
   38|     --content-type image/jpeg --cache-control "$LONG" --only-show-errors
   39|   aws s3 cp "$ASSETS/portraits/credits.json" "$DST/portraits/credits.json" \
   40|     --content-type application/json --cache-control 'public, max-age=3600' --only-show-errors
   41| else
   42|   echo "no $ASSETS/portraits; run scripts/mirror-portraits.py --out $ASSETS first" >&2
   43| fi
   44| 
   45| aws s3 ls "$DST/" --recursive --summarize | tail -2
   46| 
   47| # Invalidate (the distribution exists only after the stand-up apply).
   48| DIST=$(cd "$(dirname "$0")/../infra" && terraform output -raw assets_distribution_id 2>/dev/null || true)
   49| if [ -n "$DIST" ]; then
   50|   aws cloudfront create-invalidation --distribution-id "$DIST" --paths '/*' \
   51|     --query 'Invalidation.[Id,Status]' --output text
   52| fi
```

## `scripts/size-check.ts`

```ts
    1| // Fails when any tracked source file is over the line limit.
    2| import { execFileSync } from 'node:child_process';
    3| import { readFileSync } from 'node:fs';
    4| 
    5| const LIMIT = 1000;
    6| const SOURCE = /\.(ts|svelte|js|mjs|py|css)$/;
    7| 
    8| const files = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard'], { encoding: 'utf8' })
    9|   .split('\n')
   10|   .filter((f) => SOURCE.test(f));
   11| 
   12| const over = files
   13|   .map((f) => ({ f, n: readFileSync(f, 'utf8').split('\n').length }))
   14|   .filter(({ n }) => n > LIMIT);
   15| 
   16| for (const { f, n } of over) console.error(`${f}: ${n} lines (limit ${LIMIT})`);
   17| if (over.length > 0) process.exit(1);
   18| console.log(`size: ${files.length} files, none over ${LIMIT} lines`);
```

## `scripts/sync-data.sh`

```bash
    1| #!/usr/bin/env bash
    2| # Census-derived data and service state: laptop -> private data bucket -> EFS.
    3| # Re-runnable. Nothing here ever writes to git, an image, Vercel or the assets bucket.
    4| #
    5| #   scripts/sync-data.sh upload-cache   laptop harness_cache (minus */raw/) -> s3://.../cache/
    6| #   scripts/sync-data.sh upload-seed    repo bundles/whatifs/configs/runs + laptop runs/_cache -> s3://.../seed/
    7| #   scripts/sync-data.sh seed           one-off ECS task: seed -> EFS (refuses if already seeded)
    8| #   scripts/sync-data.sh cache          one-off ECS task: cache -> EFS/cache (replaces it)
    9| #   scripts/sync-data.sh backup         tarball the laptop's harness state + cache to s3://.../backups/<date>/
   10| #
   11| # The run id hashes the cache's manifest: the bytes on EFS must match the
   12| # laptop's for run ids to line up, so the cache is synced byte-for-byte.
   13| #
   14| # Note: on aws-cli 2.23.4 (this laptop) `aws s3 cp` of a multipart object
   15| # DOWN from this versioned bucket fails with NoSuchKey; `aws s3api get-object`
   16| # works. Uploads and small-file syncs are unaffected.
   17| set -euo pipefail
   18| 
   19| B=s3://simulacra-americana-data
   20| REPO=$(cd "$(dirname "$0")/.." && pwd)
   21| CACHE=${SIMHARNESS_CACHE:-$HOME/research_notes/historical_election_sim_data/harness_cache}
   22| # The live harness the laptop has been running (its runs/_cache is the answer cache).
   23| LAPTOP_HARNESS=${LAPTOP_HARNESS:-$HOME/Documents/fromDesktop/quickmoveaway/vaultSYncWebWithLocalOPtion/vaultsync-chatwindows/src/lib/simulacra/harness}
   24| test "$(aws sts get-caller-identity --query Account --output text)" = "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID to the target AWS account}"
   25| 
   26| run_task() {
   27|   local mode=$1 o
   28|   o=$(cd "$REPO/infra" && terraform output -json seed_task)
   29|   local cluster td subnets sg
   30|   cluster=$(jq -r .cluster <<<"$o"); td=$(jq -r .task_definition <<<"$o")
   31|   subnets=$(jq -r '.subnets | join(",")' <<<"$o"); sg=$(jq -r .security_group <<<"$o")
   32|   local arn
   33|   arn=$(aws ecs run-task --cluster "$cluster" --task-definition "$td" --launch-type FARGATE \
   34|     --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$sg],assignPublicIp=ENABLED}" \
   35|     --overrides "{\"containerOverrides\":[{\"name\":\"seed\",\"environment\":[{\"name\":\"MODE\",\"value\":\"$mode\"}]}]}" \
   36|     --query 'tasks[0].taskArn' --output text)
   37|   echo "started $arn; waiting"
   38|   aws ecs wait tasks-stopped --cluster "$cluster" --tasks "$arn"
   39|   aws ecs describe-tasks --cluster "$cluster" --tasks "$arn" \
   40|     --query 'tasks[0].containers[0].[exitCode,reason]' --output text
   41|   echo "logs: aws logs tail /ecs/simulacra --log-stream-name-prefix seed --since 15m"
   42| }
   43| 
   44| case "${1:-}" in
   45|   upload-cache)
   46|     aws s3 sync "$CACHE/" "$B/cache/" --exclude '*/raw/*' --exclude '.DS_Store' --only-show-errors
   47|     aws s3 ls "$B/cache/" --recursive --summarize | tail -2 ;;
   48|   upload-seed)
   49|     for d in whatifs configs; do
   50|       aws s3 sync "$REPO/$d/" "$B/seed/$d/" --exclude '.DS_Store' --only-show-errors
   51|     done
   52|     aws s3 sync "$REPO/serve/bundles/" "$B/seed/bundles/" --exclude '.DS_Store' --only-show-errors
   53|     aws s3 sync "$REPO/runs/" "$B/seed/runs/" --exclude '.DS_Store' --only-show-errors
   54|     # The answer cache and pickles aren't in git; they come from the laptop.
   55|     aws s3 sync "$LAPTOP_HARNESS/runs/_cache/" "$B/seed/runs/_cache/" --exclude '.DS_Store' --only-show-errors
   56|     aws s3 ls "$B/seed/" --recursive --summarize | tail -2 ;;
   57|   seed)  run_task seed ;;
   58|   cache) run_task cache ;;
   59|   backup)
   60|     d=$(date +%F); tmp=$(mktemp -d)
   61|     (cd "$LAPTOP_HARNESS" && COPYFILE_DISABLE=1 tar czf "$tmp/harness-state-$d.tgz" serve/bundles sessions runs whatifs configs)
   62|     (cd "$CACHE" && COPYFILE_DISABLE=1 tar czf "$tmp/harness-cache-derived-$d.tgz" --exclude='*/raw' .)
   63|     (cd "$tmp" && shasum -a 256 ./*.tgz > SHA256SUMS)
   64|     aws s3 cp "$tmp/" "$B/backups/$d/" --recursive --only-show-errors
   65|     cat "$tmp/SHA256SUMS"; rm -rf "$tmp" ;;
   66|   *)
   67|     sed -n '2,12p' "$0"; exit 2 ;;
   68| esac
```

## `serve/app.ts`

```ts
    1| // The server: /api/simulacra plus the static SvelteKit build, with an SPA
    2| // fallback to build/index.html for any other GET.
    3| import { existsSync } from 'node:fs';
    4| import path from 'node:path';
    5| import express, { type Express } from 'express';
    6| import { createSimulacraRouter, optionsFromEnv, type SimulacraOptions } from './simulacra';
    7| 
    8| export interface AppOptions {
    9|   simulacra: SimulacraOptions;
   10|   /** The static build folder (`pnpm build`); not served when it has no index.html. */
   11|   build: string;
   12| }
   13| 
   14| export const defaultAppOptions = (): AppOptions => ({
   15|   simulacra: optionsFromEnv(),
   16|   build: path.resolve(import.meta.dirname, '..', 'build')
   17| });
   18| 
   19| export function createApp(opts: AppOptions = defaultAppOptions()): Express {
   20|   const app = express();
   21|   app.disable('x-powered-by');
   22|   app.use('/api/simulacra', createSimulacraRouter(opts.simulacra));
   23|   const index = path.join(opts.build, 'index.html');
   24|   if (existsSync(index)) {
   25|     app.use(express.static(opts.build));
   26|     app.get('/{*path}', (_req, res) => res.sendFile(index));
   27|   }
   28|   return app;
   29| }
```

## `serve/bundle.ts`

```ts
    1| // What enters the server, parsed once with zod: the bundle contract and the
    2| // request bodies (one definition, shared with the page: ./contract.ts), and
    3| // the session files the intake worker writes. The names here are the
    4| // server's: each value is also its parsed type.
    5| import { z } from 'zod';
    6| import {
    7|   BucketSchema,
    8|   BundleResultSchema,
    9|   BundleSchema,
   10|   EditsSchema,
   11|   RunRequestSchema,
   12|   SliceSchema,
   13|   StepSchema,
   14|   TableRowSchema,
   15|   ToldSchema
   16| } from './contract';
   17| 
   18| export { FIELDS, type Field, RUN_LIMITS } from './contract';
   19| 
   20| export const PageKey = BucketSchema;
   21| export type PageKey = z.infer<typeof PageKey>;
   22| 
   23| export const Slice = SliceSchema;
   24| export type Slice = z.infer<typeof Slice>;
   25| 
   26| /** One what-if combination's result, as the bundle holds it. Loose: additive fields pass through to the page. */
   27| export const Result = BundleResultSchema;
   28| export type Result = z.infer<typeof Result>;
   29| 
   30| export const TableRow = TableRowSchema;
   31| export type TableRow = z.infer<typeof TableRow>;
   32| 
   33| export const Told = ToldSchema;
   34| export type Told = z.infer<typeof Told>;
   35| 
   36| export const Bundle = BundleSchema;
   37| export type Bundle = z.infer<typeof Bundle>;
   38| 
   39| // ── Request bodies ──
   40| 
   41| /** Hand edits: per slice, changes in fractions of its adults (summing to 0). */
   42| export const Edits = EditsSchema;
   43| export type Edits = z.infer<typeof Edits>;
   44| 
   45| /** POST /runs, within RUN_LIMITS. */
   46| export const RunRequest = RunRequestSchema;
   47| export type RunRequest = z.infer<typeof RunRequest>;
   48| 
   49| // ── Session files the intake worker writes (dev only) ──
   50| 
   51| export const QueueDone = z.looseObject({
   52|   text: z.string(),
   53|   year: z.number().nullish(),
   54|   status: z.string(),
   55|   key: z.string().nullish(),
   56|   why: z.string().nullish()
   57| });
   58| export type QueueDone = z.infer<typeof QueueDone>;
   59| 
   60| export const QueueFailed = z.looseObject({
   61|   text: z.string(),
   62|   year: z.number().nullish(),
   63|   at: z.number(),
   64|   why: z.string().nullish()
   65| });
   66| export type QueueFailed = z.infer<typeof QueueFailed>;
   67| 
   68| export const Step = StepSchema;
   69| export type Step = z.infer<typeof Step>;
   70| 
   71| export const IntakeStatus = z.looseObject({ text: z.string().nullable(), steps: z.array(Step) });
```

## `serve/bundles/RUN_ID`

```
    1| 2004-01ab47632c
```

## `serve/contract.test.ts`

```ts
    1| import { existsSync, readdirSync, readFileSync } from 'node:fs';
    2| import path from 'node:path';
    3| import { describe, expect, test } from 'vitest';
    4| import { BundleSchema, RUN_LIMITS, RunRequestSchema } from './contract';
    5| 
    6| const ROOT = path.resolve(import.meta.dirname, '..');
    7| const FIXTURE = path.join(ROOT, 'tests', 'fixtures', 'bundle.example.json');
    8| const BUNDLES = path.join(ROOT, 'serve', 'bundles');
    9| 
   10| describe('BundleSchema', () => {
   11|   test('parses the shared bundle example (tests/fixtures/bundle.example.json)', () => {
   12|     const parsed = BundleSchema.safeParse(JSON.parse(readFileSync(FIXTURE, 'utf8')));
   13|     expect(parsed.error?.issues ?? []).toEqual([]);
   14|     // Published bundles write State.flipped as 0 / 1: parsed, it is a boolean.
   15|     const flips = Object.values(parsed.data?.runs ?? {}).flatMap((r) => r.states.map((s) => s.flipped));
   16|     expect(flips.length).toBeGreaterThan(0);
   17|     expect(new Set(flips.map((f) => typeof f))).toEqual(new Set(['boolean']));
   18|   });
   19| 
   20|   test('fields it does not name pass through, for the page', () => {
   21|     const raw = JSON.parse(readFileSync(FIXTURE, 'utf8'));
   22|     const run = BundleSchema.parse(raw).runs[''];
   23|     expect(run && Object.keys(run).sort()).toEqual(Object.keys(raw.runs['']).sort());
   24|   });
   25| 
   26|   const files = existsSync(BUNDLES) ? readdirSync(BUNDLES).filter((f) => /^\d{4}\.json$/.test(f)) : [];
   27|   test.skipIf(files.length === 0)('parses every served bundle (skips when serve/bundles is absent)', () => {
   28|     const bad = files.filter((f) => !BundleSchema.safeParse(JSON.parse(readFileSync(path.join(BUNDLES, f), 'utf8'))).success);
   29|     expect(bad).toEqual([]);
   30|   });
   31| });
   32| 
   33| describe('RunRequestSchema', () => {
   34|   const ok = (body: unknown) => RunRequestSchema.safeParse(body).success;
   35| 
   36|   test('a plain ask parses, with defaults and the words trimmed', () => {
   37|     expect(RunRequestSchema.parse({ year: '1920', text: '  the league passes  ' })).toEqual({
   38|       year: 1920,
   39|       whatIfs: [],
   40|       text: 'the league passes',
   41|       edits: {}
   42|     });
   43|   });
   44| 
   45|   test('the year is an election year in range', () => {
   46|     expect(ok({ year: RUN_LIMITS.firstYear })).toBe(true);
   47|     expect(ok({ year: RUN_LIMITS.lastYear })).toBe(true);
   48|     expect(ok({ year: 1788 })).toBe(false);
   49|     expect(ok({ year: 2101 })).toBe(false);
   50|     expect(ok({ year: 1920.5 })).toBe(false);
   51|     expect(ok({ year: 'soon' })).toBe(false);
   52|   });
   53| 
   54|   test('typed words: at most 300 characters once trimmed', () => {
   55|     expect(ok({ year: 1920, text: 'x'.repeat(RUN_LIMITS.text) })).toBe(true);
   56|     expect(ok({ year: 1920, text: ` ${'x'.repeat(RUN_LIMITS.text)} ` })).toBe(true);
   57|     expect(ok({ year: 1920, text: 'x'.repeat(RUN_LIMITS.text + 1) })).toBe(false);
   58|   });
   59| 
   60|   test('what-ifs: at most 32 keys of at most 80 characters', () => {
   61|     const keys = (n: number, len = 8) => Array.from({ length: n }, (_, i) => `${i}`.padStart(len, 'k'));
   62|     expect(ok({ year: 1920, whatIfs: keys(RUN_LIMITS.whatIfs) })).toBe(true);
   63|     expect(ok({ year: 1920, whatIfs: keys(RUN_LIMITS.whatIfs + 1) })).toBe(false);
   64|     expect(ok({ year: 1920, whatIfs: keys(1, RUN_LIMITS.key) })).toBe(true);
   65|     expect(ok({ year: 1920, whatIfs: keys(1, RUN_LIMITS.key + 1) })).toBe(false);
   66|   });
   67| 
   68|   test('edits: at most 64 groups, keys of at most 80 characters, each change within [-1, 1]', () => {
   69|     const groups = (n: number) => Object.fromEntries(Array.from({ length: n }, (_, i) => [`g${i}`, { A: 0.1, home: -0.1 }]));
   70|     expect(ok({ year: 1920, edits: groups(RUN_LIMITS.edits) })).toBe(true);
   71|     expect(ok({ year: 1920, edits: groups(RUN_LIMITS.edits + 1) })).toBe(false);
   72|     expect(ok({ year: 1920, edits: { ['k'.repeat(RUN_LIMITS.key + 1)]: { A: 0 } } })).toBe(false);
   73|     expect(ok({ year: 1920, edits: { women: { A: 1, home: -1 } } })).toBe(true);
   74|     expect(ok({ year: 1920, edits: { women: { A: 1.01 } } })).toBe(false);
   75|     expect(ok({ year: 1920, edits: { women: { A: Number.POSITIVE_INFINITY } } })).toBe(false);
   76|     expect(ok({ year: 1920, edits: { women: { nobody: 0.1 } } })).toBe(false);
   77|   });
   78| });
```

## `serve/contract.ts`

```ts
    1| // The page's contract with the simulation server, one definition for both
    2| // sides: serve/bundle.ts parses the published bundles and request bodies with
    3| // these, and the page (src/lib/simulacra/schemas.ts) parses every answer with
    4| // them. It lives under serve/ because the server's image is built from serve/
    5| // alone (Dockerfile); it imports nothing but zod, so the page can import it too.
    6| // The bundle mirrors simharness.serialize.Bundle; both sides test against
    7| // tests/fixtures/bundle.example.json (serve/contract.test.ts, tests/test_contract.py).
    8| //
    9| // Objects that come from a bundle are loose: fields added on the Python side
   10| // pass through the server to the page, which reads only what's named here.
   11| // Candidate keys follow history.ts: A is the winner, B the runner-up, O
   12| // everyone else.
   13| //
   14| // GET  /manifest → Manifest { years: { [year]: runId } }
   15| // GET  /elections/:year → ElectionResponse { slices, whatIfs, simulated, runId }
   16| // POST /runs RunRequest { year, whatIfs: [key], text, edits } → StartedRun { id }
   17| // GET  /runs/:id → RunStatus (running | done with a RunResult | failed)
   18| // POST /runs/:id/cancel → { ok }
   19| // GET  /elections/:year/voters/:slice?run=:id → Voter
   20| import { z } from 'zod';
   21| 
   22| /** A what-if's kind: who can vote, who lives where, what people care about, who is on the ballot. */
   23| export const KindSchema = z.enum(['franchise', 'population', 'issue', 'candidate']);
   24| export type Kind = z.infer<typeof KindSchema>;
   25| 
   26| /** What one person did: voted for A, B or someone else, stayed home, or couldn't vote. */
   27| export const ChoiceSchema = z.enum(['A', 'B', 'O', 'home', 'barred']);
   28| export type Choice = z.infer<typeof ChoiceSchema>;
   29| 
   30| /** Where a vote is counted: the winner, the runner-up, or everyone else. */
   31| export const BucketSchema = z.enum(['A', 'B', 'O']);
   32| export type Bucket = z.infer<typeof BucketSchema>;
   33| 
   34| /** The five shares every slice and table row splits its adults into. */
   35| export const FIELDS = ['barred', 'home', 'A', 'B', 'O'] as const;
   36| export type Field = (typeof FIELDS)[number];
   37| 
   38| /** One group of adults; the five fractions are of the group's adults. `adults` is in millions. */
   39| export const SliceSchema = z.looseObject({
   40|   key: z.string(),
   41|   label: z.string(),
   42|   adults: z.number(),
   43|   barred: z.number(),
   44|   home: z.number(),
   45|   A: z.number(),
   46|   B: z.number(),
   47|   O: z.number(),
   48|   source: z.string().optional()
   49| });
   50| export type Slice = z.infer<typeof SliceSchema>;
   51| 
   52| export const WhatIfSchema = z.looseObject({
   53|   key: z.string(),
   54|   label: z.string(),
   55|   kind: KindSchema,
   56|   detail: z.string(),
   57|   /** The groups it reaches. */
   58|   slices: z.array(z.string()).default([]),
   59|   assumption: z.string().optional(),
   60|   confidenceTier: z.string().optional(),
   61|   evidence: z.string().optional(),
   62|   exploratory: z.boolean().optional()
   63| });
   64| export type WhatIf = z.infer<typeof WhatIfSchema>;
   65| 
   66| /** A year's groups and what-ifs, as its bundle holds them. */
   67| export const ElectionSchema = z.looseObject({
   68|   slices: z.array(SliceSchema),
   69|   whatIfs: z.array(WhatIfSchema)
   70| });
   71| 
   72| /** GET /elections/:year. A year without a simulation answers empty lists and `simulated: false`. */
   73| export const ElectionResponseSchema = ElectionSchema.extend({
   74|   simulated: z.boolean().optional(),
   75|   /** The run this year's bundle came from; absent when there's no bundle. */
   76|   runId: z.string().optional()
   77| });
   78| export type ElectionResponse = z.infer<typeof ElectionResponseSchema>;
   79| 
   80| /** GET /manifest: every published year and its run. */
   81| export const ManifestSchema = z.object({ years: z.record(z.string(), z.string()) });
   82| 
   83| const EvSchema = z.object({ A: z.number(), B: z.number(), O: z.number() });
   84| const PairSchema = z.tuple([z.number(), z.number()]);
   85| 
   86| export const StateResultSchema = z.looseObject({
   87|   code: z.string(),
   88|   /** A candidate key ('A', 'B', 'C', …) or 'O'. */
   89|   won: z.string(),
   90|   // serialize writes a numpy bool through json's default=float, 0.0 / 1.0, in
   91|   // published bundles; the sample and hand-edited runs write a boolean.
   92|   flipped: z.union([z.boolean(), z.number()]).transform((v) => v !== false && v !== 0),
   93|   margin: z.number(),
   94|   marginRange: PairSchema.optional(),
   95|   pFlip: z.number().optional()
   96| });
   97| export type StateResult = z.infer<typeof StateResultSchema>;
   98| 
   99| export const AppliedSchema = z.looseObject({ key: z.string(), label: z.string(), kind: KindSchema });
  100| export type Applied = z.infer<typeof AppliedSchema>;
  101| 
  102| const SourceSchema = z.looseObject({ title: z.string(), url: z.string().optional(), tier: z.string().optional() });
  103| 
  104| const FindingSchema = z.looseObject({
  105|   claim: z.string(),
  106|   when: z.string().optional(),
  107|   match: z.string().optional(),
  108|   tier: z.string().optional(),
  109|   sources: z.array(SourceSchema).default([])
  110| });
  111| 
  112| export const EvidenceSchema = z.looseObject({
  113|   whatIf: z.string(),
  114|   strength: z.string().optional(),
  115|   summary: z.string().optional(),
  116|   agreement: z.string().optional(),
  117|   agreementDetail: z.string().nullable().optional(),
  118|   findings: z.array(FindingSchema).default([]),
  119|   caveats: z.array(z.string()).optional(),
  120|   researchedAt: z.string().optional()
  121| });
  122| export type Evidence = z.infer<typeof EvidenceSchema>;
  123| 
  124| export const CohortEffectSchema = z.looseObject({
  125|   whatIf: z.string(),
  126|   cohort: z.string(),
  127|   n: z.number(),
  128|   bias: z.number().optional(),
  129|   weight: z.number().optional(),
  130|   exposed: z.boolean().optional(),
  131|   dr: z.number().optional(),
  132|   dt: z.number().optional()
  133| });
  134| export type CohortEffect = z.infer<typeof CohortEffectSchema>;
  135| 
  136| /** The interviews before any change: the baseline, and the leakage probes when the run had them. */
  137| export const PreSchema = z.looseObject({
  138|   voters: z.number(),
  139|   interviews: z.number(),
  140|   items: z.array(z.number()).optional(),
  141|   asOf: z.string().optional(),
  142|   wordings: z.number().optional(),
  143|   recall: z.object({ n: z.number(), winnerRate: z.number() }).optional(),
  144|   swap: z.object({ platformRate: z.number() }).optional()
  145| });
  146| export type Pre = z.infer<typeof PreSchema>;
  147| 
  148| /** What a what-if's voters were told: settled facts, news on a nominee's line, planks added and dropped. */
  149| export const ToldSchema = z.looseObject({
  150|   facts: z.array(z.string()).optional(),
  151|   news: z.array(z.string()).optional(),
  152|   added: z.array(z.string()).optional(),
  153|   dropped: z.array(z.string()).optional(),
  154|   /** A staged what-if: news from the changed world, added to the voters' newspapers. */
  155|   items: z.array(z.object({ date: z.string(), text: z.string() })).optional(),
  156|   /** A staged what-if: how many real newspaper items the change makes false, taken out. */
  157|   removed: z.number().int().nonnegative().optional()
  158| });
  159| export type Told = z.infer<typeof ToldSchema>;
  160| 
  161| /** A dated newspaper item in the voters' briefs. */
  162| export const ReadingSchema = z.looseObject({
  163|   date: z.string(),
  164|   newspaper: z.string(),
  165|   place: z.string(),
  166|   summary: z.string().optional()
  167| });
  168| export type Reading = z.infer<typeof ReadingSchema>;
  169| 
  170| const AnswerSideSchema = z.looseObject({
  171|   choice: z.string(),
  172|   pVote: z.number().nullable().optional(),
  173|   quote: z.string(),
  174|   reason: z.string().optional()
  175| });
  176| 
  177| export const InterviewAnswerSchema = z.looseObject({
  178|   /** Index into the interview's questions. */
  179|   question: z.number(),
  180|   name: z.string(),
  181|   cohort: z.string(),
  182|   line: z.string(),
  183|   misread: z.boolean().optional(),
  184|   before: AnswerSideSchema,
  185|   after: AnswerSideSchema
  186| });
  187| export type InterviewAnswer = z.infer<typeof InterviewAnswerSchema>;
  188| 
  189| /** The interviews behind a rerun: the questions once, each person's answers per applied what-if. */
  190| export const InterviewSchema = z.object({
  191|   questions: z.array(z.string()),
  192|   byWhatIf: z.array(z.object({ whatIf: z.string(), answers: z.array(InterviewAnswerSchema) }))
  193| });
  194| export type Interview = z.infer<typeof InterviewSchema>;
  195| 
  196| /** One combination of what-ifs as a bundle holds it (serialize.Result). */
  197| export const BundleResultSchema = z.looseObject({
  198|   ev: EvSchema,
  199|   /** null: no one has a majority. */
  200|   winner: BucketSchema.nullable(),
  201|   states: z.array(StateResultSchema),
  202|   slices: z.array(SliceSchema),
  203|   summary: z.string(),
  204|   /** null: nothing was applied. */
  205|   confidence: z.enum(['high', 'medium', 'low']).nullable(),
  206|   applied: z.array(AppliedSchema),
  207|   /** The part of the typed text the server couldn't use. */
  208|   unknown: z.string().nullable(),
  209|   confidenceTier: z.string().optional(),
  210|   confidenceLabel: z.string().optional(),
  211|   confidenceFlags: z.array(z.string()).optional(),
  212|   confidenceReasons: z.array(z.string()).optional(),
  213|   range: z.object({ A: PairSchema, B: PairSchema, O: PairSchema }).optional(),
  214|   drawsWon: z.record(z.string(), z.number()).optional(),
  215|   popular: EvSchema.optional(),
  216|   assumptions: z.array(z.string()).optional(),
  217|   howIGotThis: z.array(z.string()).optional(),
  218|   sources: z.array(SourceSchema).optional(),
  219|   evidence: z.array(EvidenceSchema).optional(),
  220|   cohortEffects: z.array(CohortEffectSchema).optional(),
  221|   mode: z.string().optional(),
  222|   runId: z.string().optional()
  223| });
  224| export type BundleResult = z.infer<typeof BundleResultSchema>;
  225| 
  226| /** A rerun as the page receives it: the bundle's result plus what the server adds from the rest of the bundle. */
  227| export const RunResultSchema = BundleResultSchema.extend({
  228|   /** Why `unknown` wasn't modelled (a daily or monthly budget spent, or the worker's reason). */
  229|   unknownWhy: z.string().optional(),
  230|   pre: PreSchema.optional(),
  231|   told: z.record(z.string(), ToldSchema).optional(),
  232|   reading: z.array(ReadingSchema).optional(),
  233|   interview: InterviewSchema.optional(),
  234|   queued: z.object({ text: z.string(), worker: z.boolean() }).optional()
  235| });
  236| export type RunResult = z.infer<typeof RunResultSchema>;
  237| 
  238| export const StepSchema = z.object({ text: z.string(), state: z.enum(['done', 'doing']) });
  239| export type Step = z.infer<typeof StepSchema>;
  240| 
  241| /** GET /runs/:id. */
  242| export const RunStatusSchema = z.discriminatedUnion('status', [
  243|   z.object({
  244|     status: z.literal('running'),
  245|     done: z.number(),
  246|     total: z.number(),
  247|     /** New words being modelled on the server: its working so far. */
  248|     steps: z.array(StepSchema).optional()
  249|   }),
  250|   z.object({ status: z.literal('done'), done: z.number(), total: z.number(), result: RunResultSchema }),
  251|   z.object({ status: z.literal('failed'), error: z.string().nullable() })
  252| ]);
  253| export type RunStatus = z.infer<typeof RunStatusSchema>;
  254| 
  255| /** POST /runs. */
  256| export const StartedRunSchema = z.object({ id: z.string() });
  257| export type StartedRun = z.infer<typeof StartedRunSchema>;
  258| 
  259| /** POST /runs/:id/cancel. */
  260| export const CancelledSchema = z.object({ ok: z.boolean().optional() });
  261| 
  262| /** One simulated person from a group: what they did in history, and in the run. */
  263| export const VoterSchema = z.looseObject({
  264|   name: z.string(),
  265|   line: z.string(),
  266|   quote: z.string(),
  267|   history: ChoiceSchema,
  268|   now: ChoiceSchema,
  269|   cohort: z.string().optional()
  270| });
  271| export type Voter = z.infer<typeof VoterSchema>;
  272| 
  273| // ── The published bundle (serve/bundles/<year>.json) ──
  274| 
  275| /** One state × group cell of a run: what hand edits are applied to (serve/simulacra.ts applyEdits). */
  276| export const TableRowSchema = z.object({
  277|   state: z.string(),
  278|   slice: z.string(),
  279|   adults: z.number(),
  280|   barred: z.number(),
  281|   home: z.number(),
  282|   A: z.number(),
  283|   B: z.number(),
  284|   O: z.number()
  285| });
  286| export type TableRow = z.infer<typeof TableRowSchema>;
  287| 
  288| /** What the server holds for a year; it answers the page from it. */
  289| export const BundleSchema = z.object({
  290|   year: z.number().int(),
  291|   runId: z.string(),
  292|   election: ElectionSchema,
  293|   /** Each precomputed combination of what-ifs ('' is history; 'a+b' sorted), by key. */
  294|   runs: z.record(z.string(), BundleResultSchema),
  295|   /** The same keys as runs. */
  296|   tables: z.record(z.string(), z.array(TableRowSchema)),
  297|   /** Run key → slice key → one person. */
  298|   voters: z.record(z.string(), z.record(z.string(), VoterSchema)),
  299|   /** {} when the run had no interviews. */
  300|   interviews: z.object({
  301|     questions: z.array(z.string()).optional(),
  302|     byWhatIf: z.record(z.string(), z.array(InterviewAnswerSchema)).optional()
  303|   }),
  304|   /** Electoral votes and history's winner by state. */
  305|   ev: z.record(z.string(), z.number()),
  306|   historyWinner: z.record(z.string(), BucketSchema),
  307|   /** Keywords that read typed text as a what-if. */
  308|   words: z.array(z.object({ key: z.string(), words: z.array(z.string()) })),
  309|   // Bundles published before the briefs record (1916, 1924) lack these three.
  310|   pre: PreSchema.nullable().optional(),
  311|   told: z.record(z.string(), ToldSchema).optional(),
  312|   reading: z.array(ReadingSchema).optional()
  313| });
  314| export type Bundle = z.infer<typeof BundleSchema>;
  315| 
  316| // ── POST /runs ──
  317| 
  318| /** What one rerun may ask for. The page's field stops at `text` (WhatIfComposer). */
  319| export const RUN_LIMITS = {
  320|   firstYear: 1789,
  321|   lastYear: 2100,
  322|   /** Characters of typed words, trimmed. */
  323|   text: 300,
  324|   /** What-if keys, and characters in each. */
  325|   whatIfs: 32,
  326|   key: 80,
  327|   /** Groups edited by hand. */
  328|   edits: 64
  329| } as const;
  330| 
  331| /** Hand edits: per slice, changes in fractions of its adults (summing to 0). */
  332| export const EditsSchema = z
  333|   .record(z.string().max(RUN_LIMITS.key), z.partialRecord(z.enum(FIELDS), z.number().min(-1).max(1)))
  334|   .refine((e) => Object.keys(e).length <= RUN_LIMITS.edits, { message: `At most ${RUN_LIMITS.edits} groups.` });
  335| export type Edits = z.infer<typeof EditsSchema>;
  336| 
  337| export const RunRequestSchema = z.object({
  338|   year: z.coerce.number().int().min(RUN_LIMITS.firstYear).max(RUN_LIMITS.lastYear),
  339|   whatIfs: z.array(z.string().max(RUN_LIMITS.key)).max(RUN_LIMITS.whatIfs).default([]),
  340|   text: z.string().trim().max(RUN_LIMITS.text).default(''),
  341|   edits: EditsSchema.default({})
  342| });
  343| export type RunRequest = z.infer<typeof RunRequestSchema>;
```

## `serve/guard.test.ts`

```ts
    1| import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
    2| import { tmpdir } from 'node:os';
    3| import path from 'node:path';
    4| import { describe, expect, it } from 'vitest';
    5| import { capsFromEnv, checkCaps, parseKeyRing, pruneJsonl, RateLimiter, spent } from './guard';
    6| 
    7| const dir = mkdtempSync(path.join(tmpdir(), 'simulacra-guard-'));
    8| const DAY = 86_400_000;
    9| 
   10| describe('parseKeyRing', () => {
   11|   const ring = parseKeyRing(JSON.stringify({ ana: 'a'.repeat(24), ben: 'b'.repeat(40) }));
   12| 
   13|   it('names the key a bearer header carries', () => {
   14|     expect(ring.size).toBe(2);
   15|     expect(ring.identify(`Bearer ${'a'.repeat(24)}`)).toBe('ana');
   16|     expect(ring.identify(`Bearer ${'b'.repeat(40)}`)).toBe('ben');
   17|   });
   18| 
   19|   it('names nobody for a missing, wrong or malformed header', () => {
   20|     for (const h of [undefined, '', 'Bearer ', `Basic ${'a'.repeat(24)}`, `Bearer ${'a'.repeat(23)}`, `Bearer ${'a'.repeat(24)} `]) {
   21|       expect(ring.identify(h)).toBeNull();
   22|     }
   23|   });
   24| 
   25|   it('is empty when unset, and refuses short keys or bad names at startup', () => {
   26|     expect(parseKeyRing(undefined).size).toBe(0);
   27|     expect(parseKeyRing('  ').identify(`Bearer ${'a'.repeat(24)}`)).toBeNull();
   28|     expect(() => parseKeyRing(JSON.stringify({ ana: 'short' }))).toThrow();
   29|     expect(() => parseKeyRing(JSON.stringify({ 'Bad Name': 'a'.repeat(24) }))).toThrow();
   30|     expect(() => parseKeyRing('{not json')).toThrow();
   31|   });
   32| });
   33| 
   34| describe('RateLimiter', () => {
   35|   it('admits max per window, then says when to retry', () => {
   36|     let t = 0;
   37|     const rl = new RateLimiter({ max: 2, windowMs: 10_000 }, () => t);
   38|     expect(rl.admit('ip').ok).toBe(true);
   39|     expect(rl.admit('ip').ok).toBe(true);
   40|     t = 4_000;
   41|     expect(rl.admit('ip')).toEqual({ ok: false, retryAfterS: 6 });
   42|     expect(rl.admit('other').ok).toBe(true);
   43|     t = 10_000;
   44|     expect(rl.admit('ip').ok).toBe(true);
   45|   });
   46| 
   47|   it('holds at most maxKeys windows', () => {
   48|     let t = 0;
   49|     const rl = new RateLimiter({ max: 1, windowMs: 1_000_000 }, () => t, 3);
   50|     for (const ip of ['a', 'b', 'c', 'd', 'e']) {
   51|       t += 1;
   52|       rl.admit(ip);
   53|     }
   54|     // The oldest windows were dropped: 'a' starts afresh, 'e' is still limited.
   55|     expect(rl.admit('a').ok).toBe(true);
   56|     expect(rl.admit('e').ok).toBe(false);
   57|   });
   58| });
   59| 
   60| describe('dollar caps', () => {
   61|   const now = Date.parse('2026-10-15T12:00:00Z');
   62|   const ledger = path.join(dir, 'spend.jsonl');
   63|   writeFileSync(
   64|     ledger,
   65|     `${[
   66|       { day: '2026-10-15', dollars: 3, who: 'ana' },
   67|       { day: '2026-10-15', dollars: 2, who: null },
   68|       { day: '2026-10-15', dollars: 1 },
   69|       { day: '2026-10-02', dollars: 40, who: 'ben' },
   70|       { day: '2026-09-30', dollars: 500, who: 'ana' },
   71|       { day: '2026-10-15', dollars: 'x', who: 'ana' }
   72|     ]
   73|       .map((r) => JSON.stringify(r))
   74|       .join('\n')}\nnot json\n`
   75|   );
   76| 
   77|   it("counts every visitor's spend, today and this month (UTC); other months and bad lines count for nothing", () => {
   78|     expect(spent(ledger, now)).toEqual({ today: 6, month: 46 });
   79|     expect(spent(path.join(dir, 'missing.jsonl'), now)).toEqual({ today: 0, month: 0 });
   80|   });
   81| 
   82|   it("is over when today's or this month's total reaches its cap, the month first", () => {
   83|     expect(checkCaps(ledger, { daily: 10, monthly: 100 }, now)).toEqual({ kind: 'ok' });
   84|     expect(checkCaps(ledger, { daily: 6, monthly: 100 }, now)).toEqual({ kind: 'over', which: 'daily' });
   85|     expect(checkCaps(ledger, { daily: 6, monthly: 46 }, now)).toEqual({ kind: 'over', which: 'monthly' });
   86|   });
   87| 
   88|   it('defaults to $20 a day and $200 a month, and refuses a bad value', () => {
   89|     expect(capsFromEnv({})).toEqual({ daily: 20, monthly: 200 });
   90|     expect(capsFromEnv({ SIMULACRA_DAILY_USD: '5', SIMULACRA_MONTHLY_USD: '50' })).toEqual({ daily: 5, monthly: 50 });
   91|     expect(() => capsFromEnv({ SIMULACRA_DAILY_USD: 'lots' })).toThrow();
   92|   });
   93| });
   94| 
   95| describe('pruneJsonl', () => {
   96|   it('keeps lines inside the retention, whatever their timestamp style', () => {
   97|     const now = Date.parse('2026-10-01T12:00:00Z');
   98|     const f = path.join(dir, 'log.jsonl');
   99|     const rows = [
  100|       { ts: '2026-09-20T00:00:00Z', text: 'old iso' },
  101|       { ts: '2026-09-30T10:00:00', text: 'new, no zone' },
  102|       { ts: '2026-09-30T10:00:00+00:00', text: 'new, offset' },
  103|       { at: (now - 9 * DAY) / 1000, text: 'old epoch' },
  104|       { at: (now - DAY) / 1000, text: 'new epoch' },
  105|       { text: 'no stamp' }
  106|     ];
  107|     writeFileSync(f, `${rows.map((r) => JSON.stringify(r)).join('\n')}\n`);
  108|     expect(pruneJsonl(f, 7 * DAY, now)).toBe(3);
  109|     expect(readFileSync(f, 'utf8').trim().split('\n').map((l) => JSON.parse(l).text)).toEqual(['new, no zone', 'new, offset', 'new epoch']);
  110|     expect(pruneJsonl(f, 7 * DAY, now)).toBe(0);
  111|     expect(pruneJsonl(path.join(dir, 'missing.jsonl'), DAY, now)).toBe(0);
  112|   });
  113| 
  114|   it('with scrub, keeps old lines without the named fields', () => {
  115|     const now = Date.parse('2026-10-01T12:00:00Z');
  116|     const f = path.join(dir, 'spend.jsonl');
  117|     writeFileSync(
  118|       f,
  119|       `${[
  120|         { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 1.5, note: 'a visitor typed this' },
  121|         { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 0.5 },
  122|         { ts: '2026-09-30T00:00:00Z', day: '2026-09-30', dollars: 2, note: 'recent' }
  123|       ]
  124|         .map((r) => JSON.stringify(r))
  125|         .join('\n')}\n`
  126|     );
  127|     expect(pruneJsonl(f, 7 * DAY, now, ['note'])).toBe(1);
  128|     expect(readFileSync(f, 'utf8').trim().split('\n').map((l) => JSON.parse(l))).toEqual([
  129|       { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 1.5 },
  130|       { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 0.5 },
  131|       { ts: '2026-09-30T00:00:00Z', day: '2026-09-30', dollars: 2, note: 'recent' }
  132|     ]);
  133|   });
  134| });
```

## `serve/guard.ts`

```ts
    1| // What stands between a visitor and the API: the intake's dollar caps, per-IP
    2| // rate limits, access keys (whose names the spend ledger records), and how long
    3| // session logs keep visitors' words.
    4| //
    5| // Only typed text the page doesn't already know costs anything (the intake
    6| // worker's compile, research and interviews). Any visitor may queue text, a few
    7| // texts per IP an hour, while the spend ledger (sessions/spend.jsonl) is under
    8| // both caps, counted across every visitor together: SIMULACRA_DAILY_USD per UTC
    9| // day (default 20) and SIMULACRA_MONTHLY_USD per UTC month (default 200). The
   10| // worker (simharness/intake.py) checks the same ledger again before each text
   11| // and stops a text at the stage that crosses what is left. The caps don't
   12| // depend on IPs or keys, so a forged X-Forwarded-For can't raise them.
   13| import { createHash, timingSafeEqual } from 'node:crypto';
   14| import { readFileSync, renameSync, statSync, truncateSync, writeFileSync } from 'node:fs';
   15| import { z } from 'zod';
   16| 
   17| // ── Access keys ──
   18| 
   19| /** SIMULACRA_ACCESS_KEYS: a JSON object of key name → key. Names are what the spend ledger records. */
   20| const AccessKeys = z.record(z.string().regex(/^[a-z0-9][a-z0-9_-]{0,39}$/), z.string().regex(/^[A-Za-z0-9_-]{24,128}$/));
   21| 
   22| const digest = (s: string): Buffer => createHash('sha256').update(s).digest();
   23| 
   24| export interface KeyRing {
   25|   /** The name of the key a request's Authorization header carries, or null. */
   26|   identify(authorization: string | undefined): string | null;
   27|   readonly size: number;
   28| }
   29| 
   30| /** Parses SIMULACRA_ACCESS_KEYS; unset is an empty ring (no names recorded), malformed throws at startup. */
   31| export function parseKeyRing(raw: string | undefined): KeyRing {
   32|   const keys = raw?.trim() ? Object.entries(AccessKeys.parse(JSON.parse(raw))) : [];
   33|   const hashed = keys.map(([name, key]) => ({ name, hash: digest(key) }));
   34|   return {
   35|     size: hashed.length,
   36|     identify(authorization) {
   37|       const m = /^Bearer ([A-Za-z0-9_-]{1,256})$/.exec(authorization ?? '');
   38|       if (!m?.[1]) return null;
   39|       const h = digest(m[1]);
   40|       // Every key is compared, in constant time, whichever matches.
   41|       let found: string | null = null;
   42|       for (const k of hashed) if (timingSafeEqual(h, k.hash)) found = k.name;
   43|       return found;
   44|     }
   45|   };
   46| }
   47| 
   48| // ── Rate limits ──
   49| 
   50| export interface Limit {
   51|   /** Requests allowed per window. */
   52|   readonly max: number;
   53|   readonly windowMs: number;
   54| }
   55| 
   56| export type Admit = { readonly ok: true } | { readonly ok: false; readonly retryAfterS: number };
   57| 
   58| /** A fixed window per key (an IP). Memory is bounded: expired windows are dropped as new keys arrive. */
   59| export class RateLimiter {
   60|   private readonly windows = new Map<string, { start: number; count: number }>();
   61| 
   62|   constructor(
   63|     private readonly limit: Limit,
   64|     private readonly now: () => number = Date.now,
   65|     private readonly maxKeys = 50_000
   66|   ) {}
   67| 
   68|   admit(key: string): Admit {
   69|     const t = this.now();
   70|     const w = this.windows.get(key);
   71|     if (w && t - w.start < this.limit.windowMs) {
   72|       if (w.count >= this.limit.max) return { ok: false, retryAfterS: Math.ceil((w.start + this.limit.windowMs - t) / 1000) };
   73|       w.count += 1;
   74|       return { ok: true };
   75|     }
   76|     // A new window goes to the back, so the oldest windows are at the front.
   77|     this.windows.delete(key);
   78|     this.windows.set(key, { start: t, count: 1 });
   79|     for (const [k, old] of this.windows) {
   80|       if (t - old.start < this.limit.windowMs && this.windows.size <= this.maxKeys) break;
   81|       this.windows.delete(k);
   82|     }
   83|     return { ok: true };
   84|   }
   85| }
   86| 
   87| // ── Dollar caps ──
   88| 
   89| export interface Caps {
   90|   /** Dollars per UTC day, every visitor together. */
   91|   readonly daily: number;
   92|   /** Dollars per UTC calendar month, every visitor together. */
   93|   readonly monthly: number;
   94| }
   95| 
   96| export function capsFromEnv(env: NodeJS.ProcessEnv = process.env): Caps {
   97|   const usd = z.coerce.number().finite().nonnegative();
   98|   return {
   99|     daily: env.SIMULACRA_DAILY_USD ? usd.parse(env.SIMULACRA_DAILY_USD) : 20,
  100|     monthly: env.SIMULACRA_MONTHLY_USD ? usd.parse(env.SIMULACRA_MONTHLY_USD) : 200
  101|   };
  102| }
  103| 
  104| const SpendLine = z.looseObject({ day: z.string(), dollars: z.number() });
  105| 
  106| export const utcDay = (t: number): string => new Date(t).toISOString().slice(0, 10);
  107| 
  108| /**
  109|  * Every dollar the ledger records today and this month (UTC), whoever's text it
  110|  * was. simharness/llm.py `spent` counts the same way, for the worker.
  111|  */
  112| export function spent(ledger: string, now: number = Date.now()): { today: number; month: number } {
  113|   const day = utcDay(now);
  114|   const month = day.slice(0, 7);
  115|   let text = '';
  116|   try {
  117|     text = readFileSync(ledger, 'utf8');
  118|   } catch {
  119|     return { today: 0, month: 0 };
  120|   }
  121|   let today = 0;
  122|   let thisMonth = 0;
  123|   for (const line of text.split('\n')) {
  124|     if (!line) continue;
  125|     let row: unknown;
  126|     try {
  127|       row = JSON.parse(line);
  128|     } catch {
  129|       continue;
  130|     }
  131|     const r = SpendLine.safeParse(row);
  132|     if (!r.success) continue;
  133|     if (r.data.day.startsWith(month)) thisMonth += r.data.dollars;
  134|     if (r.data.day === day) today += r.data.dollars;
  135|   }
  136|   return { today, month: thisMonth };
  137| }
  138| 
  139| export type CapCheck = { readonly kind: 'ok' } | { readonly kind: 'over'; readonly which: 'daily' | 'monthly' };
  140| 
  141| export function checkCaps(ledger: string, caps: Caps, now: number = Date.now()): CapCheck {
  142|   const s = spent(ledger, now);
  143|   if (s.month >= caps.monthly) return { kind: 'over', which: 'monthly' };
  144|   if (s.today >= caps.daily) return { kind: 'over', which: 'daily' };
  145|   return { kind: 'ok' };
  146| }
  147| 
  148| // ── Session log retention ──
  149| 
  150| const Stamped = z.looseObject({ ts: z.string().optional(), at: z.number().optional() });
  151| 
  152| function stampOf(line: string): number | null {
  153|   let row: unknown;
  154|   try {
  155|     row = JSON.parse(line);
  156|   } catch {
  157|     return null;
  158|   }
  159|   const r = Stamped.safeParse(row);
  160|   if (!r.success) return null;
  161|   if (r.data.at !== undefined) return r.data.at * 1000;
  162|   if (r.data.ts === undefined) return null;
  163|   // Timestamps without a zone were written in the container's zone, UTC.
  164|   const t = Date.parse(/[zZ]|[+-]\d\d:\d\d$/.test(r.data.ts) ? r.data.ts : `${r.data.ts}Z`);
  165|   return Number.isNaN(t) ? null : t;
  166| }
  167| 
  168| /**
  169|  * Drops lines older than `maxAgeMs` (and unreadable ones) from a JSONL log, by
  170|  * writing a copy and renaming it over the original; with `scrub`, an old line
  171|  * is kept without the named fields instead. Only call it while no worker is
  172|  * running: the worker appends to these files. Returns lines dropped or scrubbed.
  173|  */
  174| export function pruneJsonl(file: string, maxAgeMs: number, now: number = Date.now(), scrub?: readonly string[]): number {
  175|   let text: string;
  176|   try {
  177|     text = readFileSync(file, 'utf8');
  178|   } catch {
  179|     return 0;
  180|   }
  181|   const lines = text.split('\n').filter(Boolean);
  182|   let changed = 0;
  183|   const keep = lines.flatMap((l) => {
  184|     const t = stampOf(l);
  185|     if (t !== null && now - t <= maxAgeMs) return [l];
  186|     if (t === null || !scrub) {
  187|       changed += 1;
  188|       return [];
  189|     }
  190|     const row = Stamped.parse(JSON.parse(l));
  191|     if (!scrub.some((k) => k in row)) return [l];
  192|     changed += 1;
  193|     return [JSON.stringify(Object.fromEntries(Object.entries(row).filter(([k]) => !scrub.includes(k))))];
  194|   });
  195|   if (!changed) return 0;
  196|   const tmp = `${file}.${process.pid}.tmp`;
  197|   writeFileSync(tmp, keep.length ? `${keep.join('\n')}\n` : '');
  198|   renameSync(tmp, file);
  199|   return changed;
  200| }
  201| 
  202| /** Empties a plain-text log past `maxBytes` (the worker's log; CloudWatch keeps its own copy). */
  203| export function capLog(file: string, maxBytes: number): boolean {
  204|   try {
  205|     if (statSync(file).size <= maxBytes) return false;
  206|     truncateSync(file, 0);
  207|     return true;
  208|   } catch {
  209|     return false;
  210|   }
  211| }
```

## `serve/index.ts`

```ts
    1| // `pnpm serve`: the page and its API on PORT (default 8787).
    2| import { createApp } from './app';
    3| 
    4| const port = Number(process.env.PORT || 8787);
    5| createApp().listen(port, () => {
    6|   console.log(`simulacra on http://localhost:${port} (bundles from ${process.env.SIMULACRA_BUNDLES || 'serve/bundles'})`);
    7| });
```

## `serve/server.ts`

```ts
    1| // The production entry (the API container's CMD, bundled to dist/server.mjs).
    2| // `pnpm serve` (index.ts) stays the local entry. This adds what a host behind
    3| // a load balancer needs and the local server doesn't:
    4| //   - GET /healthz: 200 "ok", no dependencies, registered before the app so a
    5| //     broken bundle or router can't fail the ALB health check;
    6| //   - trust proxy TRUST_PROXY_HOPS (default 2: the request comes through
    7| //     Vercel's proxy, then the ALB), so req.ip is the visitor's address for
    8| //     the per-IP rate limits. A request sent to the ALB directly can forge
    9| //     X-Forwarded-For; the dollar caps count every visitor together, not per IP;
   10| //   - SIGTERM: stop accepting, let in-flight requests finish, exit. A running
   11| //     worker is killed with the container; its queue item stays un-done and is
   12| //     retried by the next worker.
   13| import express from 'express';
   14| import { createApp } from './app';
   15| 
   16| const port = Number(process.env.PORT || 8080);
   17| const app = express();
   18| app.disable('x-powered-by');
   19| app.set('trust proxy', Number(process.env.TRUST_PROXY_HOPS || 2));
   20| app.get('/healthz', (_req, res) => {
   21|   res.set('Cache-Control', 'no-store').type('text/plain').send('ok');
   22| });
   23| app.use(createApp());
   24| 
   25| const server = app.listen(port, () => {
   26|   console.log(`simulacra api on :${port} (bundles from ${process.env.SIMULACRA_BUNDLES || 'serve/bundles'})`);
   27| });
   28| 
   29| function shutdown(signal: string): void {
   30|   console.log(`simulacra: ${signal}, closing`);
   31|   server.close(() => process.exit(0));
   32|   server.closeIdleConnections();
   33|   // ECS's stopTimeout is 30s; leave room to exit on our own terms.
   34|   setTimeout(() => process.exit(0), 20_000).unref();
   35| }
   36| process.on('SIGTERM', () => shutdown('SIGTERM'));
   37| process.on('SIGINT', () => shutdown('SIGINT'));
```

## `serve/simulacra.test.ts`

```ts
    1| // The real router and app, in process, over real HTTP, reading the real bundles in serve/bundles/.
    2| import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
    3| import type { AddressInfo } from 'node:net';
    4| import { tmpdir } from 'node:os';
    5| import path from 'node:path';
    6| import type { Server } from 'node:http';
    7| import { afterAll, beforeAll, describe, expect, it } from 'vitest';
    8| import { z } from 'zod';
    9| import { createApp } from './app';
   10| import { Bundle } from './bundle';
   11| import { parseKeyRing } from './guard';
   12| import { DEFAULT_LIMITS, IMMUTABLE, OVER_DAILY_CAP, OVER_MONTHLY_CAP, SHORT_CACHE, type SimulacraOptions } from './simulacra';
   13| 
   14| const ROOT = path.resolve(import.meta.dirname, '..');
   15| const scratch = mkdtempSync(path.join(tmpdir(), 'simulacra-test-'));
   16| const options: SimulacraOptions = {
   17|   bundles: path.join(ROOT, 'serve', 'bundles'),
   18|   sessions: path.join(scratch, 'sessions'),
   19|   devLog: false,
   20|   autorun: null,
   21|   python: 'python3',
   22|   root: ROOT,
   23|   keys: parseKeyRing(undefined),
   24|   caps: { daily: 20, monthly: 200 },
   25|   retainDays: 7,
   26|   limits: DEFAULT_LIMITS
   27| };
   28| 
   29| let server: Server;
   30| let base = '';
   31| 
   32| beforeAll(async () => {
   33|   const build = path.join(scratch, 'build');
   34|   mkdirSync(build, { recursive: true });
   35|   writeFileSync(path.join(build, 'index.html'), '<!doctype html><title>page</title>');
   36|   server = createApp({ simulacra: options, build }).listen(0);
   37|   await new Promise<void>((resolve) => server.once('listening', resolve));
   38|   // SAFETY: listen(0) on a TCP port always reports an AddressInfo, never a pipe name.
   39|   const { port } = server.address() as AddressInfo;
   40|   base = `http://127.0.0.1:${port}`;
   41| });
   42| 
   43| afterAll(async () => {
   44|   await new Promise<void>((resolve) => server.close(() => resolve()));
   45|   rmSync(scratch, { recursive: true, force: true });
   46| });
   47| 
   48| const Election = z.object({ simulated: z.boolean(), slices: z.array(z.object({ key: z.string() })), whatIfs: z.array(z.object({ key: z.string() })) });
   49| const RunId = z.object({ id: z.string() });
   50| const Done = z.object({
   51|   status: z.literal('done'),
   52|   result: z.looseObject({
   53|     applied: z.array(z.object({ key: z.string() })),
   54|     unknown: z.string().nullable(),
   55|     range: z.unknown().optional(),
   56|     howIGotThis: z.array(z.string())
   57|   })
   58| });
   59| 
   60| async function run(body: unknown) {
   61|   const posted = await fetch(`${base}/api/simulacra/runs`, {
   62|     method: 'POST',
   63|     headers: { 'content-type': 'application/json' },
   64|     body: JSON.stringify(body)
   65|   });
   66|   expect(posted.status).toBe(200);
   67|   const { id } = RunId.parse(await posted.json());
   68|   const got = await fetch(`${base}/api/simulacra/runs/${id}`);
   69|   return Done.parse(await got.json()).result;
   70| }
   71| 
   72| describe('/api/simulacra', () => {
   73|   it('a simulated year answers simulated: true with its slices and what-ifs', async () => {
   74|     const res = await fetch(`${base}/api/simulacra/elections/1920`);
   75|     expect(res.status).toBe(200);
   76|     const e = Election.parse(await res.json());
   77|     expect(e.simulated).toBe(true);
   78|     expect(e.slices.map((s) => s.key)).toContain('women');
   79|     expect(e.whatIfs.map((w) => w.key)).toContain('league');
   80|   });
   81| 
   82|   it('a year with no bundle answers 200 with simulated: false', async () => {
   83|     const res = await fetch(`${base}/api/simulacra/elections/1999`);
   84|     expect(res.status).toBe(200);
   85|     expect(await res.json()).toEqual({ slices: [], whatIfs: [], simulated: false });
   86|   });
   87| 
   88|   it('the manifest names each published year and its run', async () => {
   89|     const res = await fetch(`${base}/api/simulacra/manifest`);
   90|     expect(res.headers.get('cache-control')).toBe(SHORT_CACHE);
   91|     const { years } = z.object({ years: z.record(z.string(), z.string()) }).parse(await res.json());
   92|     const runId = readFileSync(path.join(ROOT, 'serve', 'bundles', '1920.json'), 'utf8').match(/"runId": ?"([^"]+)"/)?.[1];
   93|     expect(years['1920']).toBe(runId);
   94|     expect(years['1999']).toBeUndefined();
   95|   });
   96| 
   97|   it("a year's answer carries its run and is immutable only at its versioned URL", async () => {
   98|     const plain = await fetch(`${base}/api/simulacra/elections/1920`);
   99|     expect(plain.headers.get('cache-control')).toBe(SHORT_CACHE);
  100|     const { runId } = z.object({ runId: z.string() }).parse(await plain.json());
  101|     const pinned = await fetch(`${base}/api/simulacra/elections/1920?v=${encodeURIComponent(runId)}`);
  102|     expect(pinned.headers.get('cache-control')).toBe(IMMUTABLE);
  103|     const stale = await fetch(`${base}/api/simulacra/elections/1920?v=not-this-run`);
  104|     expect(stale.headers.get('cache-control')).toBe(SHORT_CACHE);
  105|     const missing = await fetch(`${base}/api/simulacra/elections/1999?v=${encodeURIComponent(runId)}`);
  106|     expect(missing.headers.get('cache-control')).toBe(SHORT_CACHE);
  107|   });
  108| 
  109|   it('matches keywords as whole words: "flu" is not in "influence"', async () => {
  110|     const miss = await run({ year: 1920, text: 'the influence of the press' });
  111|     expect(miss.applied).toEqual([]);
  112|     expect(miss.unknown).toBe('the influence of the press');
  113|     const hit = await run({ year: 1920, text: 'the flu comes back' });
  114|     expect(hit.applied.map((a) => a.key)).toEqual(['influenza-returns-in-october-1920']);
  115|     expect(hit.unknown).toBeNull();
  116|   });
  117| 
  118|   it('hand edits re-tally one run with no range', async () => {
  119|     const r = await run({ year: '1920', whatIfs: ['league', 'not-a-what-if'], edits: { women: { home: -0.1, B: 0.1 } } });
  120|     expect(r.applied.map((a) => a.key)).toEqual(['league']);
  121|     expect(r.range).toBeUndefined();
  122|     expect(r.howIGotThis.at(-1)).toMatch(/by hand/);
  123|   });
  124| 
  125|   it('rejects a malformed body at the boundary', async () => {
  126|     const res = await fetch(`${base}/api/simulacra/runs`, {
  127|       method: 'POST',
  128|       headers: { 'content-type': 'application/json' },
  129|       body: JSON.stringify({ year: 'soon' })
  130|     });
  131|     expect(res.status).toBe(400);
  132|   });
  133| 
  134|   it('serves the static build with an SPA fallback', async () => {
  135|     const res = await fetch(`${base}/some/page`);
  136|     expect(res.status).toBe(200);
  137|     expect(await res.text()).toContain('<title>page</title>');
  138|   });
  139| 
  140|   it('parses the shared bundle example', () => {
  141|     const raw: unknown = JSON.parse(readFileSync(path.join(ROOT, 'tests/fixtures/bundle.example.json'), 'utf8'));
  142|     const b = Bundle.parse(raw);
  143|     expect(Object.keys(b.runs)).toContain('');
  144|     expect(Object.keys(b.tables).sort()).toEqual(Object.keys(b.runs).sort());
  145|   });
  146| });
  147| 
  148| // The intake path: SIMULACRA_LOG on, open to every visitor, a key's name recorded, per-IP limits.
  149| describe('/api/simulacra intake guard', () => {
  150|   const KEY = 'k'.repeat(32);
  151|   const sessions = path.join(scratch, 'intake-sessions');
  152|   let guarded: Server;
  153|   let url = '';
  154| 
  155|   beforeAll(async () => {
  156|     mkdirSync(sessions, { recursive: true });
  157|     const old = new Date(Date.now() - 30 * 86_400_000).toISOString();
  158|     writeFileSync(path.join(sessions, 'requests.jsonl'), `${JSON.stringify({ ts: old, text: 'a month ago' })}\n${JSON.stringify({ ts: new Date().toISOString(), text: 'today' })}\n`);
  159|     const opts: SimulacraOptions = {
  160|       ...options,
  161|       sessions,
  162|       devLog: true,
  163|       keys: parseKeyRing(JSON.stringify({ ana: KEY })),
  164|       limits: { ...DEFAULT_LIMITS, intake: { max: 3, windowMs: 60_000 } }
  165|     };
  166|     guarded = createApp({ simulacra: opts, build: path.join(scratch, 'none') }).listen(0);
  167|     await new Promise<void>((resolve) => guarded.once('listening', resolve));
  168|     // SAFETY: listen(0) on a TCP port always reports an AddressInfo, never a pipe name.
  169|     url = `http://127.0.0.1:${(guarded.address() as AddressInfo).port}/api/simulacra`;
  170|   });
  171| 
  172|   afterAll(async () => {
  173|     await new Promise<void>((resolve) => guarded.close(() => resolve()));
  174|   });
  175| 
  176|   const Unknown = z.looseObject({ unknown: z.string().nullable(), unknownWhy: z.string().optional(), queued: z.unknown().optional() });
  177| 
  178|   async function ask(text: string, key?: string): Promise<{ status: number; result: z.infer<typeof Unknown> | null }> {
  179|     const posted = await fetch(`${url}/runs`, {
  180|       method: 'POST',
  181|       headers: { 'content-type': 'application/json', ...(key ? { authorization: `Bearer ${key}` } : {}) },
  182|       body: JSON.stringify({ year: 1920, text })
  183|     });
  184|     if (posted.status !== 200) return { status: posted.status, result: null };
  185|     const { id } = RunId.parse(await posted.json());
  186|     const got = z.object({ result: Unknown }).parse(await (await fetch(`${url}/runs/${id}`)).json());
  187|     return { status: 200, result: got.result };
  188|   }
  189| 
  190|   const queue = (): string[] => {
  191|     try {
  192|       return readFileSync(path.join(sessions, 'queue.jsonl'), 'utf8').split('\n').filter(Boolean);
  193|     } catch {
  194|       return [];
  195|     }
  196|   };
  197| 
  198|   it('drops session lines older than the retention at startup', () => {
  199|     const lines = readFileSync(path.join(sessions, 'requests.jsonl'), 'utf8');
  200|     expect(lines).not.toContain('a month ago');
  201|     expect(lines).toContain('today');
  202|   });
  203| 
  204|   it('queues text without a key, or with one it does not know, under no name', async () => {
  205|     for (const [text, key] of [['the moon votes', undefined], ['mars votes', 'x'.repeat(32)]] as const) {
  206|       const r = await ask(text, key);
  207|       expect(r.result?.queued).toBeDefined();
  208|       expect(r.result?.unknownWhy).toBeUndefined();
  209|     }
  210|     expect(queue().map((l) => JSON.parse(l))).toEqual([
  211|       expect.objectContaining({ text: 'the moon votes', who: null }),
  212|       expect.objectContaining({ text: 'mars votes', who: null })
  213|     ]);
  214|   });
  215| 
  216|   it("records a valid key's name with its text", async () => {
  217|     const r = await ask('venus votes', KEY);
  218|     expect(r.result?.queued).toBeDefined();
  219|     expect(JSON.parse(queue().at(-1) ?? '{}')).toEqual(expect.objectContaining({ text: 'venus votes', who: 'ana' }));
  220|   });
  221| 
  222|   it('limits how often one IP may queue', async () => {
  223|     expect((await ask('jupiter votes')).status).toBe(429);
  224|     expect(queue()).toHaveLength(3);
  225|   });
  226| 
  227|   it('answers a year outside any election without caching it', async () => {
  228|     const res = await fetch(`${url}/elections/123456`);
  229|     expect(await res.json()).toEqual({ slices: [], whatIfs: [], simulated: false });
  230|   });
  231| });
  232| 
  233| // The dollar caps: every visitor's spend together, read from the ledger before anything is queued.
  234| describe('/api/simulacra intake dollar caps', () => {
  235|   const sessions = path.join(scratch, 'capped-sessions');
  236|   const ledger = path.join(sessions, 'spend.jsonl');
  237|   const today = new Date().toISOString().slice(0, 10);
  238|   let capped: Server;
  239|   let url = '';
  240| 
  241|   beforeAll(async () => {
  242|     mkdirSync(sessions, { recursive: true });
  243|     const opts: SimulacraOptions = { ...options, sessions, devLog: true, caps: { daily: 5, monthly: 50 } };
  244|     capped = createApp({ simulacra: opts, build: path.join(scratch, 'none') }).listen(0);
  245|     await new Promise<void>((resolve) => capped.once('listening', resolve));
  246|     // SAFETY: listen(0) on a TCP port always reports an AddressInfo, never a pipe name.
  247|     url = `http://127.0.0.1:${(capped.address() as AddressInfo).port}/api/simulacra`;
  248|   });
  249| 
  250|   afterAll(async () => {
  251|     await new Promise<void>((resolve) => capped.close(() => resolve()));
  252|   });
  253| 
  254|   const Result = z.looseObject({ unknownWhy: z.string().optional(), queued: z.unknown().optional() });
  255| 
  256|   async function ask(text: string): Promise<z.infer<typeof Result>> {
  257|     const posted = await fetch(`${url}/runs`, {
  258|       method: 'POST',
  259|       headers: { 'content-type': 'application/json' },
  260|       body: JSON.stringify({ year: 1920, text })
  261|     });
  262|     expect(posted.status).toBe(200);
  263|     const { id } = RunId.parse(await posted.json());
  264|     return z.object({ result: Result }).parse(await (await fetch(`${url}/runs/${id}`)).json()).result;
  265|   }
  266| 
  267|   const queued = (): number => {
  268|     try {
  269|       return readFileSync(path.join(sessions, 'queue.jsonl'), 'utf8').split('\n').filter(Boolean).length;
  270|     } catch {
  271|       return 0;
  272|     }
  273|   };
  274| 
  275|   it("queues nothing once today's spend, from anyone, reaches the daily cap, and says why", async () => {
  276|     // Two visitors' lines, one with a key's name and one without: both count.
  277|     writeFileSync(ledger, `${JSON.stringify({ day: today, dollars: 3, who: 'ana' })}\n${JSON.stringify({ day: today, dollars: 2, who: null })}\n`);
  278|     const r = await ask('the moon votes');
  279|     expect(r.unknownWhy).toBe(OVER_DAILY_CAP);
  280|     expect(r.queued).toBeUndefined();
  281|     expect(queued()).toBe(0);
  282|   });
  283| 
  284|   it("queues nothing once this month's spend reaches the monthly cap", async () => {
  285|     writeFileSync(ledger, `${JSON.stringify({ day: `${today.slice(0, 8)}01`, dollars: 50, who: null })}\n`);
  286|     const r = await ask('mars votes');
  287|     expect(r.unknownWhy).toBe(OVER_MONTHLY_CAP);
  288|     expect(queued()).toBe(0);
  289|   });
  290| 
  291|   it('queues again under both caps', async () => {
  292|     writeFileSync(ledger, `${JSON.stringify({ day: '2000-01-01', dollars: 500, who: null })}\n`);
  293|     const r = await ask('venus votes');
  294|     expect(r.queued).toBeDefined();
  295|     expect(queued()).toBe(1);
  296|   });
  297| });
```

## `serve/simulacra.ts`

```ts
    1| // /api/simulacra: serves precomputed harness bundles in the page's contract.
    2| //
    3| // Bundles are the harness's `published/<year>.json` files (serve/bundles/ by
    4| // default; SIMULACRA_BUNDLES points elsewhere). Everything expensive
    5| // (population draws, the backbone, LLM agents) runs offline. Online work is
    6| // lookup plus arithmetic:
    7| //   - every combination of a year's what-ifs is precomputed (with draws);
    8| //   - typed text is matched to a what-if by keyword, or returned as `unknown`;
    9| //   - hand edits (the page's dragged dots) are applied to the point run's
   10| //     state × group table and re-tallied; an edited run carries no draws, and
   11| //     says so in `howIGotThis`.
   12| // Reading is open to everyone: the demo has to work without an account. Every
   13| // client IP is rate limited (guard.ts).
   14| //
   15| // With SIMULACRA_LOG set (production sets it, and SIMULACRA_AUTORUN):
   16| //   - every POST /runs appends one line to sessions/requests.jsonl
   17| //     (ts, year, text, whatIfs, matched, unknown, combo, exists; no IPs, no ids);
   18| //   - unmatched text is queued in sessions/queue.jsonl for
   19| //     `python -m simharness.run whatif --queue`, with the name of the access key
   20| //     the request carried (SIMULACRA_ACCESS_KEYS), if any, for the spend ledger,
   21| //     while spend is under the daily and monthly dollar caps (guard.ts, every
   22| //     visitor together); over a cap, the run answers at once with `unknownWhy`
   23| //     saying so. Each IP may queue a few texts an hour (guard.ts);
   24| //   - a queued text holds its run `running` (with the worker's `steps`) when
   25| //     SIMULACRA_AUTORUN=<config path> starts that worker in the background from
   26| //     the repo root (one at a time); otherwise the result says `queued`;
   27| //   - session logs drop lines older than SIMULACRA_RETAIN_DAYS (default 7), and
   28| //     the spend ledger keeps old lines without their `note`, so visitors'
   29| //     words aren't kept for good;
   30| //   - a bundle file that changed on disk is reloaded, so a publish needs no restart.
   31| import { type ChildProcess, spawn } from 'node:child_process';
   32| import { randomUUID } from 'node:crypto';
   33| import { appendFileSync, createWriteStream, existsSync, mkdirSync, readdirSync, readFileSync, statSync } from 'node:fs';
   34| import { homedir } from 'node:os';
   35| import path from 'node:path';
   36| import express, { type ErrorRequestHandler, type RequestHandler, type Router } from 'express';
   37| import type { z } from 'zod';
   38| import {
   39|   Bundle,
   40|   type Edits,
   41|   FIELDS,
   42|   type Field,
   43|   IntakeStatus,
   44|   type PageKey,
   45|   QueueDone,
   46|   QueueFailed,
   47|   type Result,
   48|   RunRequest,
   49|   type Slice,
   50|   type Step,
   51|   type TableRow,
   52|   type Told
   53| } from './bundle';
   54| import { type Caps, capLog, capsFromEnv, checkCaps, type KeyRing, type Limit, parseKeyRing, pruneJsonl, RateLimiter } from './guard';
   55| 
   56| const ROOT = path.resolve(import.meta.dirname, '..');
   57| 
   58| export interface SimulacraOptions {
   59|   /** Folder of `<year>.json` bundles. */
   60|   bundles: string;
   61|   /** Where dev logs, the queue and the worker's status live. */
   62|   sessions: string;
   63|   /** Dev logging and queueing (SIMULACRA_LOG). */
   64|   devLog: boolean;
   65|   /** Config path for the background intake worker (SIMULACRA_AUTORUN), relative to `root`. */
   66|   autorun: string | null;
   67|   /** Python with the harness installed (SIMULACRA_PYTHON). */
   68|   python: string;
   69|   /** The repo root: the worker runs `python -m simharness.run` from here. */
   70|   root: string;
   71|   /** Access keys whose names the spend ledger records (SIMULACRA_ACCESS_KEYS). */
   72|   keys: KeyRing;
   73|   /** Dollar caps on the intake, every visitor together (SIMULACRA_DAILY_USD, SIMULACRA_MONTHLY_USD). */
   74|   caps: Caps;
   75|   /** Days session logs keep a line (SIMULACRA_RETAIN_DAYS). */
   76|   retainDays: number;
   77|   /** Per-IP rate limits. */
   78|   limits: Limits;
   79| }
   80| 
   81| export interface Limits {
   82|   /** Every request to the router. */
   83|   readonly any: Limit;
   84|   /** POST /runs. */
   85|   readonly runs: Limit;
   86|   /** POST /runs whose text would be queued. */
   87|   readonly intake: Limit;
   88| }
   89| 
   90| const MINUTE = 60_000;
   91| // The page polls a run every 300 ms (1 s while a new what-if is modelled).
   92| export const DEFAULT_LIMITS: Limits = {
   93|   any: { max: 1200, windowMs: 10 * MINUTE },
   94|   runs: { max: 120, windowMs: 10 * MINUTE },
   95|   intake: { max: 10, windowMs: 60 * MINUTE }
   96| };
   97| 
   98| export function optionsFromEnv(env: NodeJS.ProcessEnv = process.env): SimulacraOptions {
   99|   return {
  100|     bundles: env.SIMULACRA_BUNDLES || path.join(ROOT, 'serve', 'bundles'),
  101|     sessions: path.join(ROOT, 'sessions'),
  102|     devLog: Boolean(env.SIMULACRA_LOG),
  103|     autorun: env.SIMULACRA_AUTORUN || null,
  104|     python: env.SIMULACRA_PYTHON || path.join(homedir(), '.venvs/simharness/bin/python'),
  105|     root: ROOT,
  106|     keys: parseKeyRing(env.SIMULACRA_ACCESS_KEYS),
  107|     caps: capsFromEnv(env),
  108|     retainDays: env.SIMULACRA_RETAIN_DAYS ? Number(env.SIMULACRA_RETAIN_DAYS) : 7,
  109|     limits: DEFAULT_LIMITS
  110|   };
  111| }
  112| 
  113| /** The result the page receives: a bundle result plus the brief and interviews behind it. */
  114| export type RunResult = Result & {
  115|   told?: Record<string, Told>;
  116|   reading?: Record<string, unknown>[];
  117|   pre?: Record<string, unknown>;
  118|   interview?: { questions: string[] | undefined; byWhatIf: { whatIf: string; answers: unknown[] }[] };
  119|   queued?: { text: string; worker: boolean };
  120|   unknownWhy?: string;
  121| };
  122| 
  123| interface Pending {
  124|   text: string;
  125|   keys: string[];
  126|   edits: Edits;
  127|   /** The name of the access key that queued the text, if any. */
  128|   who: string | null;
  129| }
  130| 
  131| type RunEntry =
  132|   | { state: 'done'; year: number; created: number; key: string; result: RunResult }
  133|   | { state: 'pending'; year: number; created: number; pending: Pending };
  134| 
  135| type Settled =
  136|   | { status: 'running'; steps: Step[] }
  137|   | { status: 'failed'; error: string }
  138|   | { status: 'done'; key: string; result: RunResult };
  139| 
  140| type Totals = Record<PageKey, number>;
  141| 
  142| const RUN_TTL_MS = 60 * 60 * 1000;
  143| const PENDING_MS = 10 * 60 * 1000;
  144| /** Runs held at once; past it the oldest go first. */
  145| const MAX_RUNS = 10_000;
  146| /** The worker's plain-text log is emptied past this (CloudWatch keeps a copy). */
  147| const MAX_WORKER_LOG_BYTES = 20 * 1024 * 1024;
  148| const SESSION_LOGS = ['requests.jsonl', 'queue.jsonl', 'queue-done.jsonl', 'queue-failed.jsonl', 'queue-dead.jsonl'];
  149| /** The spend ledger outlives the retention, without the visitor's words in `note`. */
  150| const LEDGER_SCRUB = ['note'];
  151| /** Years a bundle can exist for; any other year is answered without touching the cache. */
  152| const FIRST_YEAR = 1789;
  153| const LAST_YEAR = 2100;
  154| 
  155| export const OVER_DAILY_CAP = 'Today’s budget for new what-ifs is spent. Try again tomorrow.';
  156| export const OVER_MONTHLY_CAP = 'This month’s budget for new what-ifs is spent.';
  157| const KEYS: readonly PageKey[] = ['A', 'B', 'O'];
  158| 
  159| export const comboKey = (keys: readonly string[]): string => [...new Set(keys)].sort().join('+');
  160| 
  161| const escapeRegExp = (s: string): string => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  162| 
  163| /** Whole words only: compiled what-ifs bring short keywords ("flu" must not match "influence"). */
  164| export function readText(b: Bundle, text: string): { keys: string[]; unknown: string | null } {
  165|   if (!text.trim()) return { keys: [], unknown: null };
  166|   const lower = text.toLowerCase();
  167|   const has = (w: string): boolean => new RegExp(`(^|[^a-z0-9])${escapeRegExp(w)}($|[^a-z0-9])`).test(lower);
  168|   const keys = b.words.filter(({ words }) => words.some(has)).map(({ key }) => key);
  169|   return keys.length ? { keys, unknown: null } : { keys: [], unknown: text };
  170| }
  171| 
  172| function edited(row: Record<Field, number>, e: Edits[string] | undefined): Record<Field, number> {
  173|   const f = Object.fromEntries(FIELDS.map((k) => [k, Math.max(0, row[k] + (e?.[k] ?? 0))]));
  174|   // SAFETY: built from FIELDS, so every Field key is present.
  175|   return f as Record<Field, number>;
  176| }
  177| 
  178| const total = (f: Record<Field, number>): number => FIELDS.reduce((s, k) => s + f[k], 0) || 1;
  179| 
  180| /** Apply hand edits to the point run's state × group table, then re-tally states and EV. */
  181| export function applyEdits(b: Bundle, result: Result, table: readonly TableRow[], edits: Edits): RunResult {
  182|   const byState = new Map<string, Totals>();
  183|   for (const row of table) {
  184|     const f = edited(row, edits[row.slice]);
  185|     const sum = total(f);
  186|     const st = byState.get(row.state) ?? { A: 0, B: 0, O: 0 };
  187|     for (const k of KEYS) st[k] += (row.adults * f[k]) / sum;
  188|     byState.set(row.state, st);
  189|   }
  190|   const ev: Totals = { A: 0, B: 0, O: 0 };
  191|   const states = result.states.map((s) => {
  192|     const v = byState.get(s.code) ?? { A: 0, B: 0, O: 0 };
  193|     const [first = 'A', second = 'B'] = [...KEYS].sort((x, y) => v[y] - v[x]);
  194|     const votes = v.A + v.B + v.O || 1;
  195|     ev[first] += b.ev[s.code] ?? 0;
  196|     return {
  197|       code: s.code,
  198|       won: first,
  199|       flipped: first !== b.historyWinner[s.code],
  200|       margin: Math.round(((v[first] - v[second]) / votes) * 1000) / 10
  201|     };
  202|   });
  203|   const need = Object.values(b.ev).reduce((s, x) => s + x, 0) / 2;
  204|   const winner = KEYS.find((k) => ev[k] > need) ?? null;
  205|   const slices = result.slices.map((s): Slice => {
  206|     const e = edits[s.key];
  207|     if (!e) return s;
  208|     const f = edited(s, e);
  209|     const sum = total(f);
  210|     return { ...s, ...Object.fromEntries(FIELDS.map((k) => [k, f[k] / sum])) };
  211|   });
  212|   const { range: _range, drawsWon: _drawsWon, ...rest } = result;
  213|   return {
  214|     ...rest,
  215|     ev,
  216|     winner,
  217|     states,
  218|     slices,
  219|     howIGotThis: [...(result.howIGotThis ?? []), 'You moved some groups by hand, so this is one run with no range.']
  220|   };
  221| }
  222| 
  223| /** One computed result for a year's what-if keys, or null when the combination wasn't precomputed. */
  224| export function compute(
  225|   b: Bundle,
  226|   keys: readonly string[],
  227|   edits: Edits,
  228|   unknown: string | null
  229| ): { key: string; result: RunResult } | null {
  230|   const key = comboKey(keys);
  231|   const base = b.runs[key];
  232|   if (!base) return null;
  233|   const result = Object.keys(edits).length ? applyEdits(b, base, b.tables[key] ?? [], edits) : base;
  234|   // Additive: the interviews behind each applied what-if, when the bundle has them.
  235|   const byWhatIf = b.interviews.byWhatIf ?? {};
  236|   const interviews = keys.flatMap((k) => {
  237|     const answers = byWhatIf[k];
  238|     return answers ? [{ whatIf: k, answers }] : [];
  239|   });
  240|   // What the voters were told for each applied what-if, and the dated newspaper items in their briefs.
  241|   const told = Object.fromEntries(keys.flatMap((k) => (b.told?.[k] ? [[k, b.told[k]]] : [])));
  242|   return {
  243|     key,
  244|     result: {
  245|       ...result,
  246|       unknown,
  247|       ...(Object.keys(told).length ? { told } : {}),
  248|       ...(b.reading?.length ? { reading: b.reading } : {}),
  249|       ...(b.pre ? { pre: b.pre } : {}),
  250|       ...(interviews.length ? { interview: { questions: b.interviews.questions, byWhatIf: interviews } } : {})
  251|     }
  252|   };
  253| }
  254| 
  255| const norm = (t: string): string => t.toLowerCase().split(/\s+/).filter(Boolean).join(' ');
  256| 
  257| function readJsonl<T>(file: string, schema: z.ZodType<T>): T[] {
  258|   let text: string;
  259|   try {
  260|     text = readFileSync(file, 'utf8');
  261|   } catch {
  262|     return [];
  263|   }
  264|   return text
  265|     .split('\n')
  266|     .filter(Boolean)
  267|     .flatMap((line) => {
  268|       try {
  269|         const parsed = schema.safeParse(JSON.parse(line));
  270|         return parsed.success ? [parsed.data] : [];
  271|       } catch {
  272|         return [];
  273|       }
  274|     });
  275| }
  276| 
  277| /** A year's answer at a URL that names its run never changes. */
  278| export const IMMUTABLE = 'public, max-age=31536000, s-maxage=31536000, immutable';
  279| /** Unversioned answers and the manifest: a minute fresh, then revalidated. */
  280| export const SHORT_CACHE = 'public, max-age=60, s-maxage=60, stale-while-revalidate=300';
  281| 
  282| export function createSimulacraRouter(opts: SimulacraOptions = optionsFromEnv()): Router {
  283|   const bundles = new Map<number, { bundle: Bundle | null; mtime: number }>();
  284|   const runs = new Map<string, RunEntry>();
  285|   let worker: ChildProcess | null = null;
  286|   let queuedWhileBusy = false;
  287| 
  288|   const mtimeOf = (file: string): number => (existsSync(file) ? statSync(file).mtimeMs : 0);
  289| 
  290|   function loadBundle(year: number): Bundle | null {
  291|     if (!Number.isInteger(year) || year < FIRST_YEAR || year > LAST_YEAR) return null;
  292|     const file = path.join(opts.bundles, `${year}.json`);
  293|     const cached = bundles.get(year);
  294|     if (cached && (!opts.devLog || cached.mtime === mtimeOf(file))) return cached.bundle;
  295|     let bundle: Bundle | null = null;
  296|     if (existsSync(file)) {
  297|       const parsed = Bundle.safeParse(JSON.parse(readFileSync(file, 'utf8')));
  298|       if (parsed.success) bundle = parsed.data;
  299|       else console.warn(`simulacra: ${file} doesn't fit the bundle contract`, parsed.error.issues.slice(0, 3));
  300|     }
  301|     bundles.set(year, { bundle, mtime: mtimeOf(file) });
  302|     return bundle;
  303|   }
  304| 
  305|   function appendLine(name: string, row: unknown): void {
  306|     try {
  307|       mkdirSync(opts.sessions, { recursive: true });
  308|       appendFileSync(path.join(opts.sessions, name), `${JSON.stringify(row)}\n`);
  309|     } catch (e) {
  310|       console.warn('simulacra: session log failed', e instanceof Error ? e.message : e);
  311|     }
  312|   }
  313| 
  314|   function startWorker(): void {
  315|     if (!opts.autorun) return;
  316|     if (worker) {
  317|       queuedWhileBusy = true;
  318|       return;
  319|     }
  320|     queuedWhileBusy = false;
  321|     mkdirSync(opts.sessions, { recursive: true });
  322|     const child = spawn(opts.python, ['-m', 'simharness.run', 'whatif', '--queue', '--limit', '5', '--config', opts.autorun], {
  323|       cwd: opts.root,
  324|       stdio: ['ignore', 'pipe', 'pipe']
  325|     });
  326|     const out = createWriteStream(path.join(opts.sessions, 'intake.log'), { flags: 'a' });
  327|     child.stdout?.pipe(out);
  328|     child.stderr?.pipe(out);
  329|     child.on('error', (e) => out.write(`simulacra: worker failed to start: ${e.message}\n`));
  330|     // Text typed while a worker ran is picked up by a fresh one (a worker that
  331|     // stopped on a cap leaves its text queued and isn't restarted by itself).
  332|     child.on('exit', () => {
  333|       worker = null;
  334|       if (queuedWhileBusy) startWorker();
  335|     });
  336|     worker = child;
  337|   }
  338| 
  339|   // Runs are added in creation order (an entry replaced in place keeps its
  340|   // slot), so the oldest are at the front: pruning stops at the first live one.
  341|   function newRun(entry: RunEntry): string {
  342|     const id = randomUUID();
  343|     runs.set(id, entry);
  344|     for (const [k, r] of runs) {
  345|       if (Date.now() - r.created <= RUN_TTL_MS && runs.size <= MAX_RUNS) break;
  346|       runs.delete(k);
  347|     }
  348|     return id;
  349|   }
  350| 
  351|   // Session logs keep SIMULACRA_RETAIN_DAYS of lines. The worker appends to
  352|   // them, so they're rewritten only while no worker runs.
  353|   function prune(): void {
  354|     if (!opts.devLog || worker) return;
  355|     const maxAge = opts.retainDays * 24 * 60 * MINUTE;
  356|     for (const name of [...SESSION_LOGS, 'spend.jsonl']) {
  357|       try {
  358|         const scrub = name === 'spend.jsonl' ? LEDGER_SCRUB : undefined;
  359|         const n = pruneJsonl(path.join(opts.sessions, name), maxAge, Date.now(), scrub);
  360|         if (n) console.log(`simulacra: ${scrub ? 'scrubbed' : 'dropped'} ${n} lines older than ${opts.retainDays} days in ${name}`);
  361|       } catch (e) {
  362|         console.warn(`simulacra: pruning ${name} failed`, e instanceof Error ? e.message : e);
  363|       }
  364|     }
  365|     capLog(path.join(opts.sessions, 'intake.log'), MAX_WORKER_LOG_BYTES);
  366|   }
  367|   prune();
  368|   setInterval(prune, 60 * MINUTE).unref();
  369| 
  370|   const limiters = {
  371|     any: new RateLimiter(opts.limits.any),
  372|     runs: new RateLimiter(opts.limits.runs),
  373|     intake: new RateLimiter(opts.limits.intake)
  374|   };
  375|   const limited = (res: express.Response, retryAfterS: number): void => {
  376|     res.set('Retry-After', String(retryAfterS)).status(429).json({ error: 'Too many requests just now. Try again in a few minutes.' });
  377|   };
  378|   const rateLimit =
  379|     (which: keyof typeof limiters): RequestHandler =>
  380|     (req, res, next) => {
  381|       const a = limiters[which].admit(req.ip ?? 'unknown');
  382|       if (a.ok) next();
  383|       else limited(res, a.retryAfterS);
  384|     };
  385| 
  386|   // Where the worker is with a pending run's text.
  387|   function settle(r: Extract<RunEntry, { state: 'pending' }>): Settled {
  388|     const t = norm(r.pending.text);
  389|     const sameYear = (x: { year?: number | null }): boolean => (x.year ?? 1920) === r.year;
  390|     const outcome = readJsonl(path.join(opts.sessions, 'queue-done.jsonl'), QueueDone)
  391|       .filter((x) => x.text === t && sameYear(x))
  392|       .pop();
  393|     const failed = readJsonl(path.join(opts.sessions, 'queue-failed.jsonl'), QueueFailed)
  394|       .filter((x) => x.text === t && sameYear(x) && x.at * 1000 >= r.created)
  395|       .pop();
  396|     const b = loadBundle(r.year);
  397|     if (outcome && (outcome.status === 'modelled' || outcome.status === 'keyword') && outcome.key && b) {
  398|       const done =
  399|         compute(b, [...new Set([...r.pending.keys, outcome.key])], r.pending.edits, null) ??
  400|         compute(b, [outcome.key], r.pending.edits, null);
  401|       if (done) return { status: 'done', key: done.key, result: done.result };
  402|       return { status: 'failed', error: 'The new what-if was modelled, but not in this combination. Try it on its own.' };
  403|     }
  404|     const stopped = outcome ?? failed;
  405|     if (stopped) {
  406|       // Not modellable, or the worker stopped: the run finishes unchanged, saying why.
  407|       const done = b ? compute(b, r.pending.keys, r.pending.edits, r.pending.text) : null;
  408|       const why = stopped.why ?? '';
  409|       if (!done) return { status: 'failed', error: why || 'Couldn’t model that.' };
  410|       return { status: 'done', key: done.key, result: { ...done.result, unknownWhy: why } };
  411|     }
  412|     if (Date.now() - r.created > PENDING_MS) return { status: 'failed', error: 'Modelling that took too long. Try again in a minute.' };
  413|     if (!worker) startWorker();
  414|     let steps: Step[] = [{ text: 'Waiting for the what-ifs typed before this one.', state: 'doing' }];
  415|     try {
  416|       const st = IntakeStatus.safeParse(JSON.parse(readFileSync(path.join(opts.sessions, 'intake-status.json'), 'utf8')));
  417|       if (st.success && st.data.text === t) steps = st.data.steps;
  418|     } catch {
  419|       // not started
  420|     }
  421|     return { status: 'running', steps: [{ text: `Reading “${r.pending.text}”: it’s new to me.`, state: 'done' }, ...steps] };
  422|   }
  423| 
  424|   const router = express.Router();
  425|   router.use(rateLimit('any'));
  426|   router.use(express.json({ limit: '64kb' }));
  427| 
  428|   // Every published year and the run its bundle came from. The page reads it
  429|   // first and asks for each year at /elections/<year>?v=<runId>, so a year's
  430|   // answer can be cached for good: a new run means a new URL.
  431|   router.get('/manifest', (_req, res) => {
  432|     const years: Record<string, string> = {};
  433|     const files = existsSync(opts.bundles) ? readdirSync(opts.bundles) : [];
  434|     for (const f of files.filter((name) => /^\d{4}\.json$/.test(name)).sort()) {
  435|       const b = loadBundle(Number(f.slice(0, 4)));
  436|       if (b) years[f.slice(0, 4)] = b.runId;
  437|     }
  438|     res.set('Cache-Control', SHORT_CACHE).json({ years });
  439|   });
  440| 
  441|   // A year without a bundle answers 200 with `simulated: false`, not 404: the
  442|   // page reads a 404 before any answer as "there is no simulation service".
  443|   router.get('/elections/:year', (req, res) => {
  444|     const b = loadBundle(Number(req.params.year));
  445|     if (!b) {
  446|       res.set('Cache-Control', SHORT_CACHE).json({ slices: [], whatIfs: [], simulated: false });
  447|       return;
  448|     }
  449|     // Immutable only when the URL names the run being served.
  450|     res.set('Cache-Control', req.query.v === b.runId ? IMMUTABLE : SHORT_CACHE);
  451|     res.json({ ...b.election, simulated: true, runId: b.runId });
  452|   });
  453| 
  454|   router.post('/runs', rateLimit('runs'), (req, res) => {
  455|     const body = RunRequest.safeParse(req.body ?? {});
  456|     if (!body.success) {
  457|       res.status(400).json({ error: 'bad request', issues: body.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`) });
  458|       return;
  459|     }
  460|     const { year, whatIfs, text, edits } = body.data;
  461|     const b = loadBundle(year);
  462|     if (!b) {
  463|       res.status(404).json({ error: 'no simulation for this year' });
  464|       return;
  465|     }
  466|     const known = new Set(b.election.whatIfs.map((w) => w.key));
  467|     const chosen = whatIfs.filter((k) => known.has(k));
  468|     const read = readText(b, text);
  469|     const keys = [...chosen, ...read.keys];
  470|     const done = compute(b, keys, edits, read.unknown);
  471|     let queued = false;
  472|     // The access key's name, if the request carried one: the spend ledger records it.
  473|     let who: string | null = null;
  474|     // Why unknown words weren't queued, when they weren't.
  475|     let unknownWhy: string | null = null;
  476|     if (opts.devLog) {
  477|       const ts = new Date().toISOString();
  478|       appendLine('requests.jsonl', { ts, year, text, whatIfs, matched: read.keys, unknown: read.unknown, combo: comboKey(keys), exists: Boolean(done) });
  479|       if (read.unknown) {
  480|         const cap = checkCaps(path.join(opts.sessions, 'spend.jsonl'), opts.caps);
  481|         if (cap.kind === 'over') unknownWhy = cap.which === 'monthly' ? OVER_MONTHLY_CAP : OVER_DAILY_CAP;
  482|         else {
  483|           const a = limiters.intake.admit(req.ip ?? 'unknown');
  484|           if (!a.ok) {
  485|             limited(res, a.retryAfterS);
  486|             return;
  487|           }
  488|           who = opts.keys.identify(req.get('authorization'));
  489|           appendLine('queue.jsonl', { ts, year, text: read.unknown, who });
  490|           queued = true;
  491|           startWorker();
  492|         }
  493|       }
  494|     }
  495|     // With the worker on, new words hold the run open (GET reports the
  496|     // worker's steps) until they are compiled, researched, interviewed and
  497|     // published; then the run finishes with the new what-if applied.
  498|     if (queued && read.unknown && opts.autorun) {
  499|       const pending = { text: read.unknown, keys: chosen, edits, who };
  500|       res.json({ id: newRun({ state: 'pending', year, created: Date.now(), pending }) });
  501|       return;
  502|     }
  503|     if (!done) {
  504|       res.status(422).json({ error: 'That combination has not been computed.' });
  505|       return;
  506|     }
  507|     let result: RunResult = done.result;
  508|     if (queued && read.unknown) result = { ...result, queued: { text: read.unknown, worker: Boolean(worker) } };
  509|     else if (unknownWhy) result = { ...result, unknownWhy };
  510|     res.json({ id: newRun({ state: 'done', year, created: Date.now(), key: done.key, result }) });
  511|   });
  512| 
  513|   router.get('/runs/:id', (req, res) => {
  514|     const r = runs.get(req.params.id);
  515|     if (!r) {
  516|       res.status(404).json({ error: 'no such run' });
  517|       return;
  518|     }
  519|     let result: RunResult;
  520|     if (r.state === 'pending') {
  521|       const s = settle(r);
  522|       if (s.status === 'running') {
  523|         res.json({ status: 'running', done: 0, total: 0, error: null, steps: s.steps });
  524|         return;
  525|       }
  526|       if (s.status === 'failed') {
  527|         runs.delete(req.params.id);
  528|         res.json({ status: 'failed', error: s.error });
  529|         return;
  530|       }
  531|       runs.set(req.params.id, { state: 'done', year: r.year, created: r.created, key: s.key, result: s.result });
  532|       result = s.result;
  533|     } else {
  534|       result = r.result;
  535|     }
  536|     const count = result.states.length;
  537|     res.json({ status: 'done', done: count, total: count, error: null, result });
  538|   });
  539| 
  540|   router.post('/runs/:id/cancel', (req, res) => {
  541|     runs.delete(req.params.id);
  542|     res.json({ ok: true });
  543|   });
  544| 
  545|   router.get('/elections/:year/voters/:slice', (req, res) => {
  546|     const b = loadBundle(Number(req.params.year));
  547|     if (!b) {
  548|       res.status(404).json({ error: 'no simulation for this year' });
  549|       return;
  550|     }
  551|     const run = typeof req.query.run === 'string' ? runs.get(req.query.run) : undefined;
  552|     const key = run?.state === 'done' ? run.key : '';
  553|     const voter = b.voters[key]?.[req.params.slice] ?? b.voters['']?.[req.params.slice];
  554|     if (!voter) {
  555|       res.status(404).json({ error: 'no voter for this group' });
  556|       return;
  557|     }
  558|     res.json(voter);
  559|   });
  560| 
  561|   // A body that isn't JSON answers in JSON too.
  562|   const onError: ErrorRequestHandler = (err: unknown, _req, res, next) => {
  563|     if (res.headersSent) {
  564|       next(err);
  565|       return;
  566|     }
  567|     const status = err instanceof SyntaxError ? 400 : 500;
  568|     res.status(status).json({ error: status === 400 ? 'bad request' : 'server error' });
  569|   };
  570|   router.use(onError);
  571| 
  572|   return router;
  573| }
```

## `simharness/__init__.py`

```python
    1| """Simulacra Americana simulation harness.
    2| 
    3| A calibrated statistical backbone decides the counts; LLM agents supply the
    4| counterfactual response (as a within-agent paired difference) and the quotes.
    5| See ../METHOD.md.
    6| """
```
