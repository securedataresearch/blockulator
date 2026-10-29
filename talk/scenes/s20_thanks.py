"""Slide 20, "Thank you": the final poster, up through the questions.

"Thank you" at HERO types in, then the thank-you line (the user's words,
2026-10-29; "Eth Foundation" written out as Ethereum Foundation) at
BODY, on three centred lines (its 123 characters are 25.4 units at BODY;
the brief's two lines would be 12.1 and 13.2, the second wider than the
safe area). Then the two QR tiles again, smaller (1.8 units), with
blockulator.com and the repository's URL under them, and the agents'
line, blockulator.com/llms.txt, at BODY under the tiles: everything a
person or an agent needs to start is on the held frame.

Two sections: thanks, links. No numbers: numbers() carries the two URLs
(for check.py to regenerate the matrices); the names and affiliations
are exactly the user's, no other credit is invented.
"""

from __future__ import annotations

from manim import UP, FadeIn, VGroup

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    Palette,
    TextScene,
    digits,
    qr,
    words,
)

from s19_address import AGENTS, LLMS, SITE, SITE_URL, repo_url

HUES = ROW_COLOUR["s19"]  # the audiences' hues, shared with slide 19

THANK_YOU = "Thank you"
THANKS = "Special thanks to Austin Griffith (Ethereum Foundation) and Hadrien Croubois (OpenZeppelin) for extremely helpful feedback."
THANKS_LINES = ("Special thanks to Austin Griffith (Ethereum Foundation)", "and Hadrien Croubois (OpenZeppelin)", "for extremely helpful feedback.")

LITERALS = {
    THANK_YOU: "user 2026-10-29",
    **{line: "user 2026-10-29" for line in THANKS_LINES},
    SITE: "K12",
    AGENTS: "brief",
    LLMS: "K12",
}

Y_THANK_YOU = 2.5
Y_LINES = (1.55, 1.08, 0.61)
QR_SIZE = 1.8
QR_X = (-2.6, 2.6)
QR_Y = -1.15
Y_AGENTS = -3.0


def repo_label(url: str) -> str:
    return url.split("://", 1)[1]


def numbers() -> dict:
    url = repo_url()
    return {"site_url": SITE_URL, "repo_url": url, "repo_label": repo_label(url)}


class Thanks(TextScene):
    SECTIONS = ("thanks", "links")

    def construct(self):
        n = numbers()
        assert " ".join(THANKS_LINES) == THANKS
        self.section(0)
        self.wait(0.3)
        self.typed(THANK_YOU, SIZE_HERO, Palette.TEXT, place=lambda t: t.move_to([0, Y_THANK_YOU, 0]))
        for line, y in zip(THANKS_LINES, Y_LINES):
            t = self.typed(line, SIZE_BODY, Palette.TEXT, run_time=1.1, place=lambda t, y=y: t.move_to([0, y, 0]))
            assert t.width <= 12.8, (line, t.width)

        # 1 · the two tiles and the agents' line
        self.section(1, hold=1.0)
        site_tile = qr(n["site_url"], QR_SIZE, label=SITE)
        site_tile.shift([QR_X[0], QR_Y, 0] - site_tile.panel.get_center())
        repo_tile = qr(n["repo_url"], QR_SIZE, label=n["repo_label"])
        repo_tile.shift([QR_X[1], QR_Y, 0] - repo_tile.panel.get_center())
        assert site_tile.label.get_right()[0] < repo_tile.label.get_left()[0] and repo_tile.label.get_right()[0] <= 6.4, "the two labels must not touch or leave the safe area"
        self.play(FadeIn(site_tile, shift=UP * 0.1, run_time=0.6))
        self.play(FadeIn(repo_tile, shift=UP * 0.1, run_time=0.6))
        ag = words(AGENTS, SIZE_BODY, HUES["agents"])
        llms = digits(LLMS, SIZE_BODY, Palette.TEXT)
        row = VGroup(ag, llms).arrange(direction=[1, 0, 0], buff=0.3).move_to([0, Y_AGENTS, 0])
        self.play(FadeIn(row, shift=UP * 0.08, run_time=0.6))
        self.close(hold=4.0)
