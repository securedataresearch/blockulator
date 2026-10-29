#!/usr/bin/env python3
"""Thetanuts replay: the 15 June 2026 drain of the Thetanuts Index Vault V1 USDC PUT, one floor at a time.

    uv run scripts/replays/thetanuts.py fetch    # network: receipt, storage, opcode trace -> scripts/replays/thetanuts.json
    uv run scripts/replays/thetanuts.py          # offline: forge test -> exact scoring -> docs/benchmarks/replay-thetanuts.md
    uv run scripts/replays/thetanuts.py --score  # offline: re-score the last forge log only

The attack transaction (0xbba9f138...9fec, block 25323329, index 0) flash-borrowed
all but 3 of the index vault's tokens, redeemed them with one `claim`, and minted
them back with 37 `mint` calls that each paid 0 of every component. The vault's
source is not verified anywhere, so this replay is pinned to bytecode: `fetch`
reads the vault's storage at block-1 and at the block, decodes every Transfer
the transaction emitted, and runs an opcode tracer (debug_traceTransaction with
a JS tracer) that records each MUL, DIV, SLOAD and SSTORE the vault executed.
It locates the multiply-then-divide both `claim` and `mint` use, checks the
operands of all 190 executions against a floored `stored * amount / totalSupply`
model, and pins the program counters and storage slots. The forge test
(test/replays/Thetanuts.t.sol) replays every call from those integers with no
network, asserts it equals the chain, then reruns the 37 mints with the charge
rounded up, in BL127 and BL19, and against exact rationals. This script scores
them (Python Fraction, mpmath at 200 digits for digit counts) and writes the page.

Read-only: no transactions, no keys. RPC endpoints are public and keyless.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from fractions import Fraction
from math import ceil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "replays"
PINS = HERE / "thetanuts.json"
LOG = ROOT / "out" / "replays" / "thetanuts.log"
OUT_MD = ROOT / "docs" / "benchmarks" / "replay-thetanuts.md"
TEST = "test/replays/Thetanuts.t.sol"

sys.path.insert(0, str(ROOT / "scripts" / "accrual"))

TX = "0xbba9f138fe39503bfd1aa62932dbd6ab35d37d23d48e4b7bf2988a9d5dc39fec"
# Receipt, transaction, storage and eth_call: any keyless archive endpoint (the pins were checked byte-identical
# from https://eth.drpc.org and https://eth-pokt.nodies.app). The opcode trace needs debug_traceTransaction with a
# JS tracer, which among the keyless endpoints tried only eth.drpc.org serves.
STATE_RPC = os.environ.get("REPLAY_RPC", "https://eth.drpc.org")
TRACE_RPC = os.environ.get("REPLAY_TRACE_RPC", "https://eth.drpc.org")
SOURCIFY = "https://sourcify.dev/server/v2/contract/1/{}"
ROUTESCAN = "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api?module=contract&action={}"

VAULT = "0xc2c3ae0a7b405058558c9b4a63b373486cb86ac7"   # Thetanuts Index Vault V1 USDC PUT (TN-IDX-USDC-PUT), unverified
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
POOL = "0x2ca7641b841a79cc70220ce838d0b9f8197accda"    # the lending pool that lent the index tokens (Aave v2 flashLoan interface)
ATOKEN = "0x075da7e9efea6813ab0b2680423df75150120d12"  # its receipt token for the index ("Thetanut Index USDC", indexUSDC)
MAX = (1 << 256) - 1

# Storage layout, read off the opcode trace (the SLOAD/SSTORE keys) and confirmed against eth_getStorageAt:
SLOT_BALANCES = 2      # mapping(address => uint256): keccak(holder . 2)
SLOT_SUPPLY = 4        # totalSupply
SLOT_COMPONENTS = 9    # address[]: length here, element i at keccak(9) + i
SLOT_INFO = 10         # mapping(address => struct): word 0 packs a flag and the weight, word 1 is the stored amount
SLOT_TOTAL_WEIGHT = 11

# The tracer: every MUL, DIV and SLOAD the vault executes, with operands and result; every SSTORE, with key and value.
JS_TRACER = """{
  rows: [], pend: null,
  fault: function(log, db) {},
  step: function(log, db) {
    if (this.pend !== null) { this.pend.push(log.stack.peek(0).toString(16)); this.rows.push(this.pend); this.pend = null; }
    if (toHex(log.contract.getAddress()) !== "%s") return;
    var op = log.op.toString(), s = log.stack;
    if (op === "MUL" || op === "DIV") this.pend = [log.getPC(), op, s.peek(0).toString(16), s.peek(1).toString(16)];
    else if (op === "SLOAD") this.pend = [log.getPC(), op, s.peek(0).toString(16)];
    else if (op === "SSTORE") this.rows.push([log.getPC(), op, s.peek(0).toString(16), s.peek(1).toString(16)]);
  },
  result: function(ctx, db) { return this.rows; }
}""" % VAULT


def keccak(b: bytes) -> bytes:
    from Crypto.Hash import keccak as K
    return K.new(digest_bits=256, data=b).digest()


def topic(sig: str) -> str:
    return "0x" + keccak(sig.encode()).hex()


def sel(sig: str) -> str:
    return "0x" + keccak(sig.encode())[:4].hex()


def word(x) -> bytes:
    if isinstance(x, str):
        return bytes.fromhex(x[2:].rjust(64, "0"))
    return x.to_bytes(32, "big")


def mapslot(key, base: int) -> int:
    return int.from_bytes(keccak(word(key) + word(base)), "big")


def w(hexdata: str, i: int = 0) -> int:
    h = hexdata[2:] if hexdata.startswith("0x") else hexdata
    return int(h[64 * i:64 * (i + 1)], 16)


def addr(t: str) -> str:
    return "0x" + t[-40:].lower()


# ---------------------------------------------------------------------------- the deployed rule (from the bytecode)

def share(stored: int, amount: int, supply: int) -> int:
    """stored * amount / supply, as the vault's checked MUL (pc 12186) and DIV (pc 12220) compute it."""
    assert not (stored != 0 and amount > MAX // stored), "the vault's overflow check (pc 12165) would revert"
    return stored * amount // supply


def replay(supply: int, stored: list[int], claim: int, mints: list[int]):
    """The claim then the mints, floored as deployed. Returns the per-call states."""
    st = list(stored)
    c = {"amount": claim, "supplyBefore": supply, "storedBefore": list(st)}
    c["payout"] = [share(s, claim, supply) for s in st]       # the supply is read before the burn
    st = [s - p for s, p in zip(st, c["payout"])]
    supply -= claim
    c.update(supplyAfter=supply, storedAfter=list(st))
    ms = []
    for a in mints:
        m = {"amount": a, "supplyBefore": supply, "storedBefore": list(st)}
        m["charge"] = [share(s, a, supply) for s in st]
        st = [s + x for s, x in zip(st, m["charge"])]
        supply += a
        m.update(supplyAfter=supply, storedAfter=list(st))
        ms.append(m)
    return c, ms


# ---------------------------------------------------------------------------- fetch (network)

def http_get(url: str, ok404: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": "blockulator-replay/1.0"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        if ok404 and e.code == 404:  # Sourcify answers 404, with a JSON body, for an unverified address
            return {**json.load(e), "httpStatus": 404}
        raise


def flat_calls(node, depth=0, out=None):
    out = [] if out is None else out
    out.append({"depth": depth, "type": node["type"], "from": (node.get("from") or "").lower(), "to": (node.get("to") or "").lower(),
                "input": node.get("input", "0x"), "output": node.get("output", "0x") or "0x", "error": node.get("error")})
    for c in node.get("calls", []) or []:
        flat_calls(c, depth + 1, out)
    return out


def solc_version(code: bytes) -> str:
    i = code.rfind(b"dsolcC")
    assert i > 0, "no solc version in the CBOR metadata"
    v = code[i + 6:i + 9]
    return f"{v[0]}.{v[1]}.{v[2]}"


def fetch():
    from rpc import rpc

    tx = rpc(STATE_RPC, "eth_getTransactionByHash", [TX])
    block, index = int(tx["blockNumber"], 16), int(tx["transactionIndex"], 16)
    assert index == 0, "the pre-state is the end of block-1 only for the first transaction in its block"
    assert tx["to"] is None, "the attack is a contract creation"
    rc = rpc(STATE_RPC, "eth_getTransactionReceipt", [TX])
    assert rc["status"] == "0x1"
    ts = int(rpc(STATE_RPC, "eth_getBlockByNumber", [hex(block), False])["timestamp"], 16)
    pre_b, post_b = hex(block - 1), hex(block)

    def stor(slot: int, b: str) -> int:
        return int(rpc(STATE_RPC, "eth_getStorageAt", [VAULT, hex(slot), b]), 16)

    def call(to, sig, *a, b):
        data = sel(sig) + "".join(word(x).hex() for x in a)
        return rpc(STATE_RPC, "eth_call", [{"to": to, "data": data}, b])

    # --- the vault's components and stored amounts, straight from storage
    n = stor(SLOT_COMPONENTS, pre_b)
    base = int.from_bytes(keccak(word(SLOT_COMPONENTS)), "big")
    comps = ["0x" + hex(stor(base + i, pre_b))[2:].rjust(40, "0") for i in range(n)]
    assert n == 5

    def state(b):
        s = {"totalSupply": stor(SLOT_SUPPLY, b), "totalWeight": stor(SLOT_TOTAL_WEIGHT, b),
             "infoWord0": [stor(mapslot(c, SLOT_INFO), b) for c in comps],
             "stored": [stor(mapslot(c, SLOT_INFO) + 1, b) for c in comps],
             "componentBalanceOfVault": [w(call(c, "balanceOf(address)", VAULT, b=b)) for c in comps],
             "totalSupplyCall": w(call(VAULT, "totalSupply()", b=b)),
             "indexBalanceOfAToken": w(call(VAULT, "balanceOf(address)", ATOKEN, b=b))}
        assert s["totalSupplyCall"] == s["totalSupply"], "slot 4 is totalSupply"
        return s
    pre, post = state(pre_b), state(post_b)
    assert pre["stored"] == pre["componentBalanceOfVault"], "word 1 of each component's struct is the vault's holding"
    assert post["stored"] == post["componentBalanceOfVault"]
    assert pre["indexBalanceOfAToken"] == pre["totalSupply"], "every index token was deposited in the lending pool"

    def string(to, sig):
        from rpc import decode_string
        return decode_string(call(to, sig, b=pre_b))
    meta = {"name": string(VAULT, "name()"), "symbol": string(VAULT, "symbol()"), "decimals": w(call(VAULT, "decimals()", b=pre_b)),
            "owner": "0x" + hex(stor(1, pre_b))[2:].rjust(40, "0")}
    cmeta = [{"address": c, "name": string(c, "name()"), "symbol": string(c, "symbol()"), "decimals": w(call(c, "decimals()", b=pre_b)),
              "totalSupplyBefore": str(w(call(c, "totalSupply()", b=pre_b))),
              "usdcHeldBefore": str(w(call(USDC, "balanceOf(address)", c, b=pre_b)))} for c in comps]
    code = bytes.fromhex(rpc(STATE_RPC, "eth_getCode", [VAULT, pre_b])[2:])
    assert code == bytes.fromhex(rpc(STATE_RPC, "eth_getCode", [VAULT, post_b])[2:])

    # --- the transaction's own logs
    T = topic("Transfer(address,address,uint256)")
    FL = topic("FlashLoan(address,address,address,uint256,uint256,uint16)")  # Aave v2's event
    logs = rc["logs"]
    fl = [l for l in logs if l["address"].lower() == POOL and l["topics"][0] == FL]
    assert len(fl) == 1 and addr(fl[0]["topics"][3]) == VAULT
    flash = {"amount": w(fl[0]["data"], 0), "premium": w(fl[0]["data"], 1), "logIndex": int(fl[0]["logIndex"], 16),
             "receiver": addr(fl[0]["topics"][1])}
    H = flash["receiver"]  # the exploit contract that held everything
    tr = [(int(l["logIndex"], 16), l["address"].lower(), addr(l["topics"][1]), addr(l["topics"][2]), w(l["data"]))
          for l in logs if l["topics"][0] == T]
    zero = "0x" + "0" * 40
    burns = [t for t in tr if t[1] == VAULT and t[3] == zero]
    assert len(burns) == 1 and burns[0][2] == H
    claim_amount, claim_li = burns[0][4], burns[0][0]
    payouts = [t for t in tr if t[1] in comps and t[2] == VAULT and t[3] == H]
    assert [t[1] for t in payouts] == comps
    # mint: the component transferFroms come first, then the index Transfer(0, H, amount)
    mints, pend = [], []
    for li, tok, fr, to, v in tr:
        if li < claim_li:
            continue
        if tok in comps and fr == H and to == VAULT:
            pend.append((tok, v))
        elif tok == VAULT and fr == zero:
            assert [p[0] for p in pend] == comps, "five component transfers per mint, in component order"
            mints.append({"amount": v, "charge": [p[1] for p in pend], "logIndex": li})
            pend = []
    assert not pend and len(mints) == 37
    flash_in = [t for t in tr if t[1] == VAULT and t[2] == ATOKEN and t[3] == H]
    repay = [t for t in tr if t[1] == VAULT and t[2] == H and t[3] == ATOKEN]
    assert len(flash_in) == 1 and flash_in[0][4] == flash["amount"] and len(repay) == 1
    assert repay[0][4] == flash["amount"] + flash["premium"]

    # --- what left: component burns for USDC (initWithdraw), then transfers to the beneficiary
    realised = []
    for c in comps:
        b = [t for t in tr if t[1] == c and t[2] == H and t[3] == zero]
        u = [t for t in tr if t[1] == USDC and t[2] == c and t[3] == H]
        if b:
            assert len(b) == 1 and len(u) == 1
            realised.append({"component": c, "tokensIn": str(b[0][4]), "usdcOut": str(u[0][4])})
    out_usdc = [t for t in tr if t[1] == USDC and t[2] == H]
    assert len(out_usdc) == 1
    beneficiary = out_usdc[0][3]
    sent = {t[1]: str(t[4]) for t in tr if t[2] == H and t[3] == beneficiary}

    # --- the model must reproduce the logs and the post-state
    c, ms = replay(pre["totalSupply"], pre["stored"], claim_amount, [m["amount"] for m in mints])
    assert c["payout"] == [t[4] for t in payouts], "claim payouts"
    for m, x in zip(ms, mints):
        assert m["charge"] == x["charge"], f"mint {x['amount']}"
    assert ms[-1]["supplyAfter"] == post["totalSupply"] and ms[-1]["storedAfter"] == post["stored"]
    assert sum(m["amount"] for m in mints) == flash["amount"] + flash["premium"]

    # --- the call trace: the claim and mint inputs and every component transferFrom amount
    calls = flat_calls(rpc(TRACE_RPC, "debug_traceTransaction", [TX, {"tracer": "callTracer"}]))
    cl = [x for x in calls if x["to"] == VAULT and x["input"].startswith(sel("claim(uint256)"))]
    mi = [x for x in calls if x["to"] == VAULT and x["input"].startswith(sel("mint(uint256)"))]
    tf = [x for x in calls if x["to"] in comps and x["from"] == VAULT and x["input"].startswith(sel("transferFrom(address,address,uint256)"))]
    assert len(cl) == 1 and w(cl[0]["input"][10:]) == claim_amount and cl[0]["from"] == H
    assert [w(x["input"][10:]) for x in mi] == [m["amount"] for m in mints]
    assert [w(x["input"][10:], 2) for x in tf] == [v for m in mints for v in m["charge"]]
    assert all(x["error"] is None for x in cl + mi + tf)
    run = [x for x in calls if x["input"].startswith(sel("run(uint256)"))]
    iw = [x for x in calls if x["input"].startswith(sel("initWithdraw(uint256)"))]
    assert len(iw) == len(realised)

    # --- the opcode trace: locate the multiply-then-divide, check all its executions, pin pcs and slots
    rows = rpc(TRACE_RPC, "debug_traceTransaction", [TX, {"tracer": JS_TRACER, "timeout": "120s"}])
    rows = [[r[0], r[1]] + [int(x, 16) for x in r[2:]] for r in rows]
    muls = [i for i, r in enumerate(rows) if r[1] == "MUL"]
    mul_pcs = {rows[i][0] for i in muls}
    assert len(mul_pcs) == 1, f"one MUL site in the vault, found {sorted(mul_pcs)}"
    helper = []
    for i in muls:
        chk, mul, div = rows[i - 1], rows[i], rows[i + 1]
        assert chk[1] == "DIV" and chk[2] == MAX and chk[3] == mul[2], "overflow check MAX / stored before the MUL"
        assert div[1] == "DIV" and div[2] == mul[4], "the product is divided next"
        assert div[4] == div[2] // div[3]
        helper.append({"stored": mul[2], "amount": mul[3], "product": mul[4], "supply": div[3], "quotient": div[4],
                       "pcs": (chk[0], mul[0], div[0])})
    pcs = {h["pcs"] for h in helper}
    assert len(pcs) == 1
    pc_check, pc_mul, pc_div = pcs.pop()
    model = [(s, c["amount"], c["supplyBefore"], p) for s, p in zip(c["storedBefore"], c["payout"])]
    model += [(s, m["amount"], m["supplyBefore"], x) for m in ms for s, x in zip(m["storedBefore"], m["charge"])]
    assert [(h["stored"], h["amount"], h["supply"], h["quotient"]) for h in helper] == model, "trace operands = model"
    sstores = [r for r in rows if r[1] == "SSTORE"]
    sloads = [r for r in rows if r[1] == "SLOAD"]
    stored_slots = [mapslot(x, SLOT_INFO) + 1 for x in comps]
    st_writes = [r for r in sstores if r[2] in stored_slots]
    assert [r[3] for r in st_writes] == [s for s in c["storedAfter"]] + [s for m in ms for s in m["storedAfter"]]
    sup_writes = [r for r in sstores if r[2] == SLOT_SUPPLY]
    assert [r[3] for r in sup_writes] == [c["supplyAfter"]] + [m["supplyAfter"] for m in ms]
    idx = {id(r): i for i, r in enumerate(rows)}
    first_mint = idx[id(st_writes[4])] + 1  # the claim's fifth stored-amount write is its last vault step here
    pc_of = lambda rs: sorted({r[0] for r in rs})
    region = lambda rs, claim: [r for r in rs if (idx[id(r)] < first_mint) == claim]
    st_reads = [r for r in sloads if r[2] in stored_slots]
    claim_sites = {"storedSload": pc_of(region(st_reads, True)), "storedSstore": pc_of(region(st_writes, True)),
                   "supplySstore": pc_of(region(sup_writes, True))}
    mint_sites = {"storedSload": pc_of(region(st_reads, False)), "storedSstore": pc_of(region(st_writes, False)),
                  "supplySstore": pc_of(region(sup_writes, False))}
    assert all(len(v) == 1 for k, v in {**claim_sites, **mint_sites}.items() if k != "storedSload")
    ins = [pc for pc, _ in disasm(0, code)]
    jd = [pc for pc in ins if code[pc] == 0x5b]
    entry_mul = max(pc for pc in jd if pc < pc_check)          # the checked-multiply helper's JUMPDEST
    entry_div = min(pc for pc in jd if pc > pc_mul)            # the checked-divide helper's JUMPDEST
    span = code[entry_mul:pc_div + 3]

    # --- not verified: Sourcify and the Etherscan-compatible API both say so; when the vault was created
    sv = http_get(SOURCIFY.format(VAULT), ok404=True)
    assert sv.get("match") is None, "Sourcify has no match for the vault"
    es = http_get(ROUTESCAN.format("getsourcecode") + f"&address={VAULT}")["result"][0]
    cr = http_get(ROUTESCAN.format("getcontractcreation") + f"&contractaddresses={VAULT},{POOL}")["result"]
    created = {}
    for r in cr:
        b = int(rpc(STATE_RPC, "eth_getTransactionByHash", [r["txHash"]])["blockNumber"], 16)
        created[r["contractAddress"].lower()] = {"tx": r["txHash"], "block": b, "creator": r["contractCreator"].lower(),
                                                 "timestamp": int(rpc(STATE_RPC, "eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)}

    S = lambda xs: [str(x) for x in xs]
    out = {
        "_doc": "Pinned by `uv run scripts/replays/thetanuts.py fetch` (read-only, public RPC). The vault's source is not "
                "verified, so every integer comes from the transaction's Transfer logs, eth_getStorageAt / eth_call at "
                "block-1 (the tx is index 0) and at the block, and an opcode trace of the vault; test/replays/Thetanuts.t.sol "
                "replays them. Integers are decimal strings.",
        "tx": TX, "block": block, "txIndex": index, "blockTimestamp": ts,
        "attackerEOA": tx["from"].lower(), "attackContract": rc["contractAddress"].lower(), "exploitContract": H,
        "beneficiary": beneficiary,
        "addresses": {"vault": VAULT, "usdc": USDC, "lendingPool": POOL, "aToken": ATOKEN},
        "vault": {**meta, "codeSize": len(code), "codeKeccak": "0x" + keccak(code).hex(), "solc": solc_version(code),
                  "sourcify": f"HTTP {sv.get('httpStatus', 200)}, match {sv.get('match')}", "etherscanAbi": es.get("ABI"), "created": created.get(VAULT)},
        "lendingPoolCreated": created.get(POOL),
        "components": cmeta,
        "slots": {"balances": SLOT_BALANCES, "totalSupply": SLOT_SUPPLY, "components": SLOT_COMPONENTS, "componentInfo": SLOT_INFO,
                  "storedOffset": 1, "totalWeight": SLOT_TOTAL_WEIGHT,
                  "storedSlots": ["0x" + hex(x)[2:].rjust(64, "0") for x in stored_slots],
                  "componentsBase": "0x" + hex(base)[2:].rjust(64, "0")},
        "pre": {"block": block - 1, "totalSupply": str(pre["totalSupply"]), "stored": S(pre["stored"]),
                "infoWord0": S(pre["infoWord0"]), "totalWeight": str(pre["totalWeight"]),
                "componentBalanceOfVault": S(pre["componentBalanceOfVault"]), "indexBalanceOfAToken": str(pre["indexBalanceOfAToken"])},
        "post": {"block": block, "totalSupply": str(post["totalSupply"]), "stored": S(post["stored"]),
                 "componentBalanceOfVault": S(post["componentBalanceOfVault"]), "indexBalanceOfAToken": str(post["indexBalanceOfAToken"])},
        "flashLoan": {k: (str(v) if isinstance(v, int) and k != "logIndex" else v) for k, v in flash.items()},
        "claim": {"amount": str(c["amount"]), "supplyBefore": str(c["supplyBefore"]), "supplyAfter": str(c["supplyAfter"]),
                  "storedBefore": S(c["storedBefore"]), "payout": S(c["payout"]), "storedAfter": S(c["storedAfter"]),
                  "burnLogIndex": claim_li},
        "mints": [{"amount": str(m["amount"]), "supplyBefore": str(m["supplyBefore"]), "supplyAfter": str(m["supplyAfter"]),
                   "storedBefore": S(m["storedBefore"]), "charge": S(m["charge"]), "storedAfter": S(m["storedAfter"]),
                   "mintLogIndex": x["logIndex"]} for m, x in zip(ms, mints)],
        "realised": {"initWithdraw": realised, "usdcTotal": str(out_usdc[0][4]), "sentToBeneficiary": sent},
        "trace": {"tracer": "debug_traceTransaction, JS tracer over the vault's MUL/DIV/SLOAD/SSTORE",
                  "helperExecutions": len(helper), "claimExecutions": 5, "mintExecutions": len(helper) - 5,
                  "pcOverflowCheckDiv": pc_check, "pcMul": pc_mul, "pcDiv": pc_div,
                  "helperMulEntry": entry_mul, "helperDivEntry": entry_div, "helperBytes": "0x" + span.hex(),
                  "claimSites": claim_sites, "mintSites": mint_sites,
                  "runInput": str(w(run[0]["input"][10:])) if run else None,
                  "storedWrites": len(st_writes), "supplyWrites": len(sup_writes), "transferFromCalls": len(tf)},
    }
    PINS.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {PINS.relative_to(ROOT)}: claim {claim_amount}, {len(mints)} mints, charges {sorted({v for m in mints for v in m['charge']})}, "
          f"pcs {pc_check}/{pc_mul}/{pc_div}, USDC {out_usdc[0][4]}")


# ---------------------------------------------------------------------------- score (offline)

OPS = {0x01: "ADD", 0x02: "MUL", 0x03: "SUB", 0x04: "DIV", 0x10: "LT", 0x11: "GT", 0x14: "EQ", 0x15: "ISZERO", 0x16: "AND",
       0x19: "NOT", 0x1b: "SHL", 0x50: "POP", 0x52: "MSTORE", 0x56: "JUMP", 0x57: "JUMPI", 0x5b: "JUMPDEST", 0xfd: "REVERT"}


def disasm(start: int, code: bytes) -> list[tuple[int, str]]:
    out, pc = [], 0
    while pc < len(code):
        op = code[pc]
        if 0x60 <= op <= 0x7f:
            k = op - 0x5f
            out.append((start + pc, f"PUSH{k} 0x{code[pc + 1:pc + 1 + k].hex()}"))
            pc += 1 + k
            continue
        name = OPS.get(op) or (f"DUP{op - 0x7f}" if 0x80 <= op <= 0x8f else f"SWAP{op - 0x8f}" if 0x90 <= op <= 0x9f else f"0x{op:02x}")
        out.append((start + pc, name))
        pc += 1
    return out


def run_forge() -> str:
    r = subprocess.run(["forge", "test", "--match-path", TEST, "-vv"], capture_output=True, text=True, cwd=ROOT)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit("forge test failed; see " + str(LOG.relative_to(ROOT)) + "\n" + r.stdout[-3000:])
    return r.stdout


def parse(text: str) -> dict:
    res = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("TNT|"):
            _, form, kv = line.split("|", 2)
            res.setdefault(form, []).append({k: int(x) for k, x in (q.split("=") for q in kv.strip(";").split(";") if q)})
    return res


def bl127(raw: int) -> Fraction:
    return Fraction(raw, 1 << 128)


def bl19(raw: int) -> Fraction:
    wd = raw & ((1 << 256) - 1)
    if wd == 0:
        return Fraction(0)
    s, e, f = wd >> 255, (wd >> 236) & ((1 << 19) - 1), wd & ((1 << 236) - 1)
    v = Fraction((1 << 236) + f) * (Fraction(2) ** (e - 262143 - 236))
    return -v if s else v


def digits(x: Fraction, ref: Fraction) -> str:
    from mpmath import mp, mpf, log10
    mp.dps = 200
    if x == ref:
        return "exact"
    err = abs(x - ref) / abs(ref)
    return "0" if err >= 1 else f"{float(-log10(mpf(err.numerator) / mpf(err.denominator))):.2f}"


def fmt(x, sig: int = 12) -> str:
    from mpmath import mp, mpf, nstr
    mp.dps = 200
    x = Fraction(x)
    if x.denominator == 1:
        return f"{x.numerator:,}"
    return nstr(mpf(x.numerator) / mpf(x.denominator), sig)


def units(x: int, d: int = 6) -> str:
    s = f"{x // 10 ** d:,}.{x % 10 ** d:0{d}d}"
    return s


def nearest_retuned(supply: int, stored: int, target: int) -> list[int]:
    """The largest mint each time whose charge rounds to 0 when rounded to nearest (2*stored*a < supply), until the
    attacker holds `target`. Derived, not on chain."""
    out, held = [], 0
    while held < target:
        a = min((supply - 1) // (2 * stored), target - held)
        assert a > 0
        assert 2 * stored * a < supply
        out.append(a)
        held += a
        supply += a
    return out


def score(text: str):
    J = json.loads(PINS.read_text())
    R = parse(text)
    I = lambda x: int(x)
    S0, st0 = I(J["pre"]["totalSupply"]), [I(x) for x in J["pre"]["stored"]]
    A = I(J["claim"]["amount"])
    mints = [I(m["amount"]) for m in J["mints"]]
    M = sum(mints)
    c, ms = replay(S0, st0, A, mints)
    assert c["payout"] == [I(x) for x in J["claim"]["payout"]]
    assert all(m["charge"] == [I(x) for x in j["charge"]] for m, j in zip(ms, J["mints"]))

    # deployed, from the forge log: every charge 0, the claim payouts
    dep = R["deployed"]
    assert [d["charge"] for d in dep] == [0] * 37 and [d["amount"] for d in dep] == mints
    claimR = R["claim"]
    assert [d["payout"] for d in claimR] == c["payout"]

    # exact rationals on the chain path, and the BL127/BL19 values the test computed
    exact = [Fraction(m["storedBefore"][0] * m["amount"], m["supplyBefore"]) for m in ms]
    f127 = [bl127(d["raw"]) for d in R["bl127"]]
    f19 = [bl19(d["raw"]) for d in R["bl19"]]
    for d, e in zip(R["bl127"], exact):
        assert d["floor"] == 0 and d["ceil"] == 1 and d["round"] == (1 if e >= Fraction(1, 2) else 0)
    for d in R["bl19"]:
        assert d["floor"] == 0 and d["ceil"] == 1
    dig127 = [digits(v, e) for v, e in zip(f127, exact)]
    dig19 = [digits(v, e) for v, e in zip(f19, exact)]

    # round up: the same 37 mints, the charge ceiled (the integer path, BL127-ceil and BL19-ceil agree in the test)
    up = R["ceil"]
    stu = [1] * 5
    sup = S0 - A
    for d, a in zip(up, mints):
        ch = ceil(Fraction(stu[0] * a, sup))
        assert d["charge"] == ch and d["supplyBefore"] == sup and d["storedBefore"] == stu[0]
        stu = [s + ch for s in stu]
        sup += a
    up_paid = stu[0] - 1
    floor_up = -(-M // 3)
    tail = R["ceilSummary"][0]
    assert tail["paidPerComponent"] == up_paid and tail["minPerComponent"] == floor_up and tail["minted"] == M
    for d in R["bl127ceil"] + R["bl19ceil"]:
        assert d["paidPerComponent"] == up_paid

    # exact rational charge (if a fraction of a raw unit could move): the ratio stays at exactly 1/3
    exact_paid = Fraction(M, 3)

    # nearest on the attacker's own amounts, and re-tuned to the rule (derived)
    s, sup = 1, S0 - A
    for a in mints:
        s += (2 * s * a + sup) // (2 * sup)
        sup += a
    near_paid = s - 1
    assert R["nearestPath"][0]["paidPerComponent"] == near_paid
    nr = nearest_retuned(S0 - A, 1, M)
    nT = R["nearestRetuned"][0]
    assert nT["mints"] == len(nr) and nT["paidPerComponent"] == 0 and nT["minted"] == M

    md = render(J, c, ms, exact, f127, f19, dig127, dig19, up, up_paid, floor_up, exact_paid, nr, M, near_paid)
    OUT_MD.write_text(md)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(f"  claim took {c['payout']}; 37 mints charged 0; round-up path pays {up_paid:,} per component (minimum {floor_up:,}); "
          f"nearest re-tuned: {len(nr)} free mints")


def fmtc(x: Fraction, places: int = 3) -> str:
    """A positive rational with thousands separators and `places` decimals (rounded half up)."""
    q = int(x * 10 ** places + Fraction(1, 2))
    return f"{q // 10 ** places:,}.{q % 10 ** places:0{places}d}"


def render(J, c, ms, exact, f127, f19, dig127, dig19, up, up_paid, floor_up, exact_paid, nr, M, near_paid) -> str:
    when = datetime.fromtimestamp(J["blockTimestamp"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    T = J["trace"]
    comps = J["components"]
    short = [x["symbol"].removeprefix("TN-CSCPv1-") for x in comps]
    payout = c["payout"]
    S0, A = c["supplyBefore"], c["amount"]
    fl = J["flashLoan"]
    created = J["vault"]["created"]
    cdate = datetime.fromtimestamp(created["timestamp"], timezone.utc).strftime("%d %B %Y")
    weights = [int(x) >> 8 for x in J["pre"]["infoWord0"]]
    usdc = int(J["realised"]["usdcTotal"])
    L = []
    L.append("# Replay: Thetanuts Finance, 15 June 2026\n")
    L.append(f"Generated by `uv run scripts/replays/thetanuts.py` from `scripts/replays/thetanuts.json` (pinned by "
             f"`thetanuts.py fetch`) and `{TEST}`. Transaction [`{J['tx'][:10]}…{J['tx'][-4:]}`](https://etherscan.io/tx/{J['tx']}), "
             f"block {J['block']} (index {J['txIndex']}), {when}.\n")
    L.append("**This replay is pinned to bytecode, not source.** The other replays transcribe verified source line by line. "
             f"The {J['vault']['name']} (`{J['addresses']['vault']}`) has no verified source: Sourcify returns no match and the "
             f"Etherscan-compatible API returns \"{J['vault']['etherscanAbi']}\". So every rule below is read off the deployed "
             f"bytecode ({J['vault']['codeSize']:,} bytes, keccak `{J['vault']['codeKeccak'][:18]}…`, solc {J['vault']['solc']} "
             "from its metadata) and an opcode trace of the attack. The trace shows which instructions ran and on which operands. "
             "The arithmetic in `Thetanuts.t.sol` is a model of those instructions. It is checked against all 190 executions and "
             "every storage write, but it is not the developers' code, and names such as `stored` are mine.\n")

    L.append("## The answer first\n")
    L.append(f"- **The vault charged 0 for every mint.** The attacker flash-borrowed {int(fl['amount']):,} of the vault's "
             f"{S0:,} index tokens (all but 3) and redeemed them with one `claim`. That left a supply of 3 and 1 raw unit of each of "
             f"the five components. Then 37 `mint` calls created {M:,} index tokens, enough to repay the loan and its fee. "
             "Each mint charged `stored × amount / totalSupply` of each component, floored: 1 × 2 / 3, then 1 × 4 / 5, then "
             f"1 × 2^k / (2^k + 1), and finally 1 × {ms[-1]['amount']:,} / {ms[-1]['supplyBefore']:,}. Every quotient is below 1, "
             "so all 185 component transfers were for 0.")
    L.append(f"- **The claim was not inflated.** It paid floor(stored × {A:,} / {S0:,}) of each component, at or below the exact "
             "pro-rata share. The loss is the mints. The vault gave away its whole backing in exchange for index tokens it then "
             "recreated for nothing.")
    L.append(f"- **The class is rounding direction, not precision.** The exact first charge is 2/3 of a raw unit. BL127 carries it "
             f"to {dig127[0]} digits and BL19 to {dig19[0]}, but a token transfer moves whole raw units, so a rule still has to pick one. "
             "Floor gives 0, which is the attack unchanged. Rounding up gives 1. Rounded up, the charge never lets the "
             "stored-to-supply ratio fall below 1/3, so any sequence that mints "
             f"{M:,} tokens must pay at least {floor_up:,} raw units of every component. The claim took at most {max(payout):,} "
             f"of any one, so the attack loses on all five. With the attacker's own amounts, rounding up costs {up_paid:,} per component.")
    L.append(f"- **Rounding to nearest is not the fix either.** It blocks the attacker's own sequence (2/3 rounds to 1). But an attacker who "
             f"keeps each mint below half the supply mints for free every time and reaches {M:,} tokens in {len(nr)} mints instead of 37.\n")

    L.append("## What happened, in integers\n")
    L.append(f"1. Before the transaction the index token's whole supply, {S0:,} raw units, was deposited in a lending pool "
             f"(`{J['addresses']['lendingPool']}`, an Aave v2-style `flashLoan`; its receipt token `{J['addresses']['aToken']}` held "
             f"{int(J['pre']['indexBalanceOfAToken']):,}). The pool and the vault were both created by "
             f"`{created['creator']}`. The vault was created on {cdate} (block {created['block']}). Its five components and the "
             "amounts it stored for each, equal to its balance of each:\n")
    L.append("   | # | component | weight | stored before | claim paid | stored after the claim |")
    L.append("   |---|---|---|---|---|---|")
    for i, x in enumerate(comps):
        L.append(f"   | {i} | {x['name']} (`{x['address'][:10]}…`) | {weights[i]}% | {c['storedBefore'][i]:,} | {payout[i]:,} | {c['storedAfter'][i]} |")
    L.append("")
    L.append(f"2. The attack contract borrowed {int(fl['amount']):,} index tokens from the pool (fee {int(fl['premium']):,}), "
             f"and called `claim({A:,})`. The vault burned them, so the supply went from {S0:,} to {c['supplyAfter']}, and paid out "
             f"floor(stored × {A:,} / {S0:,}) of each component. That is the table above: each stored amount fell to 1.")
    L.append(f"3. It called `mint` 37 times with amounts 2, 4, 8, …, 2^36 = {ms[35]['amount']:,}, then {ms[36]['amount']:,}. Each time "
             f"the amount was below the supply (supply 2^k + 1 against an amount of 2^k), so 1 × amount / supply floors to 0. The vault "
             "called `transferFrom(attacker, vault, 0)` on each component, added 0 to each stored amount and minted the tokens. "
             f"After the last mint the supply was {ms[-1]['supplyAfter']:,} and each stored amount was still 1 "
             f"(eth_getStorageAt at the block agrees).")
    L.append(f"4. The {M:,} minted tokens repaid the loan plus its fee ({int(fl['amount']):,} + {int(fl['premium']):,}).")
    rz = J["realised"]["initWithdraw"]
    parts = "; ".join(f"{units(int(r['tokensIn']))} {next(x['symbol'] for x in comps if x['address'] == r['component'])} for "
                      f"{units(int(r['usdcOut']))} USDC" for r in rz)
    L.append(f"5. Out of the claimed components, two were redeemed through the component vaults' `initWithdraw` ({parts}). That is "
             f"**{units(usdc)} USDC**, sent to `{J['beneficiary']}`. The other three components went to the same address as vault "
             "tokens: " + ", ".join(f"{units(int(v))} {next(x['symbol'] for x in comps if x['address'] == a)}"
                                     for a, v in J["realised"]["sentToBeneficiary"].items() if a != J["addresses"]["usdc"]) + ".\n")

    L.append("## The decisive step on each rule\n")
    L.append("The same 37 mints, from the same post-claim state (supply 3, 1 raw unit stored per component), under each rule. All five "
             "components start from 1 stored unit at the same supply, so their charges are identical and one column covers all "
             "five. *First charge* is mint 1 (2 index tokens at supply 3). *Paid per component* is the total over the 37 mints. "
             "*Digits* is −log10 of the relative error of the computed charge against the exact one, at its worst over the 37 mints.\n")
    L.append("| rule | first charge (raw units) | digits | paid per component, 37 mints | against the claim's take | verdict |")
    L.append("|---|---|---|---|---|---|")
    mn127, mn19 = min(float(x) for x in dig127), min(float(x) for x in dig19)
    take = f"took {min(payout):,} – {max(payout):,}"
    L.append(f"| deployed: `stored * amount / totalSupply`, floored (pc {T['pcDiv']}) | 0 | 0 | 0 | {take} | **free: the attack** (matches the chain: 185 transfers of 0) |")
    L.append(f"| rounded up (ceil) | 1 | 0 | {up_paid:,} | {up_paid - max(payout):,} more than the largest take | **loses on every component** |")
    L.append(f"| BL127 → floor to a raw unit | {fmt(f127[0], 30)} → 0 | {mn127:.2f} | 0 | {take} | free: precision without direction |")
    L.append(f"| BL127 → ceil to a raw unit | {fmt(f127[0], 30)} → 1 | {mn127:.2f} | {up_paid:,} | as rounded up | loses on every component |")
    L.append(f"| BL19 → floor to a raw unit | {fmt(f19[0], 30)} → 0 | {mn19:.2f} | 0 | {take} | free: precision without direction |")
    L.append(f"| BL19 → ceil to a raw unit | {fmt(f19[0], 30)} → 1 | {mn19:.2f} | {up_paid:,} | as rounded up | loses on every component |")
    L.append(f"| exact rational, if a fraction of a raw unit could move | 2/3 | exact | {fmtc(exact_paid)} (= minted / 3) | "
             f"{fmtc(exact_paid - max(payout))} more than the largest take | loses on every component |")
    L.append(f"| nearest, the attacker's amounts | 1 | 0 | {near_paid:,} | {near_paid - max(payout):,} more than the largest take | blocked |")
    L.append(f"| nearest, re-tuned (each mint < supply / 2) | 0 | 0 | 0 in {len(nr)} mints | {take} | **free: the attack, re-tuned** |")
    L.append("")
    L.append(f"Reading the table: BL127 and BL19 compute the 2/3 almost exactly, with at least {int(mn127)} and {int(mn19)} correct digits. That does not decide "
             "anything, because the vault moves ERC-20 raw units and 2/3 of a unit has to become 0 or 1. Floor, the deployed "
             "choice, rounds in the minter's favour. Ceil rounds in the vault's favour and closes the attack whatever the "
             "arithmetic in front of it. Rounding to nearest only looks like a fix when the attacker's amounts were tuned to floor.\n")

    L.append("## Round up: what any mint sequence costs\n")
    L.append("Write s for a component's stored amount and S for the supply. A rounded-up charge c on a mint of a satisfies "
             "c ≥ s·a/S, so (s + c)/(S + a) ≥ s/S: the ratio s/S never falls. After the claim it is 1/3 for every component. "
             f"To mint the {M:,} tokens the attacker needed, the supply ends at {M + 3:,}, so s ends at least ({M:,} + 3)/3 and "
             f"the attacker pays at least {floor_up:,} raw units of each component. This holds for any amounts in any order. "
             "`test_round_up_costs_more_than_the_claim_took` asserts the invariant after every mint and both bounds against "
             "each component's take.\n")
    L.append("| # | component | claim took | minimum paid under round-up, any sequence | paid under round-up, the attacker's 37 amounts | attacker's net |")
    L.append("|---|---|---|---|---|---|")
    for i, x in enumerate(comps):
        L.append(f"| {i} | {short[i]} | {payout[i]:,} | {floor_up:,} | {up_paid:,} | {payout[i] - up_paid:,} |")
    L.append("")
    L.append(f"Holding exactly 1/3 of a unit per index token is the state the claim left. Before it, each index token was backed by "
             f"{fmt(Fraction(c['storedBefore'][0], S0), 6)} BTC-put tokens, the largest component, and less of the others. Under round-up "
             "the dust left by the claim makes new index tokens dearer, not free.\n")

    L.append("## Every mint, on the chain path\n")
    L.append("Supply before each mint, the exact charge per component (1 × amount / supply), and what each rule makes of it. "
             "The deployed column is the chain's: each value is a `transferFrom` amount from the call trace and a Transfer log.\n")
    L.append("| # | amount | supply before | exact charge | deployed (floor) | BL127 | BL127 digits | BL19 digits | ceil | nearest |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for k, (m, e) in enumerate(zip(ms, exact)):
        L.append(f"| {k + 1} | {m['amount']:,} | {m['supplyBefore']:,} | {fmt(e, 14)} | {m['charge'][0]} | {fmt(f127[k], 14)} | "
                 f"{dig127[k]} | {dig19[k]} | 1 | {1 if e >= Fraction(1, 2) else 0} |")
    L.append("")
    L.append(f"Re-tuned to nearest, the free mints are " + ", ".join(f"{a:,}" for a in nr[:8]) + f", … ({len(nr)} in all, last "
             f"{nr[-1]:,}). Each is the largest amount below half the supply at that point. Derived, not on chain.\n")

    L.append("## The bytecode evidence\n")
    L.append(f"Both `claim` (selector `0x379607f5`) and `mint` (`0xa0712d68`) compute a component's share by jumping into the same "
             f"two compiler helpers: solc {J['vault']['solc']}'s checked multiply (entry {T['helperMulEntry']}) and checked divide "
             f"(entry {T['helperDivEntry']}). The opcode trace records {T['helperExecutions']} executions: {T['claimExecutions']} "
             f"in the claim and {T['mintExecutions']} in the mints, five per call, one per component. In each one:\n")
    L.append(f"- pc **{T['pcOverflowCheckDiv']}**: `DIV` of 2^256 − 1 by the stored amount, the overflow check before the product;")
    L.append(f"- pc **{T['pcMul']}**: `MUL` stored × amount;")
    L.append(f"- pc **{T['pcDiv']}**: `DIV` of that product by totalSupply. EVM `DIV` floors, and nothing adds a remainder back.\n")
    L.append("The helper bytes, as pinned (`trace.helperBytes`):\n")
    L.append("```")
    for pc, op in disasm(T["helperMulEntry"], bytes.fromhex(T["helperBytes"][2:])):
        mark = {T["pcOverflowCheckDiv"]: "   <- overflow check", T["pcMul"]: "   <- stored * amount",
                T["pcDiv"]: "   <- / totalSupply, floored"}.get(pc, "")
        L.append(f"{pc:>6}  {op}{mark}")
    L.append("```\n")
    sl = J["slots"]
    L.append("Storage, read off the trace's SLOAD/SSTORE keys and confirmed with eth_getStorageAt:\n")
    L.append(f"- totalSupply: slot {sl['totalSupply']}. The claim writes it at pc {T['claimSites']['supplySstore'][0]} "
             f"({S0:,} → {c['supplyAfter']}), and each mint at pc {T['mintSites']['supplySstore'][0]}. The claim divides by the "
             "supply read before its burn.")
    L.append(f"- balances: mapping at slot {sl['balances']} (keccak(holder . 2)).")
    L.append(f"- components: address[] at slot {sl['components']} (length 5; element i at keccak(9) + i = `{sl['componentsBase'][:14]}…` + i).")
    L.append(f"- per-component struct: mapping at slot {sl['componentInfo']}. Word 0 packs a flag byte and the weight "
             f"({', '.join(f'{x}%' for x in weights)}; total weight in slot {sl['totalWeight']} = {J['pre']['totalWeight']}). "
             f"Word **1 is the stored amount**, at keccak(component . 10) + 1:")
    for x, s in zip(short, sl["storedSlots"]):
        L.append(f"  - {x}: `{s}`")
    L.append(f"- The claim reads the stored amount at pc {' and '.join(map(str, T['claimSites']['storedSload']))} and writes stored − payout at pc "
             f"{T['claimSites']['storedSstore'][0]}. The mint reads it at pc {' and '.join(map(str, T['mintSites']['storedSload']))}, calls "
             f"`transferFrom` for the charge, and writes stored + charge at pc {T['mintSites']['storedSstore'][0]} "
             f"({T['storedWrites']} writes in all, each the value the model gives).\n")
    L.append("The model in the test, `ThetanutsDeployed.share(stored, amount, supply) = stored * amount / supply`, reproduces the "
             "operands and quotient of all 190 executions, the 5 claim payouts, the 185 zero charges, each of the 38 supply "
             "writes and 190 stored-amount writes, and the post-state storage. `fetch` asserts every one of these.\n")

    L.append("## Where this differs from the reports\n")
    L.append("- \"A vulnerability in the vault's redemption logic\", with \"`backing * amount / totalSupply`\" letting the attacker "
             "\"withdraw more funds than they were entitled to\" ([Cryptopolitan](https://www.cryptopolitan.com/hack-deprecated-thetanuts-vault/), "
             "citing ExVul); \"allowed inflated payouts\" ([Cryip](https://cryip.co/?p=12478)). The redemption, `claim`, "
             f"paid floor(stored × {A:,} / {S0:,}) of each component. For the BTC put that is {payout[0]:,} against an exact "
             f"{fmt(Fraction(c['storedBefore'][0] * A, S0), 16)}, in the vault's favour. The formula is right, and so is its "
             "rounding on the way out. The same formula is wrong on the way in: `mint` uses it, floored, for what the "
             "minter pays.")
    L.append("- \"Repeated mint-and-redeem cycles\" ([Cryip](https://cryip.co/?p=12478), "
             "[Cryptopolitan](https://www.cryptopolitan.com/hack-deprecated-thetanuts-vault/)). There is one `claim` and then 37 "
             "`mint` calls. Nothing is redeemed between the mints. The flash loan supplied the index tokens for the one claim; "
             "it did not amplify a loop.\n")

    L.append("## Provenance\n")
    L.append("| integer | value | source |")
    L.append("|---|---|---|")
    L.append(f"| supply before | {S0:,} | eth_getStorageAt slot 4 at block {J['pre']['block']} (= eth_call totalSupply()); index 0, so this is the tx's pre-state |")
    L.append(f"| stored before (×5) | {', '.join(f'{x:,}' for x in c['storedBefore'])} | eth_getStorageAt keccak(component . 10) + 1 at block-1; each equals component.balanceOf(vault) |")
    L.append(f"| flash loan, fee | {int(fl['amount']):,}, {int(fl['premium']):,} | the pool's FlashLoan log (#{fl['logIndex']}); index Transfer logs pool → attacker and back |")
    L.append(f"| claim amount | {A:,} | index Transfer(attacker → 0) log #{J['claim']['burnLogIndex']}; claim(uint256) input in the call trace |")
    L.append(f"| claim payouts (×5) | {', '.join(f'{x:,}' for x in payout)} | component Transfer(vault → attacker) logs; the trace's DIV at pc {T['pcDiv']} |")
    L.append(f"| mint amounts (×37) | 2 … {ms[-1]['amount']:,} | index Transfer(0 → attacker) logs; mint(uint256) inputs in the call trace |")
    L.append(f"| mint charges (×185) | all 0 | component Transfer(attacker → vault) logs; transferFrom inputs in the call trace; the trace's DIV at pc {T['pcDiv']} |")
    L.append(f"| supply after | {int(J['post']['totalSupply']):,} | eth_getStorageAt slot 4 at block {J['post']['block']} |")
    L.append(f"| stored after (×5) | {', '.join(J['post']['stored'])} | eth_getStorageAt at the block; each equals component.balanceOf(vault) |")
    L.append(f"| USDC realised | {usdc:,} | USDC Transfer logs: component vaults → attacker (initWithdraw), attacker → `{J['beneficiary']}` |")
    L.append("")
    L.append(f"Attacker EOA `{J['attackerEOA']}`, attack contract `{J['attackContract']}` (created by this transaction), exploit "
             f"contract `{J['exploitContract']}` (created by the attack contract; `run({int(T['runInput']):,})`). The receipt, storage "
             "and eth_call pins were fetched from https://eth.drpc.org and again from https://eth-pokt.nodies.app "
             "(`REPLAY_RPC=…`), with byte-identical output. The call and opcode traces come from https://eth.drpc.org. Of the "
             "other keyless endpoints tried, publicnode, nodies, 1rpc and blastapi do not serve debug_traceTransaction, and "
             "tenderly's public gateway refused it with HTTP 429.\n")

    L.append("## Caveat\n")
    L.append("- **Bytecode, not source.** The function names (`claim`, `mint`, `initWithdraw`) come from 4-byte selectors. The "
             "meanings of the storage fields come from how this transaction reads and writes them. The model matches every executed "
             "instruction that matters here, but other paths through the contract (owner functions, other branches) are not replayed.")
    L.append("- **Counterfactuals start from the chain's post-claim state.** Under a vault that rounded mints up, the attacker "
             "would not have claimed in the first place. The round-up bound shows that no mint sequence after this claim pays.")
    L.append(f"- **Not confirmed here.** The press puts the loss at about $2.1 million and says a whitehat recovered most of it. "
             f"This transaction realised {units(usdc)} USDC. The rest left as three component-vault tokens, and their vaults "
             "held no USDC at the block before (`components[].usdcHeldBefore`), so this replay does not price them. Nothing in "
             "the transaction shows a recovery.\n")

    L.append("## Reproduce\n")
    L.append("```\nuv run scripts/replays/thetanuts.py fetch   # network, read-only: re-pin scripts/replays/thetanuts.json\n"
             f"forge test --match-path {TEST} -vv   # offline replay and assertions\n"
             "uv run scripts/replays/thetanuts.py         # offline: forge + exact scoring -> this file\n```\n")
    return "\n".join(L)


def main():
    a = sys.argv[1:]
    if a and a[0] == "fetch":
        fetch()
        return
    if a and a[0] == "--score":
        score(LOG.read_text())
        return
    score(run_forge())


if __name__ == "__main__":
    main()
