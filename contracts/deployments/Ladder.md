# Ladder deployment record

The terminal-precision ladder (docs/benchmarks/ladder.md) is reproducible on
chain: `LadderRunner.run(scenario, form, n, p)` executes any cell with one
`eth_call`, where `p` is the input's parameters floored into that library's
representation (scripts/ladder/inputs.json, served at /data/ladder-inputs.json),
and returns the raw result in that representation plus the gas the scenario
consumed inside the adapter. The harness that produced the committed dataset
called this same code, so the two cannot disagree; `scripts/ladder/livecap.py`
re-runs every cell of every input through the live runner and records the
largest N the public RPC completes.

Version 6 (eleven adapters: the ten of version 5 and FP256, the float,
as form 10) is deployed with CREATE2 through the proxy
`0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt `"FP127 ladder v6"`
(`0x4650313237206c61646465722076360000000000000000000000000000000000`).
Deployed 2026-10-15 by `make deploy-ladder-sepolia` (source commit `b548c36`),
all thirteen Sourcify `exact_match`; every cell of the ladder and of the
edges was re-run through the live runners by `scripts/ladder/livecap.py`
and `liveedges.py` (see the dataset's liveNote). Machine-readable copy:
`Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderFP127` | `0x6ACfFb7E4225456630647b5144Ed3b07E3D2D226` | [`0x3e87d0be…`](https://sepolia.etherscan.io/tx/0x3e87d0bec0446cfe7a3630ca6ed24fe08910f8e5a0fff01df519fc5c904e9772) | 11,922,431 | 7,473,328 |
| `LadderFP127Lib` | `0xaB68F88b7278634569E0C782978dEba588Caa122` | [`0xe7ec70a9…`](https://sepolia.etherscan.io/tx/0xe7ec70a998f9982d4a0855ad744f90b5997e82dd10d2d5578a31995081178e2f) | 11,922,432 | 17,660,911 |
| `LadderABDK` | `0x56506C4ccA4E8F707e4531c41994f16A9de8C172` | [`0x4fd34457…`](https://sepolia.etherscan.io/tx/0x4fd34457a3ca9a8f8888753fcb04750787fd5397a8135cf2ddc05f519e182307) | 11,922,433 | 14,677,821 |
| `LadderSolady` | `0xB0FEFE1De30fA933ecA01b7EBf0c1dDb746393f6` | [`0xc1363f62…`](https://sepolia.etherscan.io/tx/0xc1363f62fd77c7df6492b94447f0e284a08f9f1af6b9a1400c45a535b0fdefc9) | 11,922,434 | 11,885,901 |
| `LadderPRB` | `0x55e2cC994Db287F55AD1c0593C84d28e7b46849A` | [`0x857539db…`](https://sepolia.etherscan.io/tx/0x857539dbec563a605328b1fc9b2d69d31d676bfcdbfad8b723eab1af26c8a05c) | 11,922,435 | 15,052,209 |
| `LadderQuad` | `0xeAD35C97B73b4a7E3012891525D50234cC26195b` | [`0x53d65d2c…`](https://sepolia.etherscan.io/tx/0x53d65d2cf5bb63b9a1714c2d710395c4221467c734a7519d400b7e958cdc4af0) | 11,922,436 | 21,704,556 |
| `LadderBalancer` | `0xad467332fD1a2F4542Fc2cA2523B174D858B09bA` | [`0x088cf012…`](https://sepolia.etherscan.io/tx/0x088cf0126eed4766b611cd9f581afc1b06a000451e257285c54714bc1cb21858) | 11,922,437 | 12,943,499 |
| `LadderAave` | `0x0FBF152FeA6fd1da10192c179fD9b3b241ABbaa6` | [`0xd817a7e4…`](https://sepolia.etherscan.io/tx/0xd817a7e49c7a70e1178234340ee17c34289379e8cb92ecdcf183eae3a947d39d) | 11,922,438 | 1,997,702 |
| `LadderMorpho` | `0x4bc66741ad78C64761B9b6773cB77FFA831Ecc42` | [`0xbc284dd4…`](https://sepolia.etherscan.io/tx/0xbc284dd4e2eb702745635c0a8284c33565ba81eb0e674cb9077e8ea422479f69) | 11,922,439 | 1,952,916 |
| `LadderMaker` | `0xF6A2a34908F75BB561B09cc98EA10E5F5eb6082f` | [`0x7a4f38a0…`](https://sepolia.etherscan.io/tx/0x7a4f38a0959f931b8fecef0a178d32c77a984fa09ad80943061486c4976162ac) | 11,922,440 | 2,676,657 |
| `LadderFP256` | `0x8365C50e10792EbfBec014cEF00313B393BE8E56` | [`0x1a1274e4…`](https://sepolia.etherscan.io/tx/0x1a1274e4c6624be391d54f4ffccacbe39f2c5490b231e18e5cdd91cc2c5f0afc) | 11,922,441 | 16,328,923 |
| `LadderRunner` | `0x0D74eac307a3B8899f30E8297F36fB9732a2906c` | [`0xe108d7b7…`](https://sepolia.etherscan.io/tx/0xe108d7b7f9d522f313f33593f03f97e3db4c09a672264a67d9469ae4daa497ac) | 11,922,442 | 3,608,617 |
| `EdgeRunner` | `0x48630435648FB7436fE018a601069c6C105123fe` | [`0xa246cd0b…`](https://sepolia.etherscan.io/tx/0xa246cd0b44c93f52ac31172f0c394c960968c03474a7992e61678792127bed26) | 11,922,443 | 3,415,272 |

`LadderRunner` v6 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderFP127` staticcalls
FP127 v4 at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`; `LadderFP256` is
inline (FP256Lib) and does not call the FP256 object.

Version 5 (ten adapters calling FP127 v4; ABDKMathQuad, Balancer, Aave,
Morpho and Maker as forms 5 to 9; runner
`0x943E7D93386B33df8CcD4823DBf5C38aFffeF7b2`, EdgeRunner
`0x4A32B0f99FC1e888bB9e5cb85399aDd7890B0957`, salt `"FP127 ladder v5"`) was
deployed 2026-10-15, all twelve Sourcify `exact_match`, and still answers.

Version 4 (five adapters calling FP127 v3, nine scenarios; runner
`0x798C37A3E5B421D480AC850258466b5598A1A555`) was deployed with CREATE2
through the proxy `0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt
`"FP127 ladder v4"`
(`0x4650313237206c61646465722076340000000000000000000000000000000000`).
Version 3 (salt `"FP127 ladder v3"`, runner
`0xae42E3AdEb2FAd105aF59C14714801552867D5E9`) calls FP127 v2 and still answers.
Version 2 (salt `"FP127 ladder v2"`, runner
`0x2d741eC5d66D7559857da1c398AE384A389DdE17`) has the same interface and
still answers, calling FP127 v1.
Deployed 2026-10-07 by `make deploy-ladder-sepolia`, all six Sourcify `exact_match`; it still answers.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderFP127` | `0x3b3b7300B22e621a2350353f2D6BCD5B3Cf79cB6` | [`0x23aa191f…`](https://sepolia.etherscan.io/tx/0x23aa191fd3b0a2f563d7e2e6fb0836e309e85b5b0963bb747f2050198d5b69ae) | 11,861,165 | 4,103,006 |
| `LadderFP127Lib` | `0x5Fe3420fc2C330553061bc39d9fb178E7d854Fe1` | [`0x953f7b7b…`](https://sepolia.etherscan.io/tx/0x953f7b7be6a55c5b046e17779e6f0bebcdee75c59f7680cef8c4097c93216cb2) | 11,861,166 | 9,476,398 |
| `LadderABDK` | `0x8974369439217370d5D486FB12EF71C0A1F38897` | [`0x0f38a2be…`](https://sepolia.etherscan.io/tx/0x0f38a2becfe648083df4b167d2ee2dca3fc40034bf91fb30146474dba6477ef7) | 11,861,167 | 9,120,028 |
| `LadderSolady` | `0x9F7766CF9f807799CBB92068257891dAD0372de7` | [`0xe7910122…`](https://sepolia.etherscan.io/tx/0xe79101221ff0ad2d6cc758a5fd00be9a80b7446692fa537d273690780a67555f) | 11,861,168 | 5,935,658 |
| `LadderPRB` | `0xa014CCDd2F71B7D253Ba8A9bC0Fd72eba4d8E038` | [`0x363db9cf…`](https://sepolia.etherscan.io/tx/0x363db9cfd2d198e2f2ff00515d11b98ef4528b7952ad6ffc4b81950ec104c1d1) | 11,861,170 | 9,844,327 |
| `LadderRunner` | `0x798C37A3E5B421D480AC850258466b5598A1A555` | [`0x36e7ee33…`](https://sepolia.etherscan.io/tx/0x36e7ee330e95d3170111756691a4aa9bb7ef9f6916f97c7896ecd1caaa95473e) | 11,861,171 | 2,644,644 |

`LadderRunner` is constructed with the five adapter addresses in that
order; `LadderFP127` staticcalls the FP127 object at
`0xe43F720861074497db2e974E5c4554E4A3b341B9` (version 3).

The version 1 contracts (salt `"FP127 ladder v1"`, runner
`0x3FD3461EE53F9C6f2322CbB3fF97A3EdA522d4a4`, `run(uint8,uint8,uint32)` with
the parameters compiled in) remain on Sepolia and still answer for the v1
dataset, which is in the repository history up to the ladder-inputs merge.

## Calling it

An edge (one op once) through `EdgeRunner`:

```
cast call 0x48630435648FB7436fE018a601069c6C105123fe "run(uint8,uint8,int256[])(bool,int256,bytes4,uint256)" \
  <op> <form> "[<arg0>,...]" --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Op ids are the `index` field in `scripts/ladder/edges.json` (0 ln, 1 exp,
2 sqrt, 3 pow, 4 mul, 5 div, 6 lambertW0, 7 lambertWm1, 8 log1p, 9 expm1,
10 compound, 11 powu, 12 erf, 13 erfc, 14 normCdf); the arguments are the
probe's array for the form's scale in `scripts/ladder/edge-inputs.json`,
an integer exponent unscaled. A ladder cell through `LadderRunner`:

