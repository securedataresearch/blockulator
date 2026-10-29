"""Slide 19, "The reference": the addresses, the way in for engineers and
for agents, the two links.

The adoption slide: everything a person or an agent needs to use
Blockulator in the next minute. The title is chrome. Section 0: the two
main addresses type in, FP19 v6 (TEXT, its family colour) then FP127 v9
(EMERALD), each on a glow_bar() in its colour, each pulsed once when it
lands; "every op is a free eth_call" under them. Section 1: the eight
other objects (FP127E/H/N/S, FP19E/H/N/S) at CAPTION in one column,
name in the family colour, address in mono. Section 2: the two ways in,
the "engineers:" row (GOLD) with the two install commands from README.md
and the "agents:" row (SAPPHIRE) with blockulator.com/llms.txt, each on a
glow_bar(). Section 3: "today: Sepolia" beside the title, the two QR
tiles (qr(): https://blockulator.com and the repository, from `git
remote`, normalised) with their URLs under them, and the closing line
at HERO in EMERALD.

Four sections: addresses, objects, use, links. Every address and version
is from release() (RELEASE.json, V15); check.py reads the file by a
second path, asserts the commands appear in README.md verbatim and
regenerates the QR matrices. The ladder objects are not shown.

Sizes, where the frame forced them (RULES.md, legibility): the main
rows' version names are at 24 beside the 42-character addresses at BODY
(11.1 units; name and address at BODY are 13.2, wider than the safe
area); the install commands are mono at 28 beside their BODY key (at
BODY the forge line and its key are 14.1 units); the repository's URL
under its tile is three mono CAPTION lines broken at its slashes (one
line is 6.8 units, the tile column 4.1); the halos the brief names on
the address rows are the pulse at the end of typing (a row of 12.6
units leaves no room for a dot beside it).
"""

from __future__ import annotations

import subprocess

from manim import DOWN, RIGHT, UP, FadeIn, Indicate, VGroup

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
MAIN = ("FP19", "FP127")  # the two main objects, in the order they type in
OTHERS = ("FP127E", "FP127H", "FP127N", "FP127S", "FP19E", "FP19H", "FP19N", "FP19S")
ETH_CALL = "every op is a free eth_call"
ENGINEERS = "engineers:"
AGENTS = "agents:"
FORGE = "forge install securedataresearch/blockulator"
NPM = "npm install @blockulator/contracts"
LLMS = "blockulator.com/llms.txt"
TODAY = "today: Sepolia"
SITE_URL = "https://blockulator.com"
SITE = "blockulator.com"
CLOSE = "Measure yourself against it."

LITERALS = {
    TITLE: "script §19",
    ETH_CALL: "K12",
    ENGINEERS: "brief",
    AGENTS: "brief",
    FORGE: "K12",
    NPM: "K12",
    LLMS: "K12",
    TODAY: "V6",
    SITE: "K12",
    CLOSE: "script §19",
}

X_LEFT = -6.2
X_RIGHT = 6.4
SIZE_VERSION = 24  # the main rows' version names (see the module docstring)
SIZE_COMMAND = 28  # the install commands
Y_MAIN = (2.65, 2.08)
X_ADDRESS = -4.75
Y_ETH_CALL = 1.42
Y_OBJECTS_TOP = 0.92
OBJECT_PITCH = 0.28
X_OBJECT_ADDRESS = -4.75
Y_USE = (-1.85, -2.23, -2.63)  # engineers (forge), npm, agents
X_COMMAND = -3.85
Y_CLOSE = -3.28
QR_SIZE = 1.9
QR_X = (3.35, 5.45)
QR_Y = 0.85
LABEL_PITCH = 0.26  # the tile labels' rows: the site's, then the repository's three lines under it


def family(name: str) -> str:
    return FAMILY_COLOUR["fp127" if name.startswith("FP127") else "fp19"]


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
    out = {"network": rel["network"], "release": rel["release"], "main": {}, "others": {}}
    for name in MAIN:
        out["main"][name] = {"version": comps[name]["version"], "address": comps[name]["address"]}
    for name in OTHERS:
        out["others"][name] = {"version": comps[name]["version"], "address": comps[name]["address"]}
    for rec in (*out["main"].values(), *out["others"].values()):
        assert len(rec["address"]) == 42 and rec["address"].startswith("0x"), rec
    out["repo_url"] = repo_url()
    out["site_url"] = SITE_URL
    out["repo_label"] = repo_label(out["repo_url"])
    return out


