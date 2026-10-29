"""Check that each scene draws the numbers the JSON holds.

Every scene module exposes numbers(): the values it puts on screen. This
recomputes them straight from the loaders in vocab.py and compares, so a
regenerated edges.json or ladder.json that a scene silently ignored (a
hard-coded digit, a stale copy) fails here before it is rendered.

    uv run talk/scenes/check.py            # every scene that has numbers()
    uv run talk/scenes/check.py s02_exp40  # one
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vocab  # noqa: E402


def expect_s02_exp40(mod) -> dict:
    p = vocab.probe(mod.OP, mod.ARG)
    lib = vocab.libs()
    rows = []
    for lid in mod.LIBS:
        v = p["cells"][lid]["value"]
        assert not p["cells"][lid].get("reverted") and not p["cells"][lid].get("zero"), lid
        rows.append(
            {
                "id": lid,
                "label": lib[lid]["label"],
                "value": v,
                "digits": vocab.correct_digits(v, p["truth"]),
                "first_wrong": vocab.first_wrong_index(v, p["truth"]),
            }
        )
        # the integer-rounded measure edges.json reports agrees with ours
        assert int(float(p["cells"][lid]["digits"])) == rows[-1]["digits"], (lid, p["cells"][lid]["digits"], rows[-1]["digits"])
    return {
        "truth": p["truth"],
        "word_digits": len(p["truth"].partition(".")[0]) + mod.WORD_DECIMALS,
        "rows": rows,
        "correctly_rounded": vocab.correctly_rounded_18(p["truth"]),
    }


def expect_s04_grid(mod) -> dict:
    line = vocab.GridLine(mod.TICKS, length=11.5)
    return {
        "ticks": list(range(mod.TICKS[0], mod.TICKS[1] + 1)),
        "lands": {
            "first": (mod.EXACT_1, line.nearest_tick(mod.EXACT_1)),
            "wrong": (mod.EXACT_2, 8.0),
            "right": (mod.EXACT_3, line.nearest_tick(mod.EXACT_3)),
        },
    }


EXPECT = {"s02_exp40": expect_s02_exp40, "s04_grid": expect_s04_grid}


def main(argv: list[str]) -> int:
    names = argv or sorted(EXPECT)
    bad = 0
    for name in names:
        mod = importlib.import_module(name)
        drawn = mod.numbers()
        want = EXPECT[name](mod)
        if drawn == want:
            print(f"ok    {name}")
        else:
            bad += 1
            print(f"FAIL  {name}\n  drawn: {drawn}\n  json:  {want}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
