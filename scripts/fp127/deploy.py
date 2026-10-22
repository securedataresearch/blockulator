#!/usr/bin/env python3
"""Predict, deploy and size the deployed objects, in either build, from the
one objects table (gen.py's LIBS[...]["objects"], keyed as DEPLOYED).

    uv run scripts/fp127/deploy.py probe <rpc>                 # does the chain have CLZ (EIP-7939)?
    uv run scripts/fp127/deploy.py predict <key> <evm> <rpc>   # CREATE2 address, deployed or not
    uv run scripts/fp127/deploy.py deploy <key> <evm> <rpc>    # send it (reads DEPLOYER_KEY)
    uv run scripts/fp127/deploy.py address <key> <evm>         # the recorded address
    uv run scripts/fp127/deploy.py size <evm> <key>...         # runtime sizes of the artifacts

<key> is an object's make stem (fp127, fp256, fp256x, ...: gen.py --objects)
and <evm> the build, shanghai or osaka. Both go through Arachnid's CREATE2
proxy with the object's salt for that build, so an object lands at the same
address on every chain that has the proxy (and, for osaka, CLZ).

The osaka build runs CLZ, which only Fusaka/Osaka chains have. On a chain
without it the opcode is INVALID: the deployment succeeds (the init code
only copies the runtime) but every call fails and burns its gas. So deploy
and predict run `probe` first, and deploy refuses to send unless the chain
answers clz(1) = 255: an eth_call of the creation code
0x60011e60005260206000f3 (PUSH1 1, CLZ, PUSH1 0, MSTORE, PUSH1 32, PUSH1 0,
RETURN) must return the word 0xff.

Records: contracts/deployments/<Object>.json (shanghai) and
<Object>.osaka.json (osaka), receipts <Object>[.osaka].sepolia.receipt.json.
deploy writes only the receipt; the record is written by hand after verify,
as for every release.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from Crypto.Hash import keccak

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen import DEPLOYED  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CREATE2_PROXY = "0x4e59b44847b379578588920cA78FbF26c0B4956C"
CLZ_PROBE = "0x60011e60005260206000f3"
DEPLOY_GAS = os.environ.get("DEPLOY_GAS", "40000000")
NETWORK = os.environ.get("DEPLOY_NETWORK", "sepolia")


def k256(b: bytes) -> bytes:
    return keccak.new(digest_bits=256, data=b).digest()


def rpc(url: str, method: str, params: list) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json",
                                                          "User-Agent": "fp127-deploy/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def has_clz(url: str) -> tuple[bool, str]:
    """eth_call of the probe's creation code: 0x...ff where CLZ exists."""
    try:
        out = rpc(url, "eth_call", [{"data": CLZ_PROBE}, "latest"])
    except Exception as e:  # noqa: BLE001 - any transport failure is a no
        return False, f"probe failed: {e}"
    if "error" in out:
        return False, f"clz(1) reverted or failed: {out['error'].get('message', out['error'])}"
    res = out.get("result", "0x")
    ok = res.startswith("0x") and len(res) > 2 and int(res, 16) == 255
    return ok, f"clz(1) -> {res}"


def obj(key: str, evm: str) -> dict:
    if key not in DEPLOYED or evm not in ("shanghai", "osaka"):
        sys.exit(f"unknown object {key!r} or build {evm!r}; objects: {' '.join(DEPLOYED)}")
    name, lib, salts = DEPLOYED[key]
    sub = "osaka/" if evm == "osaka" else ""
    ascii_salt = salts[evm]
    salt = ascii_salt.encode().ljust(32, b"\0")
    assert len(salt) == 32, ascii_salt
    tag = ".osaka" if evm == "osaka" else ""
    return {
        "key": key, "name": name, "lib": lib, "evm": evm,
        "saltAscii": ascii_salt, "salt": salt,
        "artifact": ROOT / "out" / sub / f"{name}.yul" / f"{name}.json",
        "record": ROOT / "contracts" / "deployments" / f"{name}{tag}.json",
        "receipt": ROOT / "contracts" / "deployments" / f"{name}{tag}.{NETWORK}.receipt.json",
    }


def artifact(o: dict) -> tuple[bytes, bytes]:
    if not o["artifact"].exists():
        sys.exit(f"{o['artifact'].relative_to(ROOT)} missing: run make build{'-osaka' if o['evm'] == 'osaka' else ''}")
    d = json.loads(o["artifact"].read_text())
    return bytes.fromhex(d["bytecode"]["object"][2:]), bytes.fromhex(d["deployedBytecode"]["object"][2:])


