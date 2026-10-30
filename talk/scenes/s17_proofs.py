"""Slide 17, "Knowing it's right": three verbs, one number each, one limit.

The title is chrome. One row per click, the previous rows staying (they
are the answer): a tick and a verb in the row's hue, then its number in
white at 40: "proven" (BL127's and BL19's proven counts of their core
operations), "fuzzed" (the runs a test), "swept" with the hero "0
misrounded" at 72 in EMERALD on a halo. Last the one limit no check
covers, one MUTED line beside a hollow marker (never red: a limit is not
a bug), "none known" closing it.

Four sections: proven (autoplays under the test-and-proof lines), fuzzed,
tested (the swept row), limits (the poster). The plane of inputs, the
parentheticals (the Halmos count, the fuzzed ops, the result counts, the
oracles' digits), the second limit, the footnote and the closing line
are in the slide's notes, not on it.

Numbers from docs/benchmarks/proofs.json (.ops[] per lib with status:
the proven count and the core operations per library; .fuzz[] runs) and
docs/benchmarks/sweep.json (.rows[] for bl19 and bl127: misrounded summed
over every row; the 21 transcendentals, the BL127 README's list, V34,
are asserted among them).
"""

from __future__ import annotations

from manim import (
    LEFT,
    RIGHT,
    UP,
    Circle,
    FadeIn,
    VGroup,
)

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    DeckScene,
    Palette,
    _load,
    check_mark,
    halo,
    libs,
    proofs,
    thousands,
    words,
)

TITLE = "Knowing it's right"
KEYS = ("proven", "fuzzed", "swept")  # three verbs, each in its row's hue
MISROUNDED = "misrounded"
LIMIT = "limit: a midpoint within the last stage's error · none known"  # the one limit (V26), one line
# the 21 transcendentals, contracts/src/bl127/README.md "Rounding (3.0)": "The transcendentals
# round to nearest under the tie rule above: …" (claim V34; the same list for BL19)
TRANSCENDENTAL = (
    "exp", "exp2", "exp10", "expm1", "sinh", "cosh", "tanh", "atanh", "pow", "cbrt", "ln",
    "log2", "log10", "log1p", "powu", "compound", "lambertW0", "lambertWm1", "erf", "erfc", "normCdf",
)
LIBS = ("bl19", "bl127")

SIZE_ROW = 40  # the rows: a verb and its number, one line each
SIZE_ZERO = 72  # the hero: 0 misrounded
X_VALUE = -2.2  # the numbers' left edge; the verbs end GAP before it
GAP = 0.45
MARK_BUFF = 0.25  # mark to verb
ROW_Y = (2.05, 0.85, -0.6)  # the three rows
Y_LIMIT = -2.45
HUES = ROW_COLOUR["s17"]  # the rows: proven EMERALD, fuzzed GOLD, tested (swept) SAPPHIRE, the limit MUTED

# the digit-bearing fixed strings: none (every number on the slide is from numbers())
STEP = "Step 2. Prove it. Nobody is going to audit the auditor."  # the manual's step line, the slide's first beat
LITERALS: dict[str, str] = {STEP: "user 2026-10-30 outline"}


def numbers() -> dict:
    lib = libs()
    p = proofs()
    full = _load("docs/benchmarks/proofs.json")
    by = {name: [o for o in p["ops"] if o["lib"] == name] for name in ("BL127", "BL19")}
    proven = {name: [o["op"] for o in ops if o["status"] == "proven"] for name, ops in by.items()}
    fuzzed = {name: [o["op"] for o in ops if o["status"] == "fuzzed"] for name, ops in by.items()}
    for name, ops in by.items():
        assert len(proven[name]) + len(fuzzed[name]) == len(ops), (name, [o["status"] for o in ops])
    # every fuzz test's runs (the regression pins run once; they are not fuzz runs)
    runs = {f["runs"] for f in full["fuzz"] if f["test"].startswith("testFuzz_")}
    assert len(runs) == 1 and all(f["result"] == "pass" for f in full["fuzz"]), runs
    runs = runs.pop()
    # the sweep: every bl19 and bl127 row, plain and forced passes alike; the transcendentals among them
    sw = _load("docs/benchmarks/sweep.json")
    rows = {lid: [r for r in sw["rows"] if r["lib"] == lid] for lid in LIBS}
    assert all(set(TRANSCENDENTAL) <= {r["op"] for r in rows[lid]} for lid in LIBS)
    assert sum(r["misrounded"] for lid in LIBS for r in rows[lid] if r["op"] in TRANSCENDENTAL) == 0
    misrounded = sum(r["misrounded"] for lid in LIBS for r in rows[lid])
    assert misrounded == 0, misrounded
    return {
        "labels": {"bl19": lib["bl19"]["label"], "bl127": lib["bl127"]["label"]},
        "proven_count": {name: len(v) for name, v in proven.items()},
        "ops": {name: len(ops) for name, ops in by.items()},
        "runs": runs,
        "misrounded": misrounded,
    }


