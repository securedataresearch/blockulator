# Logos on every frame

- `blockulator.png`: the Blockulator mark, white on transparent (a copy of `static/blockulator.png`). Top-left of every frame, with the slide title to its right.
- `sdr.png`: the Secure Data Research mark, white on transparent, thresholded from `sdr-source.jpg` (the mark on black) at 128. Top-right of every frame.

`DeckScene.setup()` draws both at `LOGO_HEIGHT` inside the safe area; `DeckScene.title()` places a slide's title beside the left mark.
