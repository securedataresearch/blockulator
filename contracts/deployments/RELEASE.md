# Blockulator 3.0

The public name for this release (Sepolia, chainId 11155111; FP19 v6 on
2026-10-28, blocks 12,015,306 to 12,015,314, and FP127 v9 with ladder v14 on
2026-10-29 UTC, blocks 12,017,693 to 12,017,707). Each contract keeps its own
version in its CREATE2 salt, since the salt names the address.
Machine-readable copy: `RELEASE.json`; notes: `CHANGELOG.md`. It is not on
Ethereum mainnet yet.

| component | version | runtime | address | record |
|---|---|---:|---|---|
| FP127 | FP127 v9 | 3,728 | `0x0DF738d125677550a80A46BaF254386C66f96E0d` | [FP127.md](FP127.md) |
| FP127E | FP127E v9 | 18,808 | `0xc16F4C45B78D90A4D4C030cABF4f2A34c1Fb0808` | [FP127.md](FP127.md) |
| FP127H | FP127H v9 | 13,093 | `0xf2F99947aD1cC370bD5388a2997A5E4963a0B27B` | [FP127.md](FP127.md) |
| FP127N | FP127N v9 | 9,088 | `0xAA7Cd9635aE8630379636F533f23DBf2C193d296` | [FP127.md](FP127.md) |
| FP127S | FP127S v9 | 11,817 | `0xB9C2583a7Ad2251444DC7752658B6C1107C25036` | [FP127.md](FP127.md) |
| FP19 | FP19 v6 | 17,221 | `0x94d9d43D6202827429a8058959eeCf6d232b8729` | [FP19.md](FP19.md) |
| FP19E | FP19E v6 | 23,621 | `0x8e5eE786bDD7c35a2867Fd329441d0BD0fB61092` | [FP19.md](FP19.md) |
| FP19H | FP19H v6 | 13,020 | `0xF059611C1c42543DE6EE82353Eb082Fd8999081f` | [FP19.md](FP19.md) |
| FP19N | FP19N v6 | 17,962 | `0xCe9F09D646B37a9100F05ED1FFD14E9f43180214` | [FP19.md](FP19.md) |
| FP19S | FP19S v6 | 11,338 | `0xf74ba90535224870830e6e89D2b328d4cc09DE48` | [FP19.md](FP19.md) |
| LadderRunner | FP127 ladder v14 | | `0x7683126a7525FE2544F4E9aC1ad50A9DB5Ec3589` | [Ladder.md](Ladder.md) |
| EdgeRunner | FP127 ladder v14 | | `0xad11E2a69844A5801aa61ee98dD3E9226bfa4D6A` | [Ladder.md](Ladder.md) |

Both libraries are five objects by idea. FP127 v9: FP127 the number (32
ops: the arithmetic and its directed forms, the conversions, `sqrt`,
`cbrt`, `gavg`, `hypot`, `inv`, `factorial`, the comparisons and the
rounding ops), FP127E the elementary functions (12), FP127H the hyperbolic
functions (4), FP127N the normal distribution (3) and FP127S Lambert W (2);
every one of its 53 ops is correctly rounded on every input (the release
gate's sweep: 212,119 inputs, 0 misrounded, plain and with every rounding
test forced), where v8's transcendentals were rounded with no test.
`contracts/src/fp127/ops.json` names each op's object. FP19 v6: FP19 the
number (44 ops, now with `factorial`, a table for n ≤ 170), FP19E the
elementary functions (12), FP19H the hyperbolic functions (4), FP19N the
normal distribution (3: erf, erfc, normCdf, new in 3.0) and FP19S Lambert W
(2); `contracts/src/fp19/ops.json` names each op's object. Every object
changed, so every object has a new salt; the FP19 salts drop the library's
old name. FP127 v8 (`0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B`, block
12,015,304, one object), sent on 2026-10-28 as 3.0's FP127 with ladder v13,
and v7 (`0xb97E0b824d86470BfAA52fe44f09363755d52591`, block 12,008,542),
sent on 2026-10-27 with ladder v12, are superseded by v9 before mainnet; all
stay live and verified and are recorded in `FP127.md` and `Ladder.md`.

