#!/usr/bin/env python3
"""Standard-JSON input for the FP127 (or, with FP_LIB=fp256, the FP256) Yul
object, and the bytecode proofs built on it.

    uv run scripts/fp127/stdjson.py emit              # print the standard-json input
    uv run scripts/fp127/stdjson.py check             # compile it with solc, compare to the Foundry artifact
    uv run scripts/fp127/stdjson.py onchain <rpc> <address>   # compare the live runtime to the artifact
    FP_LIB=fp256 uv run scripts/fp127/stdjson.py artifact     # compile FP256.yul with solc and write out/FP256.yul/FP256.json
    FP_LIB=fp256x uv run scripts/fp127/stdjson.py artifact    # the same for FP256X.yul (release four's second object)
    FP_EVM=osaka FP_LIB=fp127 uv run scripts/fp127/stdjson.py artifact   # the osaka build of an object:
                                                      # contracts/src/<lib>/osaka/<Object>.yul -> out/osaka/<Object>.yul/<Object>.json

FP_LIB is any key of gen.py's DEPLOYED (the objects table). The shanghai
input uses language "Yul" and the settings from foundry.toml (solc 0.8.24,
optimizer on, 200 runs, shanghai); the osaka build (FP_EVM=osaka) the same
with solc 0.8.38 and evmVersion osaka, the pinned settings of BUILDS below.
`check` is the proof that this input reproduces the artifact's init and
runtime bytecode exactly; the same input is what the explorers receive from
verify.py.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen import DEPLOYED  # noqa: E402

# The two pinned builds. shanghai is foundry.toml's default profile and the
# deployed release; osaka is the CLZ build (gen.py --evm osaka), one pinned
# solc with the clz builtin. Its sources and artifacts live under osaka/.
#
# The osaka build pins solc 0.8.24's default Yul optimizer sequence (STEPS_0824,
# read out of the 0.8.24 binary). 0.8.26 and later default to a different
# sequence, which builds the unchanged shanghai FP256.yul at 25,074 bytes
# against 0.8.24's 24,451, over the 24,576 limit; with this sequence 0.8.38
# builds it at 24,456 and the osaka FP256 at 24,414. It also keeps the two
# builds' code shapes alike, so the gas table compares msb and little else.
STEPS_0824 = ("dhfoDgvulfnTUtnIf[xa[r]EscLMcCTUtTOntnfDIulLculVcul [j]Tpeulxa[rul]xa[r]cLgvif"
              "CTUca[r]LSsTFOtfDnca[r]Iulc]jmul[jul] VcTOcul jmul")
BUILDS = {
    "shanghai": {"solc": "0.8.24", "long": "v0.8.24+commit.e11b9ed9", "evm": "shanghai", "dir": ""},
    "osaka": {"solc": "0.8.38", "long": "v0.8.38+commit.1835d247", "evm": "osaka", "dir": "osaka/",
              "steps": STEPS_0824},
}
# FP_LIB selects the object (fp127, fp256, fp256x, ...: DEPLOYED's keys) and
# FP_EVM the build; the proofs are otherwise identical
LIB = os.environ.get("FP_LIB", "fp127")
EVM = os.environ.get("FP_EVM", "shanghai")
if LIB not in DEPLOYED or EVM not in BUILDS:
    sys.exit(f"FP_LIB must be one of {sorted(DEPLOYED)} and FP_EVM one of {sorted(BUILDS)}")
CONTRACT, LIB_DIR, _ = DEPLOYED[LIB]
BUILD = BUILDS[EVM]
SOURCE_UNIT = f"contracts/src/{LIB_DIR}/{BUILD['dir']}{CONTRACT}.yul"
SOURCE = ROOT / SOURCE_UNIT
ARTIFACT = ROOT / "out" / BUILD["dir"] / f"{CONTRACT}.yul" / f"{CONTRACT}.json"
SOLC_VERSION = BUILD["solc"]
SOLC_LONG = BUILD["long"]
EVM_VERSION = BUILD["evm"]
RUNS = 200
OPTIMIZER_DETAILS = ({"details": {"yul": True, "yulDetails": {"optimizerSteps": BUILD["steps"]}}}
                     if "steps" in BUILD else {})


def std_input() -> dict:
    return {
        "language": "Yul",
        "sources": {SOURCE_UNIT: {"content": SOURCE.read_text()}},
        "settings": {
            "optimizer": {"enabled": True, "runs": RUNS, **OPTIMIZER_DETAILS},
            "evmVersion": EVM_VERSION,
            "outputSelection": {"*": {"*": ["evm.bytecode.object", "evm.deployedBytecode.object"]}},
        },
    }


def artifact() -> tuple[str, str]:
    d = json.loads(ARTIFACT.read_text())
    return d["bytecode"]["object"][2:], d["deployedBytecode"]["object"][2:]


def keccak_hex(hexstr: str) -> str:
    return "0x" + keccak.new(digest_bits=256, data=bytes.fromhex(hexstr)).hexdigest()


def find_solc() -> str:
    candidates = [
        Path.home() / ".local" / "share" / "svm" / SOLC_VERSION / f"solc-{SOLC_VERSION}",
        Path.home() / ".svm" / SOLC_VERSION / f"solc-{SOLC_VERSION}",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    s = shutil.which("solc")
    if s:
        v = subprocess.run([s, "--version"], capture_output=True, text=True).stdout
        if SOLC_VERSION in v:
            return s
    sys.exit(f"solc {SOLC_VERSION} not found; run `forge build` once so svm installs it"
             + (" (osaka: `forge build --profile osaka`, or `svm install 0.8.38`)" if EVM == "osaka" else ""))


def compile_std(inp: dict) -> tuple[str, str]:
    out = json.loads(subprocess.run([find_solc(), "--standard-json"], input=json.dumps(inp), capture_output=True, text=True).stdout)
    errs = [e for e in out.get("errors", []) if e.get("severity") == "error"]
    if errs:
        sys.exit("solc errors:\n" + "\n".join(e.get("formattedMessage", "") for e in errs))
    evm = out["contracts"][SOURCE_UNIT][CONTRACT]["evm"]
    return evm["bytecode"]["object"], evm["deployedBytecode"]["object"]


def cmd_artifact() -> int:
    """Compile with solc and write the Foundry-shaped artifact. FP256.yul is
    kept out of forge's own build (foundry.toml `skip`): Foundry 1.8 batches
    every Yul source into one solc call, and Yul mode takes exactly one."""
    init_s, rt_s = compile_std(std_input())
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "abi": [],
        "bytecode": {"object": "0x" + init_s},
        "deployedBytecode": {"object": "0x" + rt_s},
        "_doc": f"written by scripts/fp127/stdjson.py artifact (FP_LIB={LIB}{' FP_EVM=osaka' if EVM == 'osaka' else ''}) from {SOURCE_UNIT} with solc {SOLC_LONG}",
    }, indent=1) + "\n")
    print(f"wrote {ARTIFACT.relative_to(ROOT)}: init {len(init_s)//2} bytes, runtime {len(rt_s)//2} bytes, keccak {keccak_hex(rt_s)}")
    return 0


def cmd_check() -> int:
    init_a, rt_a = artifact()
    init_s, rt_s = compile_std(std_input())
    ok = init_a == init_s and rt_a == rt_s
    print(f"init code   {len(init_a)//2} bytes  hash {keccak_hex(init_a)}  {'match' if init_a == init_s else 'MISMATCH'}")
    print(f"runtime     {len(rt_a)//2} bytes  keccak {keccak_hex(rt_a)}  {'match' if rt_a == rt_s else 'MISMATCH'}")
    return 0 if ok else 1


def cmd_onchain(rpc: str, address: str) -> int:
    _, rt_a = artifact()
    code = subprocess.run(["cast", "code", address, "--rpc-url", rpc], capture_output=True, text=True, check=True).stdout.strip()
    if code.startswith("0x"):
        code = code[2:]
    same = code == rt_a
    print(f"on-chain    {len(code)//2} bytes  keccak {keccak_hex(code) if code else '-'}")
    print(f"artifact    {len(rt_a)//2} bytes  keccak {keccak_hex(rt_a)}")
    print("MATCH" if same else "MISMATCH")
    return 0 if same else 1


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "emit":
        print(json.dumps(std_input(), indent=1))
        return 0
    if argv[0] == "check":
        return cmd_check()
    if argv[0] == "artifact":
        return cmd_artifact()
    if argv[0] == "onchain" and len(argv) == 3:
        return cmd_onchain(argv[1], argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
