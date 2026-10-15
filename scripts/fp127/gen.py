#!/usr/bin/env python3
"""Generate a library's deployable object, Solidity library, interface and ABI
from its single Yul source (contracts/src/fp127/FP127.yul.src or
contracts/src/fp256/FP256.yul.src).

Usage:
    uv run scripts/fp127/gen.py [--lib fp127|fp256]            # write outputs next to the source
    uv run scripts/fp127/gen.py [--lib fp127|fp256] --check    # regenerate and diff

The generator is deterministic. CI runs --check so the committed outputs can
never drift from the source.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[2]
SOLIDITY_PRAGMA = "^0.8.24"

# One generator, two libraries. Everything that names the library lives here;
# the parser, validator and emitters are shared.
LIBS = {
    "fp127": {
        "src": ROOT / "contracts" / "src" / "fp127" / "FP127.yul.src",
        "object": "FP127", "lib": "FP127Lib", "iface": "IFP127",
        "one": "int256 internal constant ONE = int256(1) << 128;",
        "iface_notice": "Interface of the deployed FP127 object. Values are signed 127.128\n///         fixed-point: one int256 whose value is raw / 2^128.",
        "lib_notice": "Inlinable FP127: signed 127.128 fixed-point, one int256 per value,\n///         value = raw / 2^128. Every function body is the same Yul that the\n///         deployed FP127 object runs, so the two agree by construction.",
    },
    "fp256": {
        "src": ROOT / "contracts" / "src" / "fp256" / "FP256.yul.src",
        "object": "FP256", "lib": "FP256Lib", "iface": "IFP256",
        "one": "int256 internal constant ONE = int256(0x3ffff) << 236;",
        "iface_notice": "Interface of the deployed FP256 object. Values are 256-bit binary\n///         floating point: one int256 holding sign (bit 255), a 19-bit biased\n///         exponent (bits 254..236, bias 262143) and a 236-bit fraction with an\n///         implicit leading one; zero is the all-zero word.",
        "lib_notice": "Inlinable FP256: 256-bit binary floating point, one int256 per value\n///         (sign, 19-bit exponent, 236-bit fraction). Every function body is the\n///         same Yul that the deployed FP256 object runs, so the two agree by\n///         construction.",
    },
}
LIB = LIBS["fp127"]
SRC = LIB["src"]
OUT_DIR = SRC.parent
OBJECT_NAME = LIB["object"]
LIB_NAME = LIB["lib"]
IFACE_NAME = LIB["iface"]

FORBIDDEN = [
    r"\bobject\b", r"\bcode\b", r"\bdatacopy\b", r"\bdataoffset\b",
    r"\bdatasize\b", r"\bcodecopy\b", r"\bcalldataload\b", r"\bcalldatasize\b",
    r"\bcalldatacopy\b", r"\breturn\s*\(", r"\bpc\s*\(", r"\bjump\b",
    r"\bjumpi\b", r"\bsload\b", r"\bsstore\b", r"\bcall\b", r"\bstaticcall\b",
    r"\bdelegatecall\b", r"\bcreate2?\b", r"\bselfdestruct\b", r"\blog[0-4]\s*\(",
]


def strip_comments(text: str) -> str:
    return re.sub(r"//[^\n]*", "", text)
ALLOWED_LITERAL_MEM = {"0", "0x0", "0x00", "0x20"}


def selector(sig: str) -> str:
    return "0x" + keccak.new(digest_bits=256, data=sig.encode()).hexdigest()[:8]


@dataclass
class Param:
    type: str
    name: str


@dataclass
class Export:
    sol_name: str
    inputs: list[Param]
    outputs: list[Param]
    yul_name: str
    doc: list[str] = field(default_factory=list)
    domain: str = ""
    reverts: str = ""

    @property
    def signature(self) -> str:
        return f"{self.sol_name}({','.join(p.type for p in self.inputs)})"

    @property
    def selector(self) -> str:
        return selector(self.signature)


@dataclass
class Func:
    name: str
    params: list[str]
    rets: list[str]
    text: str          # full text of the function definition
    calls: set[str] = field(default_factory=set)


@dataclass
class Source:
    header: str
    errors: dict[str, str]        # "Overflow()" -> "0x35278d12"
    funcs: dict[str, Func]
    exports: list[Export]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_FUNC_RE = re.compile(
    r"^function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(?:->\s*([^{]*))?\{",
    re.M,
)
_EXPORT_RE = re.compile(
    r"@export\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*returns\s*\(([^)]*)\)"
)
_TAG_RE = re.compile(r"///\s*@(domain|reverts)\s+(.*)$")
_ERROR_RE = re.compile(r"///\s*@error\s+([A-Za-z_][A-Za-z0-9_]*\(\))\s+(0x[0-9a-fA-F]{8})")
_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _parse_params(s: str) -> list[Param]:
    out = []
    for part in filter(None, (p.strip() for p in s.split(","))):
        t, n = part.split()
        out.append(Param(t, n))
    return out


def _find_block_end(text: str, open_idx: int) -> int:
    depth = 0
    i = open_idx
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces")


def parse(text: str) -> Source:
    errors = dict(_ERROR_RE.findall(text))
    funcs: dict[str, Func] = {}
    exports: list[Export] = []

    pos = 0
    header_end = None
    for m in _FUNC_RE.finditer(text):
        if header_end is None:
            header_end = m.start()
        start = m.start()
        open_idx = m.end() - 1
        end = _find_block_end(text, open_idx)
        body = text[start : end + 1]
        name = m.group(1)
        params = [p.strip() for p in m.group(2).split(",") if p.strip()]
        rets = [r.strip() for r in (m.group(3) or "").split(",") if r.strip()]
        calls = set(_CALL_RE.findall(re.sub(r"//[^\n]*", "", text[open_idx : end + 1])))
        funcs[name] = Func(name, params, rets, body, calls)

        # doc comment block immediately above the function
        doc_lines: list[str] = []
        j = start
        while True:
            prev_nl = text.rfind("\n", 0, j - 1)
            line = text[prev_nl + 1 : j].rstrip("\n")
            if line.strip().startswith("///"):
                doc_lines.insert(0, line.strip())
                j = prev_nl + 1
                if prev_nl < 0:
                    break
            else:
                break
        for line in doc_lines:
            em = _EXPORT_RE.search(line)
            if em:
                ins = _parse_params(em.group(2))
                outs = _parse_params(em.group(3))
                if [p.name for p in ins] != params:
                    raise ValueError(
                        f"{name}: @export params {[p.name for p in ins]} "
                        f"do not match Yul params {params}"
                    )
                if [p.name for p in outs] != rets:
                    raise ValueError(
                        f"{name}: @export returns {[p.name for p in outs]} "
                        f"do not match Yul returns {rets}"
                    )
                meta = {"domain": "", "reverts": ""}
                kept = []
                for d in doc_lines:
                    tm = _TAG_RE.match(d)
                    if tm:
                        meta[tm.group(1)] = tm.group(2).strip()
                    elif "@export" not in d:
                        kept.append(d)
                if not meta["domain"] or not meta["reverts"]:
                    raise ValueError(f"{name}: @export needs both @domain and @reverts")
                exports.append(
                    Export(em.group(1), ins, outs, name, kept,
                           meta["domain"], meta["reverts"])
                )
        pos = end + 1

    header = text[: header_end or 0]
    return Source(header, errors, funcs, exports)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(src: Source, raw: str) -> None:
    problems: list[str] = []

    # top level must be comments or functions only
    stripped = raw
    for f in src.funcs.values():
        stripped = stripped.replace(f.text, "")
    for line in stripped.splitlines():
        s = line.strip()
        if s and not s.startswith("//"):
            problems.append(f"top-level content outside a function: {s!r}")

    # error selectors must be correct
    for sig, sel in src.errors.items():
        want = selector(sig)
        if sel.lower() != want:
            problems.append(f"@error {sig} declares {sel}, keccak says {want}")

    # every rev(0x...) literal must be a declared error
    declared = {v.lower() for v in src.errors.values()}
    for m in re.finditer(r"\brev\(\s*(0x[0-9a-fA-F]{8})\s*\)", raw):
        if m.group(1).lower() not in declared:
            problems.append(f"rev({m.group(1)}) uses an undeclared error selector")

    for f in src.funcs.values():
        body = strip_comments(f.text)
        if f.name.startswith("_"):
            problems.append(f"{f.name}: Yul identifiers must not start with '_'")
        for pat in FORBIDDEN:
            if re.search(pat, body):
                problems.append(f"{f.name}: forbidden builtin {pat}")
        for m in re.finditer(r"\b(mstore8?|mload)\(\s*([^,)]+)", body):
            arg = m.group(2).strip()
            if re.fullmatch(r"0x[0-9a-fA-F]+|\d+", arg) and arg.lower() not in ALLOWED_LITERAL_MEM:
                problems.append(
                    f"{f.name}: literal memory address {arg}; use mload(0x40)-relative"
                )
        for v in re.findall(r"\blet\s+([A-Za-z_][A-Za-z0-9_]*)", body):
            if v.startswith("_"):
                problems.append(f"{f.name}: variable {v} must not start with '_'")
        for callee in f.calls:
            if callee in src.funcs:
                continue
            # builtins are fine; unknown non-builtin names are caught by solc
        # recursion is not allowed in inline assembly without care; forbid it
        if f.name in f.calls:
            problems.append(f"{f.name}: recursive functions are not allowed")

    names = [e.sol_name for e in src.exports]
    if len(names) != len(set(names)):
        problems.append("duplicate export names")
    # Inside a library assembly block every Yul identifier shares scope with
    # the library's own members, so none may reuse an export's Solidity name.
    reserved = set(names) | {"ONE"}
    for f in src.funcs.values():
        body = strip_comments(f.text)
        idents = set(f.params) | set(f.rets) | set(re.findall(r"\blet\s+([A-Za-z_][A-Za-z0-9_]*)", body)) | {f.name}
        for ident in sorted(idents & reserved):
            problems.append(f"{f.name}: identifier {ident!r} shadows a library member")
    sels = [e.selector for e in src.exports]
    if len(sels) != len(set(sels)):
        problems.append("selector collision between exports")

    if problems:
        sys.stderr.write("FP127.yul.src failed validation:\n")
        for p in problems:
            sys.stderr.write(f"  - {p}\n")
        sys.exit(1)


def closure(src: Source, root: str) -> list[Func]:
    """Transitive callees of root, in a deterministic order, root last."""
    seen: list[str] = []

    def visit(n: str) -> None:
        for c in sorted(src.funcs[n].calls):
            if c in src.funcs and c not in seen and c != n:
                visit(c)
        if n not in seen:
            seen.append(n)

    visit(root)
    return [src.funcs[n] for n in seen]


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def banner() -> str:
    return f"// GENERATED by scripts/fp127/gen.py from {SRC.name}. Do not edit.\n"


def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join((pad + l) if l.strip() else l for l in text.splitlines())


def emit_object(src: Source) -> str:
    exports = sorted(src.exports, key=lambda e: int(e.selector, 16))
    cases = []
    for e in exports:
        args = ", ".join(f"calldataload({4 + 32 * i})" for i in range(len(e.inputs)))
        cases.append(
            f"            case {e.selector} {{ /* {e.signature} */\n"
            f"                ret({e.yul_name}({args}))\n"
            f"            }}"
        )
    funcs = "\n\n".join(_indent(f.text, 12) for f in src.funcs.values())
    return f"""{banner()}object "{OBJECT_NAME}" {{
    code {{
        datacopy(0, dataoffset("runtime"), datasize("runtime"))
        return(0, datasize("runtime"))
    }}
    object "runtime" {{
        code {{
            switch shr(224, calldataload(0))
{chr(10).join(cases)}
            default {{ revert(0, 0) }}

            function ret(v) {{
                mstore(0, v)
                return(0, 32)
            }}

{funcs}
        }}
    }}
}}
"""


def emit_interface(src: Source) -> str:
    errs = "\n".join(f"    error {sig};" for sig in src.errors)
    fns = []
    for e in src.exports:
        ins = ", ".join(f"{p.type} {p.name}" for p in e.inputs)
        outs = ", ".join(f"{p.type} {p.name}" for p in e.outputs)
        doc = "\n".join(f"    {d}" for d in e.doc)
        fns.append(f"{doc}\n    function {e.sol_name}({ins}) external pure returns ({outs});")
    return f"""// SPDX-License-Identifier: MIT
