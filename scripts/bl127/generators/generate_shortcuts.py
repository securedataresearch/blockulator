#!/usr/bin/env python3
"""
Generate shortcut constants and Huff guard code for BL127 transcendental functions.

This script systematically produces precomputed input/output pairs for common values,
enabling fast-path shortcuts that bypass expensive polynomial evaluations.

Output:
  1. shortcut_constants.huff - All #define constant lines for new constants
  2. Per-function Huff guard snippets (printed to stdout)
  3. shortcut_verify.json - Verification data for testing

Usage:
  python3 generate_shortcuts.py > guards.txt
  # Then copy shortcut_constants.huff to contracts/archive/huff/src/bl127/
  # And paste guard snippets from guards.txt into each function
"""

import mpmath
import json
import sys
from fractions import Fraction
from pathlib import Path

mpmath.mp.dps = 80  # 80 decimal digits for intermediate calculations

# BL127 format constants
BL127_SCALE = mpmath.mpf(2) ** 128
BL127_MAX = (mpmath.mpf(2) ** 127) - 1  # Max positive value
BL127_MIN = -(mpmath.mpf(2) ** 127)     # Min negative value

# Existing constants in constants.huff that we can reference
EXISTING_CONSTANTS = {
    'ONE_BL127': mpmath.mpf(1),
    'HALF_BL127': mpmath.mpf('0.5'),
    'LN2_BL127': mpmath.log(2),
    'INV_LN2_BL127': 1 / mpmath.log(2),
    'SQRT2_BL127': mpmath.sqrt(2),
    'INV_E_BL127': 1 / mpmath.e,
}

# From transcendental_utils.huff
EXISTING_CONSTANTS['ONE_THIRD_BL127'] = mpmath.mpf(1) / 3
EXISTING_CONSTANTS['LOG2_10_BL127'] = mpmath.log(10, 2)
EXISTING_CONSTANTS['INV_LOG2_10_BL127'] = 1 / mpmath.log(10, 2)

# Lambert W values (W1 through W64 exist)
for i in range(1, 65):
    EXISTING_CONSTANTS[f'LAMBERTW0_W{i}'] = mpmath.lambertw(i, k=0)

def to_bl127_hex(value):
    """Convert a decimal value to 127.128 fixed-point hex string."""
    bl127_int = int(mpmath.nint(value * BL127_SCALE))
    if bl127_int < 0:
        bl127_int = (1 << 256) + bl127_int
    return f"0x{bl127_int:064x}"

def to_bl127_int(value):
    """Convert a decimal value to 127.128 fixed-point integer."""
    return int(mpmath.nint(value * BL127_SCALE))

def is_representable(value):
    """Check if value can be represented in BL127 without overflow."""
    if not mpmath.isfinite(value):
        return False
    return BL127_MIN <= value <= BL127_MAX

def find_existing_constant(value, tolerance=1e-40):
    """Find an existing constant that matches this value."""
    for name, const_val in EXISTING_CONSTANTS.items():
        if abs(float(value - const_val)) < tolerance:
            return name
    return None

def sanitize_name(s):
    """Convert a value description to a valid constant name."""
    s = str(s).upper()
    s = s.replace('.', '_DOT_')
    s = s.replace('-', 'NEG')
    s = s.replace('/', '_DIV_')
    s = s.replace('(', '_').replace(')', '_')
    s = s.replace(' ', '_')
    return s

# ============================================================================
# Input Universe
# ============================================================================

