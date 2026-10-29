#!/usr/bin/env python3
"""
Simulate EVM BL127_MUL and Horner evaluation for 2^0.5.
BL127: 128 int bits + 128 frac bits, ONE = 2^128.
"""

MASK128 = (1 << 128) - 1
MOD = 1 << 256

# Coefficients (BL127 format)
COEFFS = [
    0x7ac5115747d8,                                    # C22
    0x9f29a09462d53,                                   # C21
    0x1486d87bca24a71,                                 # C20
    0x24ae7d9788480f70,                                # C19
    0x3ee3a1d249cac3699,                               # C18
    0x661103e6e8ef83bd5e,                              # C17
    0x9c744e6a6d037e9b359,                             # C16
    0xe1b74210e03ffef9130e,                            # C15
    0x1314964d60c074d3410b05,                          # C14
    0x18161931668b3732335b8ec,                         # C13
    0x1c3bd650fc2b5e1a3c2798ba,                        # C12
    0x1e8cac7351bb1ac06cff974a0,                       # C11
    0x1e4cf5158b8eca22258a9523c8,                      # C10
    0x1b5253d395e7c3d9b7d23fb041c,                      # C9
    0x162c0223a5c823fd9180c0672a87,                     # C8
    0xffe5fe2c458634358a5e0cbc3190,                     # C7
    0xa184897c363c3b7a585493a61d0c1,                    # C6
    0x5761ff9e299cc441c5fda6496fc0bb,                  # C5
    0x276556df749cee539977c16ab26986b,                  # C4
    0xe35846b82505fc599d3b15d9947eebb,                  # C3
    0x3d7f7bff058b1d50de2d60dd92e71277,                # C2
    0xb17217f7d1cf79abc9e3b39803f2f637,                # C1
    0x100000000000000000000000000000000,                # C0
]

def bl127_sar(x):
    """Signed arithmetic shift right by 128. For x < 2^255: x >> 128."""
    if x < (1 << 255):
        return x >> 128
    # Negative: -((-x) >> 128)
    return (-((-x) & (MOD - 1)) >> 128) & (MOD - 1)

def bl127_mul_debug(a, b):
    """BL127_MUL(a,b) = (a*b)/2^128 mod 2^256. Returns (result, debug_dict)."""
    a_hi = bl127_sar(a)
    a_lo = a & MASK128
    b_hi = bl127_sar(b)
    b_lo = b & MASK128

    t1 = (a_hi * b_hi) & (MOD - 1)
    t2 = (a_hi * b_lo) & (MOD - 1)
    t3 = (a_lo * b_hi) & (MOD - 1)
    a_lo_b_lo = (a_lo * b_lo) & (MOD - 1)
    t4 = a_lo_b_lo >> 128

    # Result = t1<<128 + t2 + t3 + t4
    term1 = (t1 << 128) & (MOD - 1)
    result = (term1 + t2 + t3 + t4) & (MOD - 1)

    return result, {
        "a_hi": a_hi, "a_lo": a_lo, "b_hi": b_hi, "b_lo": b_lo,
        "t1_a_hi_b_hi": t1, "t2_a_hi_b_lo": t2, "t3_a_lo_b_hi": t3,
        "a_lo_b_lo": a_lo_b_lo, "t4_lo_lo_shifted": t4,
        "term1_shifted": term1,
    }

def bl127_mul(a, b):
    r, _ = bl127_mul_debug(a, b)
    return r

def to_decimal(bl127_val):
    """Convert BL127 to decimal (real value)."""
    return bl127_val / (1 << 128)

def main():
    frac = 0x80000000000000000000000000000000  # 0.5 in BL127
    print("=== BL127 Horner simulation for 2^0.5 ===\n")
    print(f"frac = 0x{frac:032x} = {to_decimal(frac)}\n")

    result = COEFFS[0]  # C22
    print(f"Step 0: result = C22 = 0x{result:x}")
    print(f"        decimal = {to_decimal(result)}\n")

    for i in range(1, min(6, len(COEFFS))):  # First 5 Horner steps (i=1..5)
        coef = COEFFS[i]
        print(f"--- Step {i}: result = BL127_MUL(frac, result) + C{22-i} ---")
        print(f"  result (input) = 0x{result:064x}")
        print(f"  C{22-i} = 0x{coef:x}")

        mul_result, dbg = bl127_mul_debug(frac, result)
        # In bl127_mul_debug(frac, result): a=frac, b=result
        print(f"\n  BL127_MUL(frac, result) breakdown: a=frac, b=result")
        print(f"    a_hi (frac_hi)  = 0x{dbg['a_hi']:032x}, a_lo (frac_lo)  = 0x{dbg['a_lo']:032x}")
        print(f"    b_hi (result_hi)= 0x{dbg['b_hi']:032x}, b_lo (result_lo)= 0x{dbg['b_lo']:032x}  {'<-- b_hi NONZERO!' if dbg['b_hi'] else ''}")
        print(f"    t1 = a_hi*b_hi = 0x{dbg['t1_a_hi_b_hi']:064x}")
        print(f"    t2 = a_hi*b_lo = 0x{dbg['t2_a_hi_b_lo']:064x}")
        print(f"    t3 = a_lo*b_hi = 0x{dbg['t3_a_lo_b_hi']:064x}")
        print(f"    a_lo*b_lo = 0x{dbg['a_lo_b_lo']:064x}")
        print(f"    t4 = (a_lo*b_lo)>>128 = 0x{dbg['t4_lo_lo_shifted']:032x}")
        print(f"    BL127_MUL result = 0x{mul_result:064x}")

        result = (mul_result + coef) & (MOD - 1)
        print(f"\n  result + C{22-i} = 0x{result:064x}")
        print(f"  decimal = {to_decimal(result)}\n")

    # Skip to end: continue from step 6 to 23, tracking when result_hi (b_hi) becomes nonzero
    print("--- Steps 6..23 (tracking when accumulator b_hi becomes nonzero) ---\n")
    nonzero_hi_steps = []
    for i in range(6, len(COEFFS)):
        coef = COEFFS[i]
        _, dbg_before = bl127_mul_debug(frac, result)  # b=result, check b_hi
        if dbg_before["b_hi"]:
            nonzero_hi_steps.append((i, 22 - i, result, dbg_before["b_hi"]))
        mul_result = bl127_mul(frac, result)
        result = (mul_result + coef) & (MOD - 1)
    if nonzero_hi_steps:
        print("  Steps where accumulator (result) had nonzero upper 128 bits BEFORE BL127_MUL:")
        for step_i, coef_idx, acc_val, hi_val in nonzero_hi_steps:
            print(f"    Step {step_i} (before +C{coef_idx}): result=0x{acc_val:064x}, result_hi=0x{hi_val:x}")
    else:
        print("  Accumulator stayed < 2^128 for all steps (result_hi=0 throughout).")
    print()

    # Final result
    print("=== Final result ===")
    print(f"result = 0x{result:064x}")
    print(f"decimal (value/2^128) = {to_decimal(result)}")
    print(f"\nExpected: sqrt(2) * 2^128 = {2**0.5 * (1<<128)}")
    print(f"Actual EVM output: 77190255559275030459785108813856")
    print(f"Our simulation:    {result}")

    # Check: does EVM output match our result?
    evm_out = 77190255559275030459785108813856
    print(f"\nEVM output as decimal: {evm_out / (1<<128)}")
    print(f"Our result as decimal: {result / (1<<128)}")

if __name__ == "__main__":
    main()
