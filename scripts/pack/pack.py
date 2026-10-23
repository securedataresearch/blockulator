#!/usr/bin/env python3
"""Stage the @blockulator/contracts package and check what would be published.

    uv run scripts/pack/pack.py          # make pack

Stages dist/contracts/ from packages/contracts/ (package.json, README.md), the
root LICENSE and the sources under contracts/src, laid out so that one import
path works in every install:

    @blockulator/contracts/fp127/FP127Lib.sol    fp127/  <- contracts/src/fp127
    @blockulator/contracts/fp256/FP256Lib.sol    fp256/  <- contracts/src/fp256
    @blockulator/contracts/wad/BlockulatorWad.sol wad/   <- contracts/src/wad
    @blockulator/contracts/deployments/FP127.json        <- contracts/deployments

Then it runs `npm pack --dry-run` and `forge soldeer push --dry-run` on the
staged directory and fails unless both file lists hold only the package's own
files: no tests, no cache or build output, nothing that looks like a secret,
every Solidity import relative, and the same files in both. Nothing is
published; dist/contracts/ is what the user publishes from.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "packages" / "contracts"
OUT = ROOT / "dist" / "contracts"
SOLDEER_NAME = "blockulator"

# staged dir -> (source dir, globs). A new Solidity file in a source dir (the
# typed values, say) joins the package without an edit here.
LAYOUT = {
    "fp127": (ROOT / "contracts/src/fp127", ["*.sol", "*.yul", "abi*.json"]),
    "fp256": (ROOT / "contracts/src/fp256", ["*.sol", "*.yul", "abi*.json"]),
    "wad": (ROOT / "contracts/src/wad", ["*.sol"]),
    "deployments": (ROOT / "contracts/deployments", ["*.json"]),
}

REQUIRED = [
    "package.json", "README.md", "LICENSE",
    "fp127/FP127Lib.sol", "fp127/IFP127.sol", "fp127/FP127.yul", "fp127/abi.json",
    "fp256/FP256Lib.sol", "fp256/IFP256.sol", "fp256/IFP256E.sol", "fp256/IFP256H.sol",
    "fp256/IFP256S.sol", "fp256/FP256.yul", "fp256/FP256E.yul", "fp256/FP256H.yul",
    "fp256/FP256S.yul", "fp256/abi.json", "fp256/abiE.json", "fp256/abiH.json",
    "fp256/abiS.json", "wad/BlockulatorWad.sol",
    "deployments/FP127.json", "deployments/FP256.json", "deployments/RELEASE.json",
]

# every published path must match one of these
ALLOWED = re.compile(
    r"^(package\.json|README\.md|LICENSE"
    r"|(fp127|fp256|wad)/[A-Za-z0-9_]+\.(sol|yul)"
    r"|(fp127|fp256)/abi[A-Z]?\.json"
    r"|deployments/[A-Za-z0-9_.]+\.json)$"
)
# and none of these, wherever they sit
FORBIDDEN = re.compile(
    r"(^|/)(test|tests|cache|out|out-[a-z]+|broadcast|lib|node_modules|\.git)(/|$)"
    r"|(^|/)\.env|\.t\.sol$|\.npmrc$|\.pem$|\.key$|keystore|secret|mnemonic",
    re.IGNORECASE,
)
# content that would mean a key or token made it in
SECRET = re.compile(
    r"PRIVATE_KEY\s*=|BEGIN [A-Z ]*PRIVATE KEY|ETHERSCAN_API_KEY\s*=|_authToken|npm_[A-Za-z0-9]{36}",
)
IMPORT = re.compile(r'^\s*import\s+(?:[^"\']*?\bfrom\s+)?["\']([^"\']+)["\']', re.MULTILINE)


def stage() -> list[str]:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy2(PKG / "package.json", OUT / "package.json")
    shutil.copy2(PKG / "README.md", OUT / "README.md")
    shutil.copy2(ROOT / "LICENSE", OUT / "LICENSE")
    for dst, (src, globs) in LAYOUT.items():
        (OUT / dst).mkdir()
        for g in globs:
            for f in sorted(src.glob(g)):
                shutil.copy2(f, OUT / dst / f.name)
    return sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file())


def check_list(label: str, files: list[str], staged: list[str]) -> list[str]:
    bad = []
    for f in files:
        if not ALLOWED.match(f):
            bad.append(f"{label}: unexpected file {f}")
        if FORBIDDEN.search(f):
            bad.append(f"{label}: forbidden path {f}")
    for f in REQUIRED:
        if f not in files:
            bad.append(f"{label}: missing {f}")
    if sorted(files) != staged:
        extra = sorted(set(files) - set(staged))
        lost = sorted(set(staged) - set(files))
        bad.append(f"{label}: file list differs from the staged tree (extra {extra}, missing {lost})")
    return bad


def check_contents(staged: list[str]) -> list[str]:
    bad = []
    for f in staged:
        text = (OUT / f).read_text(errors="replace")
        if SECRET.search(text):
            bad.append(f"secret-shaped text in {f}")
        if f.endswith(".sol"):
            for imp in IMPORT.findall(text):
                if not imp.startswith(("./", "../")):
                    bad.append(f"{f} imports {imp!r}: package sources must import each other by relative path")
                elif os.path.normpath(os.path.join(os.path.dirname(f), imp)) not in staged:
                    bad.append(f"{f} imports {imp!r}, which is not in the package")
                elif not (OUT / Path(f).parent / imp).resolve().is_file():
                    bad.append(f"{f} imports {imp!r}, which is not in the package")
    return bad


def npm_files() -> tuple[list[str], dict]:
    p = subprocess.run(["npm", "pack", "--dry-run", "--json", "--ignore-scripts"],
                       cwd=OUT, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"npm pack --dry-run failed:\n{p.stderr}")
    info = json.loads(p.stdout)[0]
    return sorted(f["path"] for f in info["files"]), info


def soldeer_files(version: str) -> list[str] | None:
    if shutil.which("forge") is None:
        print("pack: forge not found, skipping the Soldeer dry run")
        return None
    zip_path = OUT / f"{OUT.name}.zip"   # the dry run writes <dir>/<dir name>.zip
    zip_path.unlink(missing_ok=True)
    p = subprocess.run(["forge", "soldeer", "push", f"{SOLDEER_NAME}~{version}", str(OUT), "--dry-run"],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"forge soldeer push --dry-run failed:\n{p.stdout}{p.stderr}")
    if not zip_path.exists():
        sys.exit(f"forge soldeer push --dry-run wrote no zip at {zip_path}:\n{p.stdout}{p.stderr}")
    with zipfile.ZipFile(zip_path) as z:
        names = sorted(n for n in z.namelist() if not n.endswith("/"))
    zip_path.unlink()   # or a real push from this directory would ship it
    return names


def main() -> None:
    staged = stage()
    version = json.loads((OUT / "package.json").read_text())["version"]
    problems = check_contents(staged)

    files, info = npm_files()
    problems += check_list("npm", files, staged)

    sold = soldeer_files(version)
    if sold is not None:
        problems += check_list("soldeer", sold, staged)

    if problems:
        print("\n".join(problems))
        sys.exit(f"pack: {len(problems)} problem(s)")
    kb = lambda n: f"{n / 1024:,.0f} kB"
    print(f"pack ok: {info['name']}@{version}, {len(files)} files, "
          f"{kb(info['size'])} packed, {kb(info['unpackedSize'])} unpacked"
          + (f"; soldeer {SOLDEER_NAME}~{version}, the same {len(sold)} files" if sold is not None else ""))
    print(f"staged in {OUT.relative_to(ROOT)}/ (nothing published)")


if __name__ == "__main__":
    main()