```
cast call 0x0D74eac307a3B8899f30E8297F36fB9732a2906c \
  "run(uint8,uint8,uint32,int256[])(bool,int256,bytes4,uint256,uint256)" \
  <scenario> <form> <n> "[<p0>,<p1>,...]" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Scenario ids are the `index` field in `scripts/ladder/scenarios.json`
(0 compound, 1 compound-pow, 2 bonding-sqrt, 3 roundtrip, 4 amortise,
5 geo-mean, 6 black-scholes-chain, 7 cumulative-product, 8 compound-annual,
9 accrual-per-second, 10 accrual-continuous, 11 deep-tail-option, 12 decay;
the last four from v5);
forms are 0 fp127, 1 fp127lib, 2 abdk, 3 solady, 4 prb, and from v5
5 quad, 6 balancer, 7 aave, 8 morpho, 9 maker, and from v6 10 fp256. `p` is
the input's `fp127`, `abdk`, `wad`, `quad`, `ray` or `fp256` array from
`scripts/ladder/inputs.json` (forms 0 and 1 take `fp127`, 2 `abdk`, 3, 4, 6
and 8 `wad`, 5 `quad`, 7 and 9 `ray`, 10 `fp256`),
in the scenario's `order`. The returned `bool` is false when the library
reverted, with the selector in the `bytes4`; `BadParamCount`,
`ParamOutOfRange` and `Unsupported` are the adapter's own errors for a
wrong-length or out-of-range `p` or a scenario outside the library's model.
Decode `int256` by the form's scale (2^128, 2^128, 2^64, 1e18, 1e18; the
`quad` form returns the bit pattern of an IEEE binary128, `fp256` the FP256
word; `ray` is 1e27). The last two values
are gas per step and total gas, measured inside the adapter around the
scenario function.

Example, the headline cell (compound, reference input, FP127, N = 365):

```
cast call 0x0D74eac307a3B8899f30E8297F36fB9732a2906c \
  "run(uint8,uint8,uint32,int256[])(bool,int256,bytes4,uint256,uint256)" 0 0 365 \
  "[3402823669209384634633746074317682114560000,93228045731763962592705371899114578]" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

## Live cap

Public RPCs limit `eth_call`. Cells needing more than roughly 40M gas (the
transcendental scenarios at N = 10,000) fail with a bare revert from the
runner's try/catch, because the adapter ran out of gas inside it. The
largest N that completes for every input of a form is recorded as
`liveMaxN` in `ladder.json`; the page greys out verify above it. Anyone with
their own node can raise the cap and run every cell.

## Trust model

No storage, no owner, no upgrade path. The adapters are immutable in the
runner. A change to any scenario is a new source, new init code hashes,
new addresses and a new salt string, recorded here.

## Reproduce

```
make predict-ladder            # the addresses above, from the current source
make deploy-ladder-sepolia     # DEPLOYER_KEY in the environment; skips what is deployed
make verify-ladder-sepolia     # Sourcify (and Etherscan with ETHERSCAN_API_KEY)
uv run scripts/ladder/livecap.py   # every cell of every input against the live runner
```
