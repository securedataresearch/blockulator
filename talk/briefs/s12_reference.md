# Brief: s12_reference — "There is no reference"

## 1. Slide and line
Slide 12 of 19. Title on the slide: **There is no reference**.
Script (verbatim, script-v2 §12): "No standard says what exp should return on chain. A correctly rounded library can be that reference: one right word for every input, the same address on every chain, no owner, no upgrade path, one call to check."
Claims (all VERIFIED 2026-10-29, research_notes/talk/claims.md and verify-K.md "2026-10-29 chain probe"): V1 (we found no EIP or ERC, final or draft, that says what exp, ln or a compounded rate must return or how it rounds; ERC-4626's "MUST round down" is the only rounding rule), V2/K14 (one right word per input for a format and rule), V3 (CREATE2 through the deterministic-deployment proxy 0x4e59…956C reproduces 0x0DF7…6E0d; the proxy's code is present on all 15 chains probed), V4 (0 state or call opcodes in the ten generated .yul; Sourcify `match` and Blockscout verified for all ten RELEASE.json addresses), V5 (CLZ re-probed 2026-10-29 13:56 UTC: present on Ethereum, Sepolia, Hoodi, Arbitrum One, OP Mainnet, Unichain, Base, Polygon PoS, BNB, Gnosis, Scroll, Linea; absent on zkSync Era, Avalanche C-Chain, Polygon zkEVM), V6 (deployed on Sepolia only), V15 (the v9 addresses).

talk/scenes/data/chains.json must carry these results before you build (`probed: "2026-10-29"`, `proxy: true` on every chain, CLZ status as above); if it still says `proxy: null` or `probed: "2026-10-22"`, report and draw the rows without the proxy word.

## 2. Takeaway
One address, one word per input, nothing to trust but the code; today on Sepolia.
Closing line (verbatim): **one call to check · deployed today: Sepolia**

## 3. Data and strings
Loaders: `release()` (contracts/deployments/RELEASE.json → components.FP127.address and .version), `chains()` (talk/scenes/data/chains.json: chain, clz_since, status, probed, deployed, proxy), `edges("exp")` for the exp(40) FP127 cell and `correctly_rounded_18(truth80())` for the 18-decimal word (the same string s02 shows as its exact row).

| string | where | claim id | source |
|---|---|---|---|
| the FP127 address, all 42 characters | centre, HERO, MONO | V15 | release() |
| `FP127 v9` | under the address, CAPTION | V15 | release() |
| each chain name | rows | V5 | chains() |
| `CLZ since <date>` per supported chain | row, MUTED | V5 | chains().clz_since |
| `deployed` (Sepolia only) | row, EMERALD | V6 | chains().deployed |
| `has CLZ · proxy present · not yet deployed` (other supported chains) | row, MUTED | V3, V5, V6 | chains().status, chains().proxy |
| `no CLZ` (unsupported chains) | row, RED with `cross_mark()` | V5 | chains().status |
| `probed <date>` | caption, bottom-left | V3, V5 | chains().probed |
| `your contract` / `eth_call exp(40)` / `the reference` | section 2 boxes | V2, K14 | essay §6 |
| the 18-decimal exp(40) word, twice | section 2 | V9 | edges + correctly_rounded_18 |
| `equal` | section 2, EMERALD with `check_mark()` | V2 | — |
| `a correct implementation returns the same word` | section 2, CAPTION | V2, K14 | essay §7 "Reproducibility" |
| `no storage · no owner · no upgrade path · source verified` | section 3 | V4 | essay §6; Sourcify match + Blockscout, all ten addresses |
| `one call to check · deployed today: Sepolia` | closing | V6 | script §12 |

Not drawn: "ready" or "live"; any mainnet address claim. The word "every chain" appears only in the script.

## 4. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `address` | title; the address types in character by character (MONO, HERO) with `glow_bar()`; `FP127 v9` under it | — | "No standard says what exp should return on chain. A correctly rounded library can be that reference:" | the address | 6 |
| 1 | `chains` | the address shrinks to BODY and moves up; chain rows appear one per 0.3 s in the README's order: name, `CLZ since`, status word; Sepolia's row lands last with EMERALD `deployed` and a `halo()`; unsupported rows in RED with `cross_mark()`; the `probed <date>` caption | address | "one right word for every input, the same address on every chain," | the chain table | 10 |
| 2 | `call` | the table dims; two boxes: `your contract` (left) and `the reference` (right, carrying the address); an arrow `eth_call exp(40)` left to right; the reference's word types in (MONO, BODY); your contract's word types in beneath; an EMERALD `check_mark()` and `equal`; the CAPTION line | address | (pause) | the two equal words | 10 |
| 3 | `properties` | four phrases land under the reference box: `no storage · no owner · no upgrade path · source verified`, one per 0.5 s, with small tick glyphs | boxes | "no owner, no upgrade path," | boxes + properties | 5 |
| 4 | `closing` | the closing line (BODY, inside `glow_bar()`); hold 3 s | all | "one call to check." | everything, closing line | 5 |

## 5. Vocabulary
`digits()` for the address and words, `words()` for labels, `glow_bar()`, `halo()`, `check_mark()`, `cross_mark()`, `Arrow`, `RoundedRectangle` boxes (add a `box(label)` helper to vocab.py if none exists). No grid. White = EXACT (the two equal words); EMERALD = Sepolia's `deployed` and `equal`; RED = `no CLZ`.

## 6. Hero
The address, HERO size with `glow_bar()` in section 0; Sepolia's row with `halo()` in section 1.

## 7. Legibility
The address is 42 mono characters: HERO size fits 1920 px at 5% margins (check: 42 × 0.6 × 48 px ≈ 1,210 px). The chain table: at most 14 rows in two columns at BODY; chain names in SANS, dates in MONO.

## 8. Flags
- "deployed" appears on Sepolia's row only (V6). Every other supported chain reads `has CLZ · not yet deployed`. Never "ready", never "live".
- The probe date is on screen whenever the table is.
- The "your contract" word is illustrative; the CAPTION line says why it is equal (V2/K14), and it is the SAME string as the reference's, taken from the same loader.

## 9. Acceptance
`SECTIONS = ("address", "chains", "call", "properties", "closing")`; `numbers()` returns the address, the version, the chain rows, the probe date and the exp(40) word; `check.py` recomputes the word with `correctly_rounded_18` and reads the address straight from RELEASE.json, and asserts no row says "ready"/"live"; `-ql` render; five held-frame PNGs.

## 10. Deliverables and report
Per RULES.md.
