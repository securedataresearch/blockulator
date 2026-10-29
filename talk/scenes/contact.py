"""A contact sheet of the deck: the last frame of every section.

Reads each rendered scene's section index (talk/build/videos/<scene>/
<quality>/sections/<Scene>.json, written by `manim --save_sections`),
extracts the last frame of every section's mp4 with ffmpeg into
talk/build/frames/<scene>_<nn>_<name>.png, checks the index's section
names against the scene's SECTIONS, and tiles the frames into
talk/build/contact.png, each labelled with its scene and section name
(ImageMagick's montage where installed, else PIL).

    uv run --with pillow python talk/scenes/contact.py [--quality 1080p30]
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
BUILD = ROOT / "talk" / "build"
FRAMES = BUILD / "frames"
COLUMNS = 4


def scenes() -> list[str]:
    return sorted(p.stem for p in HERE.glob("s[0-9][0-9]*_*.py"))


def sections_of(scene: str) -> list[str]:
    from manim import config  # noqa: F401  (vocab sets the deck's config)

    import vocab

    mod = importlib.import_module(scene)
    classes = [c for c in vars(mod).values() if isinstance(c, type) and issubclass(c, vocab.DeckScene) and c is not vocab.DeckScene and c.__module__ == mod.__name__]
    assert len(classes) == 1, (scene, classes)
    return list(classes[0].SECTIONS)


def last_frame(video: Path, png: Path) -> None:
    png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.1", "-i", str(video), "-frames:v", "1", "-update", "1", str(png)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default=None, help="the quality folder, e.g. 1080p30 (default: the one with the newest index)")
    args = ap.parse_args()
    tiles: list[tuple[Path, str]] = []
    bad = 0
    for scene in scenes():
        qualities = sorted((BUILD / "videos" / scene).glob("*/sections/*.json"), key=lambda p: p.stat().st_mtime)
        if args.quality:
            qualities = [p for p in qualities if p.parent.parent.name == args.quality]
        if not qualities:
            print(f"no sections rendered for {scene}", file=sys.stderr)
            bad += 1
            continue
        index = qualities[-1]
        entries = json.loads(index.read_text())
        names = [e["name"] for e in entries]
        want = sections_of(scene)
        if names != want:
            print(f"SECTIONS MISMATCH {scene}: index {names} != SECTIONS {want}", file=sys.stderr)
            bad += 1
        for i, e in enumerate(entries):
            png = FRAMES / f"{scene}_{i:02d}_{e['name']}.png"
            last_frame(index.parent / e["video"], png)
            tiles.append((png, f"{scene} · {i} {e['name']} · {float(e['duration']):.1f} s"))
            print(f"{scene:14} {i:2} {e['name']:14} {float(e['duration']):6.1f} s")
    if not tiles:
        return 1
    out = BUILD / "contact.png"
    if shutil.which("montage"):
        cmd = ["montage", "-background", "#0c0e10", "-fill", "#e2e3df", "-pointsize", "16", "-geometry", "480x270+8+8", "-tile", f"{COLUMNS}x"]
        for png, label in tiles:
            cmd += ["-label", label, str(png)]
        subprocess.run(cmd + [str(out)], check=True)
    else:
        from PIL import Image, ImageDraw

        w, h, pad, cap = 480, 270, 8, 22
        rows = -(-len(tiles) // COLUMNS)
        sheet = Image.new("RGB", (COLUMNS * (w + 2 * pad), rows * (h + cap + 2 * pad)), "#0c0e10")
        draw = ImageDraw.Draw(sheet)
        for k, (png, label) in enumerate(tiles):
            x, y = (k % COLUMNS) * (w + 2 * pad) + pad, (k // COLUMNS) * (h + cap + 2 * pad) + pad
            sheet.paste(Image.open(png).convert("RGB").resize((w, h)), (x, y))
            draw.text((x, y + h + 4), label, fill="#e2e3df")
        sheet.save(out)
    print(out)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
