# Archived Huff implementation

BL127 was first written in Huff. This directory keeps that implementation
after the port to Yul (`contracts/src/bl127/`), for history and for the
equivalence proof. Nothing here is built by default; `make test` needs only
`forge` and `solc`.

| path | what |
|---|---|
| `src/bl127/*.huff` | the Huff sources, entry point `bl127.huff`, as last compiled for Sepolia |
| `src/bl127/Ibl127.sol` | the Huff-era Solidity interface (`uint256` arguments, `*Raw` names) |
| `src/README.md` | the original Huff README |
| `lambertwm1.huff` | a Lambert W₋₁ that never shipped; `huffc` ran out of code size, and the routine itself was never functional (undefined constant, inverted domain checks, wrong-sign seed). The Yul `lambertWm1` is a fresh implementation. |
| `compile-huff.sh` | the original build script (needs `huffc`), paths updated to this directory |
| `bl127.sepolia.runtime.hex` | runtime bytecode of the Huff contract at `0xfae694D0c2c44181791F838c54Ed64C3151FfE30`, Sepolia block 11,857,616 |

## The baseline the tests use

The equivalence suites (`test/bl127/Equivalence*.t.sol`) etch
`bl127.sepolia.runtime.hex` and compare the Yul object against it on every
input where the Huff computed a defined answer. The hex is the bytecode that
was actually live, fetched with `make fetch-baseline`; keccak256 of the hex
text is `0x74946c4dd85b8bbbab56d77d34defdf4e66ea15c0647993ea445f0b95591d10b`.

The sources here are slightly newer than that bytecode: the Sepolia build
predates `shortcut_constants.huff`, so `pow`, `cbrt` and `lambertW0` on the
shortcut inputs differ by a few ULP between the two. Rebuilding with
`huffc` therefore does not reproduce the Sepolia bytecode, and the
committed hex, not a rebuild, is the reference.

## Rebuilding anyway

```sh
cargo install --git https://github.com/huff-language/huff-rs huff_cli   # huffc 0.3.x
bash contracts/archive/huff/compile-huff.sh contracts/archive/huff/src/bl127/bl127.huff
```

Output lands under `contracts/build/huff/` (gitignored). What the Huff got
wrong and what the port changed is recorded in `docs/bl127/HISTORY.md` and
in the "What changed from the Huff" section of `contracts/src/bl127/README.md`.
