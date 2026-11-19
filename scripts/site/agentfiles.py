#!/usr/bin/env python3
"""The agent-facing files say what the deployment records say.

    python3 scripts/site/agentfiles.py            # rewrite static/.well-known/agent.json's addresses, salts and op lists
    python3 scripts/site/agentfiles.py --check    # fail if agent.json or static/llms.txt disagrees with the records

Both files are written by hand, and a hand once put the wrong salts in them. The facts they repeat have one
source each: an object's address and salt are its record's (contracts/deployments/<object>.json, .address and
.saltAscii), and its ops are ops.json's (contracts/src/<library>/ops.json, .ops[].object and .name).

agent.json: every object under primaryContract.objects and floatContract.objects takes its address, salt and
`operations` (the op names) from those; each contract's own address is its first object's and its `operations`
every op of the library. Everything else in the file stays as written.

llms.txt is prose, so it is checked, not written: each object's address must appear, and the salt quoted after an
address (`salt "..."`) must be that object's. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "static" / ".well-known" / "agent.json"
LLMS = ROOT / "static" / "llms.txt"
CONTRACTS = {"primaryContract": "bl127", "floatContract": "bl19"}   # agent.json key -> library directory


def records(lib: str) -> dict[str, dict]:
    """{object: {address, salt, operations}} for a library, in ops.json's object order."""
    ops = json.loads((ROOT / "contracts" / "src" / lib / "ops.json").read_text())["ops"]
    out: dict[str, dict] = {}
    for op in ops:
        out.setdefault(op["object"], {"operations": []})["operations"].append(op["name"])
    for name, o in out.items():
        rec = json.loads((ROOT / "contracts" / "deployments" / f"{name}.json").read_text())
        o["address"], o["salt"] = rec["address"], rec["saltAscii"]
    return out


def agent() -> str:
    doc = json.loads(AGENT.read_text())
    for key, lib in CONTRACTS.items():
        objs = records(lib)
        c = doc[key]
        if set(c["objects"]) != set(objs):
            sys.exit(f"agent.json {key}.objects names {sorted(c['objects'])}, ops.json {sorted(objs)}")
        for name, facts in objs.items():
            o = c["objects"][name]
            o["address"], o["salt"], o["operations"] = facts["address"], facts["salt"], facts["operations"]
        c["address"] = next(iter(objs.values()))["address"]
        c["operations"] = [n for facts in objs.values() for n in facts["operations"]]
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def llms_problems() -> list[str]:
    text = re.sub(r"\s+", " ", LLMS.read_text())
    bad = []
    for lib in CONTRACTS.values():
        for name, facts in records(lib).items():
            at = [m.end() for m in re.finditer(re.escape(facts["address"]), text)]
            if not at:
                bad.append(f"llms.txt does not give {name}'s address {facts['address']}")
            for i in at:
                m = re.match(r'\s*\(salt "([^"]+)"', text[i:])
                if m and m.group(1) != facts["salt"]:
                    bad.append(f'llms.txt gives salt "{m.group(1)}" for {name}; its record says "{facts["salt"]}"')
    return bad


def main() -> int:
    want = agent()
    if "--check" not in sys.argv:
        AGENT.write_text(want)
        print(f"wrote {AGENT.relative_to(ROOT)}")
    bad = llms_problems()
    if "--check" in sys.argv and AGENT.read_text() != want:
        bad.append("static/.well-known/agent.json is stale (run python3 scripts/site/agentfiles.py)")
    for b in bad:
        print(b)
    if not bad and "--check" in sys.argv:
        print("agent files match the deployment records")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