class Address(TextScene):
    SECTIONS = ("addresses", "objects", "use", "links")

    def construct(self):
        n = numbers()
        self.section(0)
        title = self.title(TITLE, SIZE_BODY, Palette.TEXT)
        self.fix(title)
        self.wait(0.3)
        # the two main addresses, each typed on its panel, pulsed when it lands
        for name, y in zip(MAIN, Y_MAIN):
            colour = family(name)
            label = words(n["main"][name]["version"], SIZE_VERSION, colour)
            label.move_to([X_LEFT - 0.1 + label.width / 2, y, 0])
            probe = digits(n["main"][name]["address"], SIZE_BODY, colour)
            probe.move_to([X_ADDRESS + probe.width / 2, y, 0])
            assert probe.get_right()[0] <= X_RIGHT, probe.get_right()[0]
            panel = glow_bar(VGroup(label, probe), colour, pad=0.1, opacity=0.08)
            panel.set_fill(opacity=0)
            self.add(panel)
            self.play(panel.animate.set_fill(opacity=0.08), FadeIn(label, run_time=0.4))
            addr = self.typed(n["main"][name]["address"], SIZE_BODY, colour, run_time=1.4, mono=True, place=lambda t, probe=probe: t.move_to(probe))
            self.play(Indicate(addr, color=colour, scale_factor=1.02, run_time=0.5))
        eth = words(ETH_CALL, SIZE_BODY, Palette.TEXT)
        eth.move_to([X_LEFT + eth.width / 2, Y_ETH_CALL, 0])
        self.play(FadeIn(eth, shift=UP * 0.08, run_time=0.6))

        # 1 · the eight other objects, one column at CAPTION
        self.section(1, hold=1.0)
        rows = VGroup()
        for i, name in enumerate(OTHERS):
            y = Y_OBJECTS_TOP - i * OBJECT_PITCH
            label = words(n["others"][name]["version"], SIZE_CAPTION, family(name))
            label.move_to([X_LEFT + label.width / 2, y, 0])
            addr = digits(n["others"][name]["address"], SIZE_CAPTION, Palette.MUTED)
            addr.move_to([X_OBJECT_ADDRESS + addr.width / 2, y, 0])
            rows.add(VGroup(label, addr))
        assert rows.get_right()[0] < QR_X[0] - QR_SIZE / 2 - 0.05, rows.get_right()[0]
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.1, run_time=0.25))

        # 2 · the two ways in: engineers (the install commands), agents (llms.txt)
        self.section(2, hold=1.0)
        eng = words(ENGINEERS, SIZE_BODY, HUES["engineers"])
        eng.move_to([X_LEFT + eng.width / 2, Y_USE[0], 0])
        forge = digits(FORGE, SIZE_COMMAND, Palette.TEXT)
        forge.move_to([X_COMMAND + forge.width / 2, Y_USE[0], 0])
        npm = digits(NPM, SIZE_COMMAND, Palette.TEXT)
        npm.move_to([X_COMMAND + npm.width / 2, Y_USE[1], 0])
        assert forge.get_right()[0] <= X_RIGHT, forge.get_right()[0]
        eng_panel = glow_bar(VGroup(eng, forge, npm), HUES["engineers"], pad=0.1, opacity=0.08)
        eng_panel.set_fill(opacity=0)
        self.add(eng_panel)
        self.play(eng_panel.animate.set_fill(opacity=0.08), FadeIn(eng, run_time=0.4))
        self.typed(FORGE, SIZE_COMMAND, Palette.TEXT, run_time=1.2, mono=True, place=lambda t: t.move_to(forge))
        self.typed(NPM, SIZE_COMMAND, Palette.TEXT, run_time=0.9, mono=True, place=lambda t: t.move_to(npm))
        ag = words(AGENTS, SIZE_BODY, HUES["agents"])
        ag.move_to([X_LEFT + ag.width / 2, Y_USE[2], 0])
        llms = digits(LLMS, SIZE_COMMAND, Palette.TEXT)
        llms.move_to([X_COMMAND + llms.width / 2, Y_USE[2], 0])
        ag_panel = glow_bar(VGroup(ag, llms), HUES["agents"], pad=0.1, opacity=0.08)
        ag_panel.set_fill(opacity=0)
        self.add(ag_panel)
        self.play(ag_panel.animate.set_fill(opacity=0.08), FadeIn(ag, run_time=0.4))
        self.typed(LLMS, SIZE_COMMAND, Palette.TEXT, run_time=0.7, mono=True, place=lambda t: t.move_to(llms))

        # 3 · today: Sepolia, the two tiles with their URLs, the closing line
        self.section(3, hold=1.0)
        today = words(TODAY, SIZE_BODY, Palette.MUTED).next_to(title, RIGHT, buff=0.6)
        today.set_y(title.get_y())
        self.play(FadeIn(today, shift=RIGHT * 0.1, run_time=0.5))
        site_tile = qr(n["site_url"], QR_SIZE, label=SITE, label_buff=0.15)
        site_tile.shift([QR_X[0], QR_Y, 0] - site_tile.panel.get_center())
        # its label starts at the tile's left edge, clear of the object rows
        site_tile.label.shift(RIGHT * (site_tile.panel.get_left()[0] - site_tile.label.get_left()[0]))
        repo_tile = qr(n["repo_url"], QR_SIZE, label=n["repo_label"], label_align="right", label_buff=0.15)
        repo_tile.shift([QR_X[1], QR_Y, 0] - repo_tile.panel.get_center())
        # the repository's three lines go under the site's label row, right-aligned to its tile
        repo_tile.label.shift(DOWN * (repo_tile.label.get_top()[1] - (site_tile.label.get_bottom()[1] - 0.1)))
        assert repo_tile.get_right()[0] <= X_RIGHT + 0.02, repo_tile.get_right()[0]
        assert site_tile.label.get_bottom()[1] > repo_tile.label.get_top()[1], "the labels' rows must not touch"
        assert min(site_tile.label.get_left()[0], repo_tile.label.get_left()[0]) > rows.get_right()[0], "the labels stay clear of the object rows"
        assert repo_tile.label.get_bottom()[1] > Y_USE[0] + 0.32, (repo_tile.label.get_bottom()[1], "clear of the use rows")
        assert site_tile.panel.get_top()[1] <= Y_MAIN[1] - 0.27, "under the FP127 row's panel"
        self.play(FadeIn(site_tile, shift=UP * 0.1, run_time=0.6))
        self.play(FadeIn(repo_tile, shift=UP * 0.1, run_time=0.6))
        self.typed(CLOSE, SIZE_HERO, Palette.CORRECT, run_time=1.2, place=lambda t: t.move_to([X_LEFT + t.width / 2, Y_CLOSE, 0]))
        self.close(hold=4.0)
