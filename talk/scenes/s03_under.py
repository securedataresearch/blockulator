"""Slide 3, "exp is under everything": four things a protocol charges for,
and the one function under all of them.

Four names, each in its own hue (GOLD, SAPPHIRE, VIOLET, SLATE), write in
down the left: a compounding rate, a discount factor, an option price, a
growth curve. Then, name by name, a line draws from it into a central e^x
(the line runs from the name's hue into EMERALD) that grows in under a
halo on the first line and pulses on each later one: the hero, the one
function the four resolve to. The lines say what the formulas said; the
sentence "if exp has no canonical value on chain, nothing built on it has
one" is the speaker's, not the slide's.

Two sections, one per click: four; resolve. The last frame holds as the
slide.

No JSON: numbers() is empty and every string is a LITERAL (claim V11,
the four examples and their root). The word "every" is in the title only:
the names are four examples, not a claim of completeness, and nothing here
says a protocol is wrong.

Pango's own <sup> scale is ~0.58 of the body; the superscript of e^x
carries a span that brings it back to ~0.72 of the hero.
"""

from __future__ import annotations

from manim import (
    LEFT,
    RIGHT,
    Create,
    GrowFromCenter,
    Indicate,
    LaggedStart,
    Line,
    VGroup,
    Write,
)

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    DeckScene,
    Palette,
    halo,
    markup,
    words,
)

HUES = ROW_COLOUR["s03"]  # one hue per name; the hero e^x EMERALD

SUP_SIZE = "125%"  # Pango's <sup> scale is ~0.58 of the body; this brings a superscript to ~0.72 of it


def sup(s: str) -> str:
    """A superscript at a legible size (see the module docstring)."""
    return f'<sup><span size="{SUP_SIZE}">{s}</span></sup>'


TITLE = "exp is under everything"
HERO = f"e{sup('x')}"
NAMES = ("compounding rate", "discount factor", "option price", "growth curve")

NAME_SIZE = 40  # four names alone on the left: larger than BODY
HERO_SIZE = 72  # the lone hero
X_LEFT = -6.3  # the names start here (5% safe area: ±6.4)
Y_NAMES = (1.5, 0.3, -0.9, -2.1)
X_HERO, Y_HERO = 3.9, -0.3  # level with the names' centre
LINE_GAP = 0.3  # a name's right end to its line
LINE_END = 0.45  # the line ends this far left of the hero's glyphs, inside the halo
STAGGER = 0.35  # name to name, section 0
PER_ROW = 0.8  # line to line, section 1

# every string on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    TITLE: "V11",
    **{name: "V11" for name in NAMES},
    HERO: "V11",
}


def numbers() -> dict:
    return {}


class Under(DeckScene):
    SECTIONS = ("four", "resolve")

    def construct(self):
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        names = []
        for name, y in zip(NAMES, Y_NAMES):
            t = words(name, NAME_SIZE, HUES[name])
            names.append(t.move_to([X_LEFT + t.width / 2, y, 0]))
        self.wait(0.3)

        # the four names write in, staggered, each in its hue
        self.play(LaggedStart(*[Write(t, run_time=0.9) for t in names], lag_ratio=STAGGER))

        # each name draws a line into e^x, which grows in under a halo
        self.section(1, hold=1.2)
        hero = markup(HERO, HERO_SIZE, Palette.EMERALD).move_to([X_HERO, Y_HERO, 0])
        glow = halo(hero.get_center(), Palette.EMERALD, radius=0.8, layers=12, spread=2.2, opacity=0.13)
        hub = VGroup(glow, hero)
        end = hero.get_left() + LEFT * LINE_END
        for i, (name, t) in enumerate(zip(NAMES, names)):
            line = Line(t.get_right() + RIGHT * LINE_GAP, end, stroke_width=3)
            line.set_color([Palette.EMERALD, HUES[name]])  # manim lays a gradient end to start: the name's hue at the name, EMERALD at the hub
            if i == 0:
                self.add(hub)
                self.play(Create(line, run_time=PER_ROW), GrowFromCenter(hub, run_time=PER_ROW))
            else:
                self.play(Create(line, run_time=PER_ROW * 0.7), Indicate(hub, color=Palette.EMERALD, scale_factor=1.06, run_time=PER_ROW * 0.7))
            self.bring_to_front(hub)
        self.close()
