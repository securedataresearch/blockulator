# Deployment records

Everything in this directory is served at blockulator.com/contracts/deployments/.

## Names: BL127 and BL19

The libraries were renamed on 2026-10-29 (on-chain name FP127 → BL127, FP19 → BL19). The deployments of 2026-11-20 UTC (BL127 v10,
BL19 v7, ladder v15) are the first under the new names: their CREATE2 salts are the ASCII strings `BL127 v10`,
`BL127E v10`, …, `BL19 v7`, …, `BL127 ladder v15`, and their verified contract names on Sourcify and Blockscout are
the names used everywhere else in this repository. Every current record's `onChainName` equals its `contract`.

Everything deployed before that keeps the old spelling, since it is bytes already on chain:

- The CREATE2 salts of the superseded versions are the deployed ASCII strings (`FP127 v1` to `FP127 v9`, `FP127E v9`,
  …, `FP19 v6`, …, `FP256 v1` to `FP256 v5`, …, `FP127 ladder v1` to `FP127 ladder v14`): a salt's bytes fix the
  address, so each `previous` entry keeps its `salt` and `saltAscii` as sent.
- The verified contract names of those versions stay the on-chain names: FP127, FP127E, FP127H, FP127N, FP127S (on-chain
  names of BL127 v9's five), FP19, FP19E, FP19H, FP19N, FP19S (on-chain names of BL19 v6's five) and ladder v14's
  LadderFP127, LadderFP19Deployed (on-chain names).

- `BL127.md`, `BL127.json`, `BL127E.json`, `BL127H.json`, `BL127N.json`,
  `BL127S.json`: BL127 v10, five objects from one source, one idea each
  (salts "BL127 v10", "BL127E v10", "BL127H v10", "BL127N v10", "BL127S v10":
  the number, the elementary, hyperbolic and normal-distribution functions,
  and Lambert W), CREATE2 through the deterministic proxy, with the
  verification recipe and the smoke test; v9 (five objects) and v1 to v8 (one
  object each) are recorded below them. Deploy a new version with `make deploy-sepolia`,
  `make verify-sepolia`, `make smoke-sepolia` (BL127's) and the `-bl127e`,
  `-bl127h`, `-bl127n`, `-bl127s` targets.
- `BL19.md`, `BL19.json`, `BL19E.json`, `BL19H.json`, `BL19N.json`,
  `BL19S.json`: BL19 v7, five objects from one source, one idea each (salts
  "BL19 v7", "BL19E v7", "BL19H v7", "BL19N v7", "BL19S v7": the number,
  the elementary, hyperbolic and normal-distribution functions, and
  Lambert W), with the `-bl19`, `-bl19e`, `-bl19h`, `-bl19n` and `-bl19s`
  targets. One record covers the five objects, as `Ladder.md` covers its
  contracts. v6 (salts "FP19 v6", …), v5 (Blockulator 2.2, salts "FP256 v5", …) and releases one to
  four are recorded below them; release four (Blockulator 2.1) was BL19,
  BL19X, BL19X2 and BL19X3 (salts "… v4"), whose `BL19X.json`,
  `BL19X2.json` and `BL19X3.json` stay here marked `"release": "Blockulator
  2.1"`, `"current": false`: those addresses are still live, and not part
  of 3.0.
- `Ladder.md`, `Ladder.json`: ladder v15 (salt "BL127 ladder v15"):
  `LadderBL127` and `LadderBL19Deployed`, which call the deployed objects,
  with `LadderRunner` and `EdgeRunner` (v1 to v14 recorded below).
  `make deploy-ladder-sepolia`, `make verify-ladder-sepolia`.
- `RELEASE.md`, `RELEASE.json`: every address in Blockulator 3.0, and those
  of 2.2, 2.1 and 2.0, which stay live.
- `*.sepolia.receipt.json`, `*.mainnet.receipt.json`: the raw receipt of each object's deployment.

## Ethereum mainnet

The library objects go to mainnet at the same CREATE2 addresses as on Sepolia; the ladder stays on Sepolia. The
deployer key is public, so ETH sent to it is swept within a block. `make deploy-mainnet` therefore sends the funding
and every deploy as one Flashbots bundle (`scripts/bl127/bundle.py`): `FUNDER_KEY`'s account moves exactly the gas
the deploys need to the deployer in the bundle's first transaction, and the relay includes the whole bundle in one
block or none of it. The bundle is rebuilt for each block at that block's base fee plus a tip.

1. `make predict-mainnet`: every object's address, and whether it is already there.
2. `make deploy-mainnet-dry`: the identical transactions on an anvil fork, which checks every address and runtime
   and prints the gas and the ETH to fund. No keys needed.
3. `FUNDER_KEY=… DEPLOYER_KEY=… make deploy-mainnet`, then `make verify-mainnet` and `make smoke-mainnet`.

The badge, game, calculator and market contracts of the Huff era were
deployed by hand; their sources and addresses are in
[blockulator-archive](https://github.com/securedataresearch/blockulator-archive).

## Chains: CLZ (Osaka) required

The BL127 and BL19 objects (and their inline libraries) count leading bits
with the CLZ opcode (EIP-7939, Fusaka/Osaka). They are built by solc 0.8.38
for evmVersion osaka, with solc 0.8.24's Yul optimizer sequence pinned
(`scripts/bl127/stdjson.py`; 0.8.38's own sequence builds the BL19 core
over 24,576 bytes), and the explorers receive that same standard-JSON input.
Blockulator 2.2 is the first CLZ build. Releases up to 2.1, recorded above,
were shanghai builds without CLZ and stay deployed on Sepolia.

Supported chains are those with CLZ, as of 2026-10-22 (each was probed live;
the probe's output is not kept in the repository, and the names are the
networks' own for the upgrade that brought CLZ):

| chain | upgrade |
|---|---|
| Ethereum mainnet | Fusaka |
| Sepolia | Fusaka |
| Hoodi | Fusaka |
| Arbitrum One | ArbOS 51 |
| OP Mainnet | Upgrade 19 "Karst" |
| Unichain | Upgrade 19 "Karst" |
| Base | "Azul" |
| Polygon PoS | Lisovo |
| BNB Chain | Osaka / Mendel |
| Gnosis | Fusaka |
| Scroll | Galileo |
| Linea |  |

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
`scripts/bl127/gen.py` (name, library, salt): for each stem `<o>` in `bl127
bl127e bl127h bl127n bl127s bl19 bl19e bl19h bl19n bl19s` (`gen.py
--objects`), `make predict-<o>`,
`deploy-<o>-sepolia` and `verify-<o>-sepolia` (`scripts/bl127/deploy.py`,
`stdjson.py`, `verify.py`); `predict`, `deploy-sepolia` and `verify-sepolia`
are BL127's. A new object or salt edits only the table.
