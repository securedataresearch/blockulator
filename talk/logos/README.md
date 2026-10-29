# Logos on every frame

- `blockulator.png`: the Blockulator mark, white on transparent (a copy of `static/blockulator.png`). Top-left of every frame, with the slide title to its right.
- `sdr.png`: the Secure Data Research mark, white on transparent, thresholded from `sdr-source.jpg` (the mark on black) at 128. Top-right of every frame.

`DeckScene.setup()` (talk/scenes/vocab.py) draws both at `LOGO_HEIGHT` (0.55 scene units, opacity 0.92), their outer corners at `LOGO_CORNER` (±6.75, 3.6), as `self.chrome`, before anything else; `DeckScene.title()` places a slide's title `TITLE_GAP` (0.3) to the right of the left mark, centred on its height. The pixel files: `blockulator.png` 593 × 492 (the mark reaches every edge of its box), `sdr.png` 397 × 400 (a transparent strip of 21 px at the top).
