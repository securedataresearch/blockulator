# Direction v3: less text, more animation, 3D where things are things

The user (2026-10-29): "these animations for the attacks are cluttered and unclear" and "we generally in the whole presentation need to do more with animations (ideally 3d) and less with text". This supersedes the replay brief's "the whole story on one frame" (that produced 14-row posters at small sizes) and governs every scene from here.

## Principles
1. **One idea per section, and the section owns the frame.** When a section starts, the previous section's story elements leave (fade, slide out, or transform into the next thing); only the chrome stays (logos, title, caption) plus at most one carried-over object that the new beat acts on. The deck holds each section's last frame, so nothing needs to accumulate.
2. **Text budget per frame:** the title, at most one sentence (BODY), and labels attached to objects (a number or a word beside the thing it names). No tables, no row lists, no formulas longer than one line. The one number that matters is HERO size and is attached to the object it describes.
3. **Things are things.** A vault, a pool, a balance, a supply is a `Tank` (a cylinder with a liquid level) or a `Stack` of blocks; a loan or a take moves as blocks or liquid between tanks; a repetition is objects multiplying (37 mints = 37 blocks appearing), with a counter ticking beside them; a rounding step is a `Ball` on a `Lattice` (a 3D ruler with tick posts) that drops and rolls to a tick; a check is a `Gate` that opens green or shuts red. The camera orbits on a reveal and dollies on a zoom, never while a number is being read.
4. **Charts stay 2D** (slides 8, 9, 10: the grammar-of-graphics rule); concept and replay scenes go 3D. The site palette and the two fonts stay; materials are flat-shaded in palette colours, lit from the upper left; the background stays `Palette.BG`.
5. **Everything else holds:** numbers from `numbers()`/`LITERALS`, no ellipses, "half a unit", hero rows last and haloed, static chrome, the full spectrum, sections as before.

## The 3D vocabulary (`talk/scenes/vocab3d.py`)
- `class DeckScene3D(ThreeDScene)`: the same `setup()` chrome as `DeckScene` (logos, title helper, caption) added with `add_fixed_in_frame_mobjects`; `SECTIONS`/`section()`; `DRAWN` registration unchanged (`words/digits/markup` are reused; 3D labels are those Text objects `fixed_in_frame` or billboarded with `add_fixed_orientation_mobjects`).
- `Lattice(x_range, tick, length, depth)`: a number line lying in the ground plane with tick posts (thin prisms) at each tick, numbers as billboarded `digits()`; `.point(x)`; `.stretch(factor, about)` for dives (grid-stretch, never camera zoom past float64).
- `Ball(colour, radius)`; `drop_snap(ball, lattice, from_x, to_x, colour)`: the ball appears above `from_x`, falls to the line, rolls to `to_x`, flashes in the result colour (RED/EMERALD) with the `direction()` arrow drawn on the ground.
- `Tank(label, capacity, level, colour, radius, height)`: cylinder + liquid (a shorter cylinder) + label billboard with the quantity as `digits()`; `fill(tank, level, run_time)`, `drain(tank, level, run_time)`, `pour(src, dst, amount, run_time)` (a stream of small spheres from one rim to the other while both levels move).
- `Stack(n, colour, cols)`: blocks (cubes) appearing one per `dt`, with a counter billboard; `transfer(stack, to_point)`.
- `Gate(text)`: a barrier across the lattice with a label; `open(gate)` (EMERALD, lifts), `shut(gate)` (RED, drops with a `cross_mark`).
- `orbit(scene, phi, theta, run_time)`, `dolly(scene, zoom, run_time)`: camera moves with ease-in-out; a `look(scene, preset)` with three presets (`front`, `three_quarter`, `top`).
- `contact.py`/`check.py` work unchanged (a `DeckScene3D` counts as a scene; `dry_run` must accept it).

## The model: s06_resupply v3 (build this first; the user sees it before anything else is rebuilt)
Same `SECTIONS` ("price", "division", "floor", "check", "half", "multiplier"), same `numbers()` and claims (V12, C1), fewer drawn strings.
- `price`: the vault `Tank` (label `cvcrvUSD vault`, empty, `0 shares`) and the attacker's `Tank` (`2,000 crvUSD`); the attacker pours 2,000 crvUSD in; one tiny block `1 share` appears; the vault's label becomes the oracle price `2,000,000,000,000,000,000,001,998,001,998,001,998 per share` (HERO, the one number).
- `division`: the tanks slide aside; a `Lattice` 0–2 (integers) rises in three-quarter view; a `Ball` appears above x = 0.4999…, label `10^36 ÷ price = 0.4999999999999999999995 (to 22 decimals)`; dolly in until the gap to the half tick reads.
- `floor`: `drop_snap` to 0 in RED; label `floor`; the lattice's tick 0 lights.
- `check`: a `Gate` labelled `10,000,000 × 0 = 0 ≤ 95,000` opens EMERALD; a `reUSD` tank of `10,000,000` pours into the attacker's tank while the `1 share` block sits as collateral; caption cites the source line as now.
- `half`: the ball lifts back to 0.4999… in white; the gate's label becomes `499,999,999,999.9999999995004995 > 95,000` and it shuts RED with the cross; `insolvent`.
- `multiplier`: everything but the gate dims; `5,263,158× the limit` HERO.
Hold 3 s; the held frame of the last section is the slide.

## Then (after the user's look): the four replays (s06b–e) in the same vocabulary, each with one Tank per balance that matters and one Lattice for its decisive step; then the concept scenes s03 (formulas resolve to a 3D e^x surface), s04 (the lattice dive), s11, s14, s15 (the bit bar as a 3D bar), s16 (the error bar on the lattice), s18. s02, s05, s07, s12, s17, s19, s20 keep their 2D form (they are words and digits by nature) but lose any text that is not a label.