class Proofs(DeckScene):
    SECTIONS = ("step", "proven", "fuzzed", "tested", "limits")

    def row(self, i: int, key: str, value, mark, gap: float = GAP):
        """A row: the mark and the verb (in the row's hue) ending GAP before X_VALUE, the value from X_VALUE."""
        hue = HUES[("proven", "fuzzed", "tested")[i]]
        verb = words(key, SIZE_ROW, hue)
        value.move_to([X_VALUE + value.width / 2, ROW_Y[i], 0])
        verb.move_to([X_VALUE - gap - verb.width / 2, ROW_Y[i], 0])
        # baselines level: the last glyphs (n, d, t; 4, t, d) have no descenders
        verb.shift(UP * (value[-1].get_bottom()[1] - verb[-1].get_bottom()[1]))
        mark.next_to(verb, LEFT, buff=MARK_BUFF)
        mark.shift(UP * (verb[-1].get_bottom()[1] - mark.get_bottom()[1]))
        assert value.get_right()[0] <= 6.4 and mark.get_left()[0] >= -6.4, (value.get_right()[0], mark.get_left()[0])
        return VGroup(mark, verb), value

    def land(self, key, value, run_time: float = 0.5):
        self.play(FadeIn(key, shift=RIGHT * 0.1, run_time=run_time))
        self.play(FadeIn(value, shift=RIGHT * 0.1, run_time=run_time))

    def construct(self):
        n = numbers()
        bl19, bl127 = n["labels"]["bl19"], n["labels"]["bl127"]

        # 0 · the step line alone, then its kicker above the title
        self.section(0)
        self.step(STEP)

        # 1 · proven
        self.section(1)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.wait(1.5)
        proven = words(
            f"{bl127} {n['proven_count']['BL127']} of {n['ops']['BL127']} · {bl19} {n['proven_count']['BL19']} of {n['ops']['BL19']}",
            SIZE_ROW,
            Palette.TEXT,
        )
        self.land(*self.row(0, KEYS[0], proven, check_mark(HUES["proven"], size=0.4)))

        # 1 · fuzzed
        self.section(2, hold=1.2)
        fuzzed = words(f"{thousands(n['runs'])} runs a test", SIZE_ROW, Palette.TEXT)
        self.land(*self.row(1, KEYS[1], fuzzed, check_mark(HUES["fuzzed"], size=0.4)))

        # 2 · swept: the hero, 0 misrounded, on a halo
        self.section(3, hold=1.2)
        zero = words(f"{n['misrounded']} {MISROUNDED}", SIZE_ZERO, Palette.CORRECT)
        key, zero = self.row(2, KEYS[2], zero, check_mark(HUES["tested"], size=0.4), gap=0.75)
        glow = halo(zero[0].get_center(), Palette.EMERALD, radius=0.32, layers=5, spread=1.2, opacity=0.26)
        self.play(FadeIn(key, shift=RIGHT * 0.1, run_time=0.5))
        self.add(glow)
        self.bring_to_back(glow)
        self.play(FadeIn(glow, run_time=0.6), FadeIn(zero, shift=UP * 0.12, scale=0.9, run_time=0.6))

        # 3 · the one known limit: a hollow marker, one line, never red
        self.section(4, hold=1.6)
        ring = Circle(radius=0.14, color=HUES["limits"], stroke_width=3, fill_opacity=0)
        limit = words(LIMIT, SIZE_BODY, HUES["limits"])
        line = VGroup(ring, limit).arrange(RIGHT, buff=0.25).move_to([0, Y_LIMIT, 0])
        assert line.width <= 12.8, line.width
        self.play(FadeIn(line, shift=RIGHT * 0.1, run_time=0.7))
        self.close()