**CLZ required.** Every object of this release is an evmVersion osaka build
and counts leading bits with CLZ (EIP-7939). It runs on Ethereum, Sepolia
and the other chains with CLZ, and not on zkSync Era, Avalanche C-Chain or
Polygon zkEVM; the list and the probe are in [README.md](README.md#chains-clz-osaka-required).

The ten objects are verified on Sourcify (`match` on creation and runtime
bytecode) and Blockscout, and pass their smoke test against the live
contracts (`make smoke-sepolia`: every committed vector against the live
FP127 and FP19 objects, each equal to the inline library). The four ladder
v14 contracts (`LadderFP127`, `LadderFP19Deployed` and the two runners) are
`exact_match` on Sourcify. Checked live on 2026-10-29: 1,913 ladder cells
through LadderRunner at block 12,017,732 and 276 edge cells through
EdgeRunner at block 12,017,760, 0 mismatches
(`scripts/ladder/livecap.py`, `scripts/ladder/liveedges.py`).

## Blockulator 2.2

2026-10-22, blocks 11,974,968 to 11,974,985, the first CLZ (osaka) builds.
All seven stay live and verified:

| component | version | runtime | address |
|---|---|---:|---|
| FP127 | FP127 v6 | 21,858 | `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4` |
| FP19 | FP19 v5 | 10,333 | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` |
| FP19E | FP19E v5 | 21,598 | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` |
| FP19H | FP19H v5 | 13,021 | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` |
| FP19S | FP19S v5 | 24,263 | `0x73E8809F163d4358773cc5F25c134997B4b842F4` |
| LadderRunner | FP127 ladder v11 | | `0x08b06D93620e7B33cD2d600118a75B45EF779Cec` |
| EdgeRunner | FP127 ladder v11 | | `0xf453Dc3C9D5d2E2bF8183941B01F6017eb833B83` |

FP19 v5 was four objects by idea: FP19 the number (43 ops), FP19E the
elementary functions (12), FP19H the hyperbolic functions (4) and FP19S
the special functions (6: erf, erfc, normCdf, both Lambert branches and
factorial). FP127 v6 has 53 ops: `pi` became the constant `FP127Lib.PI`
and `gcd` went, in both libraries. The five objects are verified on
Sourcify (`match`) and Blockscout and passed their smoke tests against the
live contracts. The thirteen ladder contracts (ladder v11, redeployed
2026-10-23 after #138's adapter fix) are `exact_match` on Sourcify. Checked
live on 2026-10-23: 9,411 ladder cells through that LadderRunner at block
11,977,397 and 1,511 edge cells through that EdgeRunner at block
11,977,550, 0 mismatches.

## Blockulator 2.1

2026-10-21, blocks 11,966,114 to 11,966,639, shanghai builds (no CLZ). All
seven stay live and verified:

| component | version | address |
|---|---|---|
| FP127 | FP127 v5 | `0x619176d72D7a12390F8970802943D344c0fd3fE2` |
| FP19 | FP19 v4 | `0xA3C8C8700465F9e20Ff9dfA64066c2EF693Aa6c9` |
| FP19X | FP19X v4 | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` |
| FP19X2 | FP19X2 v4 | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` |
| FP19X3 | FP19X3 v4 | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` |
| LadderRunner | FP127 ladder v9 | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` |
| EdgeRunner | FP127 ladder v9 | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` |

FP127 v5 and the four FP19 release-four objects passed their smoke tests
against the live contracts. Checked live on 2026-10-22: 9,383 ladder cells
through that LadderRunner at block 11,966,662 and 1,511 edge cells through
that EdgeRunner at block 11,966,815, 0 mismatches.

## Blockulator 2.0

2026-10-16: FP127 v4 `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`, FP19 v3
`0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be`, LadderRunner (ladder v8)
`0xEf689d3782490066fE911a6dD33357f59caE40fE`, EdgeRunner
`0x09b8fC41E872279A749a0221AE23D124079AcB44`. All four stay live. Checked
live on 2026-10-16: 9,373 ladder cells through that LadderRunner at block
11,929,034 and 1,511 edge cells through that EdgeRunner at block 11,929,015,
0 mismatches.
