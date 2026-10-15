+++
title = "Library"
description = "The deployed FP127 object, the inline Solidity library, the encoding, and every op."
+++

FP127 is one Yul source that generates two forms. Both are in [the repository]({{ config.extra.repo }}) and both are proven equal on the full `int256` domain, including which inputs revert and with what data.

## Encoding

A value is one `int256` holding `value × 2^128`, two's complement. Encode with `int256(value * 2**128)`, decode by dividing by `2^128`. `ONE` is `2^128`. Range about ±1.7 × 10^38, 128 fractional bits, about 38 decimal digits. Every parameter and result of every op is that one type; there is no 18-decimal flavour of each op. `fromFixed18` and `toFixed18` are the bridge to WAD, and they are the only place a WAD value should meet FP127.

Errors are `Overflow()`, `DivisionByZero()` and `OutOfRange()`. Arithmetic is checked: nothing wraps.

## Deployed form

{{ <deployment /> }}

Any contract can `staticcall` it, and every contract that does runs identical bytecode. There is no storage, no owner and no upgrade path; a change to the source is a new init code hash, a new salt and a new address, recorded in the repository.

A read from the command line, `sqrt(2)`:

```sh
cast call 0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1 "sqrt(int256)(int256)" \
  680564733841876926926749214863536422912 \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# 481231938336009023090067544955250113854
python3 -c "print(481231938336009023090067544955250113854 / 2**128)"
# 1.4142135623730951
```

From Solidity, through the interface:

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

`FP127Lib.sol` holds the same Yul bodies in `memory-safe` assembly blocks, one `internal pure` function per op, so there is no external call and no shared address. It is the cheapest per op and the form to use when the math belongs inside your contract.

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

Both examples are compiled and tested in the repository under `test/examples/`, against the compound scenario of the [ladder](/demo/). Through the deployed object each op costs about 700 gas more than inline, the price of the `staticcall`; the [compare](/compare/) page has both columns for every op.

## The ops

Generated from the Yul source: the signature and selector, what the op computes, the domain, and what it reverts on. Precision and gas are joined from the committed reports.

{{ <optable /> }}

## For agents

The same address and ABI are published for machines at [`/.well-known/agent.json`](/.well-known/agent.json) and [`/llms.txt`](/llms.txt). The ABI is [`/data/abi.json`](/data/abi.json). Reads are `eth_call`: no gas, no wallet, no transaction.