def build_input_universe():
    """Build the set of interesting input values."""
    inputs = {}
    
    # Small positive integers (1-20)
    for i in range(1, 21):
        inputs[f'INT_{i}'] = mpmath.mpf(i)
    
    # More integers up to 100
    for i in [25, 27, 32, 36, 49, 50, 64, 81, 100]:
        inputs[f'INT_{i}'] = mpmath.mpf(i)
    
    # Small negative integers
    for i in range(1, 11):
        inputs[f'NEG_{i}'] = mpmath.mpf(-i)
    
    # Simple fractions
    fractions = [
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 8), (1, 10),
        (2, 3), (3, 4), (3, 2), (5, 2), (5, 4), (7, 4), (3, 8), (5, 8), (7, 8),
        (1, 16), (1, 32), (1, 64), (1, 100),
    ]
    for num, den in fractions:
        inputs[f'FRAC_{num}_{den}'] = mpmath.mpf(num) / den
    
    # Negative fractions
    for num, den in [(1, 2), (1, 3), (1, 4), (1, 10), (3, 2)]:
        inputs[f'FRAC_NEG{num}_{den}'] = mpmath.mpf(-num) / den
    
    # Powers of 2
    for k in range(-10, 11):
        if k != 0 and k != 1:  # 1 and 2 already covered
            inputs[f'POW2_{k}' if k >= 0 else f'POW2_NEG{-k}'] = mpmath.power(2, k)
    
    # Powers of 10
    for k in [-3, -2, -1, 1, 2, 3]:
        if k != 1:  # 10 already covered as INT_10
            inputs[f'POW10_{k}' if k >= 0 else f'POW10_NEG{-k}'] = mpmath.power(10, k)
    
    # Transcendental constants
    inputs['E'] = mpmath.e
    inputs['PI'] = mpmath.pi
    inputs['PHI'] = (1 + mpmath.sqrt(5)) / 2  # Golden ratio
    inputs['SQRT2'] = mpmath.sqrt(2)
    inputs['SQRT3'] = mpmath.sqrt(3)
    inputs['LN2'] = mpmath.log(2)
    inputs['LN10'] = mpmath.log(10)
    
    # Composites
    inputs['E_SQ'] = mpmath.e ** 2
    inputs['E_CU'] = mpmath.e ** 3
    inputs['INV_E'] = 1 / mpmath.e
    inputs['PI_SQ'] = mpmath.pi ** 2
    inputs['TWO_PI'] = 2 * mpmath.pi
    inputs['PI_DIV_2'] = mpmath.pi / 2
    inputs['PI_DIV_4'] = mpmath.pi / 4
    
    return inputs

# ============================================================================
# Function Definitions
# ============================================================================

FUNCTIONS = {
    'exp': {
        'compute': lambda x: mpmath.exp(x),
        'domain': lambda x: True,  # All real numbers
        'gas': 2700,
        'done_label': 'exp_done',
    },
    'exp2': {
        'compute': lambda x: mpmath.power(2, x),
        'domain': lambda x: True,
        'gas': 2500,
        'done_label': 'exp2_done',
    },
    'ln': {
        'compute': lambda x: mpmath.log(x),
        'domain': lambda x: x > 0,
        'gas': 3800,
        'done_label': 'ln_done',
    },
    'log2': {
        'compute': lambda x: mpmath.log(x, 2),
        'domain': lambda x: x > 0,
        'gas': 3500,
        'done_label': 'log2_end',
    },
    'log10': {
        'compute': lambda x: mpmath.log10(x),
        'domain': lambda x: x > 0,
        'gas': 3600,
        'done_label': 'log10_done',
    },
    'exp10': {
        'compute': lambda x: mpmath.power(10, x),
        'domain': lambda x: True,
        'gas': 3500,
        'done_label': 'exp10_done',
    },
    'sqrt': {
        'compute': lambda x: mpmath.sqrt(x),
        'domain': lambda x: x >= 0,
        'gas': 1600,
        'done_label': 'sqrt_done',
    },
    'cbrt': {
        'compute': lambda x: mpmath.cbrt(x) if x >= 0 else -mpmath.cbrt(-x),
        'domain': lambda x: True,  # Handles negatives
        'gas': 6500,
        'done_label': 'cbrt_done',
    },
    'inv': {
        'compute': lambda x: 1 / x,
        'domain': lambda x: x != 0,
        'gas': 550,
        'done_label': 'inv_done',  # Will need to add this label
    },
    'lambertw0': {
        'compute': lambda x: mpmath.lambertw(x, k=0),
        'domain': lambda x: x >= -1/mpmath.e,
        'gas': 13000,
        'done_label': 'lambertw0_done',
    },
}

