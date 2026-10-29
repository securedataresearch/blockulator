# Huff Contracts

On-chain math implementations in pure Huff assembly, organized by number system.

## Directory Structure

```
huff/
├── bl127/              # 127.128 fixed-point arithmetic
│   ├── constants.huff         # Core constants (ONE_BL127, FRAC_BITS, etc.)
│   ├── arithmetic.huff        # Add, sub, mul, div, conversions
│   ├── tables.huff            # Lookup tables for exp/ln (generated)
│   ├── transcendental.huff    # exp, ln, sqrt
│   └── test_bl127.huff        # Deployable test contract
└── README.md           # This file
```

## BL127: 128.128 Fixed-Point Arithmetic

Signed 128.128 fixed-point: 128 integer bits + 128 fractional bits, two's complement.

- **Precision**: ~38 decimal digits
- **Range**: approximately ±1.7 × 10^38
- **Format**: One `uint256` word

### Files

| File | Purpose |
|------|---------|
| `constants.huff` | Core constants (FRAC_BITS, ONE_BL127, MASK128, etc.) |
| `arithmetic.huff` | Basic operations (add, sub, mul, div) and conversions (to/from fixed18) |
| `tables.huff` | Bit-level lookup tables for exp/ln (135 entries each, ~8.6 KB total) |
| `transcendental.huff` | exp, ln, sqrt using binary digit-by-digit table method |
| `test_bl127.huff` | Deployable test contract exposing all operations |

### Interface

All functions in `test_bl127.huff` accept and return `fixed18` values (value × 10^18):

- `add(uint256, uint256) → uint256`
- `sub(uint256, uint256) → uint256`
- `mul(uint256, uint256) → uint256`
- `div(uint256, uint256) → uint256`
- `exp(uint256) → uint256`
- `ln(uint256) → uint256`
- `sqrt(uint256) → uint256`
- `fromFixed18(uint256) → uint256` — convert to internal bl127 format
- `toFixed18(uint256) → uint256` — convert from internal bl127 format
- `expRaw(uint256) → uint256` — raw bl127 input/output
- `lnRaw(uint256) → uint256` — raw bl127 input/output
- `mulRaw(uint256, uint256) → uint256` — raw bl127 multiply
- `divRaw(uint256, uint256) → uint256` — raw bl127 divide

### How It Works

Internally, inputs are converted from fixed18 to 128.128 format: `bl127 = (fixed18 × 2^128) / 10^18`.

- **Add/Sub**: Single EVM opcodes (`ADD`, `SUB`)
- **Mul**: 4-term schoolbook decomposition to avoid overflow
- **Div**: 64-bit chunked shift-and-divide (~62-bit precision)
- **Exp/Ln**: Binary digit-by-digit table method using precomputed `e^(2^(k-128))` values
- **Sqrt**: Implemented as `exp(ln(x) / 2)` to reuse exp/ln logic

Results are converted back to fixed18 for output.

## Building

```bash
# Compile all Huff contracts
./contracts/deployments/compile-huff.sh

# Or compile individual contracts
huffc --evm-version paris contracts/src/tools/huff/bl127/test_bl127.huff -r
```

Output: `contracts/build/huff/*.bin` and `contracts/build/huff/*.runtime.bin`

## Testing

```bash
# Foundry tests
forge test --match-contract BL127Test     # BL127 arithmetic + transcendentals

# Benchmarks
forge test --match-contract ArithBench          # Gas + precision comparison
forge test --match-contract UnifiedBenchmark    # Cross-library benchmarks
```

## Table Generation

BL127 lookup tables are generated using Python with `mpmath` for high precision:

```bash
# Generate exp/ln tables (135 entries each)
python3 scripts/generators/generate_bl127_tables.py > contracts/src/tools/huff/bl127/tables.huff

# Generate transcendental constants
python3 scripts/generators/generate_bl127_coefficients.py >> contracts/src/tools/huff/bl127/constants.huff
```

## Performance

BL127 is optimized for gas efficiency:
- `add`: ~50 gas
- `mul`: ~140 gas (full precision) or ~125 gas (fast, 1 ULP error for small fractional parts)
- `exp`: ~21k gas
- `ln`: ~41k gas
- `sqrt`: ~63k gas (via exp/ln)

