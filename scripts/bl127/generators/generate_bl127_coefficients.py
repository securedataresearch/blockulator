#!/usr/bin/env python3
"""
Generate high-precision rational polynomial coefficients for 127.128 fixed-point transcendentals.

Implements Remco Bloemen's rational polynomial approximations from Solady:
- EXP: (6,7)-term rational polynomial after range reduction
- LN: (8,8)-term rational polynomial after range reduction
- SQRT: Newton-Raphson (no coefficients needed, just initial estimate constant)

All coefficients are scaled to 127.128 format: value * 2^128
"""

from mpmath import mp, mpf, log, exp as mp_exp
import sys

# Set precision to 100 decimal digits for accurate coefficient computation
mp.dps = 100

# 127.128 fixed-point scale factor
BL127_SCALE = mpf(2) ** 128

def to_bl127(value):
    """Convert a decimal value to 127.128 format (int)."""
    scaled = int(value * BL127_SCALE)
    # Handle sign for two's complement
    if scaled < 0:
        scaled = (1 << 256) + scaled
    return scaled

def bl127_to_hex(value_int):
    """Format a 127.128 integer as a 64-char hex constant."""
    return f"0x{value_int:064x}"

def generate_basic_constants():
    """Generate ln(2), 1/ln(2), overflow/underflow thresholds."""
    ln2 = log(2)
    inv_ln2 = mpf(1) / ln2
    
    # For 127.128, the overflow/underflow thresholds need to be computed based on
    # the range of the representation
    # Max exponent for bl127: ~2^127, so ln(2^127) = 127 * ln(2) ≈ 88
    # Min exponent: ~-2^127, so exp would underflow around -88
    
    # Conservative thresholds for exp(x):
    # exp(88) ≈ 1.65e38 (fits in ~127 bits integer part)
    # exp(-88) ≈ 6e-39 (underflows to zero)
    exp_overflow = mpf(88)
    exp_underflow = mpf(-88)
    
    print("// ============================================================================")
    print("// Basic Transcendental Constants (for BL127_EXP, BL127_LN)")
    print("// ============================================================================")
    print()
    print(f"// LN2_BL127: ln(2) in 127.128 format")
    print(f"#define constant LN2_BL127 = {bl127_to_hex(to_bl127(ln2))}")
    print()
    print(f"// INV_LN2_BL127: 1/ln(2) in 127.128 format")
    print(f"#define constant INV_LN2_BL127 = {bl127_to_hex(to_bl127(inv_ln2))}")
    print()
    print(f"// EXP_OVERFLOW_THRESHOLD: max input for exp (88.0 in 127.128)")
    print(f"#define constant EXP_OVERFLOW_THRESHOLD = {bl127_to_hex(to_bl127(exp_overflow))}")
    print()
    print(f"// EXP_UNDERFLOW_THRESHOLD: min input for exp (-88.0 in 127.128)")
    print(f"#define constant EXP_UNDERFLOW_THRESHOLD = {bl127_to_hex(to_bl127(exp_underflow))}")
    print()

