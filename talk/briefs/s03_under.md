# Brief: s03_under — "exp is under everything"

## 1. Slide and line
Slide 3 of 19. Title on the slide: **exp is under everything** (the script's heading; the word "every" appears in the title only, nowhere else on the slide).
Script (verbatim, script-v2 §3): "Every rate, every discount, every option price runs through exp. If exp has no canonical value on chain, nothing built on it has one. That is an attack vector."
Claims: V11 (exp sits under compounding, discount factors, option probabilities via the normal CDF, growth curves; "every" is rhetorical, soften if challenged), V10 (no canonical exp(x) on chain).

## 2. Takeaway
Four things a protocol charges for all resolve to one function, and that function has no canonical value on chain.
Closing line (verbatim): **if exp has no canonical value on chain, nothing built on it has one**

## 3. Data and strings
No JSON. `numbers()` returns `{}`. Every string below is a LITERAL.

| string | where | claim id | source |
|---|---|---|---|
| `exp is under everything` | title, top-left | V11 | script-v2 §3 heading |
| `compounding rate` / `(1 + r/n)<sup>nt</sup>` → `e<sup>nt · ln(1 + r/n)</sup>` | row 1 | V11 | essay-v7 §1 "every compounding rate" |
| `discount factor` / `e<sup>−rt</sup>` | row 2 | V11 | essay-v7 §1 |
| `option price` / `N(d)` → `erfc` → `e<sup>−x²</sup>` | row 3 | V11 | essay-v7 §1 "through the normal distribution" |
| `growth curve` / `e<sup>kt</sup>` | row 4 | V11 | essay-v7 §1 |
| `e<sup>x</sup>` | centre, hero | V11 | — |
| `if exp has no canonical value on chain, nothing built on it has one` | closing line | V10, V11 | script-v2 §3 |

Markup only (`markup()` with `<sup>`); no "½", no "√". The `²` in `x²` is a superscript two: render a test frame and confirm the glyph (Instrument Sans has it; if not, write `<sup>2</sup>`).

## 4. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `four` | title; the four rows draw in, staggered 0.4 s apart: label (SANS, BODY, MUTED) on the left, the formula (markup, BODY, TEXT) to its right. The `exp` term of each formula is still in TEXT. | — | "Every rate, every discount, every option price runs through exp." | four rows, title | 8 |
| 1 | `resolve` | in each row, the exp term lights (TEXT → EMERALD with a brief `Indicate`), and a thin EMERALD line draws from it to a central `e<sup>x</sup>` (HERO size) that grows in with a `halo()`; one row per 0.8 s, top to bottom. | all four rows, now with their exp term lit | (pause) | four lit terms wired to the central e^x | 7 |
| 2 | `alone` | the four rows dim to FAINT; `e<sup>x</sup>` stays with its halo; the closing line types under it (BODY, TEXT); hold 3 s. | e^x, halo, dim rows | "If exp has no canonical value on chain, nothing built on it has one. That is an attack vector." | e^x haloed, closing line | 8 |

## 5. Vocabulary
`markup()`, `words()`, `halo()`, `Indicate`, thin `Line`s in EMERALD. No grid on this slide. White carries "the exact function"; red is not used.

## 6. Hero
`e<sup>x</sup>` at HERO size, EMERALD with `halo()`, drawn last in section 1, alone in section 2.

## 7. Legibility
RULES.md. Four rows at BODY size leave room; the formulas are short. Safe area 5%.

## 8. Flags
- The word "every" appears only in the title. The rows are four examples, not a claim of completeness (V11).
- Nothing on this slide says these protocols are wrong; it says they share a root.

## 9. Acceptance
`SECTIONS = ("four", "resolve", "alone")`; `numbers()` empty; `LITERALS` as table 3; `check.py` entry asserts the four row labels and the closing line match the strings above and that nothing digit-bearing is drawn except `x²`/superscripts; `-ql` render; three held-frame PNGs.

## 10. Deliverables and report
Per RULES.md.
