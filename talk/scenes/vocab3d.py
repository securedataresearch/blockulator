"""The deck's 3D vocabulary: things are things (talk/briefs/3d-direction.md).

A vault, a pool, a balance is a Tank (a glass cylinder with a liquid
level); a count of things is a Stack of blocks; a rounding step is a Ball
on a Lattice (a number line lying on the ground with tick posts) that
drops and rolls to a tick; a check is a Gate across the lattice that
opens EMERALD or shuts RED, or a Gauge (a dial whose needle is driven
by its inputs, one of them wired to a Ball) standing in front of the Gate. The camera orbits on a reveal and dollies on
a zoom, never while a number is being read.

Everything is built for manim's Cairo renderer (the deck's): surfaces
are flat-shaded (one colour per face, darkened or lit per face by the
camera's light at the upper left: ThreeDCamera.light_source), in the
site's palette, on Palette.BG. Labels are vocab's words()/digits()/
markup() (so they register in DRAWN for check.py), shown either as
billboards (add_fixed_orientation_mobjects: they face the camera and
follow a 3D anchor) or as HUD text (add_fixed_in_frame_mobjects: the
chrome, the title, the caption, a hero line). The Cairo camera draws
every non-3D mobject after every 3D piece, so a label is never hidden
behind a tank; a billboard keeps its size under a dolly (the thing
grows, its number stays legible).

Axes: x to the right, y into the scene (away from the camera), z up. The
ground is the plane z = 0; objects stand on it. The camera looks from
in front (−y) and above; look() has three presets, each framed on
STAGE_CENTRE (z = 1.3) so the ground sits in the lower half and labels have the
upper half, under the chrome.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from manim import (
    DEGREES,
    DOWN,
    LEFT,
    ORIGIN,
    OUT,
    RIGHT,
    UP,
    AnimationGroup,
    Create,
    Cube,
    Cylinder,
    FadeIn,
    FadeOut,
    Group,
    GrowFromCenter,
    ImageMobject,
    LaggedStart,
    Line,
    MoveAlongPath,
    Prism,
    Rotate,
    Sphere,
    Succession,
    ThreeDScene,
    Transform,
    VGroup,
    VMobject,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_in_quad, ease_out_cubic, linear, there_and_back
from manim.utils.space_ops import rotate_vector

from vocab import (
    LOGO_CORNER,
    LOGO_DIR,
    LOGO_HEIGHT,
    LOGO_OPACITY,
    SIZE_BODY,
    SIZE_CAPTION,
    DeckScene,
    Palette,
    check_mark,
    cross_mark,
    digits,
    direction,
    setup_fonts,
    words,
)

# ------------------------------------------------------------------ camera --
LIGHT = np.array([-7.0, -9.0, 10.0])  # upper left, in front: the brief's light
STAGE_CENTRE = np.array([0.0, 0.0, 1.3])  # the frame looks here: the ground low, room above for labels
LOOKS = {
    # (phi: the tilt down from straight overhead; theta: the spin around z, −90° is from the front)
    "front": (72 * DEGREES, -90 * DEGREES),
    "three_quarter": (66 * DEGREES, -52 * DEGREES),
    "top": (28 * DEGREES, -90 * DEGREES),
}


def look(scene: ThreeDScene, preset: str, zoom: float = 1.0, centre=None) -> None:
    """Cut (no animation) to one of the three camera presets: `front`
    (from the front, a little above: tanks read as cylinders), `three_quarter`
    (from the front-left, above: depth reads), `top` (nearly overhead: a
    lattice reads like a 2D grid)."""
    phi, theta = LOOKS[preset]
    scene.set_camera_orientation(phi=phi, theta=theta, zoom=zoom, frame_center=STAGE_CENTRE if centre is None else np.array(centre, dtype=float))


def orbit(scene: ThreeDScene, phi: float | str | None = None, theta: float | None = None, run_time: float = 1.6, **kw):
    """Swing the camera to a new phi/theta (radians; a preset's name as
    `phi` takes both from LOOKS), ease-in-out. Only between reads; also
    the reveal of a new thing (play it with added_anims=[...])."""
    if isinstance(phi, str):
        phi, theta = LOOKS[phi]
    scene.move_camera(phi=phi, theta=theta, run_time=run_time, rate_func=ease_in_out_cubic, **kw)


def dolly(scene: ThreeDScene, zoom: float, at=None, run_time: float = 1.4, **kw):
    """Zoom the camera (1 is the whole stage) and, with `at`, re-centre the
    frame on a point or mobject (None: back to STAGE_CENTRE), ease-in-out.
    Only between reads; never a substitute for Lattice.stretch on a dive
    (a 10^39 zoom overflows float64)."""
    if at is None:
        centre = STAGE_CENTRE
    elif hasattr(at, "get_center"):
        centre = at.get_center()
    else:
        centre = np.array(at, dtype=float)
    scene.move_camera(zoom=zoom, frame_center=centre, run_time=run_time, rate_func=ease_in_out_cubic, **kw)


# ------------------------------------------------------------------- scene --
class DeckScene3D(ThreeDScene):
    """DeckScene's chrome in a ThreeDScene: the two marks at the top
    corners, the title beside the left mark, the caption bottom-left, all
    fixed in frame; SECTIONS/section()/close()/title() are DeckScene's.
    billboard() puts a label on a 3D thing; hud() puts text on the frame;
    show() puts a Tank/Stack/Lattice/Gate on the stage with its labels
    billboarded; dimmable(*keep) collects what a dim-everything step may
    fade. The camera starts at the three_quarter preset."""

    SECTIONS: tuple[str, ...] = ()

    def setup(self):
        setup_fonts()
        self.camera.background_color = Palette.BG
        self.renderer.camera.light_source.move_to(LIGHT)
        self._caption = None
        self.sections_called: list[str] = []
        x, y = LOGO_CORNER
        self.logo_left = ImageMobject(str(LOGO_DIR / "blockulator.png")).scale_to_fit_height(LOGO_HEIGHT).set_opacity(LOGO_OPACITY)
        self.logo_left.move_to([-x, y, 0], aligned_edge=UP + LEFT)
        self.logo_right = ImageMobject(str(LOGO_DIR / "sdr.png")).scale_to_fit_height(LOGO_HEIGHT).set_opacity(LOGO_OPACITY)
        self.logo_right.move_to([x, y, 0], aligned_edge=UP + RIGHT)
        self.chrome = Group(self.logo_left, self.logo_right)
        self.add_fixed_in_frame_mobjects(self.logo_left, self.logo_right)
        self.fixed = VGroup()
        look(self, "three_quarter")

    # the clicker's sections and the title helper are DeckScene's (they touch only self's attributes)
    section = DeckScene.section
    close = DeckScene.close
    title = DeckScene.title

    def fix(self, *mobjs):
        """Static chrome, fixed in frame (the title, a key): added at once,
        never animated, skipped by dimmable()."""
        g = VGroup(*mobjs)
        self.fixed.add(*mobjs)
        self.add_fixed_in_frame_mobjects(*mobjs)
        return g

    def hud(self, *mobjs):
        """Text on the frame that is not chrome (a hero line): fixed in
        frame, dimmable, added at once. Returns the mobjects as a VGroup."""
        self.add_fixed_in_frame_mobjects(*mobjs)
        return VGroup(*mobjs)

    def caption_now(self, text: str, size: float = SIZE_CAPTION, corner=DOWN + LEFT):
        """The source caption as static chrome (fixed in frame, no animation)."""
        new = words(text, size, Palette.FAINT).to_corner(corner, buff=0.45)
        self._caption = new
        return self.fix(new)

    def caption(self, text: str, size: float = SIZE_CAPTION, run_time: float = 0.6):
        """Replace the source caption (fixed in frame). Returns the animation."""
        new = words(text, size, Palette.FAINT).to_corner(DOWN + LEFT, buff=0.45)
        old, self._caption = self._caption, new
        self.fixed.add(new)
        self.renderer.camera.add_fixed_in_frame_mobjects(new)
        if old is None:
            return FadeIn(new, run_time=run_time)
        self.fixed.remove(old)
        return AnimationGroup(FadeOut(old, run_time=run_time), FadeIn(new, run_time=run_time))

    def billboard(self, mobj: VMobject, anchor, offset=UP * 0.45):
        """A label on a thing: `mobj` (words/digits/markup, or a VGroup of
        them) faces the camera and sits at `anchor` (a 3D point, or a
        mobject or a function to follow) plus `offset` in screen units.
        Added to the scene at once; fade it in with FadeIn if the thing is
        arriving, or build it with the thing before the frame."""
        if callable(anchor):
            centre = anchor
        elif hasattr(anchor, "get_center"):
            centre = anchor.get_center
        else:
            point = np.array(anchor, dtype=float)
            centre = lambda: point  # noqa: E731
        offset = np.array(offset, dtype=float)
        mobj.move_to(centre() + offset)
        mobj.add_updater(lambda m: m.move_to(centre() + offset))
        self.add_fixed_orientation_mobjects(mobj, center_func=centre)
        return mobj

    def relabel(self, old: VMobject, new: VMobject, run_time: float = 0.7, offset=None):
        """Swap one billboard for another at the same anchor (a tank's
        quantity becoming the number it produced): `new` takes old's anchor
        and offset (or `offset`). Returns the animation."""
        centre = self.renderer.camera.fixed_orientation_mobjects[old]
        offset = old.get_center() - centre() if offset is None else np.array(offset, dtype=float)
        self.billboard(new, centre, offset)
        return AnimationGroup(FadeOut(old, run_time=run_time), FadeIn(new, run_time=run_time))

    def show(self, *things):
        """Put things on the stage: each thing's body is added and each of
        its labels (thing.labels: (mobject, anchor, offset)) billboarded."""
        for thing in things:
            self.add(thing)
            for mobj, anchor, offset in getattr(thing, "labels", ()):
                self.billboard(mobj, anchor, offset)

    def dimmable(self, *keep):
        """Every VMobject on the stage that is not chrome, not in `keep`
        (things with their labels and marks), for a dim-everything step."""
        skip = set(self.fixed.get_family())
        for k in keep:
            skip |= set(k.get_family())
            for mobj, _, _ in getattr(k, "labels", ()):
                skip |= set(mobj.get_family())
            for extra in getattr(k, "extras", ()):
                skip |= set(extra.get_family())
        return VGroup(*[m for m in self.mobjects if isinstance(m, VMobject) and not (set(m.get_family()) & skip)])


# --------------------------------------------------------------- surfaces --
def _flat(colour: str, opacity: float = 1.0) -> dict:
    """Surface kwargs for one flat palette colour: no checkerboard, a hairline
    stroke in the same colour so the pieces show no seams."""
    return {"fill_color": colour, "fill_opacity": opacity, "checkerboard_colors": False, "stroke_color": colour, "stroke_width": 0.6, "stroke_opacity": opacity}


def _tint(colour: str, opacity: float = 1.0) -> dict:
    """The same for a Cube/Prism (six faces, no checkerboard option)."""
    return {"fill_color": colour, "fill_opacity": opacity, "stroke_color": colour, "stroke_width": 0.6, "stroke_opacity": opacity}


def _cylinder(radius: float, height: float, colour: str, opacity: float = 1.0, base=ORIGIN, segments: int = 36) -> Cylinder:
    """A cylinder standing on the ground point `base`, one piece per wall segment."""
    c = Cylinder(radius=radius, height=height, direction=OUT, resolution=(1, segments), **_flat(colour, opacity))
    c.move_to(np.array(base, dtype=float) + OUT * height / 2)
    return c


def slide(thing: VGroup, delta, run_time: float = 1.2, opacity: float | None = None):
    """A thing moves, whole, by `delta` (its labels follow their anchors),
    and with `opacity` fades to it on the way (a Tank through its own
    fade(): the glass stays glass). Returns the animation."""
    delta = np.array(delta, dtype=float)
    if hasattr(thing, "base"):
        thing.base = thing.base + delta
    target = thing.copy().shift(delta)
    if opacity is not None:
        if hasattr(target, "fade_to"):
            target.fade_to(opacity)
        else:
            target.set_opacity(opacity)
    return Transform(thing, target, run_time=run_time, rate_func=ease_in_out_cubic)


def dim(mobjs: VGroup, opacity: float = 0.15, run_time: float = 0.8):
    """Everything in `mobjs` fades to `opacity` (fill and stroke)."""
    return mobjs.animate(run_time=run_time).set_fill(opacity=opacity).set_stroke(opacity=opacity)


# --------------------------------------------------------------- the tank --
GLASS_OPACITY = 0.22


class Tank(VGroup):
    """A vault, a pool, a balance: a glass cylinder (faint SLATE) standing
    on the ground with a liquid inside (a shorter cylinder in the thing's
    colour), its name as words() at its foot and its quantity as digits()
    above its rim, both billboarded. `level` is the liquid's share of
    `capacity` (the full height); `stacked` puts the name under the
    quantity above the rim instead of at the foot; `label_shift` moves
    every label by a screen offset. .glass, .liquid, .name, .quantity;
    .labels for show(); top()/foot()/rim(side) are anchor points read from
    the glass, so they follow a slide."""

    def __init__(self, label: str, capacity: float = 1.0, level: float = 0.0, colour: str = Palette.GOLD, radius: float = 0.9, height: float = 2.0, quantity: str | None = None, at=ORIGIN, glass: str = Palette.SLATE, size: float = SIZE_BODY, stacked: bool = False, label_shift=ORIGIN):
        super().__init__()
        shift = np.array(label_shift, dtype=float)  # a screen offset added to every label (to clear a neighbour)
        self.capacity, self.colour, self.radius, self.height = capacity, colour, radius, height
        self.level = level
        self.glass = _cylinder(radius, height, glass, GLASS_OPACITY, base=at)
        self.liquid = self._liquid_at(level, colour)
        self.add(self.liquid, self.glass)
        self.name = words(label, size, Palette.MUTED)
        self.quantity = digits(quantity, size, colour) if quantity is not None else None
        if stacked and self.quantity is not None:  # the quantity over the name, both above the rim: a narrow footprint
            self.labels = [(self.quantity, self.top, UP * (0.72 + self.quantity.height / 2) + shift), (self.name, self.top, UP * 0.42 + shift)]
        else:
            self.labels = [(self.name, self.foot, DOWN * 0.42 + shift)]
            if self.quantity is not None:
                self.labels.append((self.quantity, self.top, UP * 0.42 + shift))

    def fade_to(self, opacity: float):
        """The tank at `opacity` (1 is as built): the glass keeps its faint
        share of it. In place; returns self."""
        self.glass.set_fill(opacity=GLASS_OPACITY * opacity).set_stroke(opacity=GLASS_OPACITY * opacity)
        self.liquid.set_fill(opacity=opacity).set_stroke(opacity=opacity)
        return self

    def foot(self):
        c = self.glass.get_center()
        return np.array([c[0], c[1], self.glass.get_nadir()[2]])

    def top(self):
        c = self.glass.get_center()
        return np.array([c[0], c[1], self.glass.get_zenith()[2]])

    def rim(self, side=RIGHT):
        return self.top() + np.array(side, dtype=float) * self.glass.width / 2

    def grow_to(self, radius: float, height: float, run_time: float = 1.0):
        """The animation that scales the glass to a new size on the same
        foot (the liquid keeps its level share; pour() plays both)."""
        foot = self.foot()
        self.radius, self.height = radius, height
        glass = _cylinder(radius, height, Palette.SLATE, GLASS_OPACITY, base=foot)
        glass.set_fill(opacity=self.glass.get_fill_opacity()).set_stroke(opacity=self.glass.get_stroke_opacity())
        return Transform(self.glass, glass, run_time=run_time, rate_func=ease_in_out_cubic)

    def _liquid_at(self, level: float, colour: str) -> Cylinder:
        h = max(0.02, level / self.capacity * (self.height - 0.08))
        return _cylinder(self.radius * 0.93, h, colour, 1.0, base=self.foot() + OUT * 0.04 if hasattr(self, "glass") else ORIGIN)

    def _liquid_target(self, level: float, colour: str, foot) -> Cylinder:
        h = max(0.02, level / self.capacity * (self.height - 0.08))
        return _cylinder(self.radius * 0.93, h, colour, 1.0, base=np.array(foot, dtype=float) + OUT * 0.04)

    def set_level(self, level: float, run_time: float = 1.0, colour: str | None = None):
        """The animation that moves the liquid to `level` (0..capacity), in
        `colour` if the liquid changes substance."""
        self.level = level
        self.colour = colour or self.colour
        return Transform(self.liquid, self._liquid_at(level, self.colour), run_time=run_time, rate_func=ease_in_out_cubic)


def fill(tank: Tank, level: float, run_time: float = 1.0, colour: str | None = None):
    """The liquid rises to `level`."""
    return tank.set_level(level, run_time, colour)


def drain(tank: Tank, level: float, run_time: float = 1.0):
    """The liquid falls to `level`."""
    return tank.set_level(level, run_time)


def pour(src: Tank, dst: Tank, amount: float, run_time: float = 2.0, drops: int = 9, grow: tuple[float, float] | None = None):
    """`amount` (in capacity units) leaves src and lands in dst: a stream
    of small spheres in src's colour arcs from src's rim to dst's rim
    while both levels move (dst takes src's colour). With `grow` =
    (radius, height), dst's glass grows to that size as it fills (a small
    pocket becoming a vault: the whole pool against one share). Returns
    one animation."""
    colour = src.colour
    growth = []
    if grow is not None:
        foot = dst.foot()
        growth.append(dst.grow_to(*grow, run_time=run_time))
        dst.level, dst.colour = dst.level + amount, colour
        growth.append(Transform(dst.liquid, dst._liquid_target(dst.level, colour, foot), run_time=run_time, rate_func=ease_in_out_cubic))
    towards = dst.glass.get_center() - src.glass.get_center()
    towards[2] = 0
    unit = towards / (np.linalg.norm(towards) or 1.0)
    a, b = src.rim(unit), dst.rim(-unit)
    apex = (a + b) / 2 + OUT * 0.9
    path = VMobject().set_points_smoothly([a, apex, b])
    stream = []
    for _ in range(drops):
        d = Sphere(radius=0.09, resolution=(4, 10), **_flat(colour)).move_to(a)
        stream.append(Succession(FadeIn(d, run_time=0.05), MoveAlongPath(d, path, run_time=run_time * 0.55, rate_func=linear), FadeOut(d, run_time=0.05)))
    return AnimationGroup(
        src.set_level(src.level - amount, run_time),
        *(growth or [dst.set_level(dst.level + amount, run_time, colour)]),
        LaggedStart(*stream, lag_ratio=0.9 / drops, run_time=run_time),
    )


# -------------------------------------------------------------- the stack --
class Stack(VGroup):
    """n blocks (cubes) in `cols` columns on the ground, in one colour,
    with a label (digits(): the count and its unit) billboarded above;
    appear(dt) brings them in one per dt. .blocks, .label; .labels for
    show(); top() is the anchor over the blocks."""

    def __init__(self, n: int, colour: str = Palette.VIOLET, cols: int = 10, side: float = 0.42, label: str | None = None, at=ORIGIN, size: float = SIZE_BODY):
        super().__init__()
        self.n, self.cols, self.side, self.colour = n, cols, side, colour
        base = np.array(at, dtype=float)
        gap = side * 1.25
        self.blocks = VGroup()
        for k in range(n):
            col, row = k % cols, k // cols
            cube = Cube(side_length=side, **_tint(colour))
            cube.move_to(base + RIGHT * (col - (min(n, cols) - 1) / 2) * gap + OUT * (row * gap + side / 2))
            self.blocks.add(cube)
        self.add(self.blocks)
        self.label = digits(label, size, colour) if label is not None else None
        self.labels = [(self.label, self.top, UP * 0.4)] if self.label is not None else []

    def top(self):
        c = self.blocks.get_center()
        rows = -(-self.n // self.cols)
        return np.array([c[0], c[1], rows * self.side * 1.25])

    def appear(self, dt: float = 0.08):
        """The blocks arrive one per dt (each grows from nothing)."""
        return LaggedStart(*[GrowFromCenter(b, run_time=0.3, rate_func=ease_out_cubic) for b in self.blocks], lag_ratio=dt / 0.3)


def transfer(stack: Stack, to_point, run_time: float = 1.2, opacity: float | None = None):
    """The stack slides, whole, to stand at `to_point` on the ground (its
    label follows), fading to `opacity` on the way if given."""
    c = stack.blocks.get_center()
    delta = np.array(to_point, dtype=float) - np.array([c[0], c[1], 0.0])
    target = stack.blocks.copy().shift(delta)
    if opacity is not None:
        target.set_opacity(opacity)
    return Transform(stack.blocks, target, run_time=run_time, rate_func=ease_in_out_cubic)


# ------------------------------------------------------------ the lattice --
class Lattice(VGroup):
    """A number line lying on the ground: a rail (a long thin prism) from
    x_range[0] to x_range[1], a tick post (a thin prism standing up) at
    every `tick`, each numbered by a billboarded digits() beneath it;
    `minor` adds shorter, unnumbered posts between (the half: the rounding
    boundary). point(x) is the ground point of a value (n2p too, so
    vocab.direction() reads a lattice); post(x) a post by value;
    stretch(factor, about) stretches the grid for a dive (never a camera
    zoom past float64). .labels for show()."""

    def __init__(self, x_range=(0, 2, 1), tick: float | None = None, length: float = 8.0, depth: float = 0.22, at=ORIGIN, colour: str = Palette.FAINT, minor: float | None = None, size: float = SIZE_BODY, number: Callable[[float], str] | None = None):
        super().__init__()
        number = number or (lambda x: str(int(x)) if float(x).is_integer() else str(x))
        self.x0, self.x1 = float(x_range[0]), float(x_range[1])
        self.tick = float(tick if tick is not None else (x_range[2] if len(x_range) > 2 else 1))
        self.length, self.depth, self.colour = length, depth, colour
        self.base = np.array(at, dtype=float)
        self.rail = Prism(dimensions=[length, depth, 0.06], **_tint(Palette.RULE)).move_to(self.base + OUT * 0.03)
        self.posts: dict[float, Prism] = {}
        self.numbers: dict[float, VMobject] = {}
        self.labels = []
        x = self.x0
        while x <= self.x1 + 1e-9:
            self.posts[x] = Prism(dimensions=[0.07, depth, 0.42], **_tint(colour)).move_to(self.point(x) + OUT * 0.21)
            self.numbers[x] = digits(number(x), size, colour)
            self.labels.append((self.numbers[x], (lambda p=self.posts[x]: p.get_center() - OUT * 0.21), DOWN * 0.5))
            x += self.tick
        self.minors: dict[float, Prism] = {}
        if minor:
            x = self.x0 + minor
            while x < self.x1:
                if not any(abs(x - p) < 1e-9 for p in self.posts):
                    self.minors[x] = Prism(dimensions=[0.05, depth, 0.24], **_tint(Palette.RULE)).move_to(self.point(x) + OUT * 0.12)
                x += minor
        self.add(self.rail, *self.posts.values(), *self.minors.values())

    def point(self, x: float):
        t = (float(x) - self.x0) / (self.x1 - self.x0)
        return self.base + RIGHT * (t - 0.5) * self.length

    n2p = point

    def post(self, x: float) -> Prism:
        return next(p for v, p in self.posts.items() if abs(v - x) < 1e-9)

    def stretch(self, factor: float, about: float, run_time: float = 1.2):
        """The dive: the grid stretches `factor` times about the value
        `about` (its point stays put); the posts and their numbers follow."""
        centre = self.point(about)
        self.length *= factor
        self.base = centre - RIGHT * ((about - self.x0) / (self.x1 - self.x0) - 0.5) * self.length
        anims = [self.rail.animate.stretch(factor, 0, about_point=centre)]
        for x, p in list(self.posts.items()) + list(self.minors.items()):
            anims.append(p.animate.shift(RIGHT * (self.point(x)[0] - p.get_center()[0])))
        return AnimationGroup(*anims, run_time=run_time, rate_func=ease_in_out_cubic)


# --------------------------------------------------------------- the ball --
class Ball(Sphere):
    """A value: a sphere in one flat colour (EXACT white until it rounds)."""

    def __init__(self, colour: str = Palette.EXACT, radius: float = 0.24, at=ORIGIN):
        super().__init__(radius=radius, resolution=(10, 20), **_flat(colour))
        self.colour = colour
        self.move_to(at)


def drop_snap(ball: Ball, lattice: Lattice, from_x: float, to_x: float, colour: str, run_time: float = 2.4, drop_from: float = 1.6):
    """The 3D snap: the ball (already on the scene, above from_x) falls to
    the rail, squashes, rolls to to_x, flashes in the result colour (RED
    or EMERALD) and the direction arrow is drawn on the ground. Returns
    (animation, arrow)."""
    r = ball.radius
    landed = lattice.point(from_x) + OUT * (r + 0.06)
    end = lattice.point(to_x) + OUT * (r + 0.06)
    if ball.get_center()[2] < landed[2] + 0.1:
        ball.move_to(lattice.point(from_x) + OUT * (drop_from + r))
    arrow = direction(lattice, from_x, to_x, colour, lift=0).shift(OUT * 0.08)
    squashed = ball.copy().move_to(landed).stretch(0.78, 2).stretch(1.12, 0).stretch(1.12, 1)
    at_end = ball.copy().move_to(end).set_fill(colour).set_stroke(colour)
    big = at_end.copy().scale(1.35)
    ball.colour = colour
    anim = Succession(
        ball.animate(run_time=run_time * 0.28, rate_func=ease_in_quad).move_to(landed),
        Transform(ball, squashed, run_time=run_time * 0.06),
        Transform(ball, ball.copy().move_to(landed), run_time=run_time * 0.08),
        AnimationGroup(ball.animate(rate_func=ease_in_out_cubic).move_to(end), Create(arrow), run_time=run_time * 0.38),
        Transform(ball, big, run_time=run_time * 0.1, rate_func=ease_out_cubic),
        Transform(ball, at_end, run_time=run_time * 0.1, rate_func=ease_out_cubic),
    )
    return anim, arrow


def lift(ball: Ball, lattice: Lattice, to_x: float, colour: str, run_time: float = 1.8, height: float = 1.2):
    """The ball rises, crosses to to_x and settles back on the rail in
    `colour` (the exact value restored: EXACT)."""
    r = ball.radius
    up = ball.get_center() + OUT * height
    over = lattice.point(to_x) + OUT * (r + 0.06 + height)
    down = lattice.point(to_x) + OUT * (r + 0.06)
    ball.colour = colour
    return Succession(
        ball.animate(run_time=run_time * 0.3, rate_func=ease_out_cubic).move_to(up),
        ball.animate(run_time=run_time * 0.4, rate_func=ease_in_out_cubic).move_to(over).set_fill(colour).set_stroke(colour),
        ball.animate(run_time=run_time * 0.3, rate_func=ease_in_quad).move_to(down).set_fill(colour).set_stroke(colour),
    )


# --------------------------------------------------------------- the gate --
class Gate(VGroup):
    """A check: a barrier (a thin, wide slab) standing across the lattice
    at value x between two posts, its label billboarded above the posts.
    open() lifts it in EMERALD under a check mark; shut() drops it in RED
    under a cross; label_lift and mark_lift are their screen heights
    over the posts. .slab, .posts, .label, .mark (.extras holds the marks
    and verdicts for dimmable()); .labels for show(); top() the anchor."""

    def __init__(self, text: str | None, lattice: Lattice | None = None, x: float = 0.0, at=None, width: float = 2.2, height: float = 1.5, colour: str = Palette.MUTED, size: float = SIZE_BODY, mono: bool = True, label_lift: float = 0.42, mark_lift: float = 1.0):
        super().__init__()
        self.label_lift, self.mark_lift = label_lift, mark_lift
        base = np.array(at, dtype=float) if at is not None else lattice.point(x)
        self.width, self.height, self.colour = width, height, colour
        self.slab = Prism(dimensions=[0.12, width, height], **_tint(colour, 0.95)).move_to(base + OUT * height / 2)
        post = lambda side: Prism(dimensions=[0.1, 0.1, height + 0.5], **_tint(Palette.RULE)).move_to(base + side * width / 2 + OUT * (height + 0.5) / 2)  # noqa: E731
        self.posts = VGroup(post(UP), post(DOWN))
        self.add(self.posts, self.slab)
        self.label = (digits if mono else words)(text, size, colour) if text is not None else None
        self.mark = None
        self.extras: list[VMobject] = []
        self.labels = [(self.label, self.top, UP * label_lift)] if self.label is not None else []

    def face(self, angle: float):
        """Turn the gate (built across the lattice, its face along x) about
        its foot so its face points `angle` radians round from the front
        (DOWN): the gate stands behind a Gauge that faces the camera."""
        self.rotate(angle - 90 * DEGREES, axis=OUT, about_point=self.posts.get_center() * [1, 1, 0])
        return self

    def top(self):
        return self.posts.get_center() + OUT * (self.height + 0.5) / 2


def open(gate: Gate, scene: DeckScene3D, run_time: float = 1.2):
    """The gate goes EMERALD and lifts clear; a check mark appears over it."""
    gate.colour = Palette.CORRECT
    gate.mark = check_mark(Palette.CORRECT, size=0.5)
    scene.billboard(gate.mark, gate.top, UP * gate.mark_lift)
    gate.extras.append(gate.mark)
    return Succession(
        gate.slab.animate(run_time=run_time * 0.3).set_fill(Palette.CORRECT).set_stroke(Palette.CORRECT),
        AnimationGroup(
            gate.slab.animate(rate_func=ease_out_cubic).shift(OUT * gate.height * 0.9),
            *([gate.label.animate.set_color(Palette.CORRECT)] if gate.label is not None else []),
            Create(gate.mark),
            run_time=run_time * 0.7,
        ),
    )


def shut(gate: Gate, scene: DeckScene3D, run_time: float = 1.0):
    """The gate goes RED and drops; a cross replaces the check mark."""
    gate.colour = Palette.WRONG
    old = gate.mark
    gate.mark = cross_mark(Palette.WRONG, size=0.5)
    scene.billboard(gate.mark, gate.top, UP * gate.mark_lift)
    gate.extras.append(gate.mark)
    foot = gate.posts.get_center().copy()
    foot[2] = 0
    down = gate.slab.copy().move_to(foot + OUT * gate.height / 2).set_fill(Palette.WRONG).set_stroke(Palette.WRONG)
    anims = [Transform(gate.slab, down, rate_func=ease_in_quad), Create(gate.mark)]
    if gate.label is not None:
        anims.append(gate.label.animate.set_color(Palette.WRONG))
    if old is not None:
        anims.append(FadeOut(old))
    return AnimationGroup(*anims, run_time=run_time)


# -------------------------------------------------------------- the gauge --
GAUGE_ZERO = 210 * DEGREES  # the needle's angle at 0: lower left
GAUGE_LIMIT = 60 * DEGREES  # the limit mark: upper right; green from 0 to here
GAUGE_END = -30 * DEGREES  # the end of the red arc: lower right; a value past the limit pins here
GAUGE_REST = 90 * DEGREES  # the needle before any input: straight up, MUTED


class _Swing(Rotate):
    """A Rotate whose target also takes a colour (one animation on the needle:
    two in a group would fight over it)."""

    def __init__(self, needle: Line, angle: float, axis, about_point, colour: str, run_time: float):
        self.colour = colour
        super().__init__(needle, angle=angle, axis=axis, about_point=about_point, run_time=run_time, rate_func=ease_in_out_cubic)

    def create_target(self):
        return super().create_target().set_color(self.colour)


class Gauge(VGroup):
    """A check as a dial standing on the ground, facing the camera: an arc
    from 0 to `limit` in EMERALD (GAUGE_ZERO round to GAUGE_LIMIT, where a
    tick carries `limit_label`) continuing in RED past the limit to
    GAUGE_END, a needle on a hub at the pivot, and a row of input bars
    under the dial, one per (name, value, fraction) of `inputs`: a track
    with a fill of that share, the name billboarded at its left, the value
    (digits) at its right. The needle's angle is a function of a value:
    linear over the green arc, pinned at the end of the red for anything
    past the limit (a result 5 million times the limit reads as "pinned",
    which is the truth). `facing` turns the dial about its foot so it
    faces a camera at theta = facing − 90°.

    .arc_green, .arc_red, .needle, .hub, .inputs[name] = (track, fill,
    name_label, value_label), .readout (set by read()); .labels for show();
    top() the anchor over the arc; port(name) the left end of an input's
    track (where a wire from a Ball arrives); aim(value, colour) the
    animation that swings the needle; set_input(name, fraction) the
    animation that fills or collapses an input's bar; glow() the green
    arc's flash; bracket(text) a bracket along the red arc with a HERO
    label (the multiplier)."""

    def __init__(self, limit_label: str, inputs: list[tuple[str, str | None, float]], at=ORIGIN, facing: float = 0.0, radius: float = 1.0, pivot: float = 2.35, bar_width: float = 2.2, size: float = SIZE_BODY, hues: tuple[str, ...] = (Palette.SAPPHIRE, Palette.GOLD, Palette.VIOLET)):
        super().__init__()
        self.base = np.array(at, dtype=float)
        self.radius, self.facing, self.size, self.bar_width = radius, facing, size, bar_width
        self.pivot = self.base + OUT * pivot
        self.normal = rotate_vector(DOWN, facing, OUT)  # toward the camera; the needle turns about it
        self.u = rotate_vector(RIGHT, facing, OUT)  # the dial's own horizontal
        P = self.pivot
        self.angle = GAUGE_REST
        self.arc_green = self._arc(GAUGE_ZERO, GAUGE_LIMIT, Palette.CORRECT)
        self.arc_red = self._arc(GAUGE_LIMIT, GAUGE_END, Palette.WRONG)
        self.ticks = VGroup(self._tick(GAUGE_ZERO, Palette.FAINT), self._tick(GAUGE_LIMIT, Palette.MUTED))
        self.hub = Sphere(radius=0.075, resolution=(6, 12), **_flat(Palette.TEXT)).move_to(P)
        self.needle = Line(P, self._point(self.angle, 0.86), color=Palette.MUTED, stroke_width=7)
        self.add(self.arc_green, self.arc_red, self.ticks, self.needle, self.hub)
        self.limit_label = digits(limit_label, size, Palette.MUTED)
        self.labels = [(self.limit_label, lambda: self._point(GAUGE_LIMIT, 1.22), RIGHT * 0.7 + UP * 0.42)]
        self.inputs: dict[str, tuple] = {}
        self.fractions: dict[str, float] = {}
        z0 = pivot - radius - 0.6
        for k, (name, value, fraction) in enumerate(inputs):
            z = z0 - k * 0.5
            track = Prism(dimensions=[bar_width, 0.05, 0.2], **_tint(Palette.RULE)).move_to(self.base + OUT * z)
            fill = self._fill(fraction, hues[k % len(hues)], z)
            name_label = words(name, size, Palette.MUTED)
            value_label = digits(value, size, hues[k % len(hues)]) if value is not None else None
            self.inputs[name] = (track, fill, name_label, value_label)
            self.fractions[name] = fraction
            self.add(track, fill)
            self.labels.append((name_label, lambda t=track: t.get_left(), LEFT * 0.3 + LEFT * 0.14 * len(name)))
            if value_label is not None:
                self.labels.append((value_label, lambda t=track: t.get_right(), RIGHT * 0.3 + RIGHT * 0.14 * len(value)))
        self.readout = None
        self.extras: list[VMobject] = []
        self.rotate(facing, axis=OUT, about_point=self.base)

    # the dial's geometry (before the facing turn: in the x–z plane; after: turned with it)
    def _point(self, angle: float, r: float = 1.0):
        return self.pivot + self.radius * r * (np.cos(angle) * self.u + np.sin(angle) * OUT)

    def _arc(self, a: float, b: float, colour: str, r: float = 1.0, width: float = 9.0) -> VMobject:
        pts = [self.pivot + self.radius * r * (np.cos(t) * RIGHT + np.sin(t) * OUT) for t in np.linspace(a, b, 48)]
        return VMobject(stroke_color=colour, stroke_width=width, stroke_opacity=1.0).set_points_smoothly(pts)

    def _tick(self, angle: float, colour: str) -> Line:
        a = self.pivot + self.radius * 0.98 * (np.cos(angle) * RIGHT + np.sin(angle) * OUT)
        b = self.pivot + self.radius * 1.18 * (np.cos(angle) * RIGHT + np.sin(angle) * OUT)
        return Line(a, b, color=colour, stroke_width=5)

    def _fill(self, fraction: float, colour: str, z: float) -> Prism:
        w = max(0.015, fraction * self.bar_width)
        return Prism(dimensions=[w, 0.07, 0.22], **_tint(colour)).move_to(self.base + OUT * z + RIGHT * (w - self.bar_width) / 2)

    def top(self):
        return self._point(90 * DEGREES, 1.0)

    def port(self, name: str):
        """The left end of an input's track: where a wire arrives."""
        return self.inputs[name][0].get_left()

    @staticmethod
    def angle_of(value: float, limit: float) -> float:
        """The needle's angle for a value: 0 at GAUGE_ZERO, the limit at
        GAUGE_LIMIT, anything past the limit pinned at GAUGE_END."""
        if value > limit:
            return GAUGE_END
        return GAUGE_ZERO + (GAUGE_LIMIT - GAUGE_ZERO) * (value / limit)

    def aim(self, angle: float, colour: str, run_time: float = 0.8):
        """The needle swings to `angle` (a dial angle; angle_of() gives one
        for a value) and takes `colour` on the way."""
        delta = angle - self.angle
        self.angle = angle
        return _Swing(self.needle, delta, self.normal, self.pivot, colour, run_time=run_time)

    def set_input(self, name: str, fraction: float, run_time: float = 0.6, colour: str | None = None):
        """An input's bar fills (or collapses) to `fraction` of its track."""
        track, fill, _, _ = self.inputs[name]
        self.fractions[name] = fraction
        colour = colour or fill.get_fill_color()
        z = track.get_center()[2] - self.base[2]
        target = self._fill(fraction, colour, z).rotate(self.facing, axis=OUT, about_point=self.base)
        return Transform(fill, target, run_time=run_time, rate_func=ease_in_out_cubic)

    def glow(self, run_time: float = 0.8) -> AnimationGroup:
        """The green arc flashes: a wide faint copy swells over it and fades."""
        halo = self._arc(GAUGE_ZERO, GAUGE_LIMIT, Palette.CORRECT, width=26.0).rotate(self.facing, axis=OUT, about_point=self.base).set_stroke(opacity=0.0)
        self.add(halo)
        return AnimationGroup(halo.animate(rate_func=there_and_back).set_stroke(opacity=0.35), run_time=run_time)

    def bracket(self, colour: str = Palette.WRONG) -> VMobject:
        """A bracket along the red arc, outside it, with end caps: the
        multiplier's label is billboarded at bracket_anchor()."""
        arc = self._arc(GAUGE_LIMIT, GAUGE_END, colour, r=1.34, width=3.0)
        caps = VGroup(*[Line(self.pivot + self.radius * 1.26 * d, self.pivot + self.radius * 1.42 * d, color=colour, stroke_width=3.0) for d in (np.array([np.cos(a), 0, np.sin(a)]) for a in (GAUGE_LIMIT, GAUGE_END))])
        return VGroup(arc, caps).rotate(self.facing, axis=OUT, about_point=self.base)

    def bracket_anchor(self):
        return self._point((GAUGE_LIMIT + GAUGE_END) / 2, 1.45)


def wire(ball: Ball, gauge: Gauge, name: str = "rate", colour: str | None = None) -> Line:
    """A thin line from the ball to an input's port on the gauge: the ball's
    position drives that input. Draw it with Create."""
    return Line(ball.get_center(), gauge.port(name), color=colour or ball.colour, stroke_width=2.5)


def ground_line(a, b, colour: str = Palette.RULE, stroke_width: float = 2.0) -> Line:
    """A line drawn on the ground between two 3D points."""
    return Line(np.array(a, dtype=float), np.array(b, dtype=float), color=colour, stroke_width=stroke_width)


__all__ = [
    "DeckScene3D",
    "Lattice",
    "Ball",
    "drop_snap",
    "lift",
    "Tank",
    "fill",
    "drain",
    "pour",
    "Stack",
    "transfer",
    "Gate",
    "open",
    "shut",
    "Gauge",
    "wire",
    "GAUGE_ZERO",
    "GAUGE_LIMIT",
    "GAUGE_END",
    "GAUGE_REST",
    "orbit",
    "dolly",
    "look",
    "LOOKS",
    "STAGE_CENTRE",
    "slide",
    "dim",
    "ground_line",
]