pragma solidity {SOLIDITY_PRAGMA};
{banner()}
/// @title {IFACE_NAME}
/// @notice {LIB["iface_notice"]}
interface {IFACE_NAME} {{
{errs}

{chr(10).join(fns)}
}}
"""


def emit_library(src: Source) -> str:
    errs = "\n".join(f"    error {sig};" for sig in src.errors)
    fns = []
    for e in src.exports:
        ins = ", ".join(f"{p.type} _{p.name}" for p in e.inputs)
        outs = ", ".join(f"{p.type} _{p.name}" for p in e.outputs)
        call_args = ", ".join(f"_{p.name}" for p in e.inputs)
        ret_names = ", ".join(f"_{p.name}" for p in e.outputs)
        body = "\n\n".join(_indent(f.text, 12) for f in closure(src, e.yul_name))
        doc = "\n".join(f"    {d}" for d in e.doc)
        fns.append(
            f"{doc}\n"
            f"    function {e.sol_name}({ins}) internal pure returns ({outs}) {{\n"
            f"        assembly (\"memory-safe\") {{\n"
            f"{body}\n\n"
            f"            {ret_names} := {e.yul_name}({call_args})\n"
            f"        }}\n"
            f"    }}"
        )
    return f"""// SPDX-License-Identifier: MIT
