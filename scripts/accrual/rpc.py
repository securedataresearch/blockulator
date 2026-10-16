"""Minimal JSON-RPC and ABI helpers for the deployed-accrual scripts (no web3 dependency)."""
from __future__ import annotations

import json
import time
import urllib.request

from Crypto.Hash import keccak

DEFAULT_RPC = "https://ethereum-rpc.publicnode.com"
UA = {"User-Agent": "blockulator-accrual/1.0", "content-type": "application/json"}


def sel(sig: str) -> str:
    return "0x" + keccak.new(digest_bits=256, data=sig.encode()).hexdigest()[:8]


def http_json(url: str, payload=None, tries: int = 5):
    data = None if payload is None else json.dumps(payload).encode()
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as e:  # transient RPC failures are retried
            err = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def rpc(url: str, method: str, params: list):
    r = http_json(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in r:
        raise RuntimeError(f"{method}: {r['error']}")
    return r["result"]


def batch_call(url: str, calls: list[tuple[str, str]], block: str, chunk: int = 40) -> list[str | None]:
    """eth_call for each (to, data) at `block`; None where the call reverted."""
    out: list[str | None] = []
    for i in range(0, len(calls), chunk):
        part = calls[i:i + chunk]
        payload = [{"jsonrpc": "2.0", "id": j, "method": "eth_call", "params": [{"to": to, "data": data}, block]}
                   for j, (to, data) in enumerate(part)]
        res = http_json(url, payload)
        byid = {r["id"]: r for r in res}
        for j in range(len(part)):
            r = byid[j]
            out.append(r.get("result") if "error" not in r else None)
    return out


def words(hexdata: str) -> list[int]:
    h = hexdata[2:]
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def addr_word(a: str) -> str:
    return a.lower().replace("0x", "").rjust(64, "0")


def decode_string(hexdata: str | None) -> str:
    if not hexdata or hexdata == "0x":
        return "?"
    b = bytes.fromhex(hexdata[2:])
    if len(b) == 32:  # bytes32 symbol (MKR style)
        return b.rstrip(b"\0").decode(errors="replace")
    off = int.from_bytes(b[0:32], "big")
    n = int.from_bytes(b[off:off + 32], "big")
    return b[off + 32:off + 32 + n].decode(errors="replace")
