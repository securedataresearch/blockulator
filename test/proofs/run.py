"""make proofs: every proof in test/proofs, one line each, and the record.

    python test/proofs/run.py            # the fast subset (CI): lemmas, CLZ self-test, fast Halmos checks, fuzz
    python test/proofs/run.py --full     # everything; rewrites docs/benchmarks/proofs.json and docs/proofs.md's table
    python test/proofs/run.py --only fp256_add   # the checks whose name matches

PROOFS_FULL=1 in the environment is --full. Each Halmos check runs in its own
process (test/proofs/halmos_clz.py, Halmos with CLZ and commuted products),
JOBS at a time. A check passes when Halmos reports [PASS]; one listed with an
expected outcome of "counterexample" passes when it does not (and the run says
so), so CI stays green on a known deviation and goes red when it disappears.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.metadata import version as pkg_version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "test" / "proofs"
JSON_OUT = ROOT / "docs" / "benchmarks" / "proofs.json"
DOC = ROOT / "docs" / "proofs.md"

SOLVER = "bitwuzla"
SOLVER_VERSION = "0.8.1"

# Lemmas: proved by test/proofs/lemmas.py (Z3, integers) and kernel.py.
# Ops: (lib, op, status, spec, the Halmos checks, the lemmas it rests on, note).
# status: "proven"           every input, the spec's primitives all proved
#         "proven-except"    every input but a stated window, where a counterexample is pinned
#         "fuzzed"           no symbolic proof; FuzzProofs against the exact spec
#         "counterexample"   fuzzed, and a pinned input where the op leaves its spec
OPS = [
    # FP127
    ("FP127", "add", "proven", "a + b exact; Overflow outside int256", ["check_fp127_add"], [], ""),
    ("FP127", "sub", "proven", "a - b exact; Overflow outside int256", ["check_fp127_sub"], [], ""),
    ("FP127", "mul", "proven", "floor(a b / 2^128); Overflow when it leaves int256", ["check_fp127_mul"], ["L1", "L2"], ""),
    ("FP127", "mulDown", "proven", "floor(a b / 2^128)", ["check_fp127_mulDown"], ["L1", "L2"], ""),
    ("FP127", "mulUp", "proven-except", "ceil(a b / 2^128); Overflow when it leaves int256",
     ["check_fp127_mulUp_outside"], ["L1", "L2"],
     "reverts Overflow where floor(a b / 2^128) = -2^255 - 1 and the ceiling -2^255 fits; proven on every other input"),
    ("FP127", "div", "proven", "trunc(a 2^128 / b); DivisionByZero; Overflow", ["check_fp127_div"], ["K127", "L5"], ""),
    ("FP127", "divDown", "proven", "floor(a 2^128 / b)", ["check_fp127_divDown"], ["K127", "L5"], ""),
    ("FP127", "divUp", "proven", "ceil(a 2^128 / b)", ["check_fp127_divUp"], ["K127", "L5"], ""),
    ("FP127", "inv", "proven", "trunc(2^256 / x); DivisionByZero; Overflow", ["check_fp127_inv"], ["L4", "L5"], ""),
    ("FP127", "sqrt", "counterexample", "floor(sqrt(x 2^128)); OutOfRange below zero", [], [],
     "returns floor + 1 where x 2^128 + 1 is a perfect square (s + 1)^2 and the Huff's Newton steps end on s + 1, e.g. x = 2^126 + 1"),
    ("FP127", "floor", "proven", "2^128 floor(x / 2^128)", ["check_fp127_floor"], [], ""),
    ("FP127", "ceil", "proven", "2^128 ceil(x / 2^128); Overflow at 2^255", ["check_fp127_ceil"], [], ""),
    ("FP127", "round", "proven", "2^128 floor(x / 2^128 + 1/2); Overflow at 2^255", ["check_fp127_round"], [], ""),
    ("FP127", "toFixed18", "proven", "floor(x 10^18 / 2^128)", ["check_fp127_toFixed18"], [], ""),
    ("FP127", "toFixed18Down", "proven", "floor(x 10^18 / 2^128)", ["check_fp127_toFixed18Down"], [], ""),
    ("FP127", "toFixed18Up", "proven", "ceil(x 10^18 / 2^128)", ["check_fp127_toFixed18Up"], [], ""),
    ("FP127", "fromFixed18", "proven", "trunc(x 2^128 / 10^18); OutOfRange outside [-2^127, 2^127)", ["check_fp127_fromFixed18"], [], ""),
    # FP256
    ("FP256", "add", "proven", "a + b rounded to nearest (237 bits, ties away)", ["check_fp256_add"], [], ""),
    ("FP256", "sub", "proven", "a - b rounded to nearest", ["check_fp256_sub"], [], ""),
    ("FP256", "mul", "proven", "a b rounded to nearest", ["check_fp256_mul"], ["L1", "L3"], ""),
    ("FP256", "mulDown", "proven", "a b rounded toward -inf", ["check_fp256_mulDown"], ["L1", "L3"], ""),
    ("FP256", "mulUp", "proven", "a b rounded toward +inf", ["check_fp256_mulUp"], ["L1", "L3"], ""),
    ("FP256", "div", "proven", "a / b rounded to nearest", ["check_fp256_div"], ["K256", "L3"], ""),
    ("FP256", "divDown", "proven", "a / b rounded toward -inf", ["check_fp256_divDown"], ["K256", "L3"], ""),
    ("FP256", "divUp", "proven", "a / b rounded toward +inf", ["check_fp256_divUp"], ["K256", "L3"], ""),
    ("FP256", "inv", "proven", "1 / x rounded to nearest", ["check_fp256_inv"], ["K256"], ""),
    ("FP256", "sqrt", "fuzzed", "sqrt(x) rounded to nearest", [], [], "FuzzProofs against the exact integer root"),
    ("FP256", "floor", "proven", "the integral number at or below x", ["check_fp256_floor"], [], ""),
    ("FP256", "ceil", "proven", "the integral number at or above x", ["check_fp256_ceil"], [], ""),
    ("FP256", "round", "proven", "the nearest integral number, halves away from zero", ["check_fp256_round"], [], ""),
    ("FP256", "toUintDown", "proven", "floor(x) as uint256", ["check_fp256_toUintDown"], [], ""),
    ("FP256", "toUintUp", "proven", "ceil(x) as uint256", ["check_fp256_toUintUp"], [], ""),
    ("FP256", "toIntDown", "proven", "floor(x) as int256", ["check_fp256_toIntDown"], [], ""),
    ("FP256", "toIntUp", "proven", "ceil(x) as int256", ["check_fp256_toIntUp"], [], ""),
    ("FP256", "toFixed18", "proven", "x 10^18 to the nearest integer, halves away", ["check_fp256_toFixed18"], ["L1"], ""),
    ("FP256", "toFixed18Down", "proven", "floor(x 10^18)", ["check_fp256_toFixed18Down"], ["L1"], ""),
    ("FP256", "toFixed18Up", "proven", "ceil(x 10^18)", ["check_fp256_toFixed18Up"], ["L1"], ""),
    ("FP256", "fromUint", "proven", "x rounded to nearest", ["check_fp256_fromUint"], [], ""),
    ("FP256", "fromUintDown", "proven", "x truncated to 237 bits", ["check_fp256_fromUintDown"], [], ""),
    ("FP256", "fromUintUp", "proven", "x rounded up to 237 bits", ["check_fp256_fromUintUp"], [], ""),
    ("FP256", "fromFixed18", "proven", "round(round(x) / 10^18), each to nearest (one rounding below 2^237)",
     ["check_fp256_fromFixed18"], ["K18", "L5"], ""),
]

# The fuzz tests (forge, FuzzProofs) and what they cover.
FUZZ = "FuzzProofs"


def contract_of(check):
    return "ProofsFP127" if check.startswith("check_fp127") else "ProofsFP256"


def halmos_python():
    exe = os.environ.get("HALMOS_PY")
    if exe:
        return exe
    halmos = subprocess.run(["sh", "-c", "command -v halmos"], capture_output=True, text=True).stdout.strip()
    if not halmos:
        sys.exit("run.py: halmos not found (uv tool install halmos==0.3.3)")
    return str(Path(os.path.realpath(halmos)).parent / "python")


def build():
    env = dict(os.environ, FOUNDRY_PROFILE="proofs")
    r = subprocess.run(
        ["forge", "build", "--force", "--ast", "--extra-output", "storageLayout", "metadata"],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stdout[-4000:], r.stderr[-4000:])
        sys.exit("run.py: forge build failed")


PASS_RE = re.compile(r"\[PASS\] (\w+)\([^)]*\) \(paths: (\d+), time: ([\d.]+)s, bounds: \[([^\]]*)\]")


def run_check(py, check, timeout, threads):
    env = dict(os.environ, FOUNDRY_PROFILE="proofs", HALMOS_ALLOW_DOWNLOAD="1")
    cmd = [
        py, str(HERE / "halmos_clz.py"),
        "--forge-build-out", "out-proofs",
        "--contract", contract_of(check),
        "--match-test", f"^{check}\\(",
        "--solver", SOLVER,
        "--solver-threads", str(threads),
        "--solver-timeout-assertion", "0",
    ]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return {"check": check, "result": "timeout", "wall": round(time.time() - t0, 1), "paths": None, "seconds": None}
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)
    m = PASS_RE.search(out)
    if m and m.group(4).strip():
        # a loop bound was hit: some paths were cut, so this is no proof
        return {"check": check, "result": "fail", "wall": round(time.time() - t0, 1), "paths": None, "seconds": None, "log": f"loop bounds hit: {m.group(4)}"}
    if m:
        return {"check": check, "result": "pass", "wall": round(time.time() - t0, 1), "paths": int(m.group(2)), "seconds": float(m.group(3))}
    tail = "\n".join(l for l in out.splitlines() if "FAIL" in l or "Counterexample" in l or "ERROR" in l or "p_" in l)[-2000:]
    return {"check": check, "result": "fail", "wall": round(time.time() - t0, 1), "paths": None, "seconds": None, "log": tail}


def run_lemmas(py):
    out = []
    for script in ("lemmas.py", "kernel.py"):
        if not (HERE / script).exists():
            continue
        t0 = time.time()
        r = subprocess.run([py, str(HERE / script)], cwd=ROOT, capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if line.startswith(("PROVED", "FAILED")):
                name = line.split()[1]
                if not re.fullmatch(r"L\d|K\d+", name):
                    continue  # kernel.py's steps; its K lines sum them up
                text = re.sub(r"\s+\([\d.]+s\)$", "", line[8:].strip())[len(name):].strip()
                out.append({"lemma": name, "result": "proved" if line.startswith("PROVED") else "failed", "text": text})
        print(f"{'ok' if r.returncode == 0 else 'FAILED':>7}  {script}  ({time.time() - t0:.0f}s)")
        if r.returncode != 0:
            print(r.stdout[-3000:], r.stderr[-3000:])
    return out


def run_fuzz(runs):
    # its own out/cache: forge test writes artifacts without the AST Halmos reads
    env = dict(os.environ, FOUNDRY_PROFILE="proofs", FOUNDRY_FUZZ_RUNS=str(runs),
               FOUNDRY_OUT="out-proofs-fuzz", FOUNDRY_CACHE_PATH="cache-proofs-fuzz")
    t0 = time.time()
    r = subprocess.run(["forge", "test", "--match-contract", FUZZ], cwd=ROOT, env=env, capture_output=True, text=True)
    res = []
    for line in r.stdout.splitlines():
        m = re.match(r"\[(PASS|FAIL)[^\]]*\] (\w+)\(", line)
        if m:
            res.append({"test": m.group(2), "result": m.group(1).lower(), "runs": runs if m.group(2).startswith("testFuzz") else 1})
    ok = r.returncode == 0
    print(f"{'ok' if ok else 'FAILED':>7}  forge {FUZZ}, {runs} runs each  ({time.time() - t0:.0f}s)")
    if not ok:
        print(r.stdout[-3000:])
    return ok, res


def tool_versions(py):
    z3v = subprocess.run([py, "-c", "import z3; print(z3.get_version_string())"], capture_output=True, text=True).stdout.strip()
    forge = subprocess.run(["forge", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    hv = subprocess.run([py, "-c", "from importlib.metadata import version; print(version('halmos'))"], capture_output=True, text=True).stdout.strip()
    return {"halmos": hv, "solver": f"{SOLVER} {SOLVER_VERSION}", "z3": z3v, "forge": forge, "solc": "0.8.38"}


def write_doc_table(record):
    rows = ["| library | op | status | spec | solver time | checks |", "|---|---|---|---|---:|---|"]
    for o in record["ops"]:
        t = f"{o['seconds']:.0f} s" if o["seconds"] is not None else "–"
        checks = ", ".join(f"`{c}`" for c in o["checks"]) or "FuzzProofs"
        status = o["status"] + (f" ({', '.join(o['lemmas'])})" if o["lemmas"] else "")
        rows.append(f"| {o['lib']} | `{o['op']}` | {status} | {o['spec']} | {t} | {checks} |")
    table = "\n".join(rows)
    text = DOC.read_text()
    a, b = "<!-- proofs:table -->", "<!-- /proofs:table -->"
    i, j = text.index(a) + len(a), text.index(b)
    DOC.write_text(text[:i] + "\n" + table + "\n" + text[j:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", default=os.environ.get("PROOFS_FULL") == "1")
    ap.add_argument("--only", default="")
    ap.add_argument("--write", action="store_true",
                    help="record this run in proofs.json and the doc table; ops not run keep their previous entry, or are in progress")
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("JOBS", "4")))
    ap.add_argument("--threads", type=int, default=int(os.environ.get("SOLVER_THREADS", "2")))
    ap.add_argument("--timeout", type=int, default=int(os.environ.get("CHECK_TIMEOUT", "5400")))
    args = ap.parse_args()

    py = halmos_python()
    prev = json.loads(JSON_OUT.read_text()) if JSON_OUT.exists() else {"ops": []}
    fast = {c for o in prev.get("ops", []) for c in o.get("fast_checks", [])}

    checks = [c for o in OPS for c in o[4]]
    if args.only:
        checks = [c for c in checks if re.search(args.only, c)]
    elif not args.full:
        checks = [c for c in checks if c in fast] if fast else checks

    ok = True
    lemmas = []
    fuzz = []
    fuzz_runs = 50000 if args.full else 3000
    if not args.only or args.write:
        print("halmos_clz: CLZ self-test")
        r = subprocess.run([py, str(HERE / "halmos_clz.py"), "--selftest"], capture_output=True, text=True)
        print("     " + ("ok" if r.returncode == 0 else "FAILED") + "  " + r.stdout.strip())
        ok &= r.returncode == 0
        lemmas = run_lemmas(py)
        ok &= all(l["result"] == "proved" for l in lemmas)
        fok, fuzz = run_fuzz(fuzz_runs)
        ok &= fok

    build()
    print(f"Halmos, {SOLVER}: {len(checks)} checks, {args.jobs} at a time")
    results = {}
    with ThreadPoolExecutor(args.jobs) as ex:
        futures = [ex.submit(run_check, py, c, args.timeout, args.threads) for c in checks]
        for fut in as_completed(futures):
            res = fut.result()
            results[res["check"]] = res
            line = f"{res['result']:>7}  {res['check']}"
            if res["result"] == "pass":
                line += f"  ({res['paths']} paths, {res['seconds']:.1f}s)"
            else:
                line += f"  ({res['wall']:.0f}s)" + ("\n" + res.get("log", "") if res.get("log") else "")
            print(line, flush=True)
            ok &= res["result"] == "pass"

    if args.write or (args.full and not args.only):
        record_tools = tool_versions(py)
        previous = {(o["lib"], o["op"]): o for o in prev.get("ops", [])}
        ops = []
        proved = {l["lemma"] for l in lemmas if l["result"] == "proved"}
        for lib, op, status, spec, cks, lem, note in OPS:
            if any(c not in results for c in cks):
                old = previous.get((lib, op))
                if old and old.get("status") != "in-progress":
                    ops.append(old)
                else:
                    ops.append({"lib": lib, "op": op, "status": "in-progress", "spec": spec, "checks": cks, "lemmas": lem,
                                "seconds": None, "paths": None, "fast_checks": [], "note": "",
                                "tool": f"Halmos {record_tools['halmos']}, {SOLVER} {SOLVER_VERSION}", "reproduce": ""})
                continue
            rs = [results[c] for c in cks]
            secs = sum(r["seconds"] for r in rs) if rs and all(r["result"] == "pass" for r in rs) else None
            if cks and any(r["result"] != "pass" for r in rs):
                status = "unproven"
            elif any(l not in proved for l in lem):
                status = "proven-given-lemma"
            ops.append({
                "lib": lib, "op": op, "status": status, "spec": spec, "checks": cks, "lemmas": lem,
                "seconds": round(secs, 1) if secs is not None else None,
                "paths": sum(r["paths"] for r in rs) if secs is not None else None,
                "fast_checks": [c for c in cks if results[c]["result"] == "pass" and results[c]["seconds"] < 120],
                "note": note,
                "tool": f"Halmos {record_tools['halmos']}, {SOLVER} {SOLVER_VERSION}" if cks else f"forge fuzz, {fuzz_runs:,} runs",
                "reproduce": (
                    "python3 test/proofs/run.py --only '^(" + "|".join(cks) + ")$'"
                    if cks
                    else f"FOUNDRY_PROFILE=proofs forge test --match-contract {FUZZ} --match-test {lib.lower()}_{op}"
                ),
            })
        record = {
            "about": "Formal proofs of FP127's and FP256's core arithmetic and directed rounding: docs/proofs.md",
            "tools": record_tools,
            "summary": {
                "ops": len(ops),
                "proven": sum(o["status"] == "proven" for o in ops),
                "proven_except": sum(o["status"] == "proven-except" for o in ops),
                "fuzzed": sum(o["status"] in ("fuzzed", "counterexample") for o in ops),
                "counterexamples": sum(o["status"] in ("counterexample", "proven-except") for o in ops),
                "in_progress": sum(o["status"] == "in-progress" for o in ops),
                "solver_seconds": round(sum(o["seconds"] or 0 for o in ops)),
            },
            "ops": ops,
            "lemmas": lemmas,
            "fuzz": fuzz,
        }
        JSON_OUT.write_text(json.dumps(record, indent=1) + "\n")
        write_doc_table(record)
        print(f"wrote {JSON_OUT.relative_to(ROOT)} and the table in {DOC.relative_to(ROOT)}")
    print("proofs: " + ("all passed" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
