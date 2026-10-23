#!/usr/bin/env python3
"""Generate a library's deployable object, Solidity library, interface and ABI
from its single Yul source (contracts/src/fp127/FP127.yul.src or
contracts/src/fp19/FP19.yul.src).

Usage:
    uv run scripts/fp127/gen.py [--lib fp127|fp19]            # write outputs next to the source
    uv run scripts/fp127/gen.py [--lib fp127|fp19] --check    # regenerate and diff
    uv run scripts/fp127/gen.py --lib fp19 --wide-lib <path>  # the test-only library whose
                                                               # rounding test always fails
    uv run scripts/fp127/gen.py [--lib ...] --count-lib <path>  # test only: counts each
                                                               # rounding-test fallback
    uv run scripts/fp127/gen.py [--lib ...] --probe-lib <path>  # test only: gas probes on
                                                               # the profiled helpers
    (add --forced to either for the forced second stage, as --wide-lib)
    uv run scripts/fp127/gen.py --objects [fp127|fp19]        # the deployed objects' make stems
                                                               # (fp127 fp19 fp19e ...); the
                                                               # Makefile loops over this list

An export may carry `/// @object <Name>` to go into another deployed object
(FP19 deploys as FP19, FP19E, FP19H and FP19S). Each object then holds only
its exports and their callees and gets its own interface and ABI; the
inline library holds every export.

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
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[2]
# The inline library inlines the clz builtin (msb), which solc has from
# 0.8.31 with evmVersion osaka; the interfaces use nothing new and keep the
# wider pragma, so a caller on an older compiler can still call the objects.
LIB_PRAGMA = "^0.8.31"
SOLIDITY_PRAGMA = "^0.8.24"

# One generator, two libraries. Everything that names the library lives here;
# the parser, validator and emitters are shared.
LIBS = {
    "fp127": {
        "src": ROOT / "contracts" / "src" / "fp127" / "FP127.yul.src",
        "object": "FP127", "lib": "FP127Lib", "iface": "IFP127",
        "one": "int256 internal constant ONE = int256(1) << 128;",
        "consts": "/// @notice pi as the 127.128 word nearest it, pi * 2^128 rounded to the\n    ///         nearest integer: 38 digits, the format's best. A constant, not\n    ///         an op: an object caller can copy the literal.\n    int256 internal constant PI = 0x3243f6a8885a308d313198a2e03707345;",
        "iface_notice": "Interface of the deployed FP127 object. Values are signed 127.128\n///         fixed-point: one int256 whose value is raw / 2^128.",
        "lib_notice": "Inlinable FP127: signed 127.128 fixed-point, one int256 per value,\n///         value = raw / 2^128. Every function body is the same Yul that the\n///         deployed FP127 object runs, so the two agree by construction.\n///         It uses the CLZ opcode: compile with evmVersion osaka (solc >= 0.8.31)\n///         and run only on a chain that has CLZ (EIP-7939).",
        "objects": {
            "FP127": {"iface": "IFP127", "abi": "abi.json", "salt": "FP127 v6"},
        },
    },
    "fp19": {
        "src": ROOT / "contracts" / "src" / "fp19" / "FP19.yul.src",
        "object": "FP19", "lib": "FP19Lib", "iface": "IFP19",
        "one": "int256 internal constant ONE = int256(0x3ffff) << 236;",
        "consts": "/// @notice pi as the FP19 word nearest it: 237 bits, about 71 digits.\n    ///         A constant, not an op: an object caller can copy the literal.\n    int256 internal constant PI = 0x40000921fb54442d18469898cc51701b839a252049c1114cf98e804177d4c762;",
        "iface_notice": "Interface of the deployed FP19 object, the number: arithmetic, roots,\n///         comparison, rounding and conversions. Values are 256-bit binary\n///         floating point: one int256 holding sign (bit 255), a 19-bit biased\n///         exponent (bits 254..236, bias 262143) and a 236-bit fraction with an\n///         implicit leading one; zero is the all-zero word.",
        "lib_notice": "Inlinable FP19: 256-bit binary floating point, one int256 per value\n///         (sign, 19-bit exponent, 236-bit fraction). Every function body is the\n///         same Yul that the deployed FP19 objects run, so they agree by\n///         construction. It uses the CLZ opcode: compile with evmVersion osaka\n///         (solc >= 0.8.31) and run only on a chain that has CLZ (EIP-7939).",
        # Blockulator 2.2: four deployed objects by idea from the one source.
        # FP19 is the number; FP19E the elementary functions on the one
        # exp/log kernel; FP19H the hyperbolic functions, on their own copy of
        # that kernel (with them FP19E measured 27,308 bytes, over the
        # 24,576 limit); FP19S the special functions.
        "objects": {
            "FP19": {"iface": "IFP19", "abi": "abi.json", "salt": "FP256 v5"},
            "FP19E": {"iface": "IFP19E", "abi": "abiE.json", "salt": "FP256E v5",
                       "iface_notice": "Interface of the deployed FP19E object, FP19's elementary\n///         functions on its one exp/log kernel: exp, exp2, exp10, expm1, ln,\n///         log2, log10, log2Up, log1p, pow, powu and compound, on the same\n///         256-bit binary floating point words as IFP19 (sign bit 255, a\n///         19-bit biased exponent, bias 262143, a 236-bit fraction; zero is\n///         the all-zero word)."},
            "FP19H": {"iface": "IFP19H", "abi": "abiH.json", "salt": "FP256H v5",
                       "iface_notice": "Interface of the deployed FP19H object, FP19's hyperbolic\n///         functions: sinh, cosh, tanh and atanh, on the same 256-bit binary\n///         floating point words as IFP19. They run on the exp/log kernel of\n///         FP19E, carried here as their own copy: beside FP19E's ops they\n///         would not fit one object."},
            "FP19S": {"iface": "IFP19S", "abi": "abiS.json", "salt": "FP256S v5",
                       "iface_notice": "Interface of the deployed FP19S object, FP19's special functions:\n///         erf, erfc, normCdf, lambertW0, lambertWm1 and factorial, on the\n///         same 256-bit binary floating point words as IFP19."},
        },
        "lib_dev": "Blocks are memory-safe: the only memory touched is scratch space\n///      (0x00..0x3f) for revert selectors and lerp's comparisons, and lerp's\n///      four-word accumulator just past the free memory pointer, which it does\n///      not move.",
    },
    # BlockulatorWad: Solady's WAD names on FP19's kernels. Its source calls
    # FP19.yul.src's functions (the base), and only its own exports are
    # emitted, each with its closure: an inline library, no deployed object.
    "wad": {
        "src": ROOT / "contracts" / "src" / "wad" / "BlockulatorWad.yul.src",
        "base": ROOT / "contracts" / "src" / "fp19" / "FP19.yul.src",
        "library_only": True,
        # an export without a leave is written into its block, not called
        "inline_exports": True,
        "object": "BlockulatorWad", "lib": "BlockulatorWad", "iface": "IBlockulatorWad",
        "one": "uint256 internal constant WAD = 1e18;",
        "consts": "/// @notice 10^18 as a signed word, for the int256 functions.\n    int256 internal constant SWAD = 1e18;",
        "lib_notice": "WAD maths with Solady's names (FixedPointMathLib) and every result\n///         correct to the last wei: the exact real value rounded once in the\n///         stated direction. Computed on FP19's correctly rounded kernels;\n///         where FP19's error bound reaches a wei boundary, a second stage\n///         at 2^-510 on the exact input decides it. It uses the CLZ opcode:\n///         compile with evmVersion osaka (solc >= 0.8.31) and run only on a\n///         chain that has CLZ (EIP-7939).",
        "lib_dev": "Blocks are memory-safe: the only memory touched is scratch space\n///      (0x00..0x3f) for revert selectors.",
        "objects": {},
        # --wide-lib: the test-only library whose fast-path test always fails,
        # so every result comes from the second stage
        "forced": {"wadbad": "function wadbad(F, errF) -> b {\n    b := 1\n}"},
    },
}
LIB = LIBS["fp127"]
# The objects tables above are the one list of deployed objects: each
# object's name, library and CREATE2 salt. The Makefile loops over
# `gen.py --objects`, and stdjson.py and deploy.py read DEPLOYED, so a
# re-layout or a new salt edits only the tables.
#   make stem (FP_LIB) -> (object name, library, salt)
DEPLOYED = {name.lower(): (name, lib, meta["salt"])
            for lib, cfg in LIBS.items() for name, meta in cfg["objects"].items()}


def print_objects(lib: str = "all") -> None:
    """The make stems of the deployed objects (of one library, or all)."""
    print(" ".join(k for k, (_, l, _) in DEPLOYED.items() if lib in ("all", l)))


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
    obj: str = ""

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
_TAG_RE = re.compile(r"///\s*@(domain|reverts|object)\s+(.*)$")
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
                meta = {"domain": "", "reverts": "", "object": ""}
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
                           meta["domain"], meta["reverts"], meta["object"])
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
            # reading the free memory pointer is how a block finds memory it may use
            if m.group(1) == "mload" and arg.lower() == "0x40":
                continue
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
    reserved = set(names) | {"ONE", "PI"}
    for f in src.funcs.values():
        body = strip_comments(f.text)
        idents = set(f.params) | set(f.rets) | set(re.findall(r"\blet\s+([A-Za-z_][A-Za-z0-9_]*)", body)) | {f.name}
        for ident in sorted(idents & reserved):
            problems.append(f"{f.name}: identifier {ident!r} shadows a library member")
    sels = [e.selector for e in src.exports]
    if len(sels) != len(set(sels)):
        problems.append("selector collision between exports")
    for e in src.exports:
        if object_of(e) not in objects():
            problems.append(f"{e.yul_name}: @object {e.obj} is not one of {sorted(objects())}")

    if problems:
        sys.stderr.write("FP127.yul.src failed validation:\n")
        for p in problems:
            sys.stderr.write(f"  - {p}\n")
        sys.exit(1)


def with_base(src: Source, raw: str) -> Source:
    """A library on a base source (LIB["base"]): the base's functions join its
    own, its exports and errors stay its own. Validated as one source, so every
    rule and every name check covers the functions it can call."""
    base_raw = LIB["base"].read_text()
    base = parse(base_raw)
    dup = sorted(set(src.funcs) & set(base.funcs))
    if dup:
        sys.stderr.write(f"{SRC.name} redefines {LIB['base'].name} functions: {', '.join(dup)}\n")
        sys.exit(1)
    funcs = {**base.funcs, **src.funcs}
    validate(Source(src.header, {**base.errors, **src.errors}, funcs, src.exports), base_raw + "\n" + raw)
    return Source(src.header, src.errors, funcs, src.exports)


def objects() -> dict[str, dict]:
    """The deployed objects of the current library: one unless LIB names more."""
    return LIB.get("objects") or {OBJECT_NAME: {"iface": IFACE_NAME, "abi": "abi.json"}}


def object_of(e: Export) -> str:
    return e.obj or OBJECT_NAME


def object_funcs(src: Source, name: str) -> list[Func]:
    """The functions an object carries. A one-object library keeps every
    function in source order (FP127's deployed bytes depend on it); a split
    library keeps each object's exports and their callees, in source order."""
    if len(objects()) == 1:
        return list(src.funcs.values())
    need: set[str] = set()
    for e in src.exports:
        if object_of(e) == name:
            need.update(f.name for f in closure(src, e.yul_name))
    return [f for f in src.funcs.values() if f.name in need]


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
    base = f" and {LIB['base'].name}" if LIB.get("base") else ""
    return f"// GENERATED by scripts/fp127/gen.py from {SRC.name}{base}. Do not edit.\n"


def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join((pad + l) if l.strip() else l for l in text.splitlines())


# A flat switch is a linear chain of comparisons, about 22 gas per selector
# ranked before the one called; the binary search below costs one comparison
# per level instead, and pays from a dozen or so exports (measured: FP127's
# 55 save 465 gas a call on average, release four's FP19X3 with 15 saved 72,
# FP19X2 with 10 saved 31 with some ops dearer, FP19X with 5 would have
# lost). Objects with fewer than DISPATCH_MIN exports keep the flat switch:
# FP19H (4) and FP19S (6). FP19 and FP19E (12) take the search; the FP19
# core took it in fp19-basic-fast (measured on the gas ladder: 278 gas a call
# saved on average over its 37 benched exports then, up to 656, a few of the
# first-ranked ones up to 85 dearer).
DISPATCH_MIN = 10
# A leaf of the selector search is a plain switch of at most this many cases.
DISPATCH_LEAF = 4


def dispatch_steps(selectors: list[str], flat: bool) -> dict[str, int]:
    """Comparisons the dispatch makes before it reaches each selector's case
    (selectors sorted): the rank in a flat switch; in the search, the levels
    above the leaf plus the rank in it. make profile fits the object's call
    and dispatch cost on these."""
    if flat:
        return {s: i for i, s in enumerate(selectors)}
    out: dict[str, int] = {}

    def node(ss: list[str], depth: int) -> None:
        if len(ss) <= DISPATCH_LEAF:
            out.update({s: depth + i for i, s in enumerate(ss)})
            return
        mid = len(ss) // 2
        node(ss[mid:], depth + 1)
        node(ss[:mid], depth + 1)

    node(selectors, 0)
    return out


def flat_dispatch(name: str, n: int) -> bool:
    return n < DISPATCH_MIN


def emit_dispatch(exports: list[Export], flat: bool = False) -> str:
    """The selector dispatch over exports sorted by selector: a binary search
    (switch on lt(sel, pivot)) down to switches of at most DISPATCH_LEAF
    cases, each with a reverting default; flat=True is one switch."""
    def case(e: Export, pad: str) -> str:
        args = ", ".join(f"calldataload({4 + 32 * i})" for i in range(len(e.inputs)))
        return f"{pad}case {e.selector} {{ /* {e.signature} */\n{pad}    ret({e.yul_name}({args}))\n{pad}}}"

    if flat:
        cases = "\n".join(case(e, " " * 12) for e in exports)
        return f"            switch shr(224, calldataload(0))\n{cases}\n            default {{ revert(0, 0) }}"

    def node(es: list[Export], depth: int) -> str:
        pad = " " * (12 + 4 * depth)
        if len(es) <= DISPATCH_LEAF:
            cases = "\n".join(case(e, pad) for e in es)
            return f"{pad}switch dsel\n{cases}\n{pad}default {{ revert(0, 0) }}"
        mid = len(es) // 2
        return (f"{pad}switch lt(dsel, {es[mid].selector})\n"
                f"{pad}case 0 {{\n{node(es[mid:], depth + 1)}\n{pad}}}\n"
                f"{pad}default {{\n{node(es[:mid], depth + 1)}\n{pad}}}")

    return "            let dsel := shr(224, calldataload(0))\n" + node(exports, 0)


def emit_object(src: Source, name: str | None = None) -> str:
    name = name or OBJECT_NAME
    exports = sorted((e for e in src.exports if object_of(e) == name), key=lambda e: int(e.selector, 16))
    funcs = "\n\n".join(_indent(f.text, 12) for f in object_funcs(src, name))
    return f"""{banner()}object "{name}" {{
    code {{
        datacopy(0, dataoffset("runtime"), datasize("runtime"))
        return(0, datasize("runtime"))
    }}
    object "runtime" {{
        code {{
{emit_dispatch(exports, flat_dispatch(name, len(exports)))}

            function ret(v) {{
                mstore(0, v)
                return(0, 32)
            }}

{funcs}
        }}
    }}
}}
"""


def emit_interface(src: Source, name: str | None = None) -> str:
    name = name or OBJECT_NAME
    meta = objects()[name]
    iface = meta["iface"]
    notice = meta.get("iface_notice", LIB["iface_notice"])
    errs = "\n".join(f"    error {sig};" for sig in src.errors)
    fns = []
    for e in src.exports:
        if object_of(e) != name:
            continue
        ins = ", ".join(f"{p.type} {p.name}" for p in e.inputs)
        outs = ", ".join(f"{p.type} {p.name}" for p in e.outputs)
        doc = "\n".join(f"    {d}" for d in e.doc)
        fns.append(f"{doc}\n    function {e.sol_name}({ins}) external pure returns ({outs});")
    return f"""// SPDX-License-Identifier: MIT
pragma solidity {SOLIDITY_PRAGMA};
{banner()}
/// @title {iface}
/// @notice {notice}
interface {iface} {{
{errs}

{chr(10).join(fns)}
}}
"""


# ---------------------------------------------------------------------------
# Test-only instrumented libraries (--count-lib, --probe-lib). Both keep every
# result bit for bit: a named helper is renamed and wrapped by a function of
# its old name that calls it and records into memory far above anything the
# library or its caller allocates. The caller pre-expands that memory and
# reads it after the call; a fresh external call starts it at zero.
# ---------------------------------------------------------------------------

# Where the records live. The fallback counter is one word. Probe i (in
# PROBES order) keeps three words from PROBE_BASE + 0x60 i: its inclusive gas
# (the call, net of the probes' own cost inside it), its call count, and its
# exclusive gas (less the inclusive gas of the probed helpers it calls).
# PROBE_OVH accumulates the probes' own cost and PROBE_INNER the inclusive gas
# of finished probes, so an enclosing probe can take both out.
COUNT_SLOT = 0x8000
PROBE_OVH = 0x8020
PROBE_INNER = 0x8040
PROBE_BASE = 0x8060
PROBE_STRIDE = 0x60
# The part of a probe's own cost its gas() readings cannot see: the extra
# call into the wrapper and the last mstore. Measured with make profile's
# calibration (probe total - plain total over the recorded overhead).
PROBE_RESIDUAL = 92

# The rounding-test fallbacks, by helper: "ret" counts a call that returns
# nonzero (the test said the fast value may round wrongly), "call" counts
# every call (the helper is the fallback itself).
COUNTS = {
    "fp19": {"rbad": "ret"},
    # BlockulatorWad: wadbad fires when FP19's bound reaches a wei boundary
    "wad": {"wadbad": "ret"},
    # FP127: the double-word log l2p runs exactly when the one-word log or pow
    # could not decide (nearmid, or pow2t not ok)
    "fp127": {"l2p": "call", "powus": "call"},
}

# The helpers make profile measures, in slot order.
PROBES = {
    "fp19": ["log2m", "exp2frac", "wexpm1", "wlnw", "cfrun", "erfw", "lwfix",
              "lwlog", "lwf128", "lnc", "lwq510", "lwsp", "lwy", "powslow", "compslow", "wln1ps",
              "erfser", "erfcxa", "erfcxcf", "erfasym", "expnegsq",
              # #79's ops: the hyperbolics, the logs' wide step, cbrt, the roots, lerp
              "em1k", "hserw", "hypw", "tanhw1", "tanhw2", "wln", "cbrtseed", "cbrtw", "cubegt",
              "isqrtw", "lerp3"],
    "fp127": ["expk", "log2m", "erfs", "erfcf", "lwf127", "lnc", "lwqs", "lwsp", "lwfin",
              "l2p", "powus", "einvhalf", "cbrtw", "cube"],
}


def _rename(f: Func, new: str) -> str:
    return re.sub(rf"^function\s+{re.escape(f.name)}\s*\(", f"function {new}(", f.text, count=1)


def _sig(f: Func) -> tuple[str, str, str]:
    args = ", ".join(f.params)
    rets = ", ".join(f.rets)
    head = f"function {f.name}({args})" + (f" -> {rets}" if rets else "")
    call = (f"{rets} := " if rets else "")
    return head, args, call


def count_wrap(f: Func, mode: str) -> str:
    """The helper renamed <name>cnt, and a wrapper that adds one to the word
    at COUNT_SLOT when the rounding test fires (or on every call)."""
    head, args, call = _sig(f)
    cond = f.rets[0] if mode == "ret" else "1"
    return (f"{_rename(f, f.name + 'cnt')}\n\n"
            f"{head} {{\n"
            f"    {call}{f.name}cnt({args})\n"
            f"    if {cond} {{ mstore({COUNT_SLOT:#x}, add(mload({COUNT_SLOT:#x}), 1)) }}\n"
            f"}}")


def probe_wrap(f: Func, slot: int) -> str:
    """The helper renamed <name>prb, and a wrapper that times the call: its
    gas net of the probes' own cost inside it (inclusive) goes to the word at
    slot, one to the next word, the inclusive gas less that of the probed
    helpers it called (exclusive) to the third; then its own cost to
    PROBE_OVH, and PROBE_INNER is left at its entry value plus this call's
    inclusive gas."""
    head, args, call = _sig(f)
    o, i = f"{PROBE_OVH:#x}", f"{PROBE_INNER:#x}"
    s, n, x = (f"{slot + k:#x}" for k in (0, 0x20, 0x40))
    return (f"{_rename(f, f.name + 'prb')}\n\n"
            f"{head} {{\n"
            f"    let prbt := gas()\n"
            f"    let prbo := mload({o})\n"
            f"    let prbi := mload({i})\n"
            f"    let prbg := gas()\n"
            f"    {call}{f.name}prb({args})\n"
            f"    prbg := sub(prbg, gas())\n"
            f"    prbo := sub(mload({o}), prbo)\n"
            f"    prbg := sub(prbg, prbo)\n"
            f"    mstore({s}, add(mload({s}), prbg))\n"
            f"    mstore({n}, add(mload({n}), 1))\n"
            f"    mstore({x}, add(mload({x}), sub(prbg, sub(mload({i}), prbi))))\n"
            f"    mstore({i}, add(prbi, prbg))\n"
            f"    mstore({o}, add(mload({o}), add(sub(sub(sub(prbt, gas()), prbg), prbo), {PROBE_RESIDUAL})))\n"
            f"}}")


def instrumented(lib: str, kind: str) -> dict[str, str]:
    """name -> 'ret' | 'call' (count) or name -> slot (probe), for lib."""
    if kind == "count":
        return dict(COUNTS[lib])
    return {n: PROBE_BASE + PROBE_STRIDE * i for i, n in enumerate(PROBES[lib])}


def emit_library(src: Source, lib_name: str | None = None, wide: bool = False,
                 count: dict | None = None, probe: dict | None = None) -> str:
    """The inline library. wide=True is the test-only variant: rbad (the
    rounding test of every correctly rounded op) always says the fast result
    is too close to a tie, so every call takes the wide second stage.
    count / probe (test only, never committed) wrap the named helpers to
    record fallbacks or gas in memory; see count_wrap and probe_wrap."""
    lib_name = lib_name or LIB_NAME
    errs = "\n".join(f"    error {sig};" for sig in src.errors)
    fns = []
    for e in src.exports:
        ins = ", ".join(f"{p.type} _{p.name}" for p in e.inputs)
        outs = ", ".join(f"{p.type} _{p.name}" for p in e.outputs)
        call_args = ", ".join(f"_{p.name}" for p in e.inputs)
        ret_names = ", ".join(f"_{p.name}" for p in e.outputs)
        funcs = closure(src, e.yul_name)
        texts = []
        for f in funcs:
            t = f.text
            if wide and f.name in LIB.get("forced", {"rbad": ""}):
                t = LIB.get("forced", {}).get(f.name) or "function rbad(D, err) -> b {\n    b := 1\n}"
            elif count and f.name in count:
                t = count_wrap(f, count[f.name])
            elif probe and f.name in probe:
                t = probe_wrap(f, probe[f.name])
            texts.append(t)
        call = f"            {ret_names} := {e.yul_name}({call_args})"
        export = src.funcs[e.yul_name]
        if LIB.get("inline_exports") and "leave" not in strip_comments(export.text):
            # the export's body in the block itself: an inline-assembly
            # function call costs about 70 gas, as much as a one-word mulWad,
            # and a block that defines any function about 25 more. With no
            # helpers the Solidity parameters take the Yul names; with them
            # (whose parameters may reuse those names) they are bound.
            texts = texts[:-1]
            inner = _indent(textwrap.dedent(export.text[export.text.index("{") + 1:export.text.rindex("}")].strip("\n")), 12)
            if texts:
                binds = [f"let {p.name} := _{p.name}" for p in e.inputs] + [f"let {p.name} := 0" for p in e.outputs]
                call = (_indent("\n".join(binds), 12) + "\n" + inner + "\n" + "            "
                        + ", ".join(f"_{p.name}" for p in e.outputs) + " := " + ", ".join(p.name for p in e.outputs))
            else:
                ins = ", ".join(f"{p.type} {p.name}" for p in e.inputs)
                outs = ", ".join(f"{p.type} {p.name}" for p in e.outputs)
                call = inner
        body = "\n\n".join(_indent(t, 12) for t in texts)
        doc = "\n".join(f"    {d}" for d in e.doc)
        # the instrumented variants write above the free memory, so they do
        # not claim memory safety
        asm = "assembly" if (count or probe) else 'assembly ("memory-safe")'
        mut = "view" if probe else "pure"   # the probes read gas()
        fns.append(
            f"{doc}\n"
            f"    function {e.sol_name}({ins}) internal {mut} returns ({outs}) {{\n"
            f"        {asm} {{\n"
            f"{body}\n\n"
            f"{call}\n"
            f"        }}\n"
            f"    }}"
        )
    if count or probe:
        what = (f"counts each rounding-test fallback ({', '.join(sorted(count))}) in the word at {COUNT_SLOT:#x}"
                if count else
                f"adds the gas of each call of {', '.join(probe)} to the words from {PROBE_BASE:#x}")
        if wide:
            what += ", with the rounding test forced to fail (every call takes the second stage)"
        notice = (f"TEST ONLY. {LIB_NAME} instrumented: {what}.\n///         "
                  "Results are unchanged. Generated for make sweep / make profile; never\n///         deploy or import it.")
    elif wide:
        notice = "TEST ONLY. " + LIB_NAME + " with the rounding test forced to fail, so every\n///         correctly rounded op returns its wide second stage. Generated for\n///         make sweep's second-stage pass; never deploy or import it."
    else:
        notice = LIB["lib_notice"]
    dev = LIB.get("lib_dev", "Blocks are memory-safe: the only memory touched is scratch space\n"
                             "///      (0x00..0x3f) for revert selectors.")
    if count or probe:
        dev = (f"Not memory-safe: the records live at {COUNT_SLOT:#x} and above, which the\n"
               "///      calling test pre-expands.")
    return f"""// SPDX-License-Identifier: MIT
pragma solidity {LIB_PRAGMA};
{banner()}
/// @title {lib_name}
/// @notice {notice}
/// @dev {dev}
library {lib_name} {{
{errs}

    {LIB["one"]}

    {LIB["consts"]}

{chr(10).join(fns)}
}}
"""


def emit_abi(src: Source, name: str | None = None) -> str:
    name = name or OBJECT_NAME
    abi = []
    for sig in src.errors:
        abi.append({"type": "error", "name": sig[:-2], "inputs": []})
    for e in src.exports:
        if object_of(e) != name:
            continue
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
        extra = {"object": object_of(e)} if len(objects()) > 1 else {}
        ops.append({
            **extra,
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
    out = {"ops.json": emit_ops(src)}
    if LIB.get("library_only"):
        out[f"{LIB_NAME}.sol"] = emit_library(src)
        return out
    for name, meta in objects().items():
        out[f"{name}.yul"] = emit_object(src, name)
    out[f"{LIB_NAME}.sol"] = emit_library(src)
    for name, meta in objects().items():
        out[f"{meta['iface']}.sol"] = emit_interface(src, name)
        out[meta["abi"]] = emit_abi(src, name)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="diff against committed outputs")
    ap.add_argument("--lib", choices=sorted(LIBS), default="fp127", help="which library's source and names")
    ap.add_argument("--src", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--wide-lib", type=Path, default=None, help="write only the test-only forced-second-stage library here")
    ap.add_argument("--count-lib", type=Path, default=None, help="write only the test-only library that counts rounding-test fallbacks here")
    ap.add_argument("--probe-lib", type=Path, default=None, help="write only the test-only library with gas probes on the profiled helpers here")
    ap.add_argument("--forced", action="store_true", help="with --count-lib or --probe-lib: also force the rounding test to fail, as --wide-lib")
    ap.add_argument("--objects", nargs="?", const="all", choices=["all", *sorted(LIBS)],
                    help="print the deployed objects' make stems (of one library, default all) and exit")
    args = ap.parse_args()
    global LIB, SRC, OUT_DIR, OBJECT_NAME, LIB_NAME, IFACE_NAME
    if args.objects:
        print_objects(args.objects)
        return 0
    LIB = LIBS[args.lib]
    SRC = args.src or LIB["src"]
    OUT_DIR = args.out or SRC.parent
    OBJECT_NAME, LIB_NAME, IFACE_NAME = LIB["object"], LIB["lib"], LIB["iface"]
    args.src, args.out = SRC, OUT_DIR

    raw = args.src.read_text()
    src = parse(raw)
    if LIB.get("base"):
        src = with_base(src, raw)
    else:
        validate(src, raw)
    if args.wide_lib:
        name = args.wide_lib.stem
        args.wide_lib.parent.mkdir(parents=True, exist_ok=True)
        args.wide_lib.write_text(emit_library(src, name, wide=True))
        print(f"wrote {args.wide_lib} ({name}: {', '.join(LIB.get('forced', {'rbad': ''}))} forced to 1)")
        return 0
    for path, kind in ((args.count_lib, "count"), (args.probe_lib, "probe")):
        if path:
            names = instrumented(args.lib, kind)
            missing = sorted(set(names) - set(src.funcs))
            if missing:
                sys.stderr.write(f"--{kind}-lib: no function {', '.join(missing)} in {SRC.name}\n")
                return 1
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(emit_library(src, path.stem, wide=args.forced, **{kind: names}))
            print(f"wrote {path} ({path.stem}: {kind} on {', '.join(names)}{', rbad forced to 1' if args.forced else ''})")
    if args.count_lib or args.probe_lib:
        return 0
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
