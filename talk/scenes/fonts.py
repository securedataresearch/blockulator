"""Regenerate talk/fonts/*.ttf from the site's static/fonts/*.woff2.

Pango (manim's text engine) loads TTF/OTF, not WOFF2, so the site's fonts
are unwrapped once with fontTools and committed next to their licence:

    make talk-fonts     (uv run --with fonttools --with brotli python talk/scenes/fonts.py)

Instrument Sans and JetBrains Mono are both under the SIL Open Font
License 1.1; talk/fonts/OFL.txt carries the copyright lines read from the
fonts' own name tables and the licence text.
"""

from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
PAIRS = {
    "instrument-sans.woff2": "InstrumentSans.ttf",
    "instrument-sans-italic.woff2": "InstrumentSans-Italic.ttf",
    "jetbrains-mono.woff2": "JetBrainsMono.ttf",
}


def main() -> None:
    out = ROOT / "talk" / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    for src, dst in PAIRS.items():
        font = TTFont(ROOT / "static" / "fonts" / src)
        font.flavor = None  # woff2 -> plain sfnt
        font.save(out / dst)
        name = font["name"]
        print(f"{dst}: {name.getDebugName(4)} — {name.getDebugName(0)} — {name.getDebugName(14)}")


if __name__ == "__main__":
    main()
