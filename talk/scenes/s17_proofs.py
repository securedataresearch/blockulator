"""Slide 17, "Knowing it's right": the honest table.

Two lines first: "A test checks the inputs it was given." beside a plane
of inputs on which tests land as a scatter of dots; "A proof covers every
input." and the plane fills. Then four rows land one by one, each a label
at the left of its first line (MUTED) and its string in white (EXACT, the
table's text): what is proven (an EMERALD tick), what is fuzzed (a MUTED
tick), what is tested against an oracle (the two counts ticking up from
0, then the hero "0 misrounded" at HERO size under a halo, then the
totals over every operation), and what no check covers (a hollow marker,
never red: these are limits, not bugs; its two strings in two held
sub-beats, "none is known" last). The footnote and the closing line close
the slide.

Numbers from docs/benchmarks/proofs.json (.ops[] per lib with status and
tool: the proven and fuzzed ops per library, the Halmos count, sqrt by
exact integers; .fuzz[] runs) and docs/benchmarks/sweep.json (.rows[] for
fp19 and fp127: n and misrounded summed per library, over every row and
over the rows whose op is one of the 21 transcendentals; ._doc for the
oracles' digit counts). The transcendental list is the FP127 README's
"The transcendentals round to nearest" sentence (claim V34). Six sections.
"""

from __future__ import annotations

import random
import re

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    FadeIn,
    FadeOut,
    GrowFromEdge,
    LaggedStart,
    Rectangle,
    Text,
    ValueTracker,
    VGroup,
    always_redraw,
)
from manim.utils.rate_functions import ease_out_cubic, linear

from vocab import (
    MONO,
    SIZE_BODY,
    SIZE_CAPTION,
    SIZE_HERO,
    Chart,
    DeckScene,
    Palette,
    _load,
    check_mark,
    digits,
    glow_bar,
    halo,
    libs,
    proofs,
    setup_fonts,
    thousands,
    words,
)

TITLE = "Knowing it's right"
TEST_LINE = "A test checks the inputs it was given."
PROOF_LINE = "A proof covers every input."
CLOSING = "State your own guarantees this specifically."
FOOTNOTE = "the proofs found two bugs on the way: fixed, now proven"
CAPTION = "docs/benchmarks/proofs.json · sweep.json"  # the transcendental list: contracts/src/fp127/README.md (V34)
LABELS = ("proven for every input", "fuzzed against the spec", "tested against an oracle", "known limits")
NONE_KNOWN = "none is known"
# the two limits, wrapped by hand so each digit-bearing line is a LITERAL (V38); the first
# line of each sits beside the row's label, the rest below it at the margin
LIMIT_BOUND = ("a derived bound could be wrong beyond its", "sampled margin: the measured error reaches 0.92 of FP127's\nbound and 0.79 of FP19's")
LIMIT_STAGE = ("the last stage has no test of its own: a true", "value within its error of a midpoint would misround")
NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
# the 21 transcendentals, contracts/src/fp127/README.md "Rounding (3.0)": "The transcendentals
# round to nearest under the tie rule above: …" (claim V34; the same list for FP19)
TRANSCENDENTAL = (
    "exp", "exp2", "exp10", "expm1", "sinh", "cosh", "tanh", "atanh", "pow", "cbrt", "ln",
    "log2", "log10", "log1p", "powu", "compound", "lambertW0", "lambertWm1", "erf", "erfc", "normCdf",
)
LIBS = ("fp19", "fp127")

X_LEFT = -6.4
X_RIGHT = 6.4
Y_ROWS = 2.78  # the first row's first line
PITCH = 0.46  # line to line at BODY
ROW_GAP = 0.1  # extra between rows
HERO_PITCH = 0.6  # the hero line is taller
MARK_BUFF = 0.22  # mark to label
LABEL_BUFF = 0.38  # label to the first line's text
PIECE_BUFF = 0.16  # between the pieces of a line (words · digits · words)
PLANE_SEED = 17
PLANE_DOTS = 48
PLANE_SMALL = 0.25  # the plane's scale once the table begins
PLANE_CORNER = (5.6, 2.45, 0)  # under the right mark (was 5.75, 3.12)

# the digit-bearing fixed strings, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    LIMIT_BOUND[1]: "V38",
    FOOTNOTE: "V52",
}


