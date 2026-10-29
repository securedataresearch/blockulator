"""Slide 3, "exp is under everything": four things a protocol charges for,
and the one function under all of them.

Four rows draw in, staggered: a compounding rate, a discount factor, an
option price, a growth curve, each with its formula, each formula ending
in a power of e. Then, row by row, the exp term lights (EMERALD, a brief
Indicate) and a thin EMERALD wire draws from it to a central e^x that
grows in under a halo: the hero, the one function the four resolve to.
Last, the rows dim and the closing line types under the hero: if exp has
no canonical value on chain, nothing built on it has one.

Three sections, one per click: four; resolve; alone. The last frame
holds as the slide.

No JSON: numbers() is empty and every string is a LITERAL (claims V11,
the four examples and their root; V10, no canonical exp on chain). The
word "every" is in the title only: the rows are four examples, not a
claim of completeness, and nothing here says a protocol is wrong.

Instrument Sans has no "²" (U+00B2) and no "→" (U+2192): the square is
written <sup>2</sup> as the brief allows, and the "→" between a
formula's stages is drawn as a thin arrow, not set as a glyph that would
fall back to another font. Pango's own <sup> scale puts a superscript at
BODY size under SIZE_CAPTION, so every superscript carries a span that
brings it back to about 23 (the inner "2" of x² a second span, so it
matches the exponent around it).
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    AnimationGroup,
    Arrow,
    Create,
    FadeIn,
    GrowFromCenter,
    Indicate,
    LaggedStart,
    Line,
    VGroup,
    Write,
)

from vocab import (
    SIZE_BODY,
    SIZE_HERO,
    DeckScene,
    Palette,
    halo,
    markup,
    words,
)

SUP_SIZE = "125%"  # Pango's <sup> scale is ~0.58 of the body; this brings a superscript to ~23 of 32
SUP2_SIZE = "172%"  # the "2" of x², a superscript of a superscript, back up to the exponent's size


def sup(s: str) -> str:
    """A superscript at a legible size (see the module docstring)."""
    return f'<sup><span size="{SUP_SIZE}">{s}</span></sup>'


def sup2(s: str) -> str:
    """A superscript inside a superscript: the 2 of x²."""
    return f'<sup><span size="{SUP2_SIZE}">{s}</span></sup>'


TITLE = "exp is under everything"
CLOSE = "if exp has no canonical value on chain,\nnothing built on it has one"  # one line in the script, two on the slide

# the four rows: a label, then the formula's stages left to right (an arrow is drawn between stages);
# the last stage of each is its exp term, the one that lights and wires into e^x
HERO = f"e{sup('x')}"
ROWS = (
    ("compounding rate", (f"(1 + r/n){sup('nt')}", f"e{sup('nt · ln(1 + r/n)')}")),
    ("discount factor", (f"e{sup('−rt')}",)),
    ("option price", ("N(d)", "erfc", f"e{sup('−x' + sup2('2'))}")),
    ("growth curve", (f"e{sup('kt')}",)),
)

X_LEFT = -6.3  # the labels start here (5% safe area: ±6.4)
X_FORMULA = -2.1  # the formulas start here
Y_ROWS = (1.75, 0.55, -0.65, -1.85)
X_HERO, Y_HERO = 4.75, -0.05  # between the second and third rows
Y_CLOSE = -2.9
STAGE_GAP = 0.22  # a stage to its arrow
WIRE_GAP = 0.18  # an exp term to its wire
WIRE_END = 0.32  # the wire ends this far left of the hero's glyphs, inside the halo
STAGGER = 0.4  # row to row, section 0
PER_ROW = 0.8  # row to row, section 1
DIM = 0.6  # the rows' opacity once they have resolved: FAINT alone barely recedes from MUTED

# every string on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    TITLE: "V11",
    **{label: "V11" for label, _ in ROWS},
    **{stage: "V11" for _, stages in ROWS for stage in stages},
    HERO: "V11",
    CLOSE: "V10, V11",
}


def numbers() -> dict:
    return {}


def stage_arrow(a, b) -> Arrow:
    """The "→" between a formula's stages, drawn: Instrument Sans has no
    arrow glyph. Fixed tip and stroke, as direction() draws its arrows."""
    return Arrow(
        a.get_right() + RIGHT * STAGE_GAP,
        b.get_left() + LEFT * STAGE_GAP,
        buff=0,
        color=Palette.MUTED,
        stroke_width=2,
        tip_length=0.11,
        max_tip_length_to_length_ratio=1.0,
        max_stroke_width_to_length_ratio=100.0,
    )


class Under(DeckScene):
    SECTIONS = ("four", "resolve", "alone")

    def row(self, i: int):
        """A row's label and its formula: the stages laid left to right with
        drawn arrows between them. Returns (label, formula group, exp term)."""
        label_text, stages = ROWS[i]
        y = Y_ROWS[i]
        label = words(label_text, SIZE_BODY, Palette.MUTED)
        label.move_to([X_LEFT + label.width / 2, y, 0])
        texts = [markup(s, SIZE_BODY, Palette.TEXT) for s in stages]
        parts = []
        x = X_FORMULA
        for k, t in enumerate(texts):
            if k:
                x += 2 * STAGE_GAP + 0.3
            t.move_to([x + t.width / 2, y, 0])
            if k:
                parts.append(stage_arrow(texts[k - 1], t))
            parts.append(t)
            x += t.width
        return label, VGroup(*parts), texts[-1]

    def construct(self):
        self.section(0)
        self.wait(0.3)
        title = self.title(TITLE, SIZE_BODY, Palette.TEXT)
        self.play(FadeIn(title, shift=RIGHT * 0.1, run_time=0.5))

        # the four rows draw in, staggered
        labels, formulas, terms = [], [], []
        for i in range(len(ROWS)):
            label, formula, term = self.row(i)
            labels.append(label)
            formulas.append(formula)
            terms.append(term)
        self.play(
            LaggedStart(
                *[AnimationGroup(FadeIn(labels[i], shift=RIGHT * 0.1, run_time=0.5), Write(formulas[i], run_time=1.0)) for i in range(len(ROWS))],
                lag_ratio=STAGGER,
            )
        )

        # each exp term lights and wires into e^x, which grows in under a halo
        self.section(1, hold=1.2)
        hero = markup(HERO, SIZE_HERO, Palette.EMERALD).move_to([X_HERO, Y_HERO, 0])
        glow = halo(hero.get_center(), Palette.EMERALD, radius=0.55, layers=12, spread=2.4, opacity=0.13)
        hero_group = VGroup(glow, hero)
        end = hero.get_left() + LEFT * WIRE_END
        wires = []
        for i, term in enumerate(terms):
            self.play(Indicate(term, color=Palette.EMERALD, scale_factor=1.12, run_time=PER_ROW * 0.45))
            term.set_color(Palette.EMERALD)
            wire = Line(term.get_right() + RIGHT * WIRE_GAP, end, color=Palette.EMERALD, stroke_width=2)
            wires.append(wire)
            if i == 0:
                self.add(hero_group)
                self.play(Create(wire, run_time=PER_ROW * 0.55), GrowFromCenter(hero_group, run_time=PER_ROW * 0.55))
            else:
                self.play(Create(wire, run_time=PER_ROW * 0.55), Indicate(hero_group, color=Palette.EMERALD, scale_factor=1.08, run_time=PER_ROW * 0.55))
            self.bring_to_front(hero_group)

        # the rows dim; e^x stays; the closing line types under it
        self.section(2, hold=1.2)
        rows = VGroup(*labels, *formulas)
        self.play(rows.animate.set_color(Palette.FAINT).set_opacity(DIM), VGroup(*wires).animate.set_color(Palette.FAINT).set_stroke(opacity=DIM), run_time=0.6)
        close = words(CLOSE, SIZE_BODY, Palette.TEXT, line_spacing=0.9).move_to([0, Y_CLOSE, 0])
        # Text sets its lines flush left; centre the second (spaces are not glyphs, so count the rest)
        k = len(CLOSE.split("\n")[0].replace(" ", ""))
        close[k:].shift(RIGHT * (close.get_center()[0] - close[k:].get_center()[0]))
        self.play(AddTextLetterByLetter(close, time_per_char=0.03))
        self.close()
