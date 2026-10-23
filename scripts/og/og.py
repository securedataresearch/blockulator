"""Draw static/og.png, the 1200x630 link-preview card.

    make og        (uv run --with pillow python scripts/og/og.py)

The mark is static/icon-512.png; the type is DejaVu Sans, found through
fontconfig. Colours are site.css tokens: --ink for the ground, --white for
the name, --g-300 for the eyebrow and the line under the name.
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "og.png"
MARK = ROOT / "static" / "icon-512.png"

W, H = 1200, 630
INK, WHITE, G300 = "#0a0a0a", "#ffffff", "#a3a3a3"

EYEBROW = "SECURE DATA RESEARCH"
TITLE = "blockulator"
LINES = ["FP127 and FP19: math for the EVM", "that rounds once and never runs out"]


def font(pattern: str, size: int) -> ImageFont.FreeTypeFont:
    path = subprocess.run(
        ["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True, check=True
    ).stdout
    if "DejaVu" not in path:
        raise SystemExit(f"fc-match {pattern!r} gave {path!r}; install DejaVu fonts")
    return ImageFont.truetype(path, size)


def main() -> None:
    im = Image.new("RGB", (W, H), INK)
    mark = Image.open(MARK).convert("RGB").resize((370, 370), Image.LANCZOS)
    im.paste(mark, (75, (H - 370) // 2))

    d = ImageDraw.Draw(im)
    f_eye = font("DejaVu Sans Mono:bold", 24)
    f_title = font("DejaVu Sans:bold", 76)
    f_sub = font("DejaVu Sans", 33)

    # Rows top to bottom: (text, font, colour, letter spacing, gap below the ink).
    rows = [(EYEBROW, f_eye, G300, 3, 30), (TITLE, f_title, WHITE, 0, 44)]
    rows += [(t, f_sub, G300, 0, 25) for t in LINES]
    rows[-1] = rows[-1][:4] + (0,)

    def ink(text, f, sp):
        x0, y0, x1, y1 = f.getbbox(text)
        return y0, y1 - y0, x1 + sp * (len(text) - 1)

    total = sum(ink(t, f, sp)[1] + gap for t, f, _, sp, gap in rows)
    x, y = 476, (H - total) // 2
    for text, f, colour, sp, gap in rows:
        top, height, _ = ink(text, f, sp)
        if sp:
            cx = x
            for ch in text:
                d.text((cx, y - top), ch, font=f, fill=colour)
                cx += f.getlength(ch) + sp
        else:
            d.text((x, y - top), text, font=f, fill=colour)
        y += height + gap

    im.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} {W}x{H}")


if __name__ == "__main__":
    main()
