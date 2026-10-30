"""Slide 19, "The reference": the two addresses, the way in for engineers
and for agents, the two links.

The adoption slide: everything a person or an agent needs to use
Blockulator in the next minute. The title line is chrome, "today: Sepolia"
beside the title from the first frame (the addresses are Sepolia's; the
honesty pin). Section 0: the two main addresses type in, BL19 v6 (TEXT,
its family colour) then BL127 v9 (EMERALD), each on a glow_bar() in its
colour, each pulsed once when it lands. Section 1: the two ways in, the
"engineers:" row (GOLD) with the two install commands from README.md and
the "agents:" row (SAPPHIRE) with blockulator.com/llms.txt, each on a
glow_bar(). Section 2: the two QR tiles (qr(): https://blockulator.com
and the repository, from `git remote`, normalised) with their URLs under
them, bottom right, and the closing line at HERO in EMERALD beside them.

Three sections: addresses, use, links. The eight sub-objects' addresses
(the QR tiles lead to them) and "every op is a free eth_call" are in the
notes. Every address and version is from release() (RELEASE.json, V15);
check.py reads the file by a second path, asserts the commands appear in
README.md verbatim and regenerates the QR matrices. The ladder objects
are not shown.

Sizes, where the frame forced them (RULES.md, legibility): the main
rows' version names are at 24 beside the 42-character addresses at BODY
(11.1 units; name and address at BODY are 13.2, wider than the safe
area); the install commands are mono at 28 beside their BODY key (at
BODY the forge line and its key are 14.1 units); the tiles' URLs are
mono CAPTION, the repository's broken at its slashes into three lines of
one string (one line is 6.8 units, the tile 1.8).
"""

from __future__ import annotations

import subprocess

from manim import DOWN, RIGHT, UP, AddTextLetterByLetter, FadeIn, Indicate, VGroup

from vocab import (
    FAMILY_COLOUR,
    ROOT,
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_CAPTION,
    SIZE_HERO,
    Palette,
    TextScene,
    digits,
    glow_bar,
    qr,
    release,
    words,
)

HUES = ROW_COLOUR["s19"]

TITLE = "The reference"
MAIN = ("BL19", "BL127")  # the two main objects, in the order they type in
ENGINEERS = "engineers:"
AGENTS = "agents:"
FORGE = "forge install securedataresearch/blockulator"
NPM = "npm install @blockulator/contracts"
LLMS = "blockulator.com/llms.txt"
TODAY = "today: Sepolia"
SITE_URL = "https://blockulator.com"
SITE = "blockulator.com"
CLOSE = "Measure yourself against it."
CLOSE_LINES = "Measure yourself\nagainst it."  # two lines at HERO, left of the tiles

TITLE_LINE = f'{TITLE}   <span foreground="{Palette.MUTED}">{TODAY}</span>'  # one line: the title, and the network beside it

LITERALS = {
    TITLE_LINE: "script §19 · V6",
    ENGINEERS: "brief",
    AGENTS: "brief",
    FORGE + "\n" + NPM: "K12",
    LLMS: "K12",
    SITE: "K12",
    CLOSE_LINES: "script §19",
}

X_LEFT = -6.2
X_RIGHT = 6.4
SIZE_VERSION = 24  # the main rows' version names (see the module docstring)
SIZE_COMMAND = 28  # the install commands
Y_MAIN = (2.45, 1.8)
X_ADDRESS = -4.75
Y_USE = (0.93, 0.35, -0.36)  # engineers (the forge line), npm, agents: the commands block centres between the first two
X_COMMAND = -3.85
QR_SIZE = 1.6
QR_X = (1.75, 5.6)  # the tiles' centres: the site's label centred under its tile clears the repository's, right-aligned under its own
QR_TOP = -0.9
LABEL_PITCH = 0.26
Y_CLOSE = -1.75  # the closing line centred on the tiles


def family(name: str) -> str:
    return FAMILY_COLOUR["bl127" if name.startswith("BL127") else "bl19"]


def repo_url() -> str:
    """The repository's URL from `git remote get-url origin`, normalised
    to https://github.com/<org>/<repo> (REPORT if the remote is not
    GitHub)."""
    raw = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True, check=True).stdout.strip()
    path = raw
    for prefix in ("git@github.com:", "https://github.com/", "ssh://git@github.com/"):
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break
    else:
        raise ValueError(f"REPORT: the origin remote is not GitHub: {raw}")
    if path.endswith(".git"):
        path = path[:-4]
    return f"https://github.com/{path}"


def repo_label(url: str) -> str:
    """The repository's URL as drawn under its tile: without the scheme,
    broken at its slashes into three lines."""
    bare = url.split("://", 1)[1]
    host, org, repo = bare.split("/")
    return f"{host}/\n{org}/\n{repo}"


def numbers() -> dict:
    rel = release()
    comps = rel["components"]
    out = {"network": rel["network"], "release": rel["release"], "main": {}}
    for name in MAIN:
        out["main"][name] = {"version": comps[name]["version"], "address": comps[name]["address"]}
    for rec in out["main"].values():
        assert len(rec["address"]) == 42 and rec["address"].startswith("0x"), rec
    out["repo_url"] = repo_url()
    out["site_url"] = SITE_URL
    out["repo_label"] = repo_label(out["repo_url"])
    return out


