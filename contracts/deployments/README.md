# Deployment records

Everything in this directory is served at blockulator.com/contracts/deployments/.

- `FP127.md`, `FP127.json`: the FP127 object on Sepolia, CREATE2 through the
  deterministic proxy with salt "FP127 v8" (v1 to v7 recorded below it), the
  verification recipe and the smoke test. Deploy a new version with
  `make deploy-sepolia`, `make verify-sepolia`, `make smoke-sepolia`.
- `FP19.md`, `FP19.json`, `FP19E.json`, `FP19H.json`, `FP19N.json`,
  `FP19S.json`: FP19 v6, five objects from one source, one idea each (salts
  "FP19 v6", "FP19E v6", "FP19H v6", "FP19N v6", "FP19S v6": the number,
  the elementary, hyperbolic and normal-distribution functions, and
  Lambert W), with the `-fp19`, `-fp19e`, `-fp19h`, `-fp19n` and `-fp19s`
  targets. One record covers the five objects, as `Ladder.md` covers its
  contracts. v5 (Blockulator 2.2, salts "FP256 v5", …) and releases one to
  four are recorded below them; release four (Blockulator 2.1) was FP19,
  FP19X, FP19X2 and FP19X3 (salts "… v4"), whose `FP19X.json`,
  `FP19X2.json` and `FP19X3.json` stay here marked `"release": "Blockulator
  2.1"`, `"current": false`: those addresses are still live, and not part
  of 3.0.
- `Ladder.md`, `Ladder.json`: ladder v13 (salt "FP127 ladder v13"):
  `LadderFP127` and `LadderFP19Deployed`, which call the deployed objects,
  with `LadderRunner` and `EdgeRunner` (v1 to v12 recorded below).
  `make deploy-ladder-sepolia`, `make verify-ladder-sepolia`.
- `RELEASE.md`, `RELEASE.json`: every address in Blockulator 3.0, and those
  of 2.2, 2.1 and 2.0, which stay live.
- `*.sepolia.receipt.json`, `*.mainnet.receipt.json`: the raw receipt of each object's deployment.

## Ethereum mainnet

The library objects go to mainnet at the same CREATE2 addresses as on Sepolia; the ladder stays on Sepolia. The
deployer key is public, so ETH sent to it is swept within a block. `make deploy-mainnet` therefore sends the funding
and every deploy as one Flashbots bundle (`scripts/fp127/bundle.py`): `FUNDER_KEY`'s account moves exactly the gas
the deploys need to the deployer in the bundle's first transaction, and the relay includes the whole bundle in one
block or none of it. The bundle is rebuilt for each block at that block's base fee plus a tip.

1. `make predict-mainnet`: every object's address, and whether it is already there.
2. `make deploy-mainnet-dry`: the identical transactions on an anvil fork, which checks every address and runtime
   and prints the gas and the ETH to fund. No keys needed.
3. `FUNDER_KEY=… DEPLOYER_KEY=… make deploy-mainnet`, then `make verify-mainnet` and `make smoke-mainnet`.

The badge, game, calculator and market contracts were deployed by hand in
the Huff era; their addresses live in
`static/js/legacy/infrastructure/config/contract-registry.js`, the game
modules, and `/.well-known/agent.json`.

## Chains: CLZ (Osaka) required

The FP127 and FP19 objects (and their inline libraries) count leading bits
with the CLZ opcode (EIP-7939, Fusaka/Osaka). They are built by solc 0.8.38
for evmVersion osaka, with solc 0.8.24's Yul optimizer sequence pinned
(`scripts/fp127/stdjson.py`; 0.8.38's own sequence builds the FP19 core
over 24,576 bytes), and the explorers receive that same standard-JSON input.
Blockulator 2.2 is the first CLZ build. Releases up to 2.1, recorded above,
were shanghai builds without CLZ and stay deployed on Sepolia.

Supported chains are those with CLZ, as of 2026-10-22 (each probed live;
dates and names are the networks' announced activations):

| chain | CLZ since | upgrade |
|---|---|---|
| Ethereum mainnet | 2025-12-03 | Fusaka |
| Sepolia | 2025-10-14 | Fusaka |
| Hoodi | (probe) | Fusaka |
| Arbitrum One | 2026-01-08 | ArbOS 51 |
| OP Mainnet | 2026-07-08 | Upgrade 19 "Karst" |
| Unichain | 2026-07-08 | Upgrade 19 "Karst" |
| Base | 2026-05-28 | "Azul" |
| Polygon PoS | 2026-03-04 | Lisovo |
| BNB Chain | 2026-04-28 | Osaka / Mendel |
| Gnosis | 2026-04-14 | Fusaka |
| Scroll | (probe) | Galileo |
| Linea | (probe) | |

**Unsupported** (no CLZ, probed 2026-10-22): zkSync Era, Avalanche C-Chain,
Polygon zkEVM.

The objects deploy fine on a chain without CLZ (the init code only copies
the runtime), but there the opcode is invalid and every call that counts
leading bits fails and burns all the gas it was given. Probe a chain before
deploying to it or calling it: an `eth_call` with no `to` and the creation
code `0x60011e60005260206000f3` (PUSH1 1, CLZ, PUSH1 0, MSTORE, PUSH1 32,
PUSH1 0, RETURN) returns the word `0xff` where CLZ exists. `make probe-clz
RPC=<url>` runs it, and every `deploy-*` target runs it first and refuses
to send unless the answer is 255.

The deploy targets are pattern rules over the objects table in
`scripts/fp127/gen.py` (name, library, salt): for each stem `<o>` in `fp127
fp19 fp19e fp19h fp19n fp19s` (`gen.py --objects`), `make predict-<o>`,
`deploy-<o>-sepolia` and `verify-<o>-sepolia` (`scripts/fp127/deploy.py`,
`stdjson.py`, `verify.py`); `predict`, `deploy-sepolia` and `verify-sepolia`
are FP127's. A new object or salt edits only the table.
