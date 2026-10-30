"""How much text each held frame asks the eye to read.

Dry-runs every scene (as check.py does) and prints, for the held frame of
every section, the lit strings, the ghost strings (dimmed leftovers,
vocab.GHOST_OPACITY) and the glyphs in the lit ones; then one line per
slide with its poster (the last section). The deck's edit pass budgets
these (talk/briefs/edit-pass.md): a poster at or under TEXT_BUDGET
strings and GLYPH_BUDGET glyphs, no ghosts.

    uv run talk/scenes/census.py            # every scene
    uv run talk/scenes/census.py s02_exp40  # one
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check  # noqa: E402  (the dry-run harness)

TEXT_BUDGET = 12  # lit strings on a poster, the logos and the caption included
GLYPH_BUDGET = 260  # glyphs on a poster: about two BODY lines of digits plus labels


def main(names: list[str]) -> int:
    scenes = names or sorted(p.stem for p in HERE.glob("s[0-9][0-9]*_*.py"))
    posters = []
    for name in scenes:
        mod = importlib.import_module(name)
        scene = check.dry_run(mod)
        for sec, lit, ghost, glyphs in scene.held:
            print(f"{name:20s} {sec:14s} lit {lit:3d}  ghost {ghost:3d}  glyphs {glyphs:5d}")
        posters.append((name, *scene.held[-1]))
    print()
    print(f"{'poster':20s} {'section':14s} {'lit':>4s} {'ghost':>6s} {'glyphs':>7s}  over")
    over = 0
    for name, sec, lit, ghost, glyphs in posters:
        flags = []
        if lit > TEXT_BUDGET:
            flags.append(f"+{lit - TEXT_BUDGET} strings")
        if glyphs > GLYPH_BUDGET:
            flags.append(f"+{glyphs - GLYPH_BUDGET} glyphs")
        if ghost:
            flags.append(f"{ghost} ghosts")
        over += bool(flags)
        print(f"{name:20s} {sec:14s} {lit:4d} {ghost:6d} {glyphs:7d}  {' · '.join(flags)}")
    print(f"\n{over} of {len(posters)} posters over budget")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