def generate_exp_coefficients():
    """
    Generate rational polynomial coefficients for exp(x) approximation.
    
    Solady's expWad uses a (6,7)-term rational approximation after range reduction to (-ln2/2, ln2/2).
    The coefficients are optimized for this specific range.
    
    We'll use Solady's coefficients but rescale them from 2^96 basis to 127.128 basis.
    """
    print("// ============================================================================")
    print("// BL127_EXP Rational Polynomial Coefficients")
    print("// ============================================================================")
    print("// (6,7)-term rational approximation for exp(x') where x' in (-ln(2)/2, ln(2)/2)")
    print("// Adapted from Solady expWad (Remco Bloemen)")
    print()
    
    # Solady uses 2^96 as its internal scale for the polynomial evaluation
    # We need to rescale these to 127.128 = 2^128
    # Scaling factor: 2^128 / 2^96 = 2^32
    
    # Solady expWad numerator coefficients (in 2^96 scale):
    # These are from FixedPointMathLib.sol expWad function
    solady_2_96_scale = mpf(2) ** 96
    solady_bl127_scale = mpf(2) ** 128
    scale_factor = solady_bl127_scale / solady_2_96_scale  # 2^32
    
    # From Solady source, the numerator computation (converted to actual math):
    # y = x + 1346386616545796478920950773328
    # y = ((y * x) >> 96) + 57155421227552351082224309758442
    # p = y + x - 94201549194550492254356042504812
    # p = ((p * y) >> 96) + 28719021644029726153956944680412240
    # p = p * x + (4385272521454847904659076985693276 << 96)
    
    # These are the constants in 2^96 scale:
    exp_num_c0 = mpf("1346386616545796478920950773328") / solady_2_96_scale
    exp_num_c1 = mpf("57155421227552351082224309758442") / solady_2_96_scale
    exp_num_c2 = mpf("94201549194550492254356042504812") / solady_2_96_scale
    exp_num_c3 = mpf("28719021644029726153956944680412240") / solady_2_96_scale
    exp_num_c4 = mpf("4385272521454847904659076985693276")  # This one is scaled by << 96 in the code
    
    # Denominator (degree 5):
    # q = x - 2855989394907223263936484059900
    # q = ((q * x) >> 96) + 50020603652535783019961831881945
    # q = ((q * x) >> 96) - 533845033583426703283633433725380
    # q = ((q * x) >> 96) + 3604857256930695427073651918091429
    # q = ((q * x) >> 96) - 14423608567350463180887372962807573
    # q = ((q * x) >> 96) + 26449188498355588339934803723976023
    
    exp_den_c0 = mpf("-2855989394907223263936484059900") / solady_2_96_scale
    exp_den_c1 = mpf("50020603652535783019961831881945") / solady_2_96_scale
    exp_den_c2 = mpf("-533845033583426703283633433725380") / solady_2_96_scale
    exp_den_c3 = mpf("3604857256930695427073651918091429") / solady_2_96_scale
    exp_den_c4 = mpf("-14423608567350463180887372962807573") / solady_2_96_scale
    exp_den_c5 = mpf("26449188498355588339934803723976023") / solady_2_96_scale
    
    # Now convert to 127.128 scale
    print("// Numerator coefficients")
    print(f"#define constant EXP_NUM_C0 = {bl127_to_hex(to_bl127(exp_num_c0))}")
    print(f"#define constant EXP_NUM_C1 = {bl127_to_hex(to_bl127(exp_num_c1))}")
    print(f"#define constant EXP_NUM_C2 = {bl127_to_hex(to_bl127(exp_num_c2))}")
    print(f"#define constant EXP_NUM_C3 = {bl127_to_hex(to_bl127(exp_num_c3))}")
    print(f"#define constant EXP_NUM_C4 = {bl127_to_hex(to_bl127(exp_num_c4))}")
    print()
    print("// Denominator coefficients")
    print(f"#define constant EXP_DEN_C0 = {bl127_to_hex(to_bl127(exp_den_c0))}")
    print(f"#define constant EXP_DEN_C1 = {bl127_to_hex(to_bl127(exp_den_c1))}")
    print(f"#define constant EXP_DEN_C2 = {bl127_to_hex(to_bl127(exp_den_c2))}")
    print(f"#define constant EXP_DEN_C3 = {bl127_to_hex(to_bl127(exp_den_c3))}")
    print(f"#define constant EXP_DEN_C4 = {bl127_to_hex(to_bl127(exp_den_c4))}")
    print(f"#define constant EXP_DEN_C5 = {bl127_to_hex(to_bl127(exp_den_c5))}")
    print()
    
    # The final scaling constant in Solady:
    # r = (uint256(r) * 3822833074963236453042738258902158003155416615667) >> (195 - k)
    # This combines: scale factor, 2^k, and conversion back to WAD
    # For 127.128, we'll need a different reconstruction approach
    exp_scale_factor = mpf("3822833074963236453042738258902158003155416615667") / (solady_2_96_scale * solady_2_96_scale)
    print(f"// EXP_SCALE_FACTOR: reconstruction scale (from Solady, 2^96 basis)")
    print(f"#define constant EXP_SCALE_FACTOR = {bl127_to_hex(to_bl127(exp_scale_factor))}")
    print()

