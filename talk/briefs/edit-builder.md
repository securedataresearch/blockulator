# Edit-pass builder: how to work (read with RULES.md and edit-pass.md)

The user, after watching every slide: "these animations are super impressive, the talk is moving in the right direction. But the slides are FAR too busy. There is just too much going on everywhere. It's time to edit." You are editing scenes to that standard. The two approved models are `s02_exp40.py` and `s06c_balancer_v2.py` (commit 55a55a5): read both before you start, and look at their frames in `talk/build/frames/s02_exp40_*.png` and `s06c_balancer_v2_*.png`. Match their density, not more.

## Read first
`talk/briefs/RULES.md` (the section "The edit pass" overrides older habits), `talk/briefs/edit-pass.md` (the per-slide table: your rows), `talk/scenes/README.md`, your scene file(s) and their current frames in `talk/build/frames/`.

## The budget, for EVERY held frame (not only the poster)
≤ 12 lit text strings, ≤ 260 glyphs, 0 ghosts (text left on screen below fill opacity 0.5). Measure: `uv run talk/scenes/census.py <scene>`. A chart's key (the 17-library legend) is chrome and does not count: the user decided all 17 libraries stay on every chart, as one compact CAPTION-size column, with the "no value because" reasons as ONE line inside it. If census counts the key, tag those mobjects so it does not: add them to `self.key` (a VGroup you create) and report it; the coordinator will teach census to skip `self.key`.

## The replay template (s06c)
Title is fixed chrome. The one balance or object that matters, drawn simply. ONE GridLine for the decisive rounding with the operands typing in and the result "(to N decimals)". A red direction arrow + the rounding word + one red line with a cross for the effect. A counter with N red dots (or blocks) for the repetition. The loss alone at 72. The poster: the line again with Blockulator's value in emerald with a halo, and ONE emerald line with a tick saying what Blockulator does and the consequence ("would" when it is a projection, not an observation). Each beat fades out its own pieces.

## Rules that bite
- Every drawn digit from `numbers()` or `LITERALS` (check.py). Remove unused LITERALS. Keep your `expect_<scene>` in `talk/scenes/check.py` correct by a second route; edit ONLY your function(s) there (other builders edit theirs in the same file at the same time: use targeted edits, never rewrite the file).
- No `caption_now`/`caption` calls: provenance goes to your report for the notes.
- No ellipses; "to N decimals"; wrong = red + cross/arrow; correct = emerald + halo/tick; "half a unit".
- Never shrink type to fit: cut instead. Labels ≥ BODY 32; a lone hero 64–72.
- Keep section NAMES if you can (slides.yaml maps the script's cues to them). If you merge or drop sections, report the new SECTIONS and which old cue each new section carries. ≤ 4 sections per slide (≤ 6 for a replay is tolerated if the names stay).
- Do NOT edit `talk/deck/slides.yaml`, `vocab.py` (report a needed primitive), other builders' scenes, docs/, scripts/, contracts/, research_notes/.
- Do NOT git commit or push: the coordinator commits. Other builders share this worktree.
- Facts: if the data and the brief disagree, the data wins; report it. Never change a value to pass a check.

## Render and verify
Iterate at `-ql` (`uv run manim -ql talk/scenes/<scene>.py <Class>`). One final `make anim SCENE=<scene>` (-qh). Delete your scene's old `talk/build/frames/<scene>_*.png`, then extract each section's last frame: `ffmpeg -v error -sseof -0.1 -i <section>.mp4 -frames:v 1 -update 1 talk/build/frames/<scene>_NN_<name>.png` from `talk/build/videos/<scene>/1080p30/sections/`. LOOK at every PNG yourself. Green: `uv run talk/scenes/check.py <scene>` and census with every held frame under budget.

## Report (≤ 12 lines per scene)
SECTIONS with seconds; census line per held frame; check.py result; strings moved to notes, verbatim, by section (provenance included); new SECTIONS ↔ cue mapping if changed; judgement calls; rules not met and why.