# ============================================================================
# Shortcut Generation
# ============================================================================

def generate_shortcuts():
    """Generate all shortcuts for all functions."""
    inputs = build_input_universe()
    
    # Track all constants we need to define
    new_constants = {}  # name -> (value, hex, description)
    
    # Track shortcuts per function
    shortcuts = {func: [] for func in FUNCTIONS}
    
    # For verification output
    verification = {func: [] for func in FUNCTIONS}
    
    for func_name, func_info in FUNCTIONS.items():
        compute = func_info['compute']
        domain = func_info['domain']
        gas = func_info['gas']
        
        for input_name, input_val in inputs.items():
            # Check domain
            try:
                if not domain(input_val):
                    continue
            except:
                continue
            
            # Compute result
            try:
                result = compute(input_val)
            except:
                continue
            
            # Check if result is representable
            if not is_representable(result):
                continue
            
            # Check if result is real (not complex)
            if not mpmath.isfinite(result) or hasattr(result, 'imag') and result.imag != 0:
                continue
            
            # Find or create input constant name
            input_existing = find_existing_constant(input_val)
            if input_existing:
                input_const_name = input_existing
            else:
                input_const_name = f'SC_IN_{input_name}'
                if input_const_name not in new_constants:
                    new_constants[input_const_name] = (
                        input_val,
                        to_bl127_hex(input_val),
                        f'{float(input_val):.18g}'
                    )
            
            # Find or create output constant name
            output_existing = find_existing_constant(result)
            if output_existing:
                output_const_name = output_existing
            else:
                # Special case: result is 0
                if abs(float(result)) < 1e-50:
                    output_const_name = '0x00'  # Inline zero
                else:
                    output_const_name = f'SC_{func_name.upper()}_{input_name}'
                    if output_const_name not in new_constants:
                        new_constants[output_const_name] = (
                            result,
                            to_bl127_hex(result),
                            f'{func_name}({float(input_val):.18g}) = {float(result):.18g}'
                        )
            
            shortcuts[func_name].append({
                'input_name': input_name,
                'input_const': input_const_name,
                'input_val': float(input_val),
                'output_const': output_const_name,
                'output_val': float(result),
                'gas_saved': gas,
            })
            
            verification[func_name].append({
                'input_hex': to_bl127_hex(input_val),
                'output_hex': to_bl127_hex(result),
                'input_decimal': str(float(input_val)),
                'output_decimal': str(float(result)),
            })
    
    return shortcuts, new_constants, verification

def generate_pow_special_shortcuts():
    """Generate special dispatch shortcuts for pow(x, y)."""
    # These route to cheaper functions rather than returning constants
    pow_specials = [
        # (y_check, description, dispatch_code)
        ('ONE_BL127', 'y == 1 -> return x', 'swap1 pop'),  # Just return x
        ('SC_IN_INT_2', 'y == 2 -> x*x', 'pop dup1 BL127_MUL()'),
        ('HALF_BL127', 'y == 0.5 -> sqrt(x)', 'pop BL127_SQRT()'),
        ('SC_IN_INT_3', 'y == 3 -> x*x*x', 'pop dup1 dup1 BL127_MUL() BL127_MUL()'),
        ('SC_IN_NEG_1', 'y == -1 -> 1/x', 'pop BL127_INV()'),
        ('ONE_THIRD_BL127', 'y == 1/3 -> cbrt', 'pop BL127_LOG2() [ONE_THIRD_BL127] BL127_MUL() BL127_EXP2()'),
    ]
    
    # x-based dispatches (check dup2)
    pow_x_specials = [
        ('SC_IN_INT_2', 'x == 2 -> 2^y = exp2(y)', 'swap1 pop BL127_EXP2()'),
        ('SC_IN_INT_10', 'x == 10 -> 10^y = exp10(y)', 'swap1 pop BL127_EXP10()'),
    ]
    
    return pow_specials, pow_x_specials