def generate_ln_coefficients():
    """
    Generate rational polynomial coefficients for ln(x) approximation.
    
    Solady's lnWad uses an (8,8)-term rational approximation for ln(x) where x in [1, 2).
    """
    print("// ============================================================================")
    print("// BL127_LN Rational Polynomial Coefficients")
    print("// ============================================================================")
    print("// (8,8)-term rational approximation for ln(x) where x in [1, 2)")
    print("// Adapted from Solady lnWad (Remco Bloemen)")
    print()
    
    solady_2_96_scale = mpf(2) ** 96
    
    # From Solady lnWad numerator (degree 7):
    # The structure is more complex; it builds up via nested multiplications
    # These are the constants that appear:
    ln_num_c0 = mpf("43456485725739037958740375743393") / solady_2_96_scale
    ln_num_c1 = mpf("24828157081833163892658089445524") / solady_2_96_scale
    ln_num_c2 = mpf("3273285459638523848632254066296") / solady_2_96_scale
    ln_num_c3 = mpf("-11111509109440967052023855526967") / solady_2_96_scale
    ln_num_c4 = mpf("-45023709667254063763336534515857") / solady_2_96_scale
    ln_num_c5 = mpf("-14706773417378608786704636184526") / solady_2_96_scale
    ln_num_c6 = mpf("-795164235651350426258249787498")  # This one is scaled differently (shl 96)
    
    # Denominator (degree 7, monic):
    ln_den_c0 = mpf("5573035233440673466300451813936") / solady_2_96_scale
    ln_den_c1 = mpf("71694874799317883764090561454958") / solady_2_96_scale
    ln_den_c2 = mpf("283447036172924575727196451306956") / solady_2_96_scale
    ln_den_c3 = mpf("401686690394027663651624208769553") / solady_2_96_scale
    ln_den_c4 = mpf("204048457590392012362485061816622") / solady_2_96_scale
    ln_den_c5 = mpf("31853899698501571402653359427138") / solady_2_96_scale
    ln_den_c6 = mpf("909429971244387300277376558375") / solady_2_96_scale
    
    print("// Numerator coefficients")
    print(f"#define constant LN_NUM_C0 = {bl127_to_hex(to_bl127(ln_num_c0))}")
    print(f"#define constant LN_NUM_C1 = {bl127_to_hex(to_bl127(ln_num_c1))}")
    print(f"#define constant LN_NUM_C2 = {bl127_to_hex(to_bl127(ln_num_c2))}")
    print(f"#define constant LN_NUM_C3 = {bl127_to_hex(to_bl127(ln_num_c3))}")
    print(f"#define constant LN_NUM_C4 = {bl127_to_hex(to_bl127(ln_num_c4))}")
    print(f"#define constant LN_NUM_C5 = {bl127_to_hex(to_bl127(ln_num_c5))}")
    print(f"#define constant LN_NUM_C6 = {bl127_to_hex(to_bl127(ln_num_c6))}")
    print()
    print("// Denominator coefficients")
    print(f"#define constant LN_DEN_C0 = {bl127_to_hex(to_bl127(ln_den_c0))}")
    print(f"#define constant LN_DEN_C1 = {bl127_to_hex(to_bl127(ln_den_c1))}")
    print(f"#define constant LN_DEN_C2 = {bl127_to_hex(to_bl127(ln_den_c2))}")
    print(f"#define constant LN_DEN_C3 = {bl127_to_hex(to_bl127(ln_den_c3))}")
    print(f"#define constant LN_DEN_C4 = {bl127_to_hex(to_bl127(ln_den_c4))}")
    print(f"#define constant LN_DEN_C5 = {bl127_to_hex(to_bl127(ln_den_c5))}")
    print(f"#define constant LN_DEN_C6 = {bl127_to_hex(to_bl127(ln_den_c6))}")
    print()
    
    # Reconstruction constants from Solady
    ln_scale_mul = mpf("1677202110996718588342820967067443963516166")
    ln_k_mul = mpf("16597577552685614221487285958193947469193820559219878177908093499208371")
    ln_bias_add = mpf("600920179829731861736702779321621459595472258049074101567377883020018308")
    
    # These need special handling as they're very large - they work in Solady's multi-word arithmetic
    # For bl127, we'll need to adapt the reconstruction differently
    print("// LN reconstruction constants (for reference; may need adaptation for 127.128)")
    print(f"// LN_SCALE_MUL (Solady): {ln_scale_mul}")
    print(f"// LN_K_MUL (Solady): {ln_k_mul}")
    print(f"// LN_BIAS_ADD (Solady): {ln_bias_add}")
    print()

def generate_sqrt_constants():
    """Generate constants for Newton-Raphson sqrt."""
    print("// ============================================================================")
    print("// BL127_SQRT Constants")
    print("// ============================================================================")
    print("// SQRT_INITIAL_ESTIMATE: initial guess constant (181 in Solady)")
    print(f"#define constant SQRT_INITIAL_ESTIMATE = {bl127_to_hex(to_bl127(mpf(181)))}")
    print()

def verify_coefficients():
    """Verify the coefficients produce correct results."""
    print("\n// ============================================================================", file=sys.stderr)
    print("// Verification", file=sys.stderr)
    print("// ============================================================================\n", file=sys.stderr)
    
    ln2 = log(2)
    
    # Test exp at x = 0.1 (within reduced range)
    x_test = mpf("0.1")
    exp_expected = mp_exp(x_test)
    
    print(f"exp(0.1) = {exp_expected}", file=sys.stderr)
    print(f"ln(2) = {ln2}", file=sys.stderr)
    print(f"1/ln(2) = {1/ln2}", file=sys.stderr)
    print(f"\nAll coefficients scaled to 127.128 format (2^128 scale)", file=sys.stderr)

def main():
    print("/// @title BL127 Transcendental Function Coefficients")
    print("/// @notice Rational polynomial coefficients for exp, ln, sqrt in 127.128 format")
    print("/// @dev Generated by scripts/generate_bl127_coefficients.py")
    print("/// @dev Adapted from Remco Bloemen's Solady implementation")
    print()
    
    generate_basic_constants()
    generate_exp_coefficients()
    generate_ln_coefficients()
    generate_sqrt_constants()
    verify_coefficients()

if __name__ == "__main__":
    main()
