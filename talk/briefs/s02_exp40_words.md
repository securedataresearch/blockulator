# Brief: s02_exp40 revision — show every digit of e^40 the Blockulator words hold

The user (2026-10-29): "we need to visually show all digits for e^40 computed by blockulator libs in that slide… it's really impressive." The current `blockulator` section shows the two rows to 18 decimals with a "73 digits right" label that cannot be counted. Replace that section with the full words.

## 1. What changes (only the `blockulator` and `closing` sections; the `exact` and `libraries` sections stay as they are)
- Data: `edges("exp")` probe ["40"] cells `fp19.raw` (the 256-bit word: sign bit 255, 19-bit biased exponent bits 254..236 with bias 262,143, fraction bits 235..0, significand 2^236 + F; value = significand × 2^(E − 262,143 − 236)) and `fp127.raw` (an int256; value = raw / 2^128). Decode each to an exact `Fraction`, then to its exact decimal expansion (both terminate: power-of-two denominators). Add `decode_fp19(raw) -> Fraction` and `decode_fp127(raw) -> Fraction` to vocab.py with a docstring citing contracts/src/fp19/README.md lines 21–24 and K1/K3; check.py decodes by a second route (bit arithmetic written independently) and also asserts each word rounded to 18 decimals equals the exact row and that `matching_digits(word, truth80())` gives the counts drawn.
- Truth: `truth80()` (80 decimals). Matching prefix of each word against it: expected FP127 57 digits (18 integer + 39 decimals), FP19 73 (18 + 55). These counts come from `matching_digits`, never typed.

## 2. The `blockulator` section (click 3), redesigned
1. The three library rows fade to FAINT and slide up under the exact row (they stay as context, 60% size is NOT allowed; keep BODY, just FAINT).
2. **FP127's word** unfolds: label `FP127` (EMERALD) on the left; the integer part and the point, then the decimals typed in blocks of ten with a thin ruler under the row marking every tenth decimal (`10 20 30 …`), wrapping to new lines at 46 mono characters per line (continuation lines indented under the first decimal). Digits that match the truth are EMERALD; from the first digit past the matching prefix the digits are MUTED, and a small bracket under that point reads `the word's precision ends here · 39 decimals`. The expansion is drawn in full (128 decimals; 3 lines), because that IS the word: nothing is hidden, nothing is "…".
3. **FP19's word** unfolds the same way beneath: label `FP19` (TEXT), matching digits TEXT with a `glow_line()` under the matched span, tail MUTED, bracket `the word's precision ends here · 55 decimals`. Its exact expansion is long (the exponent is negative, so up to about 180 decimals; draw them all, 4–5 lines). If the two words together do not fit at BODY within the safe area with the four context rows above, drop the context rows to a single FAINT line `Solady · Balancer · PRBMath: 2 · 3 · 0 decimals right` (strings from numbers(); ids as the existing LITERALS) rather than shrinking the words.
4. Labels at the right end of each word's first line: `57 digits right` and `73 digits right` (matching-prefix counts from numbers()); under them `39 decimals` / `55 decimals`. The ruler makes those countable.
5. Timing: FP127 unfolds in ~6 s, FP19 in ~8 s (blocks of ten, 0.25 s each), then 2 s hold.

## 3. The `closing` section
Closing line as now (`three good answers, none the closest · Blockulator: all 18`) plus a second line `FP127: 39 decimals · FP19: 55 decimals · every one of them right` where "every one" is justified by the matching counts (both words match the truth through their full stated decimals). Hold 3 s.

## 4. Rules that bite here
- The tail digits beyond the matching prefix are the word's own exact expansion, not errors: MUTED, never RED, no cross; the bracket says "precision ends here". (Never present a library's precision as a defect; least of all ours.)
- No "…": every decimal of each expansion is on screen.
- Every digit from `numbers()`; the counts from `matching_digits`; the labels in `LITERALS` with id V9/V29.
- White = FP19's family colour on this slide (as now); EXACT is the exact row at the top (also white): keep the exact row's label `the closest 18-decimal value` so the two whites are disambiguated by their labels.

## 5. Acceptance
`SECTIONS` unchanged (`exact`, `libraries`, `blockulator`, `closing`); numbers() adds `fp127_word`, `fp19_word` (full decimal strings), `fp127_match`, `fp19_match`, `fp127_decimals`, `fp19_decimals`; check.py recomputes the words by an independent decode and asserts the 18-decimal roundings and the counts; `-ql` then one `-qh`; four held-frame PNGs; the `blockulator` held frame shows both complete words.