# ============================================================================
# Output Generation
# ============================================================================

def output_constants_file(new_constants, output_path):
    """Write the shortcut_constants.huff file."""
    with open(output_path, 'w') as f:
        f.write("/// @title BL127 Shortcut Constants\n")
        f.write("/// @notice Precomputed constants for common-value shortcuts\n")
        f.write("/// @dev Auto-generated by scripts/bl127/generators/generate_shortcuts.py\n")
        f.write("/// DO NOT EDIT MANUALLY\n\n")
        
        # Group by type: inputs vs outputs
        input_consts = [(k, v) for k, v in new_constants.items() if k.startswith('SC_IN_')]
        output_consts = [(k, v) for k, v in new_constants.items() if not k.startswith('SC_IN_')]
        
        f.write("// ============================================================================\n")
        f.write("// Input Constants\n")
        f.write("// ============================================================================\n\n")
        
        for name, (val, hex_str, desc) in sorted(input_consts):
            f.write(f"// {desc}\n")
            f.write(f"#define constant {name} = {hex_str}\n\n")
        
        f.write("// ============================================================================\n")
        f.write("// Output Constants (precomputed function results)\n")
        f.write("// ============================================================================\n\n")
        
        for name, (val, hex_str, desc) in sorted(output_consts):
            f.write(f"// {desc}\n")
            f.write(f"#define constant {name} = {hex_str}\n\n")

def select_shortcuts_within_budget(shortcuts, new_constants, max_bytecode=10000):
    """
    Select shortcuts to fit within bytecode budget.
    
    Bytecode costs:
    - Each new constant: ~33 bytes (PUSH32 + storage)
    - Each guard check: ~7 bytes (DUP1 + PUSH32_ref + EQ + PUSH2 + JUMPI)
    - Each landing pad: ~7 bytes (JUMPDEST + POP + PUSH32_ref + PUSH2 + JUMP)
    - Shared constants save significant space
    
    Strategy: Prioritize high-gas functions and inputs that use existing constants.
    """
    # Track which constants are actually needed
    needed_constants = set()
    selected = {func: [] for func in shortcuts}
    
    # Cost estimates (bytes)
    COST_PER_GUARD = 7      # dup1 [const] eq label jumpi
    COST_PER_PAD = 7        # label: pop [const] done jump
    COST_PER_NEW_CONST = 33 # PUSH32 data
    
    # Prioritize by gas saved per bytecode cost
    all_shortcuts = []
    for func_name, func_shortcuts in shortcuts.items():
        gas = FUNCTIONS[func_name]['gas']
        for sc in func_shortcuts:
            # Calculate cost for this shortcut
            input_is_new = sc['input_const'] not in EXISTING_CONSTANTS and sc['input_const'] not in needed_constants
            output_is_new = sc['output_const'] not in EXISTING_CONSTANTS and sc['output_const'] not in needed_constants and sc['output_const'] != '0x00'
            
            cost = COST_PER_GUARD + COST_PER_PAD
            if input_is_new:
                cost += COST_PER_NEW_CONST
            if output_is_new:
                cost += COST_PER_NEW_CONST
            
            # Score = gas saved / cost (higher is better)
            score = gas / cost
            
            all_shortcuts.append({
                'func': func_name,
                'sc': sc,
                'cost': cost,
                'gas': gas,
                'score': score,
                'input_is_new': input_is_new,
                'output_is_new': output_is_new,
            })
    
    # Sort by score descending
    all_shortcuts.sort(key=lambda x: -x['score'])
    
    # Select shortcuts within budget
    total_cost = 0
    func_counts = {func: 0 for func in shortcuts}
    MAX_PER_FUNC = 15  # Limit per function to avoid excessive checks
    
    for item in all_shortcuts:
        func = item['func']
        sc = item['sc']
        
        # Skip if we have too many for this function
        if func_counts[func] >= MAX_PER_FUNC:
            continue
        
        # Recalculate cost with current needed_constants
        input_is_new = sc['input_const'] not in EXISTING_CONSTANTS and sc['input_const'] not in needed_constants
        output_is_new = sc['output_const'] not in EXISTING_CONSTANTS and sc['output_const'] not in needed_constants and sc['output_const'] != '0x00'
        
        cost = COST_PER_GUARD + COST_PER_PAD
        if input_is_new:
            cost += COST_PER_NEW_CONST
        if output_is_new:
            cost += COST_PER_NEW_CONST
        
        if total_cost + cost > max_bytecode:
            continue
        
        # Add this shortcut
        selected[func].append(sc)
        func_counts[func] += 1
        total_cost += cost
        
        # Mark constants as needed
        if input_is_new:
            needed_constants.add(sc['input_const'])
        if output_is_new:
            needed_constants.add(sc['output_const'])
    
    # Filter new_constants to only those needed
    filtered_constants = {k: v for k, v in new_constants.items() if k in needed_constants}
    
    return selected, filtered_constants, total_cost

