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

Version 14 (Blockulator 3.0, 2026-10-29, salt `"FP127 ladder v14"`,
`0x4650313237206c61646465722076313400000000000000000000000000000000`) puts
only our deployed objects' forms on chain: `LadderBL127`, which staticcalls
BL127 v9's five objects (BL127 `0x0DF738d125677550a80A46BaF254386C66f96E0d`,
BL127E `0xc16F4C45B78D90A4D4C030cABF4f2A34c1Fb0808`, BL127H
`0xf2F99947aD1cC370bD5388a2997A5E4963a0B27B`, BL127N
`0xAA7Cd9635aE8630379636F533f23DBf2C193d296`, BL127S
`0xB9C2583a7Ad2251444DC7752658B6C1107C25036`; the op's object by
`contracts/src/bl127/ops.json`), and `LadderBL19Deployed`, which staticcalls
BL19 v6's five objects (add, sub and fromUint inline, as `LadderBase` keeps
them pure), with the two runners. The runners take eighteen adapter slots in
form-id order (form 0 `bl127`, form 10 `bl19`); every other slot is the zero
address. The other libraries' adapters run the same Solidity locally (`make
ladder`, `make edges`), and ladder v11's runners, still live, run 2.2's
eleven forms (BL127 v6 and BL19 v5 among them). Deployed 2026-10-29 (UTC) by
`make deploy-ladder-sepolia`, blocks 12,017,704 to 12,017,707, with source
commit `80d0656`. All four are verified on Sourcify, `exact_match`.
`scripts/ladder/livecap.py` and `liveedges.py` re-ran every cell through
these runners on 2026-10-29: 1,913 ladder cells at block 12,017,732 and 276
edge cells at block 12,017,760, 0 mismatches (the datasets' live stamps).
Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0x29409AA44f185b649c614Ece5F49007363C95C92` | [`0x460b2730…`](https://sepolia.etherscan.io/tx/0x460b2730f57ea81db41f3d2818e37687ee5fd5f7211e1af00ab56491ab2bb7c6) | 12,017,704 | 8,004,033 |
| `LadderBL19Deployed` | `0x25B7Ffce88Cc8742720c33B7B74Dd3076E4Ec5B8` | [`0xea7bf1bf…`](https://sepolia.etherscan.io/tx/0xea7bf1bf3e689387253e611c280cf793be688b5b26635b0fc30c57cf82f5b28d) | 12,017,705 | 8,704,753 |
| `LadderRunner` | `0x7683126a7525FE2544F4E9aC1ad50A9DB5Ec3589` | [`0x118cc8ba…`](https://sepolia.etherscan.io/tx/0x118cc8badea6940df5fcd54ff9bd24031b15c1f887cf41e6ecf1a9843c07fc59) | 12,017,706 | 4,728,716 |
| `EdgeRunner` | `0xad11E2a69844A5801aa61ee98dD3E9226bfa4D6A` | [`0x64b0d45d…`](https://sepolia.etherscan.io/tx/0x64b0d45d194d1aac6101318eb4949698d0ca4aa49d582e8b2fab2496797a53c0) | 12,017,707 | 4,541,546 |

Version 13 (2026-10-28, salt `"FP127 ladder v13"`,
`0x4650313237206c61646465722076313300000000000000000000000000000000`;
superseded by v14 on 2026-10-29, still live) put the same two forms on
chain: `LadderBL127`, which staticcalls BL127 v8, the one object, at
`0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B`, and `LadderBL19Deployed`,
which staticcalls BL19 v6's five objects, with the two runners. Deployed
2026-10-28, blocks 12,015,319 to 12,015,322, with source commit `81e4771`.
All four are verified on Sourcify, `exact_match`. The live check on
2026-10-28: 1,920 ladder cells at block 12,015,346 and 276 edge cells at
block 12,015,374, 0 mismatches.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0x01e247ad6b623EB0A3c49342a9eDbEA3e70cDc53` | [`0x6d696462…`](https://sepolia.etherscan.io/tx/0x6d696462d7027197202649432fec050f98f5e3371cc4997375c41f7660971d9c) | 12,015,319 | 7,618,765 |
| `LadderBL19Deployed` | `0xF3b7D5c4Dd2BDda9Be5Ca23D5ea4f1D125afd87c` | [`0xf5b1e683…`](https://sepolia.etherscan.io/tx/0xf5b1e6833193ac536b117c1168ebd355e70818c86f95a85f09af361fe48d149b) | 12,015,320 | 8,704,753 |
| `LadderRunner` | `0xCbD62BdD4Fdd66EA814198B3B7804Cfab80e170C` | [`0x0f908503…`](https://sepolia.etherscan.io/tx/0x0f9085032570dac5bade2975bfd0bd9ffb99137e6aea105094389eceb32233b9) | 12,015,321 | 4,728,740 |
| `EdgeRunner` | `0x05A77934179b701EE2a093bAd83497765ED20d91` | [`0x46d51ee6…`](https://sepolia.etherscan.io/tx/0x46d51ee67424d7752b4f2cf64cadc5a8bd4f34b48e53363a14fcb4000c399ff1) | 12,015,322 | 4,541,570 |

Version 12 (2026-10-27, salt `"FP127 ladder v12"`; superseded by v13 on 2026-10-28, still live) put only our
deployed objects' forms on chain: `LadderBL127`, which staticcalls BL127 v7 at
`0xb97E0b824d86470BfAA52fe44f09363755d52591`, and `LadderBL19Deployed`, which staticcalls BL19 v5's four objects (add, sub and fromUint inline, as `LadderBase` keeps
them pure), with the two runners. Every other form's slot in the runners is the zero address. The other libraries'
adapters run the same Solidity locally (`make ladder`, `make edges`); on chain they would prove nothing more, and
BL127Lib is compiled into its users' contracts, never called at an address of its own. `LadderBL19Deployed` returns
the same word as the inline `LadderBL19` on every cell (`test/ladder/Bl19Deployed.t.sol`).

| contract | address |
|---|---|
| `LadderBL127` | `0x62c48bba4a319225172871B4e2fffF9dB54aB517` |
| `LadderBL19Deployed` | `0x1Ac6cc7a8b10A6610878Ce1f13c65F984c14b50A` |
| `LadderRunner` | `0xe19142cFF76CB942Fa1eEe78956DC9492F25802d` |
| `EdgeRunner` | `0x7759691DAd3Fd4F6aed4a7D8ddBA61a287eF7781` |

All four are verified on Sourcify (`make verify-ladder-sepolia`, exact match). The live check on 2026-10-28:
1,917 ladder cells at block 12,008,919 and 276 edge cells at block
12,008,946, 0 mismatches. An earlier attempt the same day sent
eleven of the full ladder's twenty-one v12 contracts before the account ran dry; they sit unused at their CREATE2
addresses.

Version 11 (the eleven adapters; `LadderBL127` calls BL127 v6,
`LadderBL127Lib` inlines it, and `LadderBL19` inlines BL19 v5 and now
accrues per-second through `compound`; Blockulator 2.2) is deployed with
CREATE2 through the proxy `0x4e59b44847b379578588920cA78FbF26c0B4956C` with
salt `"FP127 ladder v11"` (`0x4650313237206c61646465722076313100000000000000000000000000000000`).
Deployed 2026-10-23 by `make deploy-ladder-sepolia`, blocks 11,977,285 to
11,977,390; ten adapters are byte-identical to v10's (only the salt moved
them), `LadderBL19` changed (#138). All thirteen are verified on Sourcify,
`exact_match`. `scripts/ladder/livecap.py` and `liveedges.py` re-ran every
ladder and edge cell through these runners on 2026-10-23: 9,411 ladder cells
at block 11,977,397 and 1,511 edge cells at block 11,977,550, 0 mismatches.
Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0x81a0F7d29563bC01bFb2004D35D2182af1927D29` | [`0x3fd1862c…`](https://sepolia.etherscan.io/tx/0x3fd1862cce2438e20b055e99506651977d42f9e8f6da483648531a0ff0eff654) | 11,977,285 | 7,476,428 |
| `LadderBL127Lib` | `0xE002CB9Be7Bb6811eF31605851E09ab2dB3BC12D` | [`0x28c6cf25…`](https://sepolia.etherscan.io/tx/0x28c6cf2586385c03c008ee4dab2a20aee3c0e7c68b2b6c2577221f7e036198ce) | 11,977,286 | 35,140,711 |
| `LadderABDK` | `0x4e69D1ED68938730F13d133975EF51A4782b5Ff7` | [`0x8ecdb60f…`](https://sepolia.etherscan.io/tx/0x8ecdb60f1e49a9714a3b98e9c125afd05576206383e8e7e731bb9072e7d53e12) | 11,977,287 | 14,685,571 |
| `LadderSolady` | `0xD9D0094ED27604D3d217Ae94039f3dc75D32Bbcd` | [`0x30d2cd09…`](https://sepolia.etherscan.io/tx/0x30d2cd097fcb6f3d4eb6d37770e146a6ccfa0acb7f030efeb672b4ff0b828917) | 11,977,289 | 11,893,652 |
| `LadderPRB` | `0x6a0edCb1aa47A29af6d1713b4A809B9363f9B675` | [`0x3376df44…`](https://sepolia.etherscan.io/tx/0x3376df449a1a94c72ff9f09929cb11a4cffb50b3334fe101541bf3826ce83d5b) | 11,977,290 | 15,059,948 |
| `LadderQuad` | `0xA8FD4D6402792fD9d72d821CFE3a2876a7F0A25b` | [`0x80c32b49…`](https://sepolia.etherscan.io/tx/0x80c32b49947f41b36158137d78af389a2bfd1f77bb82fe413b3a3cec9f519187) | 11,977,292 | 21,712,282 |
| `LadderBalancer` | `0xd963c032635AA81452199fee949b8d2227d94635` | [`0x36431e3e…`](https://sepolia.etherscan.io/tx/0x36431e3e15af37050c16e7ab86b4b70d1653326c7cd5527ea5bd775f520fd3e8) | 11,977,293 | 12,951,213 |
| `LadderAave` | `0xED5f7672a75F71741A5298610fdf33B3172A648d` | [`0xf90bffca…`](https://sepolia.etherscan.io/tx/0xf90bffcaa676b94d75bf8774f16e602f1965ebf350e4dc757eb571e9e16601e3) | 11,977,294 | 1,997,710 |
| `LadderMorpho` | `0x83D42B353B371772020d0f7cb84eC8E309e328a6` | [`0x4238c560…`](https://sepolia.etherscan.io/tx/0x4238c5600322cbee3adbfabeb407caad1c86d4b5b9302ba9e81e8f51c7e602a4) | 11,977,295 | 1,952,936 |
| `LadderMaker` | `0x49dA892bcAf90726Bf36e0B09109835d97cdc18C` | [`0x8c5cf272…`](https://sepolia.etherscan.io/tx/0x8c5cf2729ebdea8e8ec2536dd57f9796fe557582aca913dd11a1941cb070ce46) | 11,977,297 | 2,676,665 |
| `LadderBL19` | `0xa47a4Fa0aAe8359dABF752ca495625d5315F40e7` | [`0x6ace319c…`](https://sepolia.etherscan.io/tx/0x6ace319cf5c4208d938192a6aba05a5a5d3fb705424144b008c72738f8522b1f) | 11,977,388 | 66,765,131 |
| `LadderRunner` | `0x08b06D93620e7B33cD2d600118a75B45EF779Cec` | [`0x296c3114…`](https://sepolia.etherscan.io/tx/0x296c3114f520c92da7bf9e12a9224cc03c92aa56b2bbee1836214e0e79e711d3) | 11,977,389 | 3,613,397 |
| `EdgeRunner` | `0xf453Dc3C9D5d2E2bF8183941B01F6017eb833B83` | [`0x936b3d38…`](https://sepolia.etherscan.io/tx/0x936b3d38a1be4db0bc4ca45a0b5b00de8bad236e64ae62f98c2be2bca5eddda3) | 11,977,390 | 3,426,239 |

`LadderRunner` and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderBL127` staticcalls
BL127 v6 at `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4`; `LadderBL19` is
inline (BL19Lib) and does not call the BL19 objects.

Version 9 (Blockulator 2.1, still live; the eleven adapters;
`LadderBL127` calls BL127 v5, `LadderBL127Lib` inlines it, and
`LadderBL19` inlines BL19 release four, 67 ops, every one correctly
rounded or exact) is deployed with CREATE2
through the proxy `0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt
`"FP127 ladder v9"`
(`0x4650313237206c61646465722076390000000000000000000000000000000000`).
Deployed 2026-10-21 by `make deploy-ladder-sepolia` (a public RPC answered
one run from a node a block behind its receipt, so the adapters span two
runs; the re-run skipped the three already deployed). All thirteen are
verified on Sourcify: `exact_match` for `LadderBL127`, `LadderBL127Lib`,
`LadderBL19` and both runners, `match` (creation and runtime) for the
other eight. On 2026-10-22 `scripts/ladder/livecap.py` and `liveedges.py`
re-ran 9,383 ladder cells (block 11,966,662) and 1,511 edge cells (block
11,966,815) through these runners, 0 mismatches.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0x95CA3692C51481C68E79679e8296e24571Ce6325` | [`0xf1da4a42…`](https://sepolia.etherscan.io/tx/0xf1da4a42f151fe993fe515926f48aefc6dd596c2a3b18bc3141d6326f5f00435) | 11,966,525 | 7,473,340 |
| `LadderBL127Lib` | `0xdc7236cFfD20d08232DEeaF9E9b5f14a1C6BA6Fa` | [`0x33db4852…`](https://sepolia.etherscan.io/tx/0x33db4852f8bf12685784c05e0e7036ce0cc4a2936e5bb6f9ff9a05c054e2591a) | 11,966,526 | 30,606,536 |
| `LadderABDK` | `0xF73581935FC099EC0e2d2888998c235560da8295` | [`0x588775c7…`](https://sepolia.etherscan.io/tx/0x588775c79ada6a1e9f171cfbcac1378ab84549668f1261002bd1beea34e55104) | 11,966,527 | 14,677,821 |
| `LadderSolady` | `0xD6E506F4aB569b88d54592b985d305e6a3206d88` | [`0x6a8b5ea1…`](https://sepolia.etherscan.io/tx/0x6a8b5ea1f735dfaec2dfe1cbf50e845c9dd95c5e237428f56d27db91ca18676d) | 11,966,630 | 11,885,901 |
| `LadderPRB` | `0x2500fe75cA5AA8bd413dFD2D4D3AE50dE0304b77` | [`0x1c993ddd…`](https://sepolia.etherscan.io/tx/0x1c993ddda5aee7adfd586163b713ebfe335fc09e4f485de6ae3718e7fa601d68) | 11,966,631 | 15,052,209 |
| `LadderQuad` | `0x75c21CDe03D41d30A6E9b12fb7D103258580d785` | [`0x5c378ce7…`](https://sepolia.etherscan.io/tx/0x5c378ce7478be955d991f5c275f787b2f8c0512a684b2cb7c5824e5584841580) | 11,966,632 | 21,704,556 |
| `LadderBalancer` | `0x0499Ec29724A3466E8AFF306feA4Ed91021a964d` | [`0xadde6c8a…`](https://sepolia.etherscan.io/tx/0xadde6c8a4bee2a285fdf9c80b4a6916b961863bf1f0bb7c0d578504f4fef4ac5) | 11,966,633 | 12,943,499 |
| `LadderAave` | `0x7c76453a5C894A69eCb0d5bC33601cD02EC5Af6a` | [`0x48156066…`](https://sepolia.etherscan.io/tx/0x4815606656c0bf738c41e6a9961a88ce6b1be5a7ad7fc51c2ef35dc2e44edd85) | 11,966,634 | 1,997,702 |
| `LadderMorpho` | `0x8117A6a2fF705fA59c1a54575EbE101F77eCf3c0` | [`0xd518b2e9…`](https://sepolia.etherscan.io/tx/0xd518b2e93614cdb74bb0cb62793be4a14b6d11834680c9764c3f8dd9f8c0e558) | 11,966,635 | 1,952,928 |
| `LadderMaker` | `0x18a9E7FF4E3cD2809C56845C9108dbb7616E583c` | [`0xd7d6fe49…`](https://sepolia.etherscan.io/tx/0xd7d6fe49e163ebde904ea501d4661107b5c376b343e4f620b4a1bd40f398c1a7) | 11,966,636 | 2,676,657 |
| `LadderBL19` | `0x6c9b2Bbe9F2fa6A0EB942Dd80eD05edfF8b236CE` | [`0xaedc01e0…`](https://sepolia.etherscan.io/tx/0xaedc01e0cef34d105b0865309245a438b605f3ddad84b3cf0a57c334e1549d3c) | 11,966,637 | 59,926,763 |
| `LadderRunner` | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` | [`0xdc53f3e7…`](https://sepolia.etherscan.io/tx/0xdc53f3e7d1712d2c48d88dbe9f86ccd15ba1820aae41ae3ee7e58efb0d1e63b8) | 11,966,638 | 3,608,617 |
| `EdgeRunner` | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` | [`0x24c6ea71…`](https://sepolia.etherscan.io/tx/0x24c6ea71b802c85740856a3460762136591a76e045f5cfe10ff84d6a670a3060) | 11,966,639 | 3,415,260 |

`LadderRunner` v9 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderBL127` staticcalls
BL127 v5 at `0x619176d72D7a12390F8970802943D344c0fd3fE2`; `LadderBL19` is
inline (BL19Lib) and does not call the BL19 objects.

Version 8 (the eleven adapters; `LadderBL19` inlines BL19 release three, 28 ops,
and answers log1p, expm1, erf, erfc, normCdf, both Lambert branches, powu and
compound on the edges) is deployed with CREATE2 through the proxy
`0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt `"FP127 ladder v8"`
(`0x4650313237206c61646465722076380000000000000000000000000000000000`).
Deployed 2026-10-16 by `make deploy-ladder-sepolia`, all thirteen Sourcify
`exact_match`; every ladder cell a public RPC can execute (9,373 of 9,570)
and every edge cell that makes a call (1,511 of 1,529; the rest are out of
range) was re-run through the live runners by `scripts/ladder/livecap.py`
and `liveedges.py` (see the dataset's live stamp). Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0xeD1AF61768A974Ee7937Bc88BE1ac8b09f5c7489` | [`0xa49d1e12…`](https://sepolia.etherscan.io/tx/0xa49d1e12626a8dccb99eeb6d29708d45c0732666fb43a5dbeaf681c0178c8558) | 11,928,985 | 7,473,340 |
| `LadderBL127Lib` | `0x20f729C8c242c700422D13034d178b697995C227` | [`0xc5772c91…`](https://sepolia.etherscan.io/tx/0xc5772c913b234d4907fefa75af43983febad943d6040fad49b72d14ab4ca902f) | 11,928,986 | 17,660,911 |
| `LadderABDK` | `0xcD9d82eAdb450b61554259A8F5746960f2d513d6` | [`0x00513e36…`](https://sepolia.etherscan.io/tx/0x00513e36816685619089d8601cfcada2378aad7be626c0662611830ffb0d5090) | 11,928,987 | 14,677,821 |
| `LadderSolady` | `0x6B62d824807Ad4832a5cAAf6eeF9aDEdE1DAbf55` | [`0xe763aab4…`](https://sepolia.etherscan.io/tx/0xe763aab4decfdf134a4026dd586a2160f5eb1783654ac886a752c322e50328ef) | 11,928,988 | 11,885,901 |
| `LadderPRB` | `0x7a64b51E343eD5d81cCE075408514d6c87CEA9C9` | [`0x18c7bcdc…`](https://sepolia.etherscan.io/tx/0x18c7bcdc457ef997db4c295f5cb24e64541231cbdc481dfcadea292905822fea) | 11,928,989 | 15,052,209 |
| `LadderQuad` | `0x544276580721Ebf22Aa34b4d7cFAD6af59e9494C` | [`0x836308ed…`](https://sepolia.etherscan.io/tx/0x836308ed8b6419bdcb9832c3a69d4dff1c922949c92c1e7f47261a80d0cdca27) | 11,928,990 | 21,704,556 |
| `LadderBalancer` | `0x1450d0E43c806bEecA93f4f8a48eC8d37b5cd790` | [`0xab63c981…`](https://sepolia.etherscan.io/tx/0xab63c981ae3f197e307124a238b7ff32809ddaf8ad6b7430ebb16bbe7b9979e6) | 11,928,991 | 12,943,499 |
| `LadderAave` | `0xD44a40c99D8b90b996e0f517e95ABa613240c483` | [`0x317690d3…`](https://sepolia.etherscan.io/tx/0x317690d37914e72a8dc103b9d5688052c1f91bd53ed029f3c3b8e201f65ef452) | 11,928,992 | 1,997,702 |
| `LadderMorpho` | `0xFCF803465289B57eD33C1469E40bcbe0B88fb1b9` | [`0x09db2a29…`](https://sepolia.etherscan.io/tx/0x09db2a2961058524a158ad9bdcc82efc61beed6ccc9f6ff852d9a5bf037c7757) | 11,928,993 | 1,952,928 |
| `LadderMaker` | `0x6eB340263F541A35Afb23b06c68Fe698AF8Bb102` | [`0x3fff3b19…`](https://sepolia.etherscan.io/tx/0x3fff3b191d229e32875b1925d5018e6d8c7550f48e41f8eece9814c4f7ea2532) | 11,928,994 | 2,676,657 |
| `LadderBL19` | `0xE33503e51d4BF13DB4d92358cFbE83d4b00F78ED` | [`0x3dfba3ce…`](https://sepolia.etherscan.io/tx/0x3dfba3cee53f8a7bb0c170a812e0a58432b119b90846505364f54c55c70f5e1c) | 11,928,995 | 35,957,651 |
| `LadderRunner` | `0xEf689d3782490066fE911a6dD33357f59caE40fE` | [`0xb8e95d85…`](https://sepolia.etherscan.io/tx/0xb8e95d8570b0433b654ac2e089f57e554573bc4463f272be97749a2a6618cd2c) | 11,928,996 | 3,608,605 |
| `EdgeRunner` | `0x09b8fC41E872279A749a0221AE23D124079AcB44` | [`0xdf3192ad…`](https://sepolia.etherscan.io/tx/0xdf3192ad9df3c9d2e997b796b6c948486539f553801b6da9c4156329a9b30b98) | 11,928,997 | 3,415,260 |

`LadderRunner` v8 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderBL127` staticcalls
BL127 v4 at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`; `LadderBL19` is
inline (BL19Lib) and does not call the BL19 object.

Version 7 (the eleven adapters of version 6; `LadderBL19` now inlines BL19
release two, the 2^-254 kernels) is deployed with CREATE2 through the proxy
`0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt `"FP127 ladder v7"`
(`0x4650313237206c61646465722076370000000000000000000000000000000000`).
Deployed 2026-10-16 by `make deploy-ladder-sepolia`, all thirteen Sourcify
`exact_match`; every cell of the ladder and of the edges was re-run through
the live runners by `scripts/ladder/livecap.py` and `liveedges.py` (see the
dataset's live stamp). Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0x7A2AFB3c8920F2FD9438C31BE76616C46F908f7A` | [`0x29f9db6c…`](https://sepolia.etherscan.io/tx/0x29f9db6c71fec359546fea0b0cc87ebe2f63586bd65073534101e14bd9cd3160) | 11,928,195 | 7,473,340 |
| `LadderBL127Lib` | `0xEc9118F1391151FeAfCfA85e4c7A725eEbf60e35` | [`0x5af28acd…`](https://sepolia.etherscan.io/tx/0x5af28acd8acc144158bf44a43e0a0607bca94b12228cf1326b58360840095cd6) | 11,928,196 | 17,660,911 |
| `LadderABDK` | `0x6757dE3c1408636edc137340bEc5CE662DA713Fd` | [`0x05404842…`](https://sepolia.etherscan.io/tx/0x054048420e215eb4b0f20c1fb59462eea82810bada46336e7e80597fb330aa42) | 11,928,197 | 14,677,821 |
| `LadderSolady` | `0xA8934fCA7852501fC4091A7032fdECFCDb5d49fe` | [`0x7f9e1f11…`](https://sepolia.etherscan.io/tx/0x7f9e1f11680918903c3563235e8cf9ae37121e6f0d794043a0f14dc8a5b69c07) | 11,928,198 | 11,885,901 |
| `LadderPRB` | `0x6548DDB8C5527Bb5aB988d53F086F8Efe4e2272d` | [`0x85bc2ff1…`](https://sepolia.etherscan.io/tx/0x85bc2ff194207a02c414b05634cd94a98bff9efad6136de8fa51e0a6df349c54) | 11,928,199 | 15,052,209 |
| `LadderQuad` | `0xBD94F52a93be55dE10C648aAc4F2E69797A550Ae` | [`0xf5d9f220…`](https://sepolia.etherscan.io/tx/0xf5d9f22031d2086a67e22b5d0af9c508c493b292057ef45214804f5a9e7a04b0) | 11,928,200 | 21,704,556 |
| `LadderBalancer` | `0xe59Bd8D5D5D37aEa387811a3D6840fD4C7BEdB9b` | [`0x5696acab…`](https://sepolia.etherscan.io/tx/0x5696acab3cf42c807a49e2de18e9709e54774187f869d1be152a02182bb8d624) | 11,928,201 | 12,943,499 |
| `LadderAave` | `0x75203daf626a8cB28Be2DDfb7eD10E86CE02952E` | [`0x96b0a85f…`](https://sepolia.etherscan.io/tx/0x96b0a85f7092e051726cd3cde96a86cbb7987a03ef2d12f521a741c7effe7fb4) | 11,928,202 | 1,997,702 |
| `LadderMorpho` | `0xd675ed4E52b77b192D1f573EA41184a795E9AB23` | [`0x272e7d2d…`](https://sepolia.etherscan.io/tx/0x272e7d2da1ec2c2e38a1813900d825dd34c52bddc8e2f7058739d201803ecb92) | 11,928,203 | 1,952,916 |
| `LadderMaker` | `0x0cbADe79657e1b23D8A6bB1143A725F45E41ca75` | [`0x3c1bfb73…`](https://sepolia.etherscan.io/tx/0x3c1bfb73d8be970e1483e2ff2af77560fa479b98ec53ebff2a3bd42ec7437951) | 11,928,204 | 2,676,657 |
| `LadderBL19` | `0xE7fB5f5128dDf48cb4728fF883FA93A95d8a1745` | [`0x6c71f112…`](https://sepolia.etherscan.io/tx/0x6c71f112eeee5ec726c2aa2b5e9adf00042ca966dafceaa29da17fb1eaa4b11c) | 11,928,205 | 20,514,722 |
| `LadderRunner` | `0xfcdf2f1887308316fCF6bb741D79E6edE6800Ec9` | [`0x6cbe682f…`](https://sepolia.etherscan.io/tx/0x6cbe682ff52b105a3915618836b700baca5bef2c156d8346d196ee22be220628) | 11,928,206 | 3,608,629 |
| `EdgeRunner` | `0xa9f8C514F5834eB5dB4fB8c78f2FDe41f671e06E` | [`0x488a564e…`](https://sepolia.etherscan.io/tx/0x488a564eb27b0621d11e5b2a0a4ff9fe278659248a014a9ea7e3e8c30ae41c5f) | 11,928,207 | 3,415,272 |

`LadderRunner` v7 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderBL127` staticcalls
BL127 v4 at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`; `LadderBL19` is
inline (BL19Lib) and does not call the BL19 object.

Version 6 (eleven adapters: the ten of version 5 and BL19, the float,
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
| `LadderBL127` | `0x6ACfFb7E4225456630647b5144Ed3b07E3D2D226` | [`0x3e87d0be…`](https://sepolia.etherscan.io/tx/0x3e87d0bec0446cfe7a3630ca6ed24fe08910f8e5a0fff01df519fc5c904e9772) | 11,922,431 | 7,473,328 |
| `LadderBL127Lib` | `0xaB68F88b7278634569E0C782978dEba588Caa122` | [`0xe7ec70a9…`](https://sepolia.etherscan.io/tx/0xe7ec70a998f9982d4a0855ad744f90b5997e82dd10d2d5578a31995081178e2f) | 11,922,432 | 17,660,911 |
| `LadderABDK` | `0x56506C4ccA4E8F707e4531c41994f16A9de8C172` | [`0x4fd34457…`](https://sepolia.etherscan.io/tx/0x4fd34457a3ca9a8f8888753fcb04750787fd5397a8135cf2ddc05f519e182307) | 11,922,433 | 14,677,821 |
| `LadderSolady` | `0xB0FEFE1De30fA933ecA01b7EBf0c1dDb746393f6` | [`0xc1363f62…`](https://sepolia.etherscan.io/tx/0xc1363f62fd77c7df6492b94447f0e284a08f9f1af6b9a1400c45a535b0fdefc9) | 11,922,434 | 11,885,901 |
| `LadderPRB` | `0x55e2cC994Db287F55AD1c0593C84d28e7b46849A` | [`0x857539db…`](https://sepolia.etherscan.io/tx/0x857539dbec563a605328b1fc9b2d69d31d676bfcdbfad8b723eab1af26c8a05c) | 11,922,435 | 15,052,209 |
| `LadderQuad` | `0xeAD35C97B73b4a7E3012891525D50234cC26195b` | [`0x53d65d2c…`](https://sepolia.etherscan.io/tx/0x53d65d2cf5bb63b9a1714c2d710395c4221467c734a7519d400b7e958cdc4af0) | 11,922,436 | 21,704,556 |
| `LadderBalancer` | `0xad467332fD1a2F4542Fc2cA2523B174D858B09bA` | [`0x088cf012…`](https://sepolia.etherscan.io/tx/0x088cf0126eed4766b611cd9f581afc1b06a000451e257285c54714bc1cb21858) | 11,922,437 | 12,943,499 |
| `LadderAave` | `0x0FBF152FeA6fd1da10192c179fD9b3b241ABbaa6` | [`0xd817a7e4…`](https://sepolia.etherscan.io/tx/0xd817a7e49c7a70e1178234340ee17c34289379e8cb92ecdcf183eae3a947d39d) | 11,922,438 | 1,997,702 |
| `LadderMorpho` | `0x4bc66741ad78C64761B9b6773cB77FFA831Ecc42` | [`0xbc284dd4…`](https://sepolia.etherscan.io/tx/0xbc284dd4e2eb702745635c0a8284c33565ba81eb0e674cb9077e8ea422479f69) | 11,922,439 | 1,952,916 |
| `LadderMaker` | `0xF6A2a34908F75BB561B09cc98EA10E5F5eb6082f` | [`0x7a4f38a0…`](https://sepolia.etherscan.io/tx/0x7a4f38a0959f931b8fecef0a178d32c77a984fa09ad80943061486c4976162ac) | 11,922,440 | 2,676,657 |
| `LadderBL19` | `0x8365C50e10792EbfBec014cEF00313B393BE8E56` | [`0x1a1274e4…`](https://sepolia.etherscan.io/tx/0x1a1274e4c6624be391d54f4ffccacbe39f2c5490b231e18e5cdd91cc2c5f0afc) | 11,922,441 | 16,328,923 |
| `LadderRunner` | `0x0D74eac307a3B8899f30E8297F36fB9732a2906c` | [`0xe108d7b7…`](https://sepolia.etherscan.io/tx/0xe108d7b7f9d522f313f33593f03f97e3db4c09a672264a67d9469ae4daa497ac) | 11,922,442 | 3,608,617 |
| `EdgeRunner` | `0x48630435648FB7436fE018a601069c6C105123fe` | [`0xa246cd0b…`](https://sepolia.etherscan.io/tx/0xa246cd0b44c93f52ac31172f0c394c960968c03474a7992e61678792127bed26) | 11,922,443 | 3,415,272 |

`LadderRunner` v6 and `EdgeRunner` are constructed with the eleven adapter
addresses as one `address[11]` in form-id order; `LadderBL127` staticcalls
BL127 v4 at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`; `LadderBL19` is
inline (BL19Lib) and does not call the BL19 object.

Version 5 (ten adapters calling BL127 v4; ABDKMathQuad, Balancer, Aave,
Morpho and Maker as forms 5 to 9; runner
`0x943E7D93386B33df8CcD4823DBf5C38aFffeF7b2`, EdgeRunner
`0x4A32B0f99FC1e888bB9e5cb85399aDd7890B0957`, salt `"FP127 ladder v5"`) was
deployed 2026-10-15, all twelve Sourcify `exact_match`, and still answers.

Version 4 (five adapters calling BL127 v3, nine scenarios; runner
`0x798C37A3E5B421D480AC850258466b5598A1A555`) was deployed with CREATE2
through the proxy `0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt
`"FP127 ladder v4"`
(`0x4650313237206c61646465722076340000000000000000000000000000000000`).
Version 3 (salt `"FP127 ladder v3"`, runner
`0xae42E3AdEb2FAd105aF59C14714801552867D5E9`) calls BL127 v2 and still answers.
Version 2 (salt `"FP127 ladder v2"`, runner
`0x2d741eC5d66D7559857da1c398AE384A389DdE17`) has the same interface and
still answers, calling BL127 v1.
Deployed 2026-10-07 by `make deploy-ladder-sepolia`, all six Sourcify `exact_match`; it still answers.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0x3b3b7300B22e621a2350353f2D6BCD5B3Cf79cB6` | [`0x23aa191f…`](https://sepolia.etherscan.io/tx/0x23aa191fd3b0a2f563d7e2e6fb0836e309e85b5b0963bb747f2050198d5b69ae) | 11,861,165 | 4,103,006 |
| `LadderBL127Lib` | `0x5Fe3420fc2C330553061bc39d9fb178E7d854Fe1` | [`0x953f7b7b…`](https://sepolia.etherscan.io/tx/0x953f7b7be6a55c5b046e17779e6f0bebcdee75c59f7680cef8c4097c93216cb2) | 11,861,166 | 9,476,398 |
| `LadderABDK` | `0x8974369439217370d5D486FB12EF71C0A1F38897` | [`0x0f38a2be…`](https://sepolia.etherscan.io/tx/0x0f38a2becfe648083df4b167d2ee2dca3fc40034bf91fb30146474dba6477ef7) | 11,861,167 | 9,120,028 |
| `LadderSolady` | `0x9F7766CF9f807799CBB92068257891dAD0372de7` | [`0xe7910122…`](https://sepolia.etherscan.io/tx/0xe79101221ff0ad2d6cc758a5fd00be9a80b7446692fa537d273690780a67555f) | 11,861,168 | 5,935,658 |
| `LadderPRB` | `0xa014CCDd2F71B7D253Ba8A9bC0Fd72eba4d8E038` | [`0x363db9cf…`](https://sepolia.etherscan.io/tx/0x363db9cfd2d198e2f2ff00515d11b98ef4528b7952ad6ffc4b81950ec104c1d1) | 11,861,170 | 9,844,327 |
| `LadderRunner` | `0x798C37A3E5B421D480AC850258466b5598A1A555` | [`0x36e7ee33…`](https://sepolia.etherscan.io/tx/0x36e7ee330e95d3170111756691a4aa9bb7ef9f6916f97c7896ecd1caaa95473e) | 11,861,171 | 2,644,644 |

`LadderRunner` is constructed with the five adapter addresses in that
order; `LadderBL127` staticcalls the BL127 object at
`0xe43F720861074497db2e974E5c4554E4A3b341B9` (version 3).

The version 1 contracts (salt `"FP127 ladder v1"`, runner
`0x3FD3461EE53F9C6f2322CbB3fF97A3EdA522d4a4`, `run(uint8,uint8,uint32)` with
the parameters compiled in) remain on Sepolia and still answer for the v1
dataset, which is in the repository history up to the ladder-inputs merge.

### Version 10

Version 10, superseded by v11 on 2026-10-23 (the eleven adapters; `LadderBL127` calls BL127 v6,
`LadderBL127Lib` inlines it, and `LadderBL19` inlines BL19 v5, 65 ops,
every one correctly rounded or exact; Blockulator 2.2) is deployed with
CREATE2 through the proxy `0x4e59b44847b379578588920cA78FbF26c0B4956C` with
salt `"FP127 ladder v10"`
(`0x4650313237206c61646465722076313000000000000000000000000000000000`).
Deployed 2026-10-22 by `make deploy-ladder-sepolia`, blocks 11,974,973 to
11,974,985; the inline libraries are evmVersion osaka (CLZ) builds. All
thirteen are verified on Sourcify, `exact_match`. `scripts/ladder/livecap.py`
and `liveedges.py` re-ran every ladder and edge cell through these runners
on 2026-10-23: 9,408 ladder cells at block 11,975,057 and 1,511 edge cells
at block 11,975,211, 0 mismatches (`RELEASE.json` and the datasets' live
stamps). Machine-readable copy: `Ladder.json`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderBL127` | `0xA900606ED9e598Cb480d5A83D82482e50Cef34F3` | [`0x7c6329fd…`](https://sepolia.etherscan.io/tx/0x7c6329fd802b3c2781f6fd07a3e5750abd415dd02786c2fa457395301ba4aa20) | 11,974,973 | 7,476,428 |
| `LadderBL127Lib` | `0xdBF8A6fA70aef7d17Ab43e6c0Fdc0dFC9Da97B2d` | [`0x4467861f…`](https://sepolia.etherscan.io/tx/0x4467861fe8a1bc2ee1279f1238550ebf7dab08be583c54512f7f27cc874e7b28) | 11,974,974 | 35,140,711 |
| `LadderABDK` | `0x350c70d2D56f9FD6D468Ec498a307c1d45342437` | [`0x498ec7c3…`](https://sepolia.etherscan.io/tx/0x498ec7c3e7dd3edbb51d2a6b9df9f39381c41a7e827e2ddec869be05c15a9ec5) | 11,974,975 | 14,685,571 |
| `LadderSolady` | `0x234b5b13CCC5c24a39490f1Dee55f29b877B4654` | [`0x67575211…`](https://sepolia.etherscan.io/tx/0x67575211f0bde3c0c25b1598f6bb589d33f03f9cca7fe7f35107dd7246990f8e) | 11,974,976 | 11,893,652 |
| `LadderPRB` | `0x989dc75364b9f01E71a3AbC4b04c01ebBeD518B8` | [`0x738facef…`](https://sepolia.etherscan.io/tx/0x738facef6f7580e3ccf1aebcc0a7d7c907b9d62ded194922a6869344a60688b1) | 11,974,977 | 15,059,948 |
| `LadderQuad` | `0xD72075D5Cf699bF43cD8763802eFFCbe0897a59F` | [`0xb3b617f4…`](https://sepolia.etherscan.io/tx/0xb3b617f451f06987254add9f0766005f2f6413552b3cac4236ca09a0bb741490) | 11,974,978 | 21,712,282 |
| `LadderBalancer` | `0xA07B097e0ebe269A30F8D6CF0231464399Fa1842` | [`0x0918ede4…`](https://sepolia.etherscan.io/tx/0x0918ede46135792191130d876d1d72a3a756db32cf999a756c7a583a43091f1c) | 11,974,979 | 12,951,213 |
| `LadderAave` | `0x8E02fAc70a253CCd1e839A353c7cad28F4d8752b` | [`0x140e580f…`](https://sepolia.etherscan.io/tx/0x140e580fa90320658739eac88243b9feef5fec0749fbb76d232d6252a09f576d) | 11,974,980 | 1,997,710 |
| `LadderMorpho` | `0x2f7D25db5592076159499b0C073717666Ba3D19b` | [`0xabe0c21b…`](https://sepolia.etherscan.io/tx/0xabe0c21b76ef4ec3bb7895d45a41a861a04c9f0e55314055443023cc80ce1a38) | 11,974,981 | 1,952,936 |
| `LadderMaker` | `0x827fEb5AEAc444b36f2DB20BC8edF620cA596C16` | [`0xfc2047c4…`](https://sepolia.etherscan.io/tx/0xfc2047c49f8bfe9bd030b30259d666fb376ef9d077484588c57cd45d1f0c3181) | 11,974,982 | 2,676,665 |
| `LadderBL19` | `0xAcaccb3d337331CB5f9BD89ADA10453D0360E63c` | [`0x11316432…`](https://sepolia.etherscan.io/tx/0x11316432163a62120e6d3a8781f12868687be3975f706f85804cf19d82375347) | 11,974,983 | 66,792,964 |
| `LadderRunner` | `0xF14Ac5DDA9C0c10C50aa4Be9D219509fAa936A9b` | [`0xeece3139…`](https://sepolia.etherscan.io/tx/0xeece3139fee0898c83b0b533fe30aa09e2cfed41a4614302a56a703fd65a466f) | 11,974,984 | 3,613,397 |
| `EdgeRunner` | `0x5123DaA96A96e550665401Bd56AD0770DDB9004e` | [`0xa2a38843…`](https://sepolia.etherscan.io/tx/0xa2a388435f0b6d2263d75e4293716b52cc745b06101d3877ba31721773b568c7) | 11,974,985 | 3,426,239 |


## Calling it

An edge (one op once) through `EdgeRunner`:

```
cast call 0xad11E2a69844A5801aa61ee98dD3E9226bfa4D6A "run(uint8,uint8,int256[])(bool,int256,bytes4,uint256)" \
  <op> <form> "[<arg0>,...]" --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Op ids are the `index` field in `scripts/ladder/edges.json` (0 ln, 1 exp,
2 sqrt, 3 pow, 4 mul, 5 div, 6 lambertW0, 7 lambertWm1, 8 log1p, 9 expm1,
10 compound, 11 powu, 12 erf, 13 erfc, 14 normCdf); the arguments are the
probe's array for the form's scale in `scripts/ladder/edge-inputs.json`,
an integer exponent unscaled. A ladder cell through `LadderRunner`:

```
cast call 0x7683126a7525FE2544F4E9aC1ad50A9DB5Ec3589 \
  "run(uint8,uint8,uint32,int256[])(bool,int256,bytes4,uint256,uint256)" \
  <scenario> <form> <n> "[<p0>,<p1>,...]" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Scenario ids are the `index` field in `scripts/ladder/scenarios.json`
(0 compound, 1 compound-pow, 2 bonding-sqrt, 3 roundtrip, 4 amortise,
5 geo-mean, 6 black-scholes-chain, 7 cumulative-product, 8 compound-annual,
9 accrual-per-second, 10 accrual-continuous, 11 deep-tail-option, 12 decay;
the last four from v5);
forms are 0 bl127, 1 bl127lib, 2 abdk, 3 solady, 4 prb, and from v5
5 quad, 6 balancer, 7 aave, 8 morpho, 9 maker, and from v6 10 bl19. On
the v12 to v14 runners only forms 0 and 10 have an adapter; the others
run on v11's runner, `0x08b06D93620e7B33cD2d600118a75B45EF779Cec`. `p` is
the input's `bl127`, `abdk`, `wad`, `quad`, `ray` or `bl19` array from
`scripts/ladder/inputs.json` (forms 0 and 1 take `bl127`, 2 `abdk`, 3, 4, 6
and 8 `wad`, 5 `quad`, 7 and 9 `ray`, 10 `bl19`),
in the scenario's `order`. The returned `bool` is false when the library
reverted, with the selector in the `bytes4`; `BadParamCount`,
`ParamOutOfRange` and `Unsupported` are the adapter's own errors for a
wrong-length or out-of-range `p` or a scenario outside the library's model.
Decode `int256` by the form's scale (2^128, 2^128, 2^64, 1e18, 1e18; the
`quad` form returns the bit pattern of an IEEE binary128, `bl19` the BL19
word; `ray` is 1e27). The last two values
are gas per step and total gas, measured inside the adapter around the
scenario function.

Example, the headline cell (compound, reference input, BL127, N = 365):

```
cast call 0x7683126a7525FE2544F4E9aC1ad50A9DB5Ec3589 \
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
