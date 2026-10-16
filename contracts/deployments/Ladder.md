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

Version 8 (the eleven adapters; `LadderFP256` inlines FP256 release three, 28 ops,
and answers log1p, expm1, erf, erfc, normCdf, both Lambert branches, powu and
compound on the edges) is deployed with CREATE2 through the proxy
`0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt `"FP127 ladder v8"`
(`0x4650313237206c61646465722076380000000000000000000000000000000000`).
Deployed 2026-10-16 by `make deploy-ladder-sepolia`, all thirteen Sourcify
`exact_match`; every cell of the ladder and of the edges was re-run through
the live runners by `scripts/ladder/livecap.py` and `liveedges.py` (see the
dataset's live stamp). Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderFP127` | `0xeD1AF61768A974Ee7937Bc88BE1ac8b09f5c7489` | [`0xa49d1e12…`](https://sepolia.etherscan.io/tx/0xa49d1e12626a8dccb99eeb6d29708d45c0732666fb43a5dbeaf681c0178c8558) | 11,928,985 | 7,473,340 |
| `LadderFP127Lib` | `0x20f729C8c242c700422D13034d178b697995C227` | [`0xc5772c91…`](https://sepolia.etherscan.io/tx/0xc5772c913b234d4907fefa75af43983febad943d6040fad49b72d14ab4ca902f) | 11,928,986 | 17,660,911 |
| `LadderABDK` | `0xcD9d82eAdb450b61554259A8F5746960f2d513d6` | [`0x00513e36…`](https://sepolia.etherscan.io/tx/0x00513e36816685619089d8601cfcada2378aad7be626c0662611830ffb0d5090) | 11,928,987 | 14,677,821 |
| `LadderSolady` | `0x6B62d824807Ad4832a5cAAf6eeF9aDEdE1DAbf55` | [`0xe763aab4…`](https://sepolia.etherscan.io/tx/0xe763aab4decfdf134a4026dd586a2160f5eb1783654ac886a752c322e50328ef) | 11,928,988 | 11,885,901 |
| `LadderPRB` | `0x7a64b51E343eD5d81cCE075408514d6c87CEA9C9` | [`0x18c7bcdc…`](https://sepolia.etherscan.io/tx/0x18c7bcdc457ef997db4c295f5cb24e64541231cbdc481dfcadea292905822fea) | 11,928,989 | 15,052,209 |
| `LadderQuad` | `0x544276580721Ebf22Aa34b4d7cFAD6af59e9494C` | [`0x836308ed…`](https://sepolia.etherscan.io/tx/0x836308ed8b6419bdcb9832c3a69d4dff1c922949c92c1e7f47261a80d0cdca27) | 11,928,990 | 21,704,556 |
| `LadderBalancer` | `0x1450d0E43c806bEecA93f4f8a48eC8d37b5cd790` | [`0xab63c981…`](https://sepolia.etherscan.io/tx/0xab63c981ae3f197e307124a238b7ff32809ddaf8ad6b7430ebb16bbe7b9979e6) | 11,928,991 | 12,943,499 |
| `LadderAave` | `0xD44a40c99D8b90b996e0f517e95ABa613240c483` | [`0x317690d3…`](https://sepolia.etherscan.io/tx/0x317690d37914e72a8dc103b9d5688052c1f91bd53ed029f3c3b8e201f65ef452) | 11,928,992 | 1,997,702 |
| `LadderMorpho` | `0xFCF803465289B57eD33C1469E40bcbe0B88fb1b9` | [`0x09db2a29…`](https://sepolia.etherscan.io/tx/0x09db2a2961058524a158ad9bdcc82efc61beed6ccc9f6ff852d9a5bf037c7757) | 11,928,993 | 1,952,928 |
| `LadderMaker` | `0x6eB340263F541A35Afb23b06c68Fe698AF8Bb102` | [`0x3fff3b19…`](https://sepolia.etherscan.io/tx/0x3fff3b191d229e32875b1925d5018e6d8c7550f48e41f8eece9814c4f7ea2532) | 11,928,994 | 2,676,657 |
| `LadderFP256` | `0xE33503e51d4BF13DB4d92358cFbE83d4b00F78ED` | [`0x3dfba3ce…`](https://sepolia.etherscan.io/tx/0x3dfba3cee53f8a7bb0c170a812e0a58432b119b90846505364f54c55c70f5e1c) | 11,928,995 | 35,957,651 |
| `LadderRunner` | `0xEf689d3782490066fE911a6dD33357f59caE40fE` | [`0xb8e95d85…`](https://sepolia.etherscan.io/tx/0xb8e95d8570b0433b654ac2e089f57e554573bc4463f272be97749a2a6618cd2c) | 11,928,996 | 3,608,605 |
| `EdgeRunner` | `0x09b8fC41E872279A749a0221AE23D124079AcB44` | [`0xdf3192ad…`](https://sepolia.etherscan.io/tx/0xdf3192ad9df3c9d2e997b796b6c948486539f553801b6da9c4156329a9b30b98) | 11,928,997 | 3,415,260 |

`LadderRunner` v8 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderFP127` staticcalls
FP127 v4 at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`; `LadderFP256` is
inline (FP256Lib) and does not call the FP256 object.

Version 7 (the eleven adapters of version 6; `LadderFP256` now inlines FP256
release two, the 2^-254 kernels) is deployed with CREATE2 through the proxy
`0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt `"FP127 ladder v7"`
(`0x4650313237206c61646465722076370000000000000000000000000000000000`).
Deployed 2026-10-16 by `make deploy-ladder-sepolia`, all thirteen Sourcify
`exact_match`; every cell of the ladder and of the edges was re-run through
the live runners by `scripts/ladder/livecap.py` and `liveedges.py` (see the
dataset's live stamp). Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderFP127` | `0x7A2AFB3c8920F2FD9438C31BE76616C46F908f7A` | [`0x29f9db6c…`](https://sepolia.etherscan.io/tx/0x29f9db6c71fec359546fea0b0cc87ebe2f63586bd65073534101e14bd9cd3160) | 11,928,195 | 7,473,340 |
| `LadderFP127Lib` | `0xEc9118F1391151FeAfCfA85e4c7A725eEbf60e35` | [`0x5af28acd…`](https://sepolia.etherscan.io/tx/0x5af28acd8acc144158bf44a43e0a0607bca94b12228cf1326b58360840095cd6) | 11,928,196 | 17,660,911 |
| `LadderABDK` | `0x6757dE3c1408636edc137340bEc5CE662DA713Fd` | [`0x05404842…`](https://sepolia.etherscan.io/tx/0x054048420e215eb4b0f20c1fb59462eea82810bada46336e7e80597fb330aa42) | 11,928,197 | 14,677,821 |
| `LadderSolady` | `0xA8934fCA7852501fC4091A7032fdECFCDb5d49fe` | [`0x7f9e1f11…`](https://sepolia.etherscan.io/tx/0x7f9e1f11680918903c3563235e8cf9ae37121e6f0d794043a0f14dc8a5b69c07) | 11,928,198 | 11,885,901 |
| `LadderPRB` | `0x6548DDB8C5527Bb5aB988d53F086F8Efe4e2272d` | [`0x85bc2ff1…`](https://sepolia.etherscan.io/tx/0x85bc2ff194207a02c414b05634cd94a98bff9efad6136de8fa51e0a6df349c54) | 11,928,199 | 15,052,209 |
| `LadderQuad` | `0xBD94F52a93be55dE10C648aAc4F2E69797A550Ae` | [`0xf5d9f220…`](https://sepolia.etherscan.io/tx/0xf5d9f22031d2086a67e22b5d0af9c508c493b292057ef45214804f5a9e7a04b0) | 11,928,200 | 21,704,556 |
| `LadderBalancer` | `0xe59Bd8D5D5D37aEa387811a3D6840fD4C7BEdB9b` | [`0x5696acab…`](https://sepolia.etherscan.io/tx/0x5696acab3cf42c807a49e2de18e9709e54774187f869d1be152a02182bb8d624) | 11,928,201 | 12,943,499 |
| `LadderAave` | `0x75203daf626a8cB28Be2DDfb7eD10E86CE02952E` | [`0x96b0a85f…`](https://sepolia.etherscan.io/tx/0x96b0a85f7092e051726cd3cde96a86cbb7987a03ef2d12f521a741c7effe7fb4) | 11,928,202 | 1,997,702 |
| `LadderMorpho` | `0xd675ed4E52b77b192D1f573EA41184a795E9AB23` | [`0x272e7d2d…`](https://sepolia.etherscan.io/tx/0x272e7d2da1ec2c2e38a1813900d825dd34c52bddc8e2f7058739d201803ecb92) | 11,928,203 | 1,952,916 |
| `LadderMaker` | `0x0cbADe79657e1b23D8A6bB1143A725F45E41ca75` | [`0x3c1bfb73…`](https://sepolia.etherscan.io/tx/0x3c1bfb73d8be970e1483e2ff2af77560fa479b98ec53ebff2a3bd42ec7437951) | 11,928,204 | 2,676,657 |
| `LadderFP256` | `0xE7fB5f5128dDf48cb4728fF883FA93A95d8a1745` | [`0x6c71f112…`](https://sepolia.etherscan.io/tx/0x6c71f112eeee5ec726c2aa2b5e9adf00042ca966dafceaa29da17fb1eaa4b11c) | 11,928,205 | 20,514,722 |
| `LadderRunner` | `0xfcdf2f1887308316fCF6bb741D79E6edE6800Ec9` | [`0x6cbe682f…`](https://sepolia.etherscan.io/tx/0x6cbe682ff52b105a3915618836b700baca5bef2c156d8346d196ee22be220628) | 11,928,206 | 3,608,629 |
| `EdgeRunner` | `0xa9f8C514F5834eB5dB4fB8c78f2FDe41f671e06E` | [`0x488a564e…`](https://sepolia.etherscan.io/tx/0x488a564eb27b0621d11e5b2a0a4ff9fe278659248a014a9ea7e3e8c30ae41c5f) | 11,928,207 | 3,415,272 |

`LadderRunner` v7 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderFP127` staticcalls
FP127 v4 at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`; `LadderFP256` is
inline (FP256Lib) and does not call the FP256 object.

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
cast call 0x09b8fC41E872279A749a0221AE23D124079AcB44 "run(uint8,uint8,int256[])(bool,int256,bytes4,uint256)" \
  <op> <form> "[<arg0>,...]" --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Op ids are the `index` field in `scripts/ladder/edges.json` (0 ln, 1 exp,
2 sqrt, 3 pow, 4 mul, 5 div, 6 lambertW0, 7 lambertWm1, 8 log1p, 9 expm1,
10 compound, 11 powu, 12 erf, 13 erfc, 14 normCdf); the arguments are the
probe's array for the form's scale in `scripts/ladder/edge-inputs.json`,
an integer exponent unscaled. A ladder cell through `LadderRunner`:

```
cast call 0xEf689d3782490066fE911a6dD33357f59caE40fE \
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
cast call 0xEf689d3782490066fE911a6dD33357f59caE40fE \
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