def output_huff_guards(shortcuts, pow_y_specials, pow_x_specials):
    """Print the Huff guard code for each function."""
    
    # First output pow special cases
    print("// ============================================================================")
    print("// BL127_POW() shortcuts - INSERT AFTER existing guards (y==0, x==0, x==1, x<0)")
    print("// ============================================================================")
    print()
    print("// --- Y-based checks (check dup1 = y) ---")
    for const, desc, _ in pow_y_specials:
        label = f"sc_pow_{const.lower().replace('sc_in_', '').replace('_bl127', '')}"
        print(f"    dup1 [{const}] eq {label} jumpi    // {desc}")
    print()
    print("// --- X-based checks (check dup2 = x) ---")
    for const, desc, _ in pow_x_specials:
        label = f"sc_pow_x{const.lower().replace('sc_in_int_', '')}"
        print(f"    dup2 [{const}] eq {label} jumpi    // {desc}")
    print()
    print("// --- Landing pads (BEFORE pow_done label) ---")
    for const, desc, dispatch in pow_y_specials:
        label = f"sc_pow_{const.lower().replace('sc_in_', '').replace('_bl127', '')}"
        print(f"    {label}:")
        print(f"    {dispatch}")
        print(f"    pow_done jump")
        print()
    for const, desc, dispatch in pow_x_specials:
        label = f"sc_pow_x{const.lower().replace('sc_in_int_', '')}"
        print(f"    {label}:")
        print(f"    {dispatch}")
        print(f"    pow_done jump")
        print()
    
    # Now output regular shortcuts per function
    for func_name, func_shortcuts in shortcuts.items():
        if not func_shortcuts:
            continue
        
        done_label = FUNCTIONS[func_name]['done_label']
        gas = FUNCTIONS[func_name]['gas']
        
        print(f"// ============================================================================")
        print(f"// BL127_{func_name.upper()}() shortcuts ({len(func_shortcuts)} entries, ~{gas} gas each)")
        print(f"// INSERT AFTER existing guards, BEFORE main computation")
        print(f"// ============================================================================")
        print()
        
        print("// --- Guard checks ---")
        for sc in func_shortcuts:
            label = f"sc_{func_name}_{sc['input_name'].lower()}"
            print(f"    dup1 [{sc['input_const']}] eq {label} jumpi")
        
        print()
        print(f"// --- Landing pads (BEFORE {done_label} label) ---")
        for sc in func_shortcuts:
            label = f"sc_{func_name}_{sc['input_name'].lower()}"
            out = sc['output_const']
            # Handle inline zero
            if out == '0x00':
                print(f"    {label}: pop 0x00 {done_label} jump")
            else:
                print(f"    {label}: pop [{out}] {done_label} jump")
        print()

