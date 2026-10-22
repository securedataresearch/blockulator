# Deployment records

Everything in this directory is served at blockulator.com/contracts/deployments/.

- `FP127.md`, `FP127.json`: the FP127 object on Sepolia, CREATE2 through the
  deterministic proxy with salt "FP127 v5" (v1 to v4 recorded below it), the
  verification recipe and the smoke test. Deploy a new version with
  `make deploy-sepolia`, `make verify-sepolia`, `make smoke-sepolia`.
- `FP256.md`, `FP256.json`, `FP256X.json`, `FP256X2.json`, `FP256X3.json`:
  FP256 release four, four objects from one source (salts "FP256 v4",
  "FP256X v4", "FP256X2 v4", "FP256X3 v4"; releases one to three recorded
  below them), the same way with the `-fp256`, `-fp256x`, `-fp256x2` and
  `-fp256x3` targets. One record covers the four objects, as `Ladder.md`
  covers its thirteen contracts.
- `Ladder.md`, `Ladder.json`: the eleven ladder adapters, `LadderRunner` and
  `EdgeRunner`, salt "FP127 ladder v9". `make deploy-ladder-sepolia`,
  `make verify-ladder-sepolia`.
- `RELEASE.md`, `RELEASE.json`: every address in Blockulator 2.1.
- `*.sepolia.receipt.json`: the raw receipt of each object's deployment.

The badge, game, calculator and market contracts were deployed by hand in
the Huff era; their addresses live in
`static/js/legacy/infrastructure/config/contract-registry.js`, the game
modules, and `/.well-known/agent.json`.

## Two builds: shanghai and osaka

Every deployed object (FP127, FP256, FP256X, FP256X2, FP256X3) is built
twice from the same source (`scripts/fp127/gen.py`, the objects table in
`LIBS[...]["objects"]`):

- **shanghai**, the default and the release above: solc 0.8.24, evmVersion
  shanghai, the files beside each `.yul.src`, artifacts in `out/`. It runs
  on every EVM chain.
- **osaka**: the same Yul except that the leading-bit count `msb(x)` is
  `255 - clz(x)` on the CLZ opcode (EIP-7939, 0x1e, 5 gas; FP256's `ctz`
  too), behind the same zero guard, so msb(0) is still 0. Files in
  `contracts/src/*/osaka/`, solc 0.8.38 with evmVersion osaka and 0.8.24's
  optimizer sequence (pinned in `scripts/fp127/stdjson.py`), artifacts in
  `out/osaka/`. It returns the same word or the same revert as the
  shanghai object on every input (`make test-osaka`) and costs less gas
  (`make bench-osaka`, `docs/benchmarks/gas-osaka.md`).

**Which to use.** On a chain with CLZ (the table below), the osaka object:
same results, less gas. Anywhere else, or when in doubt, the shanghai
object. The inline libraries follow the same rule: `FP127Lib.sol` /
`FP256Lib.sol` compile for any target; `osaka/FP127LibOsaka.sol` /
`osaka/FP256LibOsaka.sol` are opt-in, need `pragma solidity ^0.8.31` with
`evm_version = "osaka"`, and the contract that inlines them must only ever
run on a CLZ chain.

**Warning.** Osaka code deploys fine on a chain without CLZ (the init code
only copies the runtime), but there 0x1e is an invalid opcode: every call
that reaches msb fails and burns all the gas it was given. Probe first:
an `eth_call` with no `to` and the creation code `0x60011e60005260206000f3`
(PUSH1 1, CLZ, PUSH1 0, MSTORE, PUSH1 32, PUSH1 0, RETURN) returns the word
`0xff` where CLZ exists and fails where it does not. `make probe-clz
RPC=<url>` runs it, and every `deploy-*-osaka-*` target runs it against
its RPC first and refuses to send unless it answers 255.

| chain | CLZ | since | upgrade |
|---|---|---|---|
| Ethereum mainnet | yes | 2025-12-03 | Fusaka |
| Sepolia | yes | 2025-10-14 | Fusaka |
| Hoodi | yes | (probe) | Fusaka |
| Arbitrum One | yes | 2026-01-08 | ArbOS 51 |
| OP Mainnet | yes | 2026-07-08 | Upgrade 19 "Karst" |
| Unichain | yes | 2026-07-08 | Upgrade 19 "Karst" |
| Base | yes | 2026-05-28 | "Azul" |
| Polygon PoS | yes | 2026-03-04 | Lisovo |
| BNB Chain | yes | 2026-04-28 | Osaka / Mendel |
| Gnosis | yes | 2026-04-14 | Fusaka |
| Scroll | yes | (probe) | Galileo |
| Linea | yes | (probe) | |
| zkSync Era | **no** | | |
| Avalanche C-Chain | **no** | | |
| Polygon zkEVM | **no** | | |

Every row was probed live on 2026-10-22 with the `eth_call` above; the
dates and upgrade names are each network's announced activation. Probe
again before deploying: a chain's answer is the only authority.

**Targets.** For each object stem `<o>` (`fp127 fp256 fp256x fp256x2
fp256x3`, `gen.py --objects`): `make build-osaka`, `make size-osaka`,
`make predict-<o>-osaka`, `make deploy-<o>-osaka-sepolia`, `make
verify-<o>-osaka-sepolia`, beside the shanghai `predict-<o>`,
`deploy-<o>-sepolia`, `verify-<o>-sepolia` (FP127's are also `predict`,
`deploy-sepolia`, `verify-sepolia`). Both are pattern rules over the
objects table; a new object or salt edits only the table. The osaka salts
carry the build: "FP127 v6 osaka", "FP256 v5 osaka", "FP256X v5 osaka",
"FP256X2 v5 osaka", "FP256X3 v5 osaka". The shanghai salts are unchanged.

**Records.** An osaka deployment is recorded beside the shanghai one, never
inside it: `<Object>.osaka.json` with the same fields as `<Object>.json`
(`contract`, `chainId`, `network`, `address`, `deployer`, `salt`,
`saltAscii`, `initCodeHash`, `runtimeKeccak`, `runtimeBytes`, `source`
= `contracts/src/<lib>/osaka/<Object>.yul`, `sourceCommit`, `compiler`
with `"solc": "0.8.38+commit.1835d247"`, `"evmVersion": "osaka"` and
`"optimizerSteps"` as in `stdjson.py`, `txHash`, `block`, `verification`,
`abi` (the shanghai object's: the ABI is the same), `deployedBy`,
`gasUsed`, `explorerTx`), plus `"build": "osaka"` and `"clzProbe"`: the
RPC's answer to the probe at deploy time. The receipt is
`<Object>.osaka.sepolia.receipt.json`. `make verify-<o>-osaka-sepolia`
reads the address from `<Object>.osaka.json`. No osaka object is deployed
yet.
