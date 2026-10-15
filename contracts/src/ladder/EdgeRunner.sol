// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Form, FP127_ADDRESS} from "./ILadder.sol";

/// @title EdgeRunner
/// @notice One eth_call re-verifies any cell of the edges dataset
///         (docs/benchmarks/edges.json): run(op, form, args) evaluates one op
///         once through the chosen library's adapter, with the arguments
///         already in that library's representation
///         (scripts/ladder/edge-inputs.json), and returns the raw result. A
///         revert inside the library is caught and returned as its
///         selector. The adapters are the ladder's; no storage, no owner.
contract EdgeRunner {
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
    address public immutable fp256;

    /// The adapters in form-id order (ILadder.sol `Form`).
    constructor(address[11] memory adapters) {
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
        fp256 = adapters[10];
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
        if (form == Form.FP256) return fp256;
        revert UnknownForm(form);
    }

    /// @return ok      false if the library reverted
    /// @return raw     the result in the library's representation (0 when !ok)
    /// @return reason  the first four bytes of the revert data (0 when ok)
    /// @return gasUsed gas the op consumed inside the adapter, after the
    ///                 adapter and the FP127 object are warm (0 when !ok)
    function run(uint8 op, uint8 form, int256[] calldata args)
        external
        view
        returns (bool ok, int256 raw, bytes4 reason, uint256 gasUsed)
    {
        ILadderAdapter a = ILadderAdapter(adapter(form));
        uint256 warm = address(a).code.length + FP127_ADDRESS.code.length;
        try a.op(op, args) returns (int256 r, uint256 g) {
            ok = true;
            raw = r;
            gasUsed = g + (warm & 0);
        } catch (bytes memory err) {
            if (err.length >= 4) reason = bytes4(err);
        }
    }
}
