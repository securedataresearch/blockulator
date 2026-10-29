"""The deck's 3D vocabulary: things are things (talk/briefs/3d-direction.md).

A vault, a pool, a balance is a Tank (a glass cylinder with a liquid
level); a count of things is a Stack of blocks; a rounding step is a Ball
on a Lattice (a number line lying on the ground with tick posts) that
drops and rolls to a tick; a check is a Gate across the lattice that
opens EMERALD or shuts RED. The camera orbits on a reveal and dollies on
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
    Sphere,
    Succession,
    ThreeDScene,
    Transform,
    VGroup,
    VMobject,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_in_quad, ease_out_cubic, linear

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
    `capacity` (the full height). .glass, .liquid, .name, .quantity;
    .labels for show(); top()/foot()/rim(side) are anchor points read from
    the glass, so they follow a slide."""

    def __init__(self, label: str, capacity: float = 1.0, level: float = 0.0, colour: str = Palette.GOLD, radius: float = 0.9, height: float = 2.0, quantity: str | None = None, at=ORIGIN, glass: str = Palette.SLATE, size: float = SIZE_BODY):
        super().__init__()
        self.capacity, self.colour, self.radius, self.height = capacity, colour, radius, height
        self.level = level
        self.glass = _cylinder(radius, height, glass, GLASS_OPACITY, base=at)
        self.liquid = self._liquid_at(level, colour)
        self.add(self.liquid, self.glass)
        self.name = words(label, size, Palette.MUTED)
        self.quantity = digits(quantity, size, colour) if quantity is not None else None
        self.labels = [(self.name, self.foot, DOWN * 0.42)]
        if self.quantity is not None:
            self.labels.append((self.quantity, self.top, UP * 0.42))

    def fade_to(self, opacity: float):
        """The tank at `opacity` (1 is as built): the glass keeps its faint
        share of it. In place; returns self."""
        self.glass.set_fill(opacity=GLASS_OPACITY * opacity).set_stroke(opacity=GLASS_OPACITY * opacity)
        self.liquid.set_fill(opacity=opacity).set_stroke(opacity=opacity)
        return self

    def foot(self):
        return self.glass.get_center() + OUT * (-self.height / 2)

    def top(self):
        return self.glass.get_center() + OUT * (self.height / 2)

    def rim(self, side=RIGHT):
        return self.top() + np.array(side, dtype=float) * self.radius

    def _liquid_at(self, level: float, colour: str) -> Cylinder:
        h = max(0.02, level / self.capacity * (self.height - 0.08))
        return _cylinder(self.radius * 0.93, h, colour, 1.0, base=self.foot() + OUT * 0.04 if hasattr(self, "glass") else ORIGIN)

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


def pour(src: Tank, dst: Tank, amount: float, run_time: float = 2.0, drops: int = 9):
    """`amount` (in capacity units) leaves src and lands in dst: a stream
    of small spheres in src's colour arcs from src's rim to dst's rim
    while both levels move (dst takes src's colour). Returns one animation."""
    colour = src.colour
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
        dst.set_level(dst.level + amount, run_time, colour),
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

    def __init__(self, text: str, lattice: Lattice | None = None, x: float = 0.0, at=None, width: float = 2.2, height: float = 1.5, colour: str = Palette.MUTED, size: float = SIZE_BODY, mono: bool = True, label_lift: float = 0.42, mark_lift: float = 1.0):
        super().__init__()
        self.label_lift, self.mark_lift = label_lift, mark_lift
        base = np.array(at, dtype=float) if at is not None else lattice.point(x)
        self.width, self.height, self.colour = width, height, colour
        self.slab = Prism(dimensions=[0.12, width, height], **_tint(colour, 0.95)).move_to(base + OUT * height / 2)
        post = lambda side: Prism(dimensions=[0.1, 0.1, height + 0.5], **_tint(Palette.RULE)).move_to(base + side * width / 2 + OUT * (height + 0.5) / 2)  # noqa: E731
        self.posts = VGroup(post(UP), post(DOWN))
        self.add(self.posts, self.slab)
        self.label = (digits if mono else words)(text, size, colour)
        self.mark = None
        self.extras: list[VMobject] = []
        self.labels = [(self.label, self.top, UP * label_lift)]

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
            gate.label.animate.set_color(Palette.CORRECT),
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
    anims = [Transform(gate.slab, down, rate_func=ease_in_quad), gate.label.animate.set_color(Palette.WRONG), Create(gate.mark)]
    if old is not None:
        anims.append(FadeOut(old))
    return AnimationGroup(*anims, run_time=run_time)


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
    "orbit",
    "dolly",
    "look",
    "LOOKS",
    "STAGE_CENTRE",
    "slide",
    "dim",
    "ground_line",
]
