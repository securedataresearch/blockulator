# Blockulator 2.0

The public name for this release (2026-10-16, Sepolia, chainId 11155111).
Each contract keeps its own version in its CREATE2 salt, since the salt names
the address. Machine-readable copy: `RELEASE.json`; notes: `CHANGELOG.md`.

| component | version | address | record |
|---|---|---|---|
| FP127 | FP127 v4 | `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1` | [FP127.md](FP127.md) |
| FP256 | FP256 v3 | `0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be` | [FP256.md](FP256.md) |
| LadderRunner | FP127 ladder v8 | `0xEf689d3782490066fE911a6dD33357f59caE40fE` | [Ladder.md](Ladder.md) |
| EdgeRunner | FP127 ladder v8 | `0x09b8fC41E872279A749a0221AE23D124079AcB44` | [Ladder.md](Ladder.md) |

Checked live on 2026-10-16: 9,373 ladder cells through LadderRunner at block
11,929,034 and 1,511 edge cells through EdgeRunner at block 11,929,015, 0
mismatches (`scripts/ladder/livecap.py`, `scripts/ladder/liveedges.py`).
