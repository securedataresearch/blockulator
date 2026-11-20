# Blockulator 3.0

The public name for this release (Sepolia, chainId 11155111; BL127 v10,
BL19 v7 and ladder v15, all deployed on 2026-11-20 UTC, blocks 12,177,776 to
12,177,815). Each contract keeps its own version in its CREATE2 salt, since
the salt names the address. Machine-readable copy: `RELEASE.json`; notes:
`CHANGELOG.md`. It is not on Ethereum mainnet yet.

| component | version | runtime | address | record |
|---|---|---:|---|---|
| BL127 | BL127 v10 | 3,728 | `0x9D7f2c78EB802b83368E816E332A2aFa0997B3f2` | [BL127.md](BL127.md) |
| BL127E | BL127E v10 | 18,808 | `0xfE4627Ba196d0c9c2D068C8599837688A8BE8bD1` | [BL127.md](BL127.md) |
| BL127H | BL127H v10 | 13,093 | `0xC3B57948d3839b6B3358AC25E17fD7A055023704` | [BL127.md](BL127.md) |
| BL127N | BL127N v10 | 9,088 | `0x42f0FDe3EF14d10218126e37A672BE33012f8902` | [BL127.md](BL127.md) |
| BL127S | BL127S v10 | 11,817 | `0x315bF86feeCd5aCF3F9105f94A33ceBFa2e1Cc7E` | [BL127.md](BL127.md) |
| BL19 | BL19 v7 | 17,221 | `0xbbb79a1B3c41553ee6C904D40a13f17EEFDC8230` | [BL19.md](BL19.md) |
| BL19E | BL19E v7 | 23,621 | `0x498DCcD03606E2f7B156Ec1bAE3800E8012cfD64` | [BL19.md](BL19.md) |
| BL19H | BL19H v7 | 13,020 | `0x2431fAeDd11E52EB8c104b051F2dac5DEA67dE5b` | [BL19.md](BL19.md) |
| BL19N | BL19N v7 | 17,962 | `0x0540A33443bc4b2Db8D96CBbcb8117A993227E41` | [BL19.md](BL19.md) |
| BL19S | BL19S v7 | 11,338 | `0x5a1266F89FC5b741e57077CbfEE59a6E48e32BCF` | [BL19.md](BL19.md) |
| LadderRunner | BL127 ladder v15 | | `0xac1f69b4FBAA275429DCb21619f4f39257d7Ba93` | [Ladder.md](Ladder.md) |
| EdgeRunner | BL127 ladder v15 | | `0x4009927DEE803eABFD76057aFF06752611856A60` | [Ladder.md](Ladder.md) |

Both libraries are five objects by idea. BL127 v10: BL127 the number (32
ops: the arithmetic and its directed forms, the conversions, `sqrt`,
`cbrt`, `gavg`, `hypot`, `inv`, `factorial`, the comparisons and the
rounding ops), BL127E the elementary functions (12), BL127H the hyperbolic
functions (4), BL127N the normal distribution (3) and BL127S Lambert W (2);
every one of its 53 ops is correctly rounded on every input (the release
gate's sweep: 217,000 inputs, 212,119 returned results, 0 misrounded, plain and with every rounding
test forced), where v8's transcendentals were rounded with no test.
`contracts/src/bl127/ops.json` names each op's object. BL19 v7: BL19 the
number (44 ops, with `factorial`, a table for n ≤ 170), BL19E the
elementary functions (12), BL19H the hyperbolic functions (4), BL19N the
normal distribution (3: erf, erfc, normCdf, new in 3.0) and BL19S Lambert W
(2); `contracts/src/bl19/ops.json` names each op's object.

BL127 v10 and BL19 v7 are the first deployments under the names BL127 and
BL19: the salts and the verified contract names carry them. Two objects
differ from the ones they supersede. BL127E passes 2^135 in the
middle-stage test of `ln` and `log10`, as the derivation gives, where v9's
passes 2^131. BL19 answers `toBL127` and `fromBL127`, where v6's answers
`toFP127` and `fromFP127`. The other eight objects have the runtime
bytecode of their predecessors, at new addresses under the new salts.

Superseded before mainnet, all still live and verified: BL127 v9 (five
objects, salts `"FP127 v9"` to `"FP127S v9"`, BL127 at
`0x0DF738d125677550a80A46BaF254386C66f96E0d`, blocks 12,017,693 to
12,017,701, 2026-10-29 UTC) and BL19 v6 (five objects, salts `"FP19 v6"` to
`"FP19S v6"`, BL19 at `0x94d9d43D6202827429a8058959eeCf6d232b8729`, blocks
12,015,306 to 12,015,314, 2026-10-28), with ladder v14; BL127 v8
(`0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B`, block 12,015,304, one
object), sent on 2026-10-28 with ladder v13; and BL127 v7
(`0xb97E0b824d86470BfAA52fe44f09363755d52591`, block 12,008,542), sent on
2026-10-27 with ladder v12. They are recorded in `BL127.md`, `BL19.md` and
`Ladder.md`.

**CLZ required.** Every object of this release is an evmVersion osaka build
and counts leading bits with CLZ (EIP-7939). It runs on Ethereum, Sepolia
and the other chains with CLZ, and not on zkSync Era, Avalanche C-Chain or
Polygon zkEVM; the list and the probe are in [README.md](README.md#chains-clz-osaka-required).

The ten objects are verified on Sourcify (`match` on creation and runtime
bytecode) and Blockscout, and pass their smoke test against the live
contracts (`make smoke-sepolia`: every committed vector against the live
BL127 and BL19 objects, each equal to the inline library). The four ladder
v15 contracts (`LadderBL127`, `LadderBL19Deployed` and the two runners) are
`exact_match` on Sourcify. Checked live on 2026-11-20: 1,918 ladder cells
through LadderRunner at block 12,177,870 and 276 edge cells through
EdgeRunner at block 12,177,896, 0 mismatches
(`scripts/ladder/livecap.py`, `scripts/ladder/liveedges.py`).

## Blockulator 2.2

2026-10-23 UTC, the first CLZ (osaka) builds. The five library objects are in
blocks 11,974,968 to 11,974,972. The ladder's v11 runners are in blocks
11,977,389 and 11,977,390; they replaced v10's runners of blocks 11,974,984
and 11,974,985 eight hours later. All seven stay live and verified:

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

2026-10-22 UTC, blocks 11,966,114 to 11,966,639, shanghai builds (no CLZ). All
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