pragma solidity {SOLIDITY_PRAGMA};
{banner()}
/// @title {LIB_NAME}
/// @notice {LIB["lib_notice"]}
/// @dev Blocks are memory-safe: the only memory touched is scratch space
///      (0x00..0x3f) for revert selectors.
library {LIB_NAME} {{
{errs}

    {LIB["one"]}

{chr(10).join(fns)}
}}
"""


def emit_abi(src: Source) -> str:
    abi = []
    for sig in src.errors:
        abi.append({"type": "error", "name": sig[:-2], "inputs": []})
    for e in src.exports:
        abi.append({
            "type": "function",
            "name": e.sol_name,
            "stateMutability": "pure",
            "inputs": [{"type": p.type, "name": p.name, "internalType": p.type} for p in e.inputs],
            "outputs": [{"type": p.type, "name": p.name, "internalType": p.type} for p in e.outputs],
        })
    return json.dumps(abi, indent=2) + "\n"


def emit_ops(src: Source) -> str:
    """Machine-readable op table for the site: everything the source says
    about each export. Precision and gas are joined at site build time from
    docs/fp127/precision.json and docs/benchmarks/gas.json."""
    ops = []
    for e in src.exports:
        # the notice runs until the first other tag
        lines, grab = [], False
        for d in e.doc:
            if d.startswith("/// @notice"):
                grab = True
                lines.append(d[len("/// @notice"):].strip())
            elif d.startswith("/// @"):
                grab = False
            elif grab:
                lines.append(d[3:].strip())
        notice = " ".join(lines)
        ops.append({
            "name": e.sol_name,
            "signature": e.signature,
            "selector": e.selector,
            "inputs": [p.name for p in e.inputs],
            "notice": notice,
            "domain": e.domain,
            "reverts": e.reverts,
        })
    return json.dumps({"errors": src.errors, "ops": ops}, indent=2, ensure_ascii=False) + "\n"


def emit_all(src: Source) -> dict[str, str]:
    return {
        "ops.json": emit_ops(src),
        f"{OBJECT_NAME}.yul": emit_object(src),
        f"{LIB_NAME}.sol": emit_library(src),
        f"{IFACE_NAME}.sol": emit_interface(src),
        "abi.json": emit_abi(src),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="diff against committed outputs")
    ap.add_argument("--lib", choices=sorted(LIBS), default="fp127", help="which library's source and names")
    ap.add_argument("--src", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    global LIB, SRC, OUT_DIR, OBJECT_NAME, LIB_NAME, IFACE_NAME
    LIB = LIBS[args.lib]
    SRC = args.src or LIB["src"]
    OUT_DIR = args.out or SRC.parent
    OBJECT_NAME, LIB_NAME, IFACE_NAME = LIB["object"], LIB["lib"], LIB["iface"]
    args.src, args.out = SRC, OUT_DIR

    raw = args.src.read_text()
    src = parse(raw)
    validate(src, raw)
    outputs = emit_all(src)

    if args.check:
        dirty = False
        for name, text in outputs.items():
            path = args.out / name
            current = path.read_text() if path.exists() else ""
            if current != text:
                dirty = True
                sys.stderr.write(f"--- {path} is stale\n")
                for line in difflib.unified_diff(
                    current.splitlines(), text.splitlines(), str(path), "generated", lineterm="", n=2
                ):
                    sys.stderr.write(line + "\n")
        if dirty:
            sys.stderr.write(f"run: uv run scripts/fp127/gen.py --lib {args.lib}\n")
            return 1
        print(f"gen-check ok: {len(src.exports)} exports, {len(src.funcs)} functions")
        return 0

    for name, text in outputs.items():
        (args.out / name).write_text(text)
    print(f"wrote {', '.join(outputs)} ({len(src.exports)} exports, {len(src.funcs)} functions)")
    for e in sorted(src.exports, key=lambda e: int(e.selector, 16)):
        print(f"  {e.selector}  {e.signature}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
