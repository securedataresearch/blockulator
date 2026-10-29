# Standing rules for every scene (pasted into every builder prompt)

These are the user's rules. They are not negotiable and they are not summarised; a builder who cannot satisfy one reports it, and does not work around it.

## Facts
- **No typed numbers.** Every digit drawn comes from the scene's `numbers()` (which reads JSON through a `vocab.py` loader) or from the module's `LITERALS = {string: claim_id}` table that the brief gives you. `check.py` dry-runs `construct`, collects every drawn string through `vocab.DRAWN`, and fails on any digit-bearing string outside those two. A string with no claim id is a REPORT item: you do not draw it, you list it in your report.
- **Report facts, don't fix facts.** If a number in the brief does not match the JSON, if a loader returns something else, if a claim looks wrong: stop that string, keep going on the rest, and report it. Never adjust a value to make a check pass.
- **No ellipses in numbers.** A number is complete in a stated format: an 18-decimal value shows all 18 decimals; a binary word shows its full fraction in hex; an irrational is shown "to N decimals". Never "…".
- **Count what the eye can count.** A digit label is the matching-prefix count against the truth ("21 of 36 digits", "2 right · wrong at the 3rd decimal"). The log measure stays in the ledger.
- **Name the mechanism, not the vendor.** A library's documented precision is never presented as a defect. Protocols in the incidents are named; libraries on charts are labelled by the registry's label.
- **All 17 libraries on any chart** (`talk_libs()`); a library with no value is listed with its reason ("no exp", "rejects negative inputs", "not offered", "no result"), never silently dropped.

## Vocabulary and colour
- One visual language: a number line (`GridLine`) is the grid, a value is a `Dot`, rounding is `snap()`. `measure()` brackets a gap, `direction()` shows which way a value went, `check_mark()`/`cross_mark()` judge, `halo()`/`glow_line()`/`glow_bar()` mark the hero. `Chart` for axes. New primitives only when the brief names them, and they go into `vocab.py`, not inline.
- Colour by meaning: `EXACT` (white) the exact value, `WRONG` (red) a wrong result, `CORRECT` (emerald) the correctly rounded one. Families on charts: `FAMILY_COLOUR`. The brief says which meaning white carries on its slide, because FP19's family colour and EXACT are both white; the other meaning is not used on that slide.
- **Never colour alone:** wrong = red AND a cross or an arrow; correct = emerald AND a halo or a tick.
- **Blockulator is the hero:** FP19 and FP127 rows, lines and dots are drawn last, with halos, and the closing line names the margin in digits.
- **Zoom from real units:** a number line starts at a scale people recognise and dives to the grid. Dive by stretching the grid, never by moving the camera (a 10^39 camera zoom overflows float64 and thickens strokes).
- "half a unit", never "½" (the font has no glyph). Avoid "√"; write the chain in words or tokens.
- Always more impressive: staggered reveals, halos, ticking counters, depth; never static text where a drawn thing can carry it.

## Chrome and colour (user, 2026-10-29)
- **Titles, axes and keys are always visible, like the logos.** They are on the first frame of section 0 (drawn with `add`, not animated) and never revealed, faded, moved or dimmed; only the data and the story elements animate. A chart's axes, gridlines, axis titles and its legend (every series that will appear, in its colour) are complete before the first dot lands.
- **Use the complete spectrum.** Distinct things get distinct hues from the whole palette (EMERALD, GOLD, SAPPHIRE, VIOLET, SLATE, RED, TEXT, plus MUTED/FAINT for de-emphasis), so a slide reads at a glance. The fixed meanings keep theirs: RED = wrong, EMERALD = FP127/correct, TEXT = FP19/exact; everything else in a scene (incidents, protocols, formulas, rows, steps) takes the remaining hues consistently within the scene and across the deck (one protocol = one hue everywhere; one library family = its family colour). Never two categories in one hue on the same slide; never a hue with no meaning.

## Legibility (1920×1080, a dark room, the back row)
- `SIZE_CAPTION = 20` (the source caption only), `SIZE_BODY = 32` (everything else), `SIZE_HERO = 48` (the one hero number or line). These are manim font sizes in scene units, not pixels: the frame is 14.2 units wide, a mono character at size 32 is about 0.26 units, so a mono line holds about 46 characters at BODY and a 42-character address does not fit at HERO (draw it at the largest size that fits, and say so in the report). Nothing below CAPTION, ever; below BODY only when a string cannot fit, reported.
- 5% safe area on every edge. One idea per section. Nothing smaller than `SIZE_CAPTION`, ever.

## Sections (the deck steps one click per section)
- `SECTIONS = (...)` on the class; `self.section(i)` in order; the brief names them. Section 0 autoplays when the slide arrives; each later section plays on a click and then HOLDS its last frame. The last section's last frame is the slide's poster and its PDF page: it must read as a finished slide. No fade-out, no reset to background.
- Target seconds per section are in the brief; a section that runs long is a report item, not a crime.

## Process
- Work only in the worktree you are given, on branch `talk-deck`. Commit as you go; push at the end. End commit messages with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Do not edit `docs/benchmarks/*`, `scripts/replays/*`, `contracts/*`, `research_notes/*`, or another scene's file. Loaders go in `vocab.py`; new primitives go in `vocab.py`.
- Iterate at `-ql` (480p). One `-qh` render at the end. Renders run one at a time.
- Verify before you report: `uv run talk/scenes/check.py sNN_name` green; `make anim SCENE=sNN_name` green; last-frame PNGs for every section (`make contact` or ffmpeg `-sseof -0.1`).
- Deliver: the scene file; its `numbers()`, `LITERALS`, `SECTIONS`; a `check.py` expectation that recomputes the numbers by a second route; a row in `talk/scenes/README.md`'s table; the PNGs under `talk/build/frames/`.
- Report in at most eight lines: commit hash; section names with seconds; REPORT items (strings with no id, mismatches); judgment calls; rules you could not satisfy and why. Nothing else.
