#!/usr/bin/env python3
"""Run every merge gate and print one line per gate.

    uv run scripts/gates.py                  # all gates, the whole sweep
    uv run scripts/gates.py --ops exp,ln     # the sweep for those ops only
    uv run scripts/gates.py --quick          # every gate but the sweep
    uv run scripts/gates.py --only test,size # a subset, by name

Each gate's full output goes to cache/gates/<gate>.log and only a summary is
printed: PASS or FAIL with the numbers that matter (tests passed, misrounded
words, bytes of headroom, cells checked). On a failure the log's last lines
follow, so the cause is visible without reading the whole log. The exit code
is 1 if any gate failed.

The names gate fails on the library's old name anywhere outside lib/, in a
file or a path, except the salt literals of contracts already deployed (on a
line that says salt), whose bytes fix their addresses, and the site's redirects
from old URLs (Zola `aliases`).

The sweep gate compares the fresh sweep.json with the committed one (git HEAD):
FP19 must have 0 misrounded in both passes, and no FP127 row may have fewer
nearest results than before.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "cache" / "gates"
LIMIT = 24576
TAIL = 25


def run(name: str, cmd: str) -> tuple[bool, str, float]:
    """Run cmd in the repo, log everything, return (ok, output, seconds)."""
    t = time.time()
    p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    out = p.stdout + p.stderr
    (LOGS / f"{name}.log").write_text(out)
    return p.returncode == 0, out, time.time() - t


def tests(out: str) -> str:
    passed = sum(int(m) for m in re.findall(r"(\d+) tests? passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed, \d+ skipped \(", out))
    return f"{passed} passed, {failed} failed"


def sizes(out: str) -> tuple[bool, str]:
    rows = re.findall(r"(\w+) runtime: (\d+) bytes of (\d+)", out)
    if not rows:
        return False, "no sizes found"
    over = [n for n, b, _ in rows if int(b) > LIMIT]
    tight = min(rows, key=lambda r: LIMIT - int(r[1]))
    return not over, (f"{len(rows)} objects, tightest {tight[0]} {LIMIT - int(tight[1]):,} B free"
                      + (f"; OVER: {', '.join(over)}" if over else ""))


OLD = "fp" "256"  # split, so this file passes its own gate
SALT_LITERAL = re.compile(OLD.upper() + r"[A-Z0-9]* v\d+")


def names_check() -> tuple[bool, str, str]:
    """Every use of the old name that is not a deployed salt, as git grep lines."""
    grep = subprocess.run(["git", "grep", "-n", "-i", "-I", OLD, "--", ".", ":!lib"], cwd=ROOT, capture_output=True, text=True).stdout
    bad = [l for l in grep.splitlines()
           if not (re.search(r"(?i)salt", l) and not re.search(rf"(?i){OLD}", SALT_LITERAL.sub("", l)))
           and not re.search(r"^content/[^:]+:\d+:aliases = ", l)]
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    bad += [f"path {f}" for f in files if OLD in f.lower() and not f.startswith("lib/")]
    return not bad, f"{len(bad)} uses of the old name" if bad else "no old names", "\n".join(bad)


def sweep_check() -> tuple[bool, str]:
    new = json.loads((ROOT / "docs/benchmarks/sweep.json").read_text())["rows"]
    try:
        old = json.loads(subprocess.check_output(["git", "show", "HEAD:docs/benchmarks/sweep.json"],
                                                 cwd=ROOT, text=True))["rows"]
    except subprocess.CalledProcessError:
        old = []
    key = lambda r: (r["lib"], r["op"], r.get("stage"))  # noqa: E731
    before = {key(r): r for r in old}
    mis = [f"{r['op']}{'/' + r['stage'] if r.get('stage') else ''}={r['misrounded']}"
           for r in new if r["lib"] == "fp19" and r.get("misrounded")]
    worse = [r["op"] for r in new if r["lib"] == "fp127" and key(r) in before
             and r.get("nearest", 0) < before[key(r)].get("nearest", 0)]
    n19 = sum(1 for r in new if r["lib"] == "fp19")
    n127 = sum(1 for r in new if r["lib"] == "fp127")
    # BlockulatorWad: every row, both passes, at 0 wrong wei (and its rows present)
    wad = [r for r in new if r["lib"] == "wad"]
    wrong = [f"{r['op']}{'/' + r['stage'] if r.get('stage') else ''}={r['wrong']}" for r in wad if r.get("wrong")]
    mis += wrong
    ok = not mis and not worse and bool(wad)
    msg = (f"FP19 {n19} rows, misrounded {len(mis) - len(wrong)}; FP127 {n127} rows, nearest fell on {len(worse)}; "
           f"WAD {len(wad)} rows, {sum(r['n'] for r in wad):,} results, wrong {len(wrong)}")
    if mis:
        msg += f" [{', '.join(mis[:8])}]"
    if worse:
        msg += f" [{', '.join(worse[:8])}]"
    return ok, msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ops", help="sweep only these ops (comma-separated)")
    ap.add_argument("--quick", action="store_true", help="skip the sweep")
    ap.add_argument("--only", help="run only these gates (comma-separated names)")
    a = ap.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)

    sweep = "make sweep" + (f" OPS={a.ops}" if a.ops else "")
    gates = [
        ("names", None),
        ("gen-check", "make gen-check vectors-check gen-inputs-check gen-edges-check"),
        ("build", "make build"),
        ("test", "make test"),
        ("bounds", "uv run scripts/fp19/generators/bounds.py"),
        ("bounds127", "uv run scripts/fp127/generators/bounds127.py"),
        ("size", "make size size-fp19 size-inline-check"),
        ("ladder", "make ladder-check"),
        ("edges", "make edges-check"),
        ("cdf", "make cdf-check"),
        ("sweep", sweep),
    ]
    if a.quick:
        gates = [g for g in gates if g[0] != "sweep"]
    if a.only:
        want = set(a.only.split(","))
        gates = [g for g in gates if g[0] in want]

    failed = []
    for name, cmd in gates:
        tty = sys.stdout.isatty()
        if tty:
            print(f"{name:<10} ...", end="", flush=True)
        if cmd is None:
            t = time.time()
            ok, detail, out = names_check()
            secs = time.time() - t
        else:
            ok, out, secs = run(name, cmd)
        if name == "names":
            pass
        elif name == "test":
            detail = tests(out)
        elif name in ("bounds", "bounds127"):
            n = out.count("EXCEEDS")
            ok = ok and n == 0
            detail = f"{n} regions over their bound"
        elif name == "size":
            sok, detail = sizes(out)
            ok = ok and sok
        elif name in ("ladder", "edges"):
            m = re.search(rf"{name} ok: ([^\n]+)", out)
            detail = m.group(1) if m else "no ok line"
            ok = ok and bool(m)
        elif name == "sweep" and ok:
            ok, detail = sweep_check()
        else:
            detail = ""
        print(f"{chr(13) if tty else ''}{name:<10} {'PASS' if ok else 'FAIL'}  {secs:6.0f}s  {detail}".rstrip())
        if not ok:
            failed.append(name)
            tail = out.strip().splitlines()[-TAIL:]
            print("\n".join(f"           | {l}" for l in tail))
    print(f"\n{'all gates pass' if not failed else 'FAILED: ' + ', '.join(failed)}  (logs in cache/gates/)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
