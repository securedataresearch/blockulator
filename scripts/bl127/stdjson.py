#!/usr/bin/env python3
"""Standard-JSON input for a deployed Yul object (FP_LIB, default bl127: any
make stem of gen.py's objects table), and the bytecode proofs built on it.

    uv run scripts/bl127/stdjson.py emit              # print the standard-json input
    uv run scripts/bl127/stdjson.py check             # compile it with solc, compare to the Foundry artifact
    uv run scripts/bl127/stdjson.py onchain <rpc> <address>   # compare the live runtime to the artifact
    FP_LIB=bl19 uv run scripts/bl127/stdjson.py artifact     # compile BL19.yul with solc and write out/BL19.yul/BL19.json
    FP_LIB=bl19e uv run scripts/bl127/stdjson.py artifact    # the same for BL19E.yul (any make stem of the objects table)

The input uses language "Yul", solc 0.8.38, optimizer on, 200 runs,
evmVersion osaka (the objects use CLZ), and solc 0.8.24's default Yul
optimizer sequence (STEPS_0824, below). `artifact` writes every object's
Foundry-shaped artifact (forge builds no Yul: foundry.toml skips it). `check`
is the proof that this input reproduces the artifact's init and runtime
bytecode exactly; the same input is what the explorers receive from
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

LIB = os.environ.get("FP_LIB", "bl127")
if LIB not in DEPLOYED:
    sys.exit(f"FP_LIB must be one of {' '.join(DEPLOYED)}")
CONTRACT, LIB_DIR, _ = DEPLOYED[LIB]
SOURCE = ROOT / "contracts" / "src" / LIB_DIR / f"{CONTRACT}.yul"
ARTIFACT = ROOT / "out" / f"{CONTRACT}.yul" / f"{CONTRACT}.json"
SOURCE_UNIT = f"contracts/src/{LIB_DIR}/{CONTRACT}.yul"
SOLC_VERSION = "0.8.38"
SOLC_LONG = "v0.8.38+commit.1835d247"
EVM_VERSION = "osaka"
RUNS = 200
# Pinned: solc 0.8.24's default Yul optimizer sequence, read out of the 0.8.24
# binary. Every solc from 0.8.26 defaults to a different sequence, which on
# these objects inlines more and builds larger: the BL19 core of master
# (24,451 bytes under 0.8.24) comes out at 25,074 under 0.8.26 to 0.8.38,
# over the 24,576-byte limit, and with this sequence at 24,456. The objects
# are size-bound, so the sequence is part of the build.
STEPS_0824 = ("dhfoDgvulfnTUtnIf[xa[r]EscLMcCTUtTOntnfDIulLculVcul [j]Tpeulxa[rul]xa[r]cLgvif"
              "CTUca[r]LSsTFOtfDnca[r]Iulc]jmul[jul] VcTOcul jmul")


def std_input() -> dict:
    return {
        "language": "Yul",
        "sources": {SOURCE_UNIT: {"content": SOURCE.read_text()}},
        "settings": {
            "optimizer": {"enabled": True, "runs": RUNS,
                          "details": {"yul": True, "yulDetails": {"optimizerSteps": STEPS_0824}}},
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
    sys.exit(f"solc {SOLC_VERSION} not found; run `forge build` once so svm installs it (foundry.toml pins it)")


def compile_std(inp: dict) -> tuple[str, str]:
    out = json.loads(subprocess.run([find_solc(), "--standard-json"], input=json.dumps(inp), capture_output=True, text=True).stdout)
    errs = [e for e in out.get("errors", []) if e.get("severity") == "error"]
    if errs:
        sys.exit("solc errors:\n" + "\n".join(e.get("formattedMessage", "") for e in errs))
    evm = out["contracts"][SOURCE_UNIT][CONTRACT]["evm"]
    return evm["bytecode"]["object"], evm["deployedBytecode"]["object"]


def cmd_artifact() -> int:
    """Compile with solc and write the Foundry-shaped artifact. The Yul
    objects are kept out of forge's own build (foundry.toml `skip`): Foundry
    batches every Yul source into one solc call, Yul mode takes exactly one,
    and forge cannot pin the optimizer sequence for Yul alone."""
    init_s, rt_s = compile_std(std_input())
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "abi": [],
        "bytecode": {"object": "0x" + init_s},
        "deployedBytecode": {"object": "0x" + rt_s},
        "_doc": f"written by scripts/bl127/stdjson.py artifact (FP_LIB={LIB}) from {SOURCE_UNIT} with solc {SOLC_LONG}",
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