def numbers() -> dict:
    lib = libs()
    p = proofs()
    full = _load("docs/benchmarks/proofs.json")
    by = {name: [o for o in p["ops"] if o["lib"] == name] for name in ("FP127", "FP19")}
    proven = {name: [o["op"] for o in ops if o["status"] == "proven"] for name, ops in by.items()}
    fuzzed = {name: [o["op"] for o in ops if o["status"] == "fuzzed"] for name, ops in by.items()}
    for name, ops in by.items():
        assert len(proven[name]) + len(fuzzed[name]) == len(ops), (name, [o["status"] for o in ops])
    halmos = [o["op"] for o in by["FP127"] if o["status"] == "proven" and o["tool"].startswith("Halmos")]
    exact = [o["op"] for o in by["FP127"] if o["status"] == "proven" and not o["tool"].startswith("Halmos")]
    assert exact == ["sqrt"] and "exact integer" in next(o["tool"] for o in by["FP127"] if o["op"] == "sqrt"), exact
    # every fuzz test's runs (the regression pins run once; they are not fuzz runs)
    runs = {f["runs"] for f in full["fuzz"] if f["test"].startswith("testFuzz_")}
    assert len(runs) == 1 and all(f["result"] == "pass" for f in full["fuzz"]), runs
    runs = runs.pop()
    # the sweep: every fp19 and fp127 row, plain and forced passes alike
    sw = _load("docs/benchmarks/sweep.json")
    rows = {lid: [r for r in sw["rows"] if r["lib"] == lid] for lid in LIBS}
    total = {lid: sum(r["n"] for r in rows[lid]) for lid in LIBS}
    misrounded = {lid: sum(r["misrounded"] for r in rows[lid]) for lid in LIBS}
    transcendental = {lid: sum(r["n"] for r in rows[lid] if r["op"] in TRANSCENDENTAL) for lid in LIBS}
    assert all(set(TRANSCENDENTAL) <= {r["op"] for r in rows[lid]} for lid in LIBS)
    doc = sw["_doc"]
    ref = {"fp19": int(re.search(r"mpmath at (\d+) digits", doc).group(1)), "fp127": int(re.search(r"truth at (\d+) digits", doc).group(1))}
    assert misrounded == {"fp19": 0, "fp127": 0}, misrounded
    return {
        "labels": {"fp19": lib["fp19"]["label"], "fp127": lib["fp127"]["label"]},
        "proven": proven,
        "fuzzed": fuzzed,
        "ops": {name: len(ops) for name, ops in by.items()},
        "proven_count": {name: len(v) for name, v in proven.items()},
        "halmos_count": len(halmos),
        "exact_integer": exact,
        "fp19_fuzzed_word": NUMBER_WORDS[len(fuzzed["FP19"])],
        "runs": runs,
        "rows": {lid: len(rows[lid]) for lid in LIBS},
        "total": total,
        "misrounded": misrounded,
        "transcendental": transcendental,
        "reference_digits": ref,
    }


