// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Form, FP127_ADDRESS} from "./ILadder.sol";

/// @title LadderRunner
/// @notice One eth_call re-verifies any cell of the terminal-precision ladder
///         (docs/benchmarks/ladder.json): run(scenario, form, n, p) executes the
///         scenario for n steps through the chosen library's adapter, with the
///         parameters p already in that library's representation
///         (scripts/ladder/inputs.json), and returns the raw result. A revert
///         inside the library is caught and returned as its selector, so the
///         caller sees `reverts` instead of a failed call. No storage, no
///         owner; the adapter addresses are immutable.
contract LadderRunner {
    error UnknownForm(uint8 form);

    address public immutable fp127;
    address public immutable fp127lib;
    address public immutable abdk;
    address public immutable solady;
    address public immutable prb;
    address public immutable quad;
    address public immutable balancer;
    address public immutable aave;
    address public immutable morpho;
    address public immutable maker;
    address public immutable fp19;
    address public immutable solmate;
    address public immutable oz;
    address public immutable uniswap;
    address public immutable prbud;
    address public immutable snekmate;

    /// The adapters in form-id order (ILadder.sol `Form`).
    constructor(address[16] memory adapters) {
        fp127 = adapters[0];
        fp127lib = adapters[1];
        abdk = adapters[2];
        solady = adapters[3];
        prb = adapters[4];
        quad = adapters[5];
        balancer = adapters[6];
        aave = adapters[7];
        morpho = adapters[8];
        maker = adapters[9];
        fp19 = adapters[10];
        solmate = adapters[11];
        oz = adapters[12];
        uniswap = adapters[13];
        prbud = adapters[14];
        snekmate = adapters[15];
    }

    function adapter(uint8 form) public view returns (address) {
        if (form == Form.FP127) return fp127;
        if (form == Form.FP127LIB) return fp127lib;
        if (form == Form.ABDK) return abdk;
        if (form == Form.SOLADY) return solady;
        if (form == Form.PRB) return prb;
        if (form == Form.QUAD) return quad;
        if (form == Form.BALANCER) return balancer;
        if (form == Form.AAVE) return aave;
        if (form == Form.MORPHO) return morpho;
        if (form == Form.MAKER) return maker;
        if (form == Form.FP19) return fp19;
        if (form == Form.SOLMATE) return solmate;
        if (form == Form.OZ) return oz;
        if (form == Form.UNISWAP) return uniswap;
        if (form == Form.PRBUD) return prbud;
        if (form == Form.SNEKMATE) return snekmate;
        revert UnknownForm(form);
    }

    /// @return ok          false if the library reverted
    /// @return raw         the result in the library's representation (0 when !ok)
    /// @return reason      the first four bytes of the revert data (0 when ok)
    /// @return gasPerStep  gasTotal / n (0 when !ok)
    /// @return gasTotal    gas the scenario function consumed inside the adapter:
    ///                     the parameter reads and the loop, not the call into the
    ///                     adapter. The adapter and the FP127 object are warmed
    ///                     first, so the FP127 form's staticcalls are steady-state
    ///                     and the figure does not depend on what the caller
    ///                     touched earlier in the transaction. 0 when !ok.
    function run(uint8 scenario, uint8 form, uint32 n, int256[] calldata p)
        external
        view
        returns (bool ok, int256 raw, bytes4 reason, uint256 gasPerStep, uint256 gasTotal)
    {
        ILadderAdapter a = ILadderAdapter(adapter(form));
        uint256 warm = address(a).code.length + FP127_ADDRESS.code.length;
        try a.run(scenario, n, p) returns (int256 r, uint256 g) {
            ok = true;
            raw = r;
            gasTotal = g + (warm & 0);
            gasPerStep = n == 0 ? g : g / n;
        } catch (bytes memory err) {
            if (err.length >= 4) reason = bytes4(err);
        }
    }
}
