+++
title = "FP127"
description = "Signed 127.128 fixed point. One int256, 128 fractional bits (38 digits at 1), 49 ops. One Yul source, two forms: a deployed object and an inline library."

[extra]
group = "library"
+++

Both forms are generated from one file and fuzzed equal across the full `int256` domain, reverts included.

## Encoding

`value × 2^128` in an `int256`, two's complement. `ONE` is `2^128`. Range ±1.7 × 10^38, 128 fractional bits: 38 digits at 1, 32 at 10^−6, 8 at 10^−30. Every op takes and returns this one type. `fromFixed18` and `toFixed18` convert to and from WAD.

Errors: `Overflow()`, `DivisionByZero()`, `OutOfRange()`. Nothing wraps.

## Deployed form

{{ <deployment /> }}

No storage, no owner, no upgrade path. A new version is a new salt and a new address.

`sqrt(2)` from the command line:

```sh
cast call 0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1 "sqrt(int256)(int256)" \
  680564733841876926926749214863536422912 \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# 481231938336009023090067544955250113854
python3 -c "print(481231938336009023090067544955250113854 / 2**128)"
# 1.4142135623730951
```

From Solidity:

```solidity
import {IFP127} from "fp127/IFP127.sol";

contract StaticcallExample {
    IFP127 public constant FP127 = IFP127(0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1);
    int256 internal constant ONE = int256(1) << 128;

    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external view returns (int256 balanceWad) {
        int256 b = FP127.fromFixed18(principalWad);
        int256 growth = FP127.add(ONE, FP127.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127.mul(b, growth);
        }
        return FP127.toFixed18(b);
    }
}
```

## Inline form

`FP127Lib.sol`: the same Yul in `memory-safe` assembly, one `internal pure` function per op. No external call: about 1,200 gas cheaper than the `staticcall` on `add` and `mul`, 170 on `exp` and `sqrt`; on `pow`, the erf family and Lambert W the deployed object is cheaper.

```sh
forge install securedataresearch/blockulator
echo "fp127/=lib/blockulator/contracts/src/fp127/" >> remappings.txt
```

```solidity
import {FP127Lib} from "fp127/FP127Lib.sol";

contract CompoundExample {
    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external pure returns (int256 balanceWad) {
        int256 b = FP127Lib.fromFixed18(principalWad);
        int256 growth = FP127Lib.add(FP127Lib.ONE, FP127Lib.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127Lib.mul(b, growth);
        }
        return FP127Lib.toFixed18(b);
    }
}
```

Both examples are compiled and tested in `test/examples/` against the [ladder's](/results/ladder/#compound) compound scenario.

## The ops

{{ <optable /> }}

## For agents

[`/.well-known/agent.json`](/.well-known/agent.json), [`/llms.txt`](/llms.txt), ABI at [`/data/abi.json`](/data/abi.json). Reads are `eth_call`: no gas, no wallet.