class Proofs(DeckScene):
    SECTIONS = ("test-proof", "proven", "fuzzed", "tested", "limits", "closing")

    # ---------------------------------------------------------------- rows --
    def label(self, text: str, mark, y: float) -> VGroup:
        """A row's left cell: its mark, then the label in MUTED, at the margin."""
        lbl = words(text, SIZE_BODY, Palette.MUTED)
        mark.move_to([X_LEFT + mark.width / 2 + 0.02, y, 0])
        lbl.next_to(mark, RIGHT, buff=MARK_BUFF).set_y(y)
        return VGroup(mark, lbl)

    @staticmethod
    def line(pieces, y: float, x: float = X_LEFT) -> VGroup:
        """A line of the right cell: its pieces side by side from x, baselines level."""
        g = VGroup(*pieces).arrange(RIGHT, buff=PIECE_BUFF, aligned_edge=DOWN)
        for piece in pieces:
            piece.set_y(y)
        g.align_to([x, 0, 0], LEFT)
        return g

    @staticmethod
    def block(text: str, y_top: float) -> Text:
        """The rest of a right cell, wrapped at the margin, its first line at y_top."""
        t = words(text, SIZE_BODY, Palette.TEXT, line_spacing=0.6)
        return t.move_to([X_LEFT + t.width / 2, y_top - (t.height - 0.42) / 2, 0])

    def ticking(self, tracker: ValueTracker, size: float, colour: str):
        """A thousands-separated count following the tracker; the frames on the
        way are plain Text (not a claim), the final string is drawn by digits()."""
        setup_fonts()
        return always_redraw(lambda: Text(thousands(int(round(tracker.get_value()))), font=MONO, font_size=size, color=colour, disable_ligatures=True))

    def land(self, *mobjs, run_time: float = 0.45):
        self.play(*[FadeIn(m, shift=RIGHT * 0.1, run_time=run_time) for m in mobjs])

    # ------------------------------------------------------------- the slide --
    def construct(self):
        n = numbers()
        fp19, fp127 = n["labels"]["fp19"], n["labels"]["fp127"]

        # 0 · a test, a proof: the two lines and the plane of inputs
        self.section(0)
        self.wait(0.3)
        title = self.title(TITLE, SIZE_BODY, Palette.TEXT)
        self.play(FadeIn(title, shift=RIGHT * 0.1, run_time=0.5), self.caption(CAPTION))
        plane = Chart((0, 8, 1), (0, 6, 1), width=4.6, height=3.5, origin=(1.3, -1.5, 0))
        grid = plane.grid()
        self.play(Create(plane.x_axis, run_time=0.6), Create(plane.y_axis, run_time=0.6), FadeIn(grid, run_time=0.6))
        test_line = words(TEST_LINE, SIZE_BODY, Palette.TEXT).move_to([0, 0.9, 0]).align_to([X_LEFT, 0, 0], LEFT)
        self.play(FadeIn(test_line, shift=RIGHT * 0.1, run_time=0.5))
        rng = random.Random(PLANE_SEED)
        dots = VGroup(*[plane.dot(rng.uniform(0.3, 7.7), rng.uniform(0.3, 5.7), Palette.BODY, radius=0.055) for _ in range(PLANE_DOTS)])
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.04, run_time=1.6))
        self.wait(0.6)
        proof_line = words(PROOF_LINE, SIZE_BODY, Palette.TEXT).move_to([0, 0.1, 0]).align_to([X_LEFT, 0, 0], LEFT)
        self.play(FadeIn(proof_line, shift=RIGHT * 0.1, run_time=0.5))
        fill = Rectangle(width=plane.width, height=plane.height, color=Palette.EMERALD, fill_color=Palette.EMERALD, fill_opacity=0.22, stroke_width=0)
        fill.move_to(plane.c2p(4, 3))
        self.add(fill)
        self.bring_to_back(fill)
        self.play(GrowFromEdge(fill, DOWN, rate_func=ease_out_cubic, run_time=1.2), dots.animate.set_color(Palette.EMERALD), run_time=1.2)
        proof_mark = check_mark(Palette.CORRECT, size=0.5, stroke_width=5).move_to(plane.c2p(4, 3))
        self.play(Create(proof_mark, run_time=0.4))
        whole_plane = VGroup(fill, grid, plane, dots, proof_mark)

        # 1 · proven: the plane to the corner, the first row lands
        self.section(1, hold=1.2)
        self.play(
            FadeOut(test_line, run_time=0.5),
            FadeOut(proof_line, run_time=0.5),
            whole_plane.animate.scale(PLANE_SMALL).move_to(PLANE_CORNER),
            run_time=0.9,
        )
        y = Y_ROWS
        lab1 = self.label(LABELS[0], check_mark(Palette.CORRECT), y)
        r1a = self.line([words(f"{fp127}: {n['proven_count']['FP127']} core operations", SIZE_BODY, Palette.TEXT)], y, x=lab1.get_right()[0] + LABEL_BUFF)
        y -= PITCH
        r1b = self.block(f"({n['halmos_count']} by Halmos, {n['exact_integer'][0]} in exact integers) · {fp19}: {n['proven_count']['FP19']} of {n['ops']['FP19']}", y)
        self.land(lab1)
        self.land(r1a)
        self.land(r1b)
        self.wait(0.5)

        # 2 · fuzzed
        self.section(2, hold=2.0)
        y -= PITCH + ROW_GAP
        lab2 = self.label(LABELS[1], check_mark(Palette.MUTED), y)
        r2a = self.line([words(f"{fp127}: {', '.join(n['fuzzed']['FP127'])} · {fp19}: {n['fp19_fuzzed_word']} ·", SIZE_BODY, Palette.TEXT)], y, x=lab2.get_right()[0] + LABEL_BUFF)
        y -= PITCH
        r2b = self.line([digits(thousands(n["runs"]), SIZE_BODY, Palette.TEXT), words("runs a test", SIZE_BODY, Palette.TEXT)], y)
        self.land(lab2)
        self.land(r2a)
        self.land(r2b)
        self.wait(0.4)

        # 3 · tested: the counts tick up, the hero lands last
        self.section(3, hold=1.8)
        y -= PITCH + ROW_GAP
        lab3 = self.label(LABELS[2], check_mark(Palette.MUTED), y)
        self.land(lab3)
        trackers = {lid: ValueTracker(0) for lid in LIBS}
        tick19 = self.ticking(trackers["fp19"], SIZE_BODY, Palette.TEXT)
        r3a_words = [words(f"{fp19}:", SIZE_BODY, Palette.TEXT), words("transcendental", SIZE_BODY, Palette.TEXT)]
        y3a = y
        y -= PITCH
        y3b = y
        tick127 = self.ticking(trackers["fp127"], SIZE_BODY, Palette.TEXT)
        r3b_words = [words(f"results at {n['reference_digits']['fp19']} digits · {fp127}:", SIZE_BODY, Palette.TEXT), words(f"at {n['reference_digits']['fp127']} ·", SIZE_BODY, Palette.TEXT)]
        x3a = lab3.get_right()[0] + LABEL_BUFF

        def place(y_line, x_line, count_text, pieces):
            return self.line([pieces[0], count_text, pieces[1]], y_line, x=x_line)

        final19 = digits(thousands(n["transcendental"]["fp19"]), SIZE_BODY, Palette.TEXT)
        final127 = digits(thousands(n["transcendental"]["fp127"]), SIZE_BODY, Palette.TEXT)
        # lay the lines out with the final digits (the widest), then let the tickers take their place
        r3a = place(y3a, x3a, final19, r3a_words)
        r3b = place(y3b, X_LEFT, final127, r3b_words)
        tick19.add_updater(lambda m: m.move_to(final19, aligned_edge=LEFT))
        tick127.add_updater(lambda m: m.move_to(final127, aligned_edge=LEFT))
        self.land(r3a_words[0], r3a_words[1])
        self.add(tick19)
        self.play(trackers["fp19"].animate(rate_func=linear).set_value(n["transcendental"]["fp19"]), run_time=1.4)
        self.remove(tick19)
        self.add(final19)
        self.land(r3b_words[0], r3b_words[1])
        self.add(tick127)
        self.play(trackers["fp127"].animate(rate_func=linear).set_value(n["transcendental"]["fp127"]), run_time=1.2)
        self.remove(tick127)
        self.add(final127)
        self.wait(0.3)
        y -= HERO_PITCH
        hero = digits(f"{n['misrounded']['fp19']} misrounded", SIZE_HERO, Palette.CORRECT).move_to([0, y, 0]).align_to([X_LEFT + 0.1, 0, 0], LEFT)
        glow = halo(hero.get_center(), Palette.EMERALD, radius=0.3, layers=5, spread=1.5, opacity=0.22)
        glow.stretch_to_fit_width(hero.width + 1.4)
        self.add(glow)
        self.bring_to_back(glow)
        self.play(FadeIn(glow, run_time=0.6), FadeIn(hero, shift=UP * 0.12, scale=0.9, run_time=0.6))
        self.wait(0.5)
        y -= HERO_PITCH - 0.06
        totals = words(f"({thousands(n['total']['fp19'])} and {thousands(n['total']['fp127'])} over every operation)", SIZE_BODY, Palette.MUTED).move_to([0, y, 0]).align_to([X_LEFT, 0, 0], LEFT)
        self.land(totals)

        # 4 · known limits: a hollow marker, two sub-beats, "none is known" last
        self.section(4, hold=1.6)
        y -= PITCH + ROW_GAP
        hollow = Circle(radius=0.13, color=Palette.MUTED, stroke_width=3, fill_opacity=0)
        lab4 = self.label(LABELS[3], hollow, y)
        x4 = lab4.get_right()[0] + LABEL_BUFF
        y4a = y
        bound_a = self.line([words(LIMIT_BOUND[0], SIZE_BODY, Palette.TEXT)], y4a, x=x4)
        bound_b = self.block(LIMIT_BOUND[1], y4a - PITCH)
        self.land(lab4)
        self.land(bound_a)
        self.land(bound_b, run_time=0.6)
        self.wait(1.8)
        stage_a = self.line([words(LIMIT_STAGE[0], SIZE_BODY, Palette.TEXT)], y4a, x=x4)
        stage_b = self.block(LIMIT_STAGE[1], y4a - PITCH)
        self.play(FadeOut(bound_a, run_time=0.4), FadeOut(bound_b, run_time=0.4))
        self.land(stage_a)
        self.land(stage_b, run_time=0.6)
        self.wait(0.8)
        y = y4a - 2 * PITCH
        none_known = words(NONE_KNOWN, SIZE_BODY, Palette.TEXT).move_to([0, y, 0]).align_to([X_LEFT, 0, 0], LEFT)
        self.land(none_known)

        # 5 · the footnote and the closing line
        self.section(5, hold=1.0)
        foot = words(FOOTNOTE, SIZE_CAPTION, Palette.FAINT).to_corner(DOWN + RIGHT, buff=0.45)
        self.play(FadeIn(foot, run_time=0.5))
        close = words(CLOSING, SIZE_BODY, Palette.TEXT).move_to([0, y, 0]).align_to([X_RIGHT, 0, 0], RIGHT)
        bar = glow_bar(close, Palette.EMERALD, pad=0.2, opacity=0.14)
        self.add(bar)
        self.bring_to_back(bar)
        self.play(FadeIn(bar, run_time=0.6), FadeIn(close, shift=UP * 0.08, run_time=0.6))
        self.wait(0.6)
        self.close()
