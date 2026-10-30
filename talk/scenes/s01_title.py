"""Slide 1, "How to Audit Everybody's Math": the title, and one value that
rounds once while the room settles.

The only looping scene (slides.yaml: loop: true), so its last frame is
its first: the title at HERO, blockulator.com and the speaker line under
it, a faint GridLine across the lower third with one white dot between
two ticks are all on the first frame (the title is static chrome, as
every title is; a typed title would have to be typed again at every
loop). The one ambient beat: the dot drifts toward the gap's far tick,
snaps to it in EMERALD under a halo, settles, then returns to white at
its start, and the clip holds there, so the loop has no seam.

One section, title (the one single-section scene check.py allows); the
same scene's snapshot() before and after the beat must agree.

No numbers: numbers() is empty, every string is a LITERAL. The speaker
line is the speaker line (the user supplied it 2026-10-29); no
name is invented).
"""

from __future__ import annotations

from manim import FadeIn, FadeOut, Transform
from manim.utils.rate_functions import ease_in_out_sine

from vocab import (
    SIZE_BODY,
    SIZE_HERO,
    GridLine,
    Palette,
    TextScene,
    halo,
    snap,
    words,
)

TITLE = "How to Audit Everybody's Math"
SITE = "blockulator.com"
SPEAKER_NAME = "Sam Reeves"  # the user's line (2026-10-29): "The speaker is Sam Reeves founder of secure data research, dev of blockulator"
SPEAKER_ROLE = "founder, Secure Data Research · developer of Blockulator"

LITERALS = {
    TITLE: "V-none",  # the user's own title
    SITE: "K12",
    SPEAKER_NAME: "user 2026-10-29",
    SPEAKER_ROLE: "user 2026-10-29",
}

Y_TITLE = 1.1
Y_SITE = -0.1
Y_NAME = -0.8  # the name, then the role on its own line (one line ran past the safe area); both centred
Y_ROLE = -1.35
Y_GRID = -2.4
GRID_LENGTH = 12.0
GRID_RANGE = (0, 12, 1)
X_START = 5.3  # the dot's resting place, in grid units: between ticks 5 and 6, nearer 5
X_DRIFT = 5.62  # where it drifts to before it snaps: past the gap's middle
TICK = 6  # the tick it snaps to
LOOP = True


def numbers() -> dict:
    return {}


class Title(TextScene):
    SECTIONS = ("title",)
    LOOP = LOOP

    def construct(self):
        self.section(0)
        # everything on the first frame: the title, the two lines, the grid and the dot
        title = words(TITLE, SIZE_HERO, Palette.TEXT).move_to([0, Y_TITLE, 0])
        site = words(SITE, SIZE_BODY, Palette.MUTED).move_to([0, Y_SITE, 0])
        name = words(SPEAKER_NAME, SIZE_BODY, Palette.MUTED).move_to([0, Y_NAME, 0])
        role = words(SPEAKER_ROLE, SIZE_BODY, Palette.MUTED).move_to([0, Y_ROLE, 0])
        self.fix(title, site, name, role)
        grid = GridLine(GRID_RANGE, length=GRID_LENGTH, colour=Palette.RULE).move_to([0, Y_GRID, 0])
        grid.set_stroke(opacity=0.6)
        self.fix(grid)
        dot = grid.dot_at(X_START, Palette.EXACT)
        self.add(dot)
        home = dot.copy()
        self.start_state = self.snapshot()
        self.wait(1.5)
        # the ambient beat: drift, snap under a halo, settle, return
        self.play(dot.animate.move_to(grid.n2p(X_DRIFT)), run_time=4.0, rate_func=ease_in_out_sine)
        self.wait(0.4)
        glow = halo(grid.n2p(TICK), Palette.EMERALD, radius=0.11, spread=2.6, opacity=0.22)
        self.add(glow)
        self.bring_to_front(dot)
        self.play(FadeIn(glow, run_time=0.5), snap(dot, grid, TICK, Palette.CORRECT, run_time=1.0))
        self.wait(1.6)
        self.play(FadeOut(glow, run_time=1.2), Transform(dot, home, run_time=1.8, rate_func=ease_in_out_sine))
        self.remove(glow)
        self.end_state = self.snapshot()
        assert self.start_state == self.end_state, "the loop must end where it starts"
        self.close(hold=2.5)