class Address(TextScene):
    SECTIONS = ("addresses", "use", "links")

    def panel(self, mobj, colour: str):
        """A row's glow_bar, added transparent; the caller fades it in."""
        p = glow_bar(mobj, colour, pad=0.1, opacity=0.08)
        p.set_fill(opacity=0)
        self.add(p)
        return p

    def construct(self):
        n = numbers()
        self.section(0)
        # the chrome: the title, and "today: Sepolia" beside it, from the first frame
        self.fix(self.title(TITLE_LINE, SIZE_BODY, Palette.TEXT, use_markup=True))
        self.wait(0.3)
        # the two main addresses, each typed on its panel, pulsed when it lands
        for name, y in zip(MAIN, Y_MAIN):
            colour = family(name)
            label = words(n["main"][name]["version"], SIZE_VERSION, colour)
            label.move_to([X_LEFT - 0.1 + label.width / 2, y, 0])
            probe = digits(n["main"][name]["address"], SIZE_BODY, colour)
            probe.move_to([X_ADDRESS + probe.width / 2, y, 0])
            assert probe.get_right()[0] <= X_RIGHT, probe.get_right()[0]
            panel = self.panel(VGroup(label, probe), colour)
            self.play(panel.animate.set_fill(opacity=0.08), FadeIn(label, run_time=0.4))
            addr = self.typed(n["main"][name]["address"], SIZE_BODY, colour, run_time=1.4, mono=True, place=lambda t, probe=probe: t.move_to(probe))
            self.play(Indicate(addr, color=colour, scale_factor=1.02, run_time=0.5))

        # 1 · the two ways in: engineers (the install commands), agents (llms.txt)
        self.section(1, hold=1.0)
        eng = words(ENGINEERS, SIZE_BODY, HUES["engineers"])
        eng.move_to([X_LEFT + eng.width / 2, Y_USE[0], 0])
        commands = digits(FORGE + "\n" + NPM, SIZE_COMMAND, Palette.TEXT, line_spacing=0.8)
        commands.move_to([X_COMMAND + commands.width / 2, (Y_USE[0] + Y_USE[1]) / 2, 0])
        assert commands.get_right()[0] <= X_RIGHT, commands.get_right()[0]
        eng_panel = self.panel(VGroup(eng, commands), HUES["engineers"])
        self.play(eng_panel.animate.set_fill(opacity=0.08), FadeIn(eng, run_time=0.4))
        self.play(AddTextLetterByLetter(commands, time_per_char=2.1 / len((FORGE + NPM).replace(" ", ""))))
        ag = words(AGENTS, SIZE_BODY, HUES["agents"])
        ag.move_to([X_LEFT + ag.width / 2, Y_USE[2], 0])
        llms = digits(LLMS, SIZE_COMMAND, Palette.TEXT)
        llms.move_to([X_COMMAND + llms.width / 2, Y_USE[2], 0])
        ag_panel = self.panel(VGroup(ag, llms), HUES["agents"])
        assert ag_panel.get_top()[1] < eng_panel.get_bottom()[1] - 0.05, "the two panels must not touch"
        self.play(ag_panel.animate.set_fill(opacity=0.08), FadeIn(ag, run_time=0.4))
        self.typed(LLMS, SIZE_COMMAND, Palette.TEXT, run_time=0.7, mono=True, place=lambda t: t.move_to(llms))

        # 2 · the two tiles with their URLs, bottom right; the closing line beside them
        self.section(2, hold=1.0)
        tiles = []
        for url, label, x, edge in ((n["site_url"], SITE, QR_X[0], None), (n["repo_url"], n["repo_label"], QR_X[1], RIGHT)):
            tile = qr(url, QR_SIZE, label=label.split("\n", 1)[0], label_buff=0.15)
            tile.shift([x, QR_TOP - QR_SIZE / 2, 0] - tile.panel.get_center())
            # the URL under the tile as one string (the repository's broken at its slashes, right-aligned to its tile)
            tile.remove(tile.label)
            text = digits(label, SIZE_CAPTION, Palette.MUTED, ligatures=True, line_spacing=0.6)
            text.next_to(tile.panel, DOWN, buff=0.15)
            if edge is not None:
                text.align_to(tile.panel, edge)
            tile.add(text)
            tile.label = VGroup(text)
            tiles.append(tile)
        assert tiles[0].label.get_right()[0] < tiles[1].label.get_left()[0] - 0.1, "the two URLs must not touch"
        assert tiles[1].get_right()[0] <= X_RIGHT + 0.02 and min(t.get_bottom()[1] for t in tiles) >= -3.6, [t.get_bottom()[1] for t in tiles]
        assert tiles[0].panel.get_top()[1] < ag_panel.get_bottom()[1] - 0.2, "the tiles stay clear of the agents' row"
        self.play(FadeIn(tiles[0], shift=UP * 0.1, run_time=0.6))
        self.play(FadeIn(tiles[1], shift=UP * 0.1, run_time=0.6))
        close = self.typed(CLOSE_LINES, SIZE_HERO, Palette.CORRECT, run_time=1.2, place=lambda t: t.move_to([X_LEFT + t.width / 2, Y_CLOSE, 0]), line_spacing=0.8)
        assert close.get_right()[0] < tiles[0].panel.get_left()[0] - 0.3, close.get_right()[0]
        self.close(hold=4.0)
