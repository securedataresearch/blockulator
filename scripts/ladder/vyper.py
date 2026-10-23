#!/usr/bin/env python3
"""Compile the comparison's Vyper contracts with the compiler each library pins.

    uv run scripts/ladder/vyper.py        # make build-vyper (part of make build)

Writes out/vyper/<Name>.json in the shape of a Foundry artifact
(bytecode.object, deployedBytecode.object), which the harnesses read with
vm.readFile and deploy with CREATE, and scripts/ladder/deploy.py sends
through the CREATE2 proxy. forge skips *.vy (foundry.toml).

Each contract names its compiler and its library's source path here. The
compiler runs through uvx, so the pinned version is fetched once and cached.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "vyper"
# name -> (source, vyper version, search path, evm version)
CONTRACTS = {
    # snekmate v0.1.2's math module: `# pragma version ~=0.4.3`
    "SnekmateMath": ("contracts/src/ladder/vyper/SnekmateMath.vy", "0.4.3", "lib/snekmate/src", "prague"),
}


def compile_one(name: str, src: str, version: str, path: str, evm: str) -> dict:
    cmd = ["uvx", "--from", f"vyper=={version}", "vyper", "-p", path, "--evm-version", evm,
           "-f", "bytecode,bytecode_runtime", src]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"vyper {version} failed on {src}:\n{r.stderr.strip()}")
    init, runtime = r.stdout.split()
    return {"bytecode": {"object": init}, "deployedBytecode": {"object": runtime},
            "compiler": f"vyper {version}", "evmVersion": evm, "source": src}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (src, version, path, evm) in CONTRACTS.items():
        art = compile_one(name, src, version, path, evm)
        dest = OUT / f"{name}.json"
        text = json.dumps(art, indent=1) + "\n"
        if not dest.exists() or dest.read_text() != text:
            dest.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
