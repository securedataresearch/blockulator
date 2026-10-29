"""Build the deck of *The End of Rounding Errors* from talk/deck/slides.yaml.

    uv run talk/deck/build.py [--pdf] [--quality 1080p30]

For every slide the YAML names a scene (module.Class under talk/scenes/)
and its sections, each with the script sentence spoken over it. The build
asserts, per scene, that three lists agree: the section names in manim's
index (talk/build/videos/<module>/<quality>/sections/<Class>.json, written
by `make anim`), the class's SECTIONS, and slides.yaml. Every disagreement
is reported (scene by scene, not the first one only) and the build fails
at the end; a scene with no render or no module yet is reported as "not
rendered" and gets a placeholder slide, so the deck always builds.

It writes, next to this file:

- index.html: a reveal.js deck (vendored under vendor/reveal.js/, opened
  from file:// offline). One <section> per slide; inside it one <video>
  per scene section, the first visible at once, each later one a reveal
  fragment, so one click plays one section and the clip then holds its
  last frame (no loop; the title slide alone loops). The mp4s are
  referenced by relative path under talk/build/, not copied.
- script.md: the spoken script in order, one heading per slide, a ▶ mark
  with the section's seconds before each cue, cumulative time per slide.
  Printed on paper for the talk.
- talk.pdf (with --pdf): one page per slide, the last section's last
  frame (ffmpeg -sseof -0.1) composed with img2pdf; a placeholder page
  (the title on the dark background, PIL) where there is no render.
"""

from __future__ import annotations

import argparse
import html
import importlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCENES = ROOT / "talk" / "scenes"
BUILD = ROOT / "talk" / "build"
VIDEOS = BUILD / "videos"
FRAMES = BUILD / "deck"  # last frames for the PDF
FONTS = ROOT / "talk" / "fonts"
VENDOR = "vendor/reveal.js/dist"

BG = "#0c0e10"
TEXT = "#f6f6f3"
FAINT = "#9a9d97"

sys.path.insert(0, str(SCENES))


# ------------------------------------------------------------------ data --
@dataclass
class Section:
    name: str
    cue: str
    video: Path | None = None  # absolute path of the clip, when rendered
    seconds: float | None = None


@dataclass
class Slide:
    number: int
    title: str
    module: str
    cls: str
    loop: bool
    sections: list[Section]
    notes: list[str]
    rendered: bool = False
    problems: list[str] = field(default_factory=list)

    @property
    def scene(self) -> str:
        return f"{self.module}.{self.cls}"

    @property
    def seconds(self) -> float | None:
        if not self.rendered:
            return None
        return sum(s.seconds or 0.0 for s in self.sections)


def read_slides(path: Path) -> list[Slide]:
    raw = yaml.safe_load(path.read_text())
    slides: list[Slide] = []
    for i, entry in enumerate(raw, start=1):
        assert entry["slide"] == i, f"slides.yaml: entry {i} is numbered {entry['slide']}"
        module, cls = entry["scene"].split(".")
        sections = [Section(str(s["name"]), str(s.get("cue", "") or "")) for s in entry["sections"]]
        assert sections, f"slide {i}: no sections"
        slides.append(
            Slide(
                number=i,
                title=str(entry["title"]),
                module=module,
                cls=cls,
                loop=bool(entry.get("loop", False)),
                sections=sections,
                notes=[str(n) for n in entry.get("notes", []) or []],
            )
        )
    return slides


# --------------------------------------------------------------- checks --
def class_sections(slide: Slide) -> list[str] | None:
    """The scene class's SECTIONS, or None when the module does not exist yet."""
    try:
        mod = importlib.import_module(slide.module)
    except ModuleNotFoundError as e:
        if e.name == slide.module:
            return None
        raise
    cls = getattr(mod, slide.cls, None)
    if cls is None:
        slide.problems.append(f"module {slide.module} has no class {slide.cls}")
        return None
    return list(getattr(cls, "SECTIONS", ()))


