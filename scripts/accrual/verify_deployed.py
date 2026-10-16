#!/usr/bin/env python3
"""Prove that the pinned submodules are the code deployed on Ethereum mainnet.

    uv run scripts/accrual/verify_deployed.py manifest [rpc]  # (network) refresh deployed-sources.json from Blockscout
    uv run scripts/accrual/verify_deployed.py build           # (offline) compile AdaptiveCurveIrm for the harness
    uv run scripts/accrual/verify_deployed.py check [rpc]     # (network) recompile every target from lib/, compare to eth_getCode

For each deployed contract that takes part in interest accrual (the Aave v3
Pool implementation behind the Core market proxy and its five linked logic
libraries, Morpho Blue, and the AdaptiveCurveIrm), deployed-sources.json
records the address, the compiler and settings, and the source file list
with the sha256 of each verified source as Blockscout serves it. `check`
reads every one of those files from the pinned submodules
(lib/aave-v3-origin @ v3.7.0, lib/morpho-blue @ v1.0.0,
lib/morpho-blue-irm @ v1.0.0), reports any whose bytes differ from the
verified source, compiles them with the recorded solc and settings, and
compares the runtime bytecode to the code at the address: immutables and
the library self-address are masked (their positions come from the
compiler), everything else, metadata included, must be equal.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rpc import DEFAULT_RPC, http_json, rpc  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "scripts" / "accrual" / "deployed-sources.json"
IRM_ARTIFACT = ROOT / "out" / "accrual" / "AdaptiveCurveIrm.json"
SOLC_LONG = {"0.8.19": "v0.8.19+commit.7dd6d404", "0.8.27": "v0.8.27+commit.40a35a09"}
SOLC_SHA256 = {  # binaries.soliditylang.org/linux-amd64/list.json
    "0.8.19": "7a5c1d3dc9a8eba62bb2ec37192c9178ae5fe8a54a56e5573fd3c9c17cd9eb48",
    "0.8.27": "b9977d500c17cba6f0032ca939ef98c4decf6363f19f386d05fb02f708115264",
}

# address, local tree, prefix rewrites (verified path prefix -> local path prefix), first match wins
TARGETS = [
    {"name": "AavePoolImpl", "address": "0x728a138a4823392c2efa55e028d434f526fe03cf",
     "note": "implementation behind the Aave v3 Core Pool proxy 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 (EIP-1967 slot), POOL_REVISION 11",
     "rewrite": [["lib/aave-v3-origin-private/", "lib/aave-v3-origin/"],
                 ["lib/aave-helpers/lib/aave-address-book/lib/aave-v3-origin/lib/solidity-utils/", "lib/aave-v3-origin/lib/solidity-utils/"]]},
    {"name": "AaveSupplyLogic", "address": "0x584C7d8c4cb05304FE5Ac7fbc97f20A10Fb07564",
     "rewrite": [["src/", "lib/aave-v3-origin/src/"], ["lib/solidity-utils/", "lib/aave-v3-origin/lib/solidity-utils/"]]},
    {"name": "AaveBorrowLogic", "address": "0x52Da0ce88202D1542543598D1e1e27F0d344726A",
     "rewrite": [["src/", "lib/aave-v3-origin/src/"], ["lib/solidity-utils/", "lib/aave-v3-origin/lib/solidity-utils/"]]},
    {"name": "AaveLiquidationLogic", "address": "0x96D5686812e33Ab509ECCDb38C89d15607B2a413",
     "rewrite": [["src/", "lib/aave-v3-origin/src/"], ["lib/solidity-utils/", "lib/aave-v3-origin/lib/solidity-utils/"]]},
    {"name": "AaveFlashLoanLogic", "address": "0x6D414cd0d5eAf8C43200ac0c325A7E2Ad83B8be6",
     "rewrite": [["src/", "lib/aave-v3-origin/src/"], ["lib/solidity-utils/", "lib/aave-v3-origin/lib/solidity-utils/"]]},
    {"name": "AavePoolLogic", "address": "0xD70593841C57cbaA04957cc3EAcE95708e48853b",
     "rewrite": [["src/", "lib/aave-v3-origin/src/"], ["lib/solidity-utils/", "lib/aave-v3-origin/lib/solidity-utils/"]]},
    {"name": "MorphoBlue", "address": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
     "rewrite": [["src/", "lib/morpho-blue/src/"]]},
    {"name": "AdaptiveCurveIrm", "address": "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",
     "rewrite": [["lib/morpho-blue/", "lib/morpho-blue/"], ["src/", "lib/morpho-blue-irm/src/"]]},
]


def local_path(t: dict, path: str) -> Path:
    for a, b in t["rewrite"]:
        if path.startswith(a):
            return ROOT / (b + path[len(a):])
    raise KeyError(path)


def find_solc(ver: str) -> str:
    p = Path.home() / ".local" / "share" / "svm" / ver / f"solc-{ver}"
    if not p.exists():
        lst = json.load(urllib.request.urlopen(urllib.request.Request(
            "https://binaries.soliditylang.org/linux-amd64/list.json", headers={"User-Agent": "curl/8"})))
        data = urllib.request.urlopen(urllib.request.Request(
            "https://binaries.soliditylang.org/linux-amd64/" + lst["releases"][ver], headers={"User-Agent": "curl/8"})).read()
        if hashlib.sha256(data).hexdigest() != SOLC_SHA256[ver]:
            sys.exit(f"solc {ver}: checksum mismatch")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        p.chmod(0o755)
    return str(p)


def manifest(url: str) -> None:
    out = {"_doc": "written by scripts/accrual/verify_deployed.py manifest from eth.blockscout.com verified sources",
           "targets": []}
    for t in TARGETS:
        d = http_json(f"https://eth.blockscout.com/api/v2/smart-contracts/{t['address']}")
        files = [{"path": d["file_path"], "content": d["source_code"]}] + \
                [{"path": f["file_path"], "content": f["source_code"]} for f in d.get("additional_sources", [])]
        settings = d["compiler_settings"]
        settings["outputSelection"] = {"*": {"*": ["evm.deployedBytecode"]}}
        libs: dict = {}
        for lib in d.get("external_libraries") or []:  # "file:Name" -> address, for every file that links it
            f, n = lib["name"].rsplit(":", 1)
            libs.setdefault(f, {})[n] = lib["address_hash"]
        settings["libraries"] = libs
        out["targets"].append({
            "name": t["name"], "address": t["address"], "note": t.get("note", ""),
            "contract": d["name"], "file": d["file_path"],
            "compiler": d["compiler_version"].lstrip("v").split("+")[0],
            "compilerLong": d["compiler_version"],
            "blockscout": {"is_fully_verified": d.get("is_fully_verified"), "is_partially_verified": d.get("is_partially_verified"),
                           "verified_at": d.get("verified_at")},
            "settings": settings,
            "sources": {f["path"]: hashlib.sha256(f["content"].encode()).hexdigest() for f in sorted(files, key=lambda f: f["path"])},
        })
        print(t["name"], d["name"], d["compiler_version"], len(files), "files")
    MANIFEST.write_text(json.dumps(out, indent=1) + "\n")


def compile_target(m: dict) -> tuple[dict, list[str]]:
    t = next(x for x in TARGETS if x["name"] == m["name"])
    sources, differ = {}, []
    for path, sha in m["sources"].items():
        text = local_path(t, path).read_text()
        if hashlib.sha256(text.encode()).hexdigest() != sha:
            differ.append(path)
        sources[path] = {"content": text}
    settings = json.loads(json.dumps(m["settings"]))
    settings["remappings"] = [r for r in settings.get("remappings", [])]
    inp = {"language": "Solidity", "sources": sources, "settings": settings}
    r = subprocess.run([find_solc(m["compiler"]), "--standard-json"], input=json.dumps(inp), capture_output=True, text=True)
    res = json.loads(r.stdout)
    errs = [e for e in res.get("errors", []) if e["severity"] == "error"]
    if errs:
        sys.exit("solc errors:\n" + "\n".join(e.get("formattedMessage", "") for e in errs))
    return res["contracts"][m["file"]][m["contract"]], differ


def masked(code: str, art: dict, is_library: bool) -> tuple[str, str]:
    """Return (deployed, compiled) runtime hex with immutable slots and the library self-address blanked."""
    comp = art["evm"]["deployedBytecode"]["object"]
    dep = code[2:] if code.startswith("0x") else code
    comp_b, dep_b = bytearray.fromhex(comp), bytearray.fromhex(dep)
    spans = [(r["start"], r["length"]) for refs in art["evm"]["deployedBytecode"].get("immutableReferences", {}).values() for r in refs]
    if is_library:
        spans.append((1, 20))  # PUSH20 <self address> call protection
    for s, n in spans:
        comp_b[s:s + n] = b"\0" * n
        dep_b[s:s + n] = b"\0" * n
    return dep_b.hex(), comp_b.hex()


def build() -> None:
    m = next(x for x in json.loads(MANIFEST.read_text())["targets"] if x["name"] == "AdaptiveCurveIrm")
    m = json.loads(json.dumps(m))
    m["settings"]["outputSelection"] = {"*": {"*": ["evm.bytecode.object", "evm.deployedBytecode"]}}
    art, differ = compile_target(m)
    if differ:
        sys.exit(f"AdaptiveCurveIrm: local sources differ from the verified ones: {differ}")
    IRM_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    IRM_ARTIFACT.write_text(json.dumps({
        "_doc": f"AdaptiveCurveIrm from lib/morpho-blue-irm (v1.0.0) compiled with solc {m['compilerLong']} and the verified settings",
        "bytecode": {"object": "0x" + art["evm"]["bytecode"]["object"]},
        "deployedBytecode": {"object": "0x" + art["evm"]["deployedBytecode"]["object"]},
    }) + "\n")
    print(f"wrote {IRM_ARTIFACT.relative_to(ROOT)}")


def check(url: str) -> dict:
    report = {"rpc": url, "block": int(rpc(url, "eth_blockNumber", []), 16), "targets": []}
    for m in json.loads(MANIFEST.read_text())["targets"]:
        art, differ = compile_target(m)
        code = rpc(url, "eth_getCode", [m["address"], hex(report["block"])])
        is_lib = m["name"] not in ("AavePoolImpl", "MorphoBlue", "AdaptiveCurveIrm")
        dep, comp = masked(code, art, is_lib)
        nimm = sum(len(v) for v in art["evm"]["deployedBytecode"].get("immutableReferences", {}).values())
        row = {"name": m["name"], "address": m["address"], "compiler": m["compilerLong"],
               "files": len(m["sources"]), "filesDifferFromVerified": differ,
               "runtimeBytes": len(dep) // 2, "immutableSlotsMasked": nimm, "libraryAddressMasked": is_lib,
               "runtimeMatches": dep == comp}
        if dep != comp and len(dep) == len(comp):
            row["firstDiffByte"] = next(i for i in range(0, len(dep), 2) if dep[i:i + 2] != comp[i:i + 2]) // 2
        report["targets"].append(row)
        print(f"{m['name']:22s} {m['address']} files={len(m['sources'])} differ={differ} "
              f"runtime={len(dep)//2}B masked={nimm}{'+lib' if is_lib else ''} match={dep == comp}")
    out = ROOT / "scripts" / "accrual" / "verify-report.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    return report


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    url = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_RPC
    if cmd == "manifest":
        manifest(url)
    elif cmd == "build":
        build()
    elif cmd == "check":
        r = check(url)
        if not all(t["runtimeMatches"] for t in r["targets"]):
            sys.exit("runtime mismatch")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
