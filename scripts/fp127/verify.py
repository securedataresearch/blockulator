#!/usr/bin/env python3
"""Submit the FP127 Yul object for source verification.

    uv run scripts/fp127/verify.py <chainId> <address> [sourcify|blockscout|all]

Etherscan's API accepts only Solidity single-file and Solidity standard-json
(no Yul), so the targets are Sourcify (which lists Yul as supported) and
Blockscout (whose verifier accepts standard-json with language Yul). Both
receive exactly the input that scripts/fp127/stdjson.py `check` proves
reproduces the artifact. Standard library only.
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from stdjson import CONTRACT, SOLC_LONG, SOURCE_UNIT, std_input  # noqa: E402

SOURCIFY = "https://sourcify.dev/server"
BLOCKSCOUT = {11155111: "https://eth-sepolia.blockscout.com", 1: "https://eth.blockscout.com"}
EXPLORER = {11155111: "https://repo.sourcify.dev/11155111/", 1: "https://repo.sourcify.dev/1/"}


def http(method: str, url: str, body: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fp127-verify/1.0", "Accept": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def sourcify(chain: int, address: str) -> bool:
    body = json.dumps({
        "stdJsonInput": std_input(),
        "compilerVersion": SOLC_LONG.lstrip("v"),
        "contractIdentifier": f"{SOURCE_UNIT}:{CONTRACT}",
    }).encode()
    status, text = http("POST", f"{SOURCIFY}/v2/verify/{chain}/{address}", body, {"Content-Type": "application/json"})
    print(f"sourcify submit: {status} {text[:300]}")
    if status == 409:
        print(f"sourcify: already verified  {SOURCIFY}/v2/contract/{chain}/{address}")
        return True
    if status not in (200, 202):
        return False
    vid = json.loads(text).get("verificationId")
    for _ in range(60):
        time.sleep(5)
        s, t = http("GET", f"{SOURCIFY}/v2/verify/{vid}")
        job = json.loads(t) if s == 200 else {}
        if job.get("isJobCompleted"):
            print(f"sourcify result: {json.dumps(job)[:600]}")
            ok = job.get("contract", {}).get("match") in ("exact_match", "match")
            if ok:
                print(f"sourcify: verified  {SOURCIFY}/v2/contract/{chain}/{address}")
            return ok
    print("sourcify: timed out polling")
    return False


def blockscout(chain: int, address: str) -> bool:
    base = BLOCKSCOUT.get(chain)
    if not base:
        print("blockscout: no instance configured for this chain")
        return False
    boundary = uuid.uuid4().hex
    buf = io.BytesIO()

    def field(name: str, value: str, filename: str | None = None, ctype: str | None = None) -> None:
        buf.write(f"--{boundary}\r\n".encode())
        disp = f'Content-Disposition: form-data; name="{name}"'
        if filename:
            disp += f'; filename="{filename}"'
        buf.write((disp + "\r\n").encode())
        if ctype:
            buf.write(f"Content-Type: {ctype}\r\n".encode())
        buf.write(b"\r\n" + value.encode() + b"\r\n")

    field("compiler_version", SOLC_LONG)
    field("license_type", "mit")
    field("autodetect_constructor_args", "true")
    field("files[0]", json.dumps(std_input()), f"{CONTRACT}.json", "application/json")
    buf.write(f"--{boundary}--\r\n".encode())
    status, text = http("POST", f"{base}/api/v2/smart-contracts/{address}/verification/via/standard-input",
                        buf.getvalue(), {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    print(f"blockscout submit: {status} {text[:300]}")
    if status != 200:
        return False
    for _ in range(36):
        time.sleep(5)
        s, t = http("GET", f"{base}/api/v2/smart-contracts/{address}")
        if s == 200 and json.loads(t).get("is_verified"):
            print(f"blockscout: verified  {base}/address/{address}?tab=contract")
            return True
    print("blockscout: not verified after polling; check the address page")
    return False


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    chain, address = int(argv[0]), argv[1]
    which = argv[2] if len(argv) > 2 else "all"
    results = []
    if which in ("sourcify", "all"):
        results.append(("sourcify", sourcify(chain, address)))
    if which in ("blockscout", "all"):
        results.append(("blockscout", blockscout(chain, address)))
    for name, ok in results:
        print(f"{name}: {'ok' if ok else 'FAILED'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
