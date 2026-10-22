# Blockulator 2.1

The public name for this release (2026-10-21, Sepolia, chainId 11155111,
blocks 11,966,114 to 11,966,639). Each contract keeps its own version in its
CREATE2 salt, since the salt names the address. Machine-readable copy:
`RELEASE.json`; notes: `CHANGELOG.md`.

| component | version | address | record |
|---|---|---|---|
| FP127 | FP127 v5 | `0x619176d72D7a12390F8970802943D344c0fd3fE2` | [FP127.md](FP127.md) |
| FP256 | FP256 v4 | `0xA3C8C8700465F9e20Ff9dfA64066c2EF693Aa6c9` | [FP256.md](FP256.md) |
| FP256X | FP256X v4 | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` | [FP256.md](FP256.md) |
| FP256X2 | FP256X2 v4 | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` | [FP256.md](FP256.md) |
| FP256X3 | FP256X3 v4 | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` | [FP256.md](FP256.md) |
| LadderRunner | FP127 ladder v9 | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` | [Ladder.md](Ladder.md) |
| EdgeRunner | FP127 ladder v9 | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` | [Ladder.md](Ladder.md) |

FP127 v5 and the four FP256 release-four objects pass their smoke tests
against the live contracts (`make smoke-sepolia`, `make smoke-fp256-sepolia`).
Checked live on 2026-10-22: 9,383 ladder cells through LadderRunner at block
11,966,662 and 1,511 edge cells through EdgeRunner at block 11,966,815, 0
mismatches (`scripts/ladder/livecap.py`, `scripts/ladder/liveedges.py`).

## Blockulator 2.0

2026-10-16: FP127 v4 `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`, FP256 v3
`0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be`, LadderRunner (ladder v8)
`0xEf689d3782490066fE911a6dD33357f59caE40fE`, EdgeRunner
`0x09b8fC41E872279A749a0221AE23D124079AcB44`. All four stay live. Checked
live on 2026-10-16: 9,373 ladder cells through that LadderRunner at block
11,929,034 and 1,511 edge cells through that EdgeRunner at block 11,929,015,
0 mismatches.