def predicted(o: dict, init: bytes) -> str:
    raw = k256(b"\xff" + bytes.fromhex(CREATE2_PROXY[2:]) + o["salt"] + k256(init))[12:]
    h = keccak.new(digest_bits=256, data=raw.hex().encode()).hexdigest()
    return "0x" + "".join(c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(raw.hex()))


def code_at(url: str, addr: str) -> bytes:
    return bytes.fromhex(rpc(url, "eth_getCode", [addr, "latest"])["result"][2:])


def cmd_predict(key: str, evm: str, url: str) -> int:
    o = obj(key, evm)
    init, rt = artifact(o)
    addr = predicted(o, init)
    print(f"object          {o['name']} ({evm})")
    print(f"deployer        {CREATE2_PROXY}")
    print(f"salt            0x{o['salt'].hex()} ({o['saltAscii']})")
    print(f"init code hash  0x{k256(init).hex()}")
    print(f"runtime keccak  0x{k256(rt).hex()}")
    print(f"runtime bytes   {len(rt)}")
    print(f"address         {addr}")
    code = code_at(url, addr)
    print(f"deployed here   {len(code) > 0}{'' if not code or code == rt else ' (DIFFERENT CODE)'}")
    if evm == "osaka":
        ok, msg = has_clz(url)
        print(f"chain has CLZ   {ok} ({msg})")
    return 0


def cmd_probe(url: str) -> int:
    ok, msg = has_clz(url)
    print(f"CLZ {'present' if ok else 'ABSENT'}: {msg}")
    return 0 if ok else 1


def cmd_deploy(key: str, evm: str, url: str) -> int:
    o = obj(key, evm)
    pk = os.environ.get("DEPLOYER_KEY")
    if not pk:
        sys.exit("DEPLOYER_KEY is not set")
    if evm == "osaka":
        ok, msg = has_clz(url)
        if not ok:
            sys.exit(f"refusing to deploy the osaka build: this chain has no CLZ ({msg}). "
                     "Osaka code deploys fine there but every call would fail.")
        print(f"CLZ present ({msg})")
    env = dict(os.environ, FP_LIB=key, FP_EVM=evm)
    subprocess.run(["uv", "run", "scripts/fp127/stdjson.py", "check"], cwd=ROOT, env=env, check=True)
    init, rt = artifact(o)
    addr = predicted(o, init)
    print(f"address {addr}")
    if code_at(url, addr):
        print("already deployed")
        return 0
    tmp = o["receipt"].with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        subprocess.run(["cast", "send", CREATE2_PROXY, "0x" + o["salt"].hex() + init.hex(), "--rpc-url", url,
                        "--private-key", pk, "--gas-limit", DEPLOY_GAS, "--json"], stdout=f, check=True)
    r = json.loads(tmp.read_text())
    if r["status"] != "0x1":
        sys.exit(f"reverted: {r['transactionHash']} (receipt kept in {tmp.relative_to(ROOT)})")
    tmp.rename(o["receipt"])
    print("status", r["status"], "tx", r["transactionHash"], "block", int(r["blockNumber"], 16),
          "gasUsed", int(r["gasUsed"], 16))
    code = code_at(url, addr)
    print(f"code at {addr}: {len(code)} bytes{'' if code == rt else ' (DIFFERS FROM THE ARTIFACT)'}")
    return 0 if code == rt else 1


def cmd_address(key: str, evm: str) -> int:
    o = obj(key, evm)
    if not o["record"].exists():
        sys.exit(f"{o['record'].relative_to(ROOT)} missing: deploy and record first")
    print(json.loads(o["record"].read_text())["address"])
    return 0


def cmd_size(evm: str, keys: list[str]) -> int:
    for key in keys:
        o = obj(key, evm)
        _, rt = artifact(o)
        tag = " (osaka)" if evm == "osaka" else ""
        print(f"{o['name']}{tag} runtime: {len(rt)} bytes of 24576")
        if len(rt) > 24576:
            print(f"  OVER THE LIMIT by {len(rt) - 24576}")
            return 1
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "probe":
        return cmd_probe(argv[1])
    if len(argv) == 4 and argv[0] == "predict":
        return cmd_predict(*argv[1:])
    if len(argv) == 4 and argv[0] == "deploy":
        return cmd_deploy(*argv[1:])
    if len(argv) == 3 and argv[0] == "address":
        return cmd_address(*argv[1:])
    if len(argv) >= 3 and argv[0] == "size":
        return cmd_size(argv[1], argv[2:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
