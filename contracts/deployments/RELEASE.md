# Blockulator 2.2

The public name for this release (2026-10-22, Sepolia, chainId 11155111,
blocks 11,974,968 to 11,974,985). Each contract keeps its own version in its
CREATE2 salt, since the salt names the address. Machine-readable copy:
`RELEASE.json`; notes: `CHANGELOG.md`.

| component | version | runtime | address | record |
|---|---|---:|---|---|
| FP127 | FP127 v6 | 21,858 | `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4` | [FP127.md](FP127.md) |
| FP256 | FP256 v5 | 10,333 | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` | [FP256.md](FP256.md) |
| FP256E | FP256E v5 | 21,598 | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` | [FP256.md](FP256.md) |
| FP256H | FP256H v5 | 13,021 | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` | [FP256.md](FP256.md) |
| FP256S | FP256S v5 | 24,263 | `0x73E8809F163d4358773cc5F25c134997B4b842F4` | [FP256.md](FP256.md) |
| LadderRunner | FP127 ladder v11 | | `0x08b06D93620e7B33cD2d600118a75B45EF779Cec` | [Ladder.md](Ladder.md) |
| EdgeRunner | FP127 ladder v11 | | `0xf453Dc3C9D5d2E2bF8183941B01F6017eb833B83` | [Ladder.md](Ladder.md) |

FP256 is now four objects by idea: FP256 the number (43 ops), FP256E the
elementary functions (12), FP256H the hyperbolic functions (4) and FP256S
the special functions (6); `contracts/src/fp256/ops.json` names each op's
object. FP127 v6 has 53 ops: `pi` is the constant `FP127Lib.PI` and `gcd`
is gone, in both libraries.

**CLZ required.** Every object of this release is an evmVersion osaka build
and counts leading bits with CLZ (EIP-7939). It runs on Ethereum, Sepolia
and the other chains with CLZ, and not on zkSync Era, Avalanche C-Chain or
Polygon zkEVM; the list and the probe are in [README.md](README.md#chains-clz-osaka-required).

The five objects are verified on Sourcify (`match` on creation and runtime
bytecode) and Blockscout, and pass their smoke tests against the live
contracts (`make smoke-sepolia`, `make smoke-fp256-sepolia`). The thirteen
ladder contracts (ladder v11, redeployed 2026-10-23 after #138's adapter
fix) are `exact_match` on Sourcify. Checked live on 2026-10-23: 9,411 ladder
cells through LadderRunner at block 11,977,397 and 1,511 edge cells through
EdgeRunner at block 11,977,550, 0 mismatches
(`scripts/ladder/livecap.py`, `scripts/ladder/liveedges.py`).

## Blockulator 2.1

2026-10-21, blocks 11,966,114 to 11,966,639, shanghai builds (no CLZ). All
seven stay live and verified:

| component | version | address |
|---|---|---|
| FP127 | FP127 v5 | `0x619176d72D7a12390F8970802943D344c0fd3fE2` |
| FP256 | FP256 v4 | `0xA3C8C8700465F9e20Ff9dfA64066c2EF693Aa6c9` |
| FP256X | FP256X v4 | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` |
| FP256X2 | FP256X2 v4 | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` |
| FP256X3 | FP256X3 v4 | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` |
| LadderRunner | FP127 ladder v9 | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` |
| EdgeRunner | FP127 ladder v9 | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` |

FP127 v5 and the four FP256 release-four objects passed their smoke tests
against the live contracts. Checked live on 2026-10-22: 9,383 ladder cells
through that LadderRunner at block 11,966,662 and 1,511 edge cells through
that EdgeRunner at block 11,966,815, 0 mismatches.

## Blockulator 2.0

2026-10-16: FP127 v4 `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`, FP256 v3
`0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be`, LadderRunner (ladder v8)
`0xEf689d3782490066fE911a6dD33357f59caE40fE`, EdgeRunner
`0x09b8fC41E872279A749a0221AE23D124079AcB44`. All four stay live. Checked
live on 2026-10-16: 9,373 ladder cells through that LadderRunner at block
11,929,034 and 1,511 edge cells through that EdgeRunner at block 11,929,015,
0 mismatches.
