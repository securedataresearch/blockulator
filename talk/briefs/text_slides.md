# Brief: the six text slides — s01, s11, s13, s14, s18, s19 (one builder, one `TextScene` helper)

These six slides carry words, not data. They share a helper you add to vocab.py: `class TextScene(DeckScene)` with `typed(text, size, colour, run_time)` (a `Text`/`MarkupText` revealed character by character with `AddTextLetterByLetter`), `strike(mobj, colour)` (a line drawn through a text), `checkbox(label)` returning a box + label whose `.tick()` draws an EMERALD `check_mark()` inside, and `bullet(glyph, text)` rows. Every slide below is its own scene file and its own class; the helper is shared.

Common: title at BODY top-left (SANS, MUTED) where a title is named; the hero line at HERO; body at BODY; the last section holds 3 s as the poster. White = EXACT/plain text on all six; EMERALD marks the hero line or a tick; RED only where named.

---

## s01_title — slide 1, "THE END OF ROUNDING ERRORS" (the only looping scene)
Script: "[you: who you are, one line] Computers round. That will never end. What can end is the rounding error: the wrong answer, or the wrong direction."
Strings (LITERALS): `THE END OF ROUNDING ERRORS` (the user's title, V-none: their wording); `blockulator.com` (K12); a speaker line — REPORT item: leave a placeholder string `[speaker]` in LITERALS so the user supplies it; do not invent a name.
Sections: one, `title` (this scene is flagged `loop: true` in slides.yaml; it must end in the state it starts in). Beats: a faint `GridLine` across the lower third with one white dot; the title types in at HERO; `blockulator.com` and the speaker placeholder at BODY, MUTED; then an ambient 8 s: the dot drifts slowly between two ticks and `snap()`s once in EMERALD with a `halo()`, fades back to white at its start position, so the clip loops without a seam. ~14 s.
Hero: the title. Flags: no name invented; no numbers.
Acceptance: `SECTIONS = ("title",)` is the one allowed single-section scene; check.py asserts first and last frames' mobjects match (same positions) for the loop.

## s11_budget — slide 11, "Precision is a budget"
Script: "Not every protocol should change libraries. Spend precision where it pays: long horizons, cancellation, tails, iteration. And decide the direction of every rounding at a unit."
Strings (LITERALS; essay-v7 §5, V-none: the four bullets are the essay's own list): title `Precision is a budget`; `spend precision where it pays:`; bullets `long horizons` · `cancellation` · `extreme ranges and tails` · `iteration`; the fifth line `and decide the direction of every rounding at a unit` (script §11). No numbers (A11's $55.09 has no ledger entry: not drawn).
Sections: `title` (title + the lead line), `horizons` (bullet 1 with a glyph: a `GridLine` that stretches rightward, far), `cancellation` (bullet 2: two tall bars subtract to a thin sliver with a `measure()` bracket, no number), `tails` (bullet 3: a dot slides left along a grid and drops off its last tick, turning RED with a `cross_mark()`), `iteration` (bullet 4: a loop arrow cycling a dot through three `snap()`s, the error growing as a `measure()` bracket), `direction` (the fifth line at HERO with a `direction()` arrow glyph in EMERALD, `glow_bar()`), hold. ~5 s per section.
Hero: the fifth line. Flags: no numbers anywhere; the glyphs are schematic; "every" appears in the fifth line only (script wording).

## s13_not_switch — slide 13
Script: "Not 'switch libraries'. 'Measure yourself against the reference.'"
Strings (LITERALS, script §13 / essay §6): `Not "switch libraries".` and `Measure yourself against the reference.`
Sections: `not` (the first line types at HERO in TEXT; a RED `strike()` draws through "switch libraries"), `measure` (the second line types at HERO in TEXT inside an EMERALD `glow_bar()`, the first line dims to FAINT), hold. ~4 s + 6 s.
Hero: the second line. Flags: straight quotes or typographic, consistent with s02's labels; nothing else on the slide.

## s14_institutions — slide 14, "What institutions buy"
Script: "Fees scale with the computation; errors scale with the amount. What an institution buys is not fewer cents. It is a result that can be reproduced, declared and checked."
Strings (LITERALS; essay §7): title `What institutions buy`; axis/curve labels `amount` (x), `fees · scale with the computation` (a flat line), `errors · scale with the amount` (a rising line); `not fewer cents`; the three words `reproducible` · `declared` · `checked`; small `ERC-4626 fixes the rounding direction of each vault conversion` (essay §7; V1 names ERC-4626's rounding directions).
Sections: `scales` (a `Chart` with no tick numbers: x `amount`, two curves draw: fees flat in MUTED, errors rising in RED with a `direction()`-style arrow at its end; labels at the curve ends), `not-cents` (the line `not fewer cents` at BODY, the chart shrinks to the left), `reproducible`, `declared`, `checked` (one word each, HERO, landing in a row with 0.3 s stagger within the section, each in a `glow_bar()`), `precedent` (the ERC-4626 line at BODY, MUTED), hold. ~4–5 s each.
Hero: the three words. Flags: the chart has no numbers (the "15 digits on $10 million" line stays in the essay); "errors scale with the amount" is a proportionality, not a claim about any protocol.

## s18_habits — slide 18, "Decide. Measure. Declare."
Script: "Rounding is a design decision, like access control. Decide which way. Measure your digits like your gas. Declare what you guarantee, and check it."
Strings (LITERALS; essay §10): title `Rounding is a design decision, like access control.`; checkboxes `Decide` / `for each rounding, which way, and why`; `Measure` / `know a calculation's digits the way you know its gas, and check it against a reference`; `Declare` / `write down what each operation guarantees, and test or prove it`; a declaration block: header `declares` then lines `rounding: <op> down · <op> up · exp nearest` labelled `example` and `reference: <the FP127 address from release()>` (V15; the address is the only number, from `numbers()`).
Sections: `title`, `decide` (checkbox 1 appears and ticks; its sub-line at BODY MUTED), `measure` (checkbox 2), `declare` (checkbox 3), `block` (a contract outline `RoundedRectangle` on the right; the declaration block slides in and attaches to it; the `example` tag is visible), hold. ~3 s title, 4 s each box, 6 s block.
Hero: the three ticks (EMERALD `check_mark()`s). Flags: the op names in the block are examples and are tagged `example`; the address is real and comes from RELEASE.json; nothing says any protocol does this today.

## s19_address — slide 19, "The reference"
Script: "Open source. One address on every chain that has it. Today, Sepolia. Measure yourself against it. [you: thanks]"
Strings: title `The reference`; `FP19 v6` + its full address and `FP127 v9` + its full address (HERO-adjacent: BODY mono, 42 chars) from `release()` (V15); the eight other objects `FP127E/H/N/S`, `FP19E/H/N/S` with their addresses at CAPTION, mono, from `release()`; `today: Sepolia` (V6); `blockulator.com` and the repository URL from `git remote get-url origin` normalised to `github.com/<org>/<repo>` (K12; REPORT if the remote is not GitHub); closing `Measure yourself against it.` (script §19). Ladder objects are not shown.
The goal of the whole talk is adoption: every engineer and every agent should leave with a way to use Blockulator in the next minute. This slide is that way. Three more LITERALS, verbatim from README.md lines 69–90 (K12): `engineers: forge install securedataresearch/blockulator · npm install @blockulator/contracts`; `agents: blockulator.com/llms.txt`; `every op is a free eth_call`.
Sections: `addresses` (title; the two main addresses type in, each in a `glow_bar()`, FP19 first then FP127, with `halo()`s; `every op is a free eth_call` under them at BODY), `objects` (the eight others fade in as two columns at CAPTION), `use` (two rows at BODY, MONO for the commands: the `engineers:` row with the two install commands, the `agents:` row with the llms.txt URL, each landing with a `glow_bar()`), `links` (`today: Sepolia` at BODY; `blockulator.com` and the repo at BODY; the closing line at HERO in EMERALD), hold 4 s. ~6 + 4 + 6 + 6 s.
Hero: the two addresses, then the `use` rows, then the closing line. Flags: `today: Sepolia` is on the poster frame (V6); nothing implies a mainnet deployment; no QR; the commands are copied from README.md and `check.py` asserts they appear there verbatim.
Acceptance: `numbers()` returns every address and version; `check.py` reads RELEASE.json by a second path and asserts the ten addresses match and are 42 characters.

---

## Deliverables and report (all six)
Per RULES.md, plus: the `TextScene` helper documented in `talk/scenes/README.md`; six scene files; six `check.py` entries; held-frame PNGs for every section; one report of at most ten lines covering all six (the speaker placeholder is an expected REPORT item).