def find_index(slide: Slide, quality: str | None) -> Path | None:
    folder = VIDEOS / slide.module
    if quality:
        p = folder / quality / "sections" / f"{slide.cls}.json"
        return p if p.exists() else None
    candidates = sorted(folder.glob(f"*/sections/{slide.cls}.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def diff(label_a: str, a: list[str], label_b: str, b: list[str]) -> str | None:
    if a == b:
        return None
    return f"{label_a} {a} != {label_b} {b}"


def resolve(slide: Slide, quality: str | None) -> None:
    """Fill in the clips and durations; record every disagreement."""
    yaml_names = [s.name for s in slide.sections]
    cls_names = class_sections(slide)
    index = find_index(slide, quality)
    if cls_names is not None:
        d = diff("SECTIONS", cls_names, "slides.yaml", yaml_names)
        if d:
            slide.problems.append(d)
    if index is None:
        slide.problems.append("not rendered" + ("" if cls_names is not None else " (no scene module)"))
        return
    entries = json.loads(index.read_text())
    index_names = [e["name"] for e in entries]
    d = diff("index", index_names, "slides.yaml", yaml_names)
    if d:
        slide.problems.append(d)
    if cls_names is not None:
        d = diff("index", index_names, "SECTIONS", cls_names)
        if d:
            slide.problems.append(d)
    if index_names != yaml_names:
        slide.problems.append("not rendered (index disagrees; placeholder used)")
        return
    for section, entry in zip(slide.sections, entries):
        section.video = index.parent / entry["video"]
        section.seconds = float(entry["duration"])
        if not section.video.exists():
            slide.problems.append(f"index names a missing clip {entry['video']}")
    if any(s.video is None or not s.video.exists() for s in slide.sections):
        return
    slide.rendered = True


# ----------------------------------------------------------------- html --
def rel(path: Path) -> str:
    return path.relative_to(HERE, walk_up=True).as_posix()


def slide_html(slide: Slide, total: int) -> str:
    corner = f'<div class="deck-corner">{html.escape(slide.title)} · {slide.number} / {total}</div>'
    if slide.rendered:
        clips = []
        for k, section in enumerate(slide.sections):
            assert section.video is not None
            attrs = ["class=\"clip" + (" fragment" if k else "") + "\"", "muted", "playsinline", 'preload="auto"']
            if slide.loop:
                attrs.append("loop")
            attrs.append(f'data-src="{html.escape(rel(section.video))}"')
            attrs.append(f'data-section="{html.escape(section.name)}"')
            clips.append(f"    <video {' '.join(attrs)}></video>")
        body = "\n".join(clips)
        klass = "deck-slide"
    else:
        items = []
        for k, section in enumerate(slide.sections):
            cue = html.escape(section.cue) if section.cue else "<em>(no cue)</em>"
            items.append(f'      <li class="{"fragment" if k else ""}"><span class="name">{html.escape(section.name)}</span>{cue}</li>')
        body = (
            f'    <div class="ph">\n      <h1>{html.escape(slide.title)}</h1>\n'
            f'      <div class="ph-note">{html.escape(slide.scene)} · not rendered</div>\n      <ol>\n' + "\n".join(items) + "\n      </ol>\n    </div>"
        )
        klass = "deck-slide placeholder"
    return f'  <section class="{klass}" data-slide="{slide.number}">\n{body}\n    {corner}\n  </section>'


SCRIPT_JS = r"""
// One click, one section. A clip plays when its fragment (or its slide)
// becomes visible and then holds its last frame: no loop, so the <video>
// simply pauses on the final frame when it ends. The title slide's clip
// carries `loop`. A fragment shown again starts from 0; leaving a slide
// pauses everything on it. Clips are lazy (data-src): reveal loads the
// current slide's clips (viewDistance 1) and we preload the next slide's
// first clip so it starts on arrival.
function load(v) {
  if (v.dataset.src) {
    v.setAttribute('src', v.dataset.src);
    v.setAttribute('data-lazy-loaded', '');
    v.removeAttribute('data-src');
    v.load();
  }
}
function playFromStart(v) {
  load(v);
  try { v.currentTime = 0; } catch (e) {}
  const p = v.play();
  if (p && p.catch) p.catch(() => {});
}
function holdAtEnd(v) {
  load(v);
  const seek = () => { v.pause(); if (isFinite(v.duration)) v.currentTime = Math.max(0, v.duration - 0.05); };
  if (v.readyState >= 1) seek(); else v.addEventListener('loadedmetadata', seek, { once: true });
}
function reset(v) { v.pause(); try { v.currentTime = 0; } catch (e) {} }
function pauseAll(slide) { slide.querySelectorAll('video').forEach(v => v.pause()); }
function arrive(slide) {
  const fromRight = !!slide.querySelector('video.clip.fragment.visible');  // stepping back in: every shown clip holds
  slide.querySelectorAll('video.clip').forEach(v => {
    if (!v.classList.contains('fragment')) { if (fromRight) holdAtEnd(v); else playFromStart(v); }
    else if (v.classList.contains('visible')) holdAtEnd(v);
    else reset(v);
  });
  const next = slide.nextElementSibling;
  if (next) { const first = next.querySelector('video.clip'); if (first) load(first); }
}
Reveal.initialize({
  width: 1920, height: 1080, margin: 0, minScale: 0.05, maxScale: 4,
  center: false, controls: false, progress: false, slideNumber: false, hash: false,
  transition: 'none', backgroundTransition: 'none', fragments: true,
  autoPlayMedia: false, viewDistance: 1, preloadIframes: false, help: false,
}).then(() => {
  Reveal.on('ready', e => arrive(e.currentSlide));
  Reveal.on('slidechanged', e => { if (e.previousSlide) pauseAll(e.previousSlide); arrive(e.currentSlide); });
  Reveal.on('fragmentshown', e => e.fragments.forEach(f => { if (f.matches('video.clip')) playFromStart(f); }));
  Reveal.on('fragmenthidden', e => e.fragments.forEach(f => { if (f.matches('video.clip')) reset(f); }));
  arrive(Reveal.getCurrentSlide());
});
"""


def write_html(slides: list[Slide], out: Path) -> None:
    sections = "\n".join(slide_html(s, len(slides)) for s in slides)
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The End of Rounding Errors</title>
<link rel="stylesheet" href="{VENDOR}/reset.css">
<link rel="stylesheet" href="{VENDOR}/reveal.css">
<link rel="stylesheet" href="deck.css">
</head>
<body>
<div class="reveal">
<div class="slides">
{sections}
</div>
</div>
<script src="{VENDOR}/reveal.js"></script>
<script>{SCRIPT_JS}</script>
</body>
</html>
"""
    out.write_text(doc)


# --------------------------------------------------------------- script --
def mmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def write_script(slides: list[Slide], out: Path) -> None:
    lines = [
        "# The End of Rounding Errors: the spoken script, with the clicks",
        "",
        "One ▶ is one click: it starts the named section (its motion lasts the",
        "seconds shown) and the sentence after it is spoken over it. Section 0",
        "starts when the slide arrives. Times are the clips' motion only, not",
        "the speech; the cumulative time is where each slide begins.",
        "",
    ]
    clock = 0.0
    for slide in slides:
        total = slide.seconds
        head = f"## {slide.number}. {slide.title}"
        meta = f"{slide.scene} · " + (f"{total:.0f} s of motion · at {mmss(clock)}" if total is not None else "not rendered")
        lines += [head, "", f"*{meta}*", ""]
        for k, section in enumerate(slide.sections):
            secs = f"{section.seconds:.1f} s" if section.seconds is not None else "— s"
            start = "" if k else " (on arrival)"
            lines.append(f"▶ `{section.name}` · {secs}{start}")
            lines.append("")
            lines.append(section.cue if section.cue else "*(no sentence: let it play)*")
            lines.append("")
        for note in slide.notes:
            lines += [f"> {note}", ""]
        if total is not None:
            clock += total
    lines += [f"Motion in total: {mmss(clock)} over the rendered slides.", ""]
    out.write_text("\n".join(lines))


# ------------------------------------------------------------------ pdf --
def last_frame(video: Path, png: Path) -> None:
    png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.1", "-i", str(video), "-frames:v", "1", "-update", "1", "-pix_fmt", "rgb24", str(png)],
        check=True,
    )


def placeholder_frame(slide: Slide, slides: list[Slide], png: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    png.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (1920, 1080), BG)
    d = ImageDraw.Draw(im)
    sans = ImageFont.truetype(str(FONTS / "InstrumentSans.ttf"), 72)
    mono = ImageFont.truetype(str(FONTS / "JetBrainsMono.ttf"), 26)
    d.text((96, 420), slide.title, font=sans, fill=TEXT)
    d.text((96, 530), f"{slide.scene} · not rendered", font=mono, fill=FAINT)
    d.text((96, 580), " · ".join(s.name for s in slide.sections), font=mono, fill=FAINT)
    d.text((1920 - 40, 1080 - 28), f"{slide.title} · {slide.number} / {len(slides)}", font=mono, fill=FAINT, anchor="rd")
    im.save(png)


def write_pdf(slides: list[Slide], out: Path) -> None:
    import img2pdf

    pages = []
    for slide in slides:
        png = FRAMES / f"{slide.number:02d}_{slide.module}.png"
        if slide.rendered:
            last = slide.sections[-1].video
            assert last is not None
            last_frame(last, png)
        else:
            placeholder_frame(slide, slides, png)
        pages.append(str(png))
    out.write_bytes(img2pdf.convert(pages))


# ----------------------------------------------------------------- main --
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pdf", action="store_true", help="also write talk.pdf")
    ap.add_argument("--quality", default=None, help="the render folder to use, e.g. 1080p30 (default: the newest index per scene)")
    args = ap.parse_args()

    slides = read_slides(HERE / "slides.yaml")
    for slide in slides:
        resolve(slide, args.quality)

    write_html(slides, HERE / "index.html")
    write_script(slides, HERE / "script.md")
    if args.pdf:
        write_pdf(slides, HERE / "talk.pdf")

    failed = False
    rendered = sum(s.rendered for s in slides)
    for slide in slides:
        for p in slide.problems:
            mismatch = not p.startswith("not rendered")
            failed |= mismatch
            print(f"{'MISMATCH' if mismatch else 'placeholder'}  slide {slide.number:2d}  {slide.scene}: {p}")
    print(f"deck: {len(slides)} slides, {rendered} rendered, {len(slides) - rendered} placeholders -> {HERE / 'index.html'}, {HERE / 'script.md'}" + (f", {HERE / 'talk.pdf'}" if args.pdf else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