def output_verification(verification, output_path):
    """Write verification JSON file."""
    with open(output_path, 'w') as f:
        json.dump(verification, f, indent=2)

# ============================================================================
# Main
# ============================================================================

def main():
    print("// BL127 Shortcut Generation", file=sys.stderr)
    print("// Generating shortcuts...", file=sys.stderr)
    
    shortcuts, new_constants, verification = generate_shortcuts()
    pow_y_specials, pow_x_specials = generate_pow_special_shortcuts()
    
    # Ensure INT_2 and INT_3 and INT_10 are in new_constants for pow specials
    if 'SC_IN_INT_2' not in new_constants:
        new_constants['SC_IN_INT_2'] = (mpmath.mpf(2), to_bl127_hex(mpmath.mpf(2)), '2.0')
    if 'SC_IN_INT_3' not in new_constants:
        new_constants['SC_IN_INT_3'] = (mpmath.mpf(3), to_bl127_hex(mpmath.mpf(3)), '3.0')
    if 'SC_IN_INT_10' not in new_constants:
        new_constants['SC_IN_INT_10'] = (mpmath.mpf(10), to_bl127_hex(mpmath.mpf(10)), '10.0')
    if 'SC_IN_NEG_1' not in new_constants:
        new_constants['SC_IN_NEG_1'] = (mpmath.mpf(-1), to_bl127_hex(mpmath.mpf(-1)), '-1.0')
    
    # Select shortcuts within budget (10KB = 10000 bytes, leaving ~1.8KB margin)
    shortcuts, new_constants, total_cost = select_shortcuts_within_budget(
        shortcuts, new_constants, max_bytecode=10000
    )
    
    # Output paths
    script_dir = Path(__file__).parent
    constants_path = script_dir.parent.parent.parent / 'contracts' / 'src' / 'tools' / 'huff' / 'bl127' / 'shortcut_constants.huff'
    verify_path = script_dir / 'shortcut_verify.json'
    
    # Write constants file
    output_constants_file(new_constants, constants_path)
    print(f"// Wrote {len(new_constants)} constants to {constants_path}", file=sys.stderr)
    
    # Filter verification to only selected shortcuts
    selected_verification = {}
    for func_name, func_shortcuts in shortcuts.items():
        selected_inputs = {sc['input_val'] for sc in func_shortcuts}
        selected_verification[func_name] = [
            v for v in verification[func_name] 
            if float(v['input_decimal']) in selected_inputs
        ]
    
    # Write verification JSON
    total_shortcuts = sum(len(s) for s in shortcuts.values())
    output_verification(selected_verification, verify_path)
    print(f"// Wrote {total_shortcuts} verification entries to {verify_path}", file=sys.stderr)
    
    # Print summary
    print(f"//", file=sys.stderr)
    print(f"// Summary:", file=sys.stderr)
    print(f"//   New constants: {len(new_constants)}", file=sys.stderr)
    print(f"//   Total shortcuts: {total_shortcuts}", file=sys.stderr)
    print(f"//   Estimated bytecode: ~{total_cost} bytes", file=sys.stderr)
    print(f"//", file=sys.stderr)
    for func_name, func_shortcuts in sorted(shortcuts.items(), key=lambda x: -FUNCTIONS[x[0]]['gas']):
        if func_shortcuts:
            print(f"//   {func_name}: {len(func_shortcuts)} shortcuts (saves up to {FUNCTIONS[func_name]['gas']} gas each)", file=sys.stderr)
    print(f"//", file=sys.stderr)
    
    # Output guard code to stdout
    print("// ============================================================================")
    print("// HUFF GUARD CODE - Copy these into the respective function files")
    print("// ============================================================================")
    print()
    output_huff_guards(shortcuts, pow_y_specials, pow_x_specials)

if __name__ == "__main__":
    main()
