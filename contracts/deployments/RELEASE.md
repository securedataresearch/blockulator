# Blockulator 3.0

The public name for this release (2026-10-28, Sepolia, chainId 11155111,
blocks 12,015,304 to 12,015,322). Each contract keeps its own version in its
CREATE2 salt, since the salt names the address. Machine-readable copy:
`RELEASE.json`; notes: `CHANGELOG.md`. It is not on Ethereum mainnet yet,
and the source is ahead of it: FP127 is now v9, five objects by idea with
every op correctly rounded (`FP127.md`, `CHANGELOG.md` Unreleased), not
deployed; the ladder's next runners take `"FP127 ladder v14"`.

| component | version | runtime | address | record |
|---|---|---:|---|---|
| FP127 | FP127 v8 | 23,797 | `0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B` | [FP127.md](FP127.md) |
| FP19 | FP19 v6 | 17,221 | `0x94d9d43D6202827429a8058959eeCf6d232b8729` | [FP19.md](FP19.md) |
| FP19E | FP19E v6 | 23,621 | `0x8e5eE786bDD7c35a2867Fd329441d0BD0fB61092` | [FP19.md](FP19.md) |
| FP19H | FP19H v6 | 13,020 | `0xF059611C1c42543DE6EE82353Eb082Fd8999081f` | [FP19.md](FP19.md) |
| FP19N | FP19N v6 | 17,962 | `0xCe9F09D646B37a9100F05ED1FFD14E9f43180214` | [FP19.md](FP19.md) |
| FP19S | FP19S v6 | 11,338 | `0xf74ba90535224870830e6e89D2b328d4cc09DE48` | [FP19.md](FP19.md) |
| LadderRunner | FP127 ladder v13 | | `0xCbD62BdD4Fdd66EA814198B3B7804Cfab80e170C` | [Ladder.md](Ladder.md) |
| EdgeRunner | FP127 ladder v13 | | `0x05A77934179b701EE2a093bAd83497765ED20d91` | [Ladder.md](Ladder.md) |

FP19 is now five objects by idea: FP19 the number (44 ops, now with
`factorial`, a table for n ≤ 170), FP19E the elementary functions (12),
FP19H the hyperbolic functions (4), FP19N the normal distribution (3: erf,
erfc, normCdf, new in 3.0) and FP19S Lambert W (2);
`contracts/src/fp19/ops.json` names each op's object. FP127 v8 has the same
53 ops as v6 and returns the same words. Every object changed, so every
object has a new salt; the FP19 salts drop the library's old name. FP127 v7
(`0xb97E0b824d86470BfAA52fe44f09363755d52591`, block 12,008,542), sent on
2026-10-27 as 3.0's FP127 with ladder v12, is superseded by v8 before
mainnet; both stay live and verified and are recorded in `FP127.md` and
`Ladder.md`.

**CLZ required.** Every object of this release is an evmVersion osaka build
and counts leading bits with CLZ (EIP-7939). It runs on Ethereum, Sepolia
and the other chains with CLZ, and not on zkSync Era, Avalanche C-Chain or
Polygon zkEVM; the list and the probe are in [README.md](README.md#chains-clz-osaka-required).

The six objects are verified on Sourcify (`match` on creation and runtime
bytecode) and Blockscout, and pass their smoke test against the live
contracts (`make smoke-sepolia`: every committed vector against the live
FP127 and FP19 objects, each equal to the inline library). The four ladder
v13 contracts (`LadderFP127`, `LadderFP19Deployed` and the two runners) are
`exact_match` on Sourcify. Checked live on 2026-10-28: 1,920 ladder cells
through LadderRunner at block 12,015,346 and 276 edge cells through
EdgeRunner at block 12,015,374, 0 mismatches
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
