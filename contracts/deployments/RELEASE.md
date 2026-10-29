# Blockulator 3.0

The public name for this release (Sepolia, chainId 11155111; BL19 v6 on
2026-10-28, blocks 12,015,306 to 12,015,314, and BL127 v9 with ladder v14 on
2026-10-29 UTC, blocks 12,017,693 to 12,017,707). Each contract keeps its own
version in its CREATE2 salt, since the salt names the address.
Machine-readable copy: `RELEASE.json`; notes: `CHANGELOG.md`. It is not on
Ethereum mainnet yet.

| component | version | runtime | address | record |
|---|---|---:|---|---|
| BL127 | BL127 v9 | 3,728 | `0x0DF738d125677550a80A46BaF254386C66f96E0d` | [BL127.md](BL127.md) |
| BL127E | BL127E v9 | 18,808 | `0xc16F4C45B78D90A4D4C030cABF4f2A34c1Fb0808` | [BL127.md](BL127.md) |
| BL127H | BL127H v9 | 13,093 | `0xf2F99947aD1cC370bD5388a2997A5E4963a0B27B` | [BL127.md](BL127.md) |
| BL127N | BL127N v9 | 9,088 | `0xAA7Cd9635aE8630379636F533f23DBf2C193d296` | [BL127.md](BL127.md) |
| BL127S | BL127S v9 | 11,817 | `0xB9C2583a7Ad2251444DC7752658B6C1107C25036` | [BL127.md](BL127.md) |
| BL19 | BL19 v6 | 17,221 | `0x94d9d43D6202827429a8058959eeCf6d232b8729` | [BL19.md](BL19.md) |
| BL19E | BL19E v6 | 23,621 | `0x8e5eE786bDD7c35a2867Fd329441d0BD0fB61092` | [BL19.md](BL19.md) |
| BL19H | BL19H v6 | 13,020 | `0xF059611C1c42543DE6EE82353Eb082Fd8999081f` | [BL19.md](BL19.md) |
| BL19N | BL19N v6 | 17,962 | `0xCe9F09D646B37a9100F05ED1FFD14E9f43180214` | [BL19.md](BL19.md) |
| BL19S | BL19S v6 | 11,338 | `0xf74ba90535224870830e6e89D2b328d4cc09DE48` | [BL19.md](BL19.md) |
| LadderRunner | BL127 ladder v14 | | `0x7683126a7525FE2544F4E9aC1ad50A9DB5Ec3589` | [Ladder.md](Ladder.md) |
| EdgeRunner | BL127 ladder v14 | | `0xad11E2a69844A5801aa61ee98dD3E9226bfa4D6A` | [Ladder.md](Ladder.md) |

Both libraries are five objects by idea. BL127 v9: BL127 the number (32
ops: the arithmetic and its directed forms, the conversions, `sqrt`,
`cbrt`, `gavg`, `hypot`, `inv`, `factorial`, the comparisons and the
rounding ops), BL127E the elementary functions (12), BL127H the hyperbolic
functions (4), BL127N the normal distribution (3) and BL127S Lambert W (2);
every one of its 53 ops is correctly rounded on every input (the release
gate's sweep: 212,119 inputs, 0 misrounded, plain and with every rounding
test forced), where v8's transcendentals were rounded with no test.
`contracts/src/bl127/ops.json` names each op's object. BL19 v6: BL19 the
number (44 ops, now with `factorial`, a table for n ≤ 170), BL19E the
elementary functions (12), BL19H the hyperbolic functions (4), BL19N the
normal distribution (3: erf, erfc, normCdf, new in 3.0) and BL19S Lambert W
(2); `contracts/src/bl19/ops.json` names each op's object. Every object
changed, so every object has a new salt; the BL19 salts drop the library's
old name. BL127 v8 (`0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B`, block
12,015,304, one object), sent on 2026-10-28 as 3.0's BL127 with ladder v13,
and v7 (`0xb97E0b824d86470BfAA52fe44f09363755d52591`, block 12,008,542),
sent on 2026-10-27 with ladder v12, are superseded by v9 before mainnet; all
stay live and verified and are recorded in `BL127.md` and `Ladder.md`.

**CLZ required.** Every object of this release is an evmVersion osaka build
and counts leading bits with CLZ (EIP-7939). It runs on Ethereum, Sepolia
and the other chains with CLZ, and not on zkSync Era, Avalanche C-Chain or
Polygon zkEVM; the list and the probe are in [README.md](README.md#chains-clz-osaka-required).

The ten objects are verified on Sourcify (`match` on creation and runtime
bytecode) and Blockscout, and pass their smoke test against the live
contracts (`make smoke-sepolia`: every committed vector against the live
BL127 and BL19 objects, each equal to the inline library). The four ladder
v14 contracts (`LadderBL127`, `LadderBL19Deployed` and the two runners) are
`exact_match` on Sourcify. Checked live on 2026-10-29: 1,913 ladder cells
through LadderRunner at block 12,017,732 and 276 edge cells through
EdgeRunner at block 12,017,760, 0 mismatches
(`scripts/ladder/livecap.py`, `scripts/ladder/liveedges.py`).

## Blockulator 2.2

2026-10-22, blocks 11,974,968 to 11,974,985, the first CLZ (osaka) builds.
All seven stay live and verified:

| component | version | runtime | address |
|---|---|---:|---|
| BL127 | BL127 v6 | 21,858 | `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4` |
| BL19 | BL19 v5 | 10,333 | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` |
| BL19E | BL19E v5 | 21,598 | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` |
| BL19H | BL19H v5 | 13,021 | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` |
| BL19S | BL19S v5 | 24,263 | `0x73E8809F163d4358773cc5F25c134997B4b842F4` |
| LadderRunner | BL127 ladder v11 | | `0x08b06D93620e7B33cD2d600118a75B45EF779Cec` |
| EdgeRunner | BL127 ladder v11 | | `0xf453Dc3C9D5d2E2bF8183941B01F6017eb833B83` |

BL19 v5 was four objects by idea: BL19 the number (43 ops), BL19E the
elementary functions (12), BL19H the hyperbolic functions (4) and BL19S
the special functions (6: erf, erfc, normCdf, both Lambert branches and
factorial). BL127 v6 has 53 ops: `pi` became the constant `BL127Lib.PI`
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
| BL127 | BL127 v5 | `0x619176d72D7a12390F8970802943D344c0fd3fE2` |
| BL19 | BL19 v4 | `0xA3C8C8700465F9e20Ff9dfA64066c2EF693Aa6c9` |
| BL19X | BL19X v4 | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` |
| BL19X2 | BL19X2 v4 | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` |
| BL19X3 | BL19X3 v4 | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` |
| LadderRunner | BL127 ladder v9 | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` |
| EdgeRunner | BL127 ladder v9 | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` |

BL127 v5 and the four BL19 release-four objects passed their smoke tests
against the live contracts. Checked live on 2026-10-22: 9,383 ladder cells
through that LadderRunner at block 11,966,662 and 1,511 edge cells through
that EdgeRunner at block 11,966,815, 0 mismatches.

## Blockulator 2.0

2026-10-16: BL127 v4 `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`, BL19 v3
`0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be`, LadderRunner (ladder v8)
`0xEf689d3782490066fE911a6dD33357f59caE40fE`, EdgeRunner
`0x09b8fC41E872279A749a0221AE23D124079AcB44`. All four stay live. Checked
live on 2026-10-16: 9,373 ladder cells through that LadderRunner at block
11,929,034 and 1,511 edge cells through that EdgeRunner at block 11,929,015,
0 mismatches.
