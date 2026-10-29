/**
 * Contract Registry
 * Infrastructure layer - Contract metadata for non-game contracts
 * 
 * NOTE: Game contracts are now defined in their respective game classes
 * (js/domain/games/*.js) as static metadata. This registry contains only
 * calculators, futures, identity, and other non-game contracts.
 * 
 * For calculator-specific UI configuration (input schemas, result formatting, method names),
 * see static/js/legacy/domain/calculators/calculator-registry.js, which references IDs from this file.
 */

import { getCurrentNetwork } from './network.js';

/**
 * Contract Registry - Non-game contract metadata
 * Each entry contains: type, display info, addresses, source, and ABI path
 */
export const CONTRACT_REGISTRY = {
    // ========== CALCULATORS ==========
    'exp': {
        type: 'calculator',
        name: 'Exponential',
        symbol: 'e^x',
        emoji: '📈',
        category: 'exponential',
        description: 'Calculate e^x on-chain',
        addresses: {
            sepolia: '0x66C5F46f5f650Ce3E3700866b518ff343Cc5Fb2E',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/exp.vy',
        abi: 'contracts/build/abis/exp.json'
    },
    
    'factorial': {
        type: 'calculator',
        name: 'Factorial',
        symbol: 'n!',
        emoji: '🔢',
        category: 'basic',
        description: 'Calculate factorial on-chain',
        addresses: {
            sepolia: '0x7E919e513828E212964AbfEa15c3665328C3D594',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/factorial.vy',
        abi: 'contracts/build/abis/factorial.json'
    },
    
    'norm-cdf': {
        type: 'calculator',
        name: 'Normal CDF',
        symbol: 'Φ(x)',
        emoji: '📊',
        category: 'probability',
        description: 'Standard normal cumulative distribution function',
        addresses: {
            sepolia: '0x82A934fF93FBBb02BDcE23e05B0eA82157A73fb3',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/norm_cdf.vy',
        abi: 'contracts/build/abis/norm-cdf.json'
    },
    
    'ln-factorial': {
        type: 'calculator',
        name: 'Log Factorial',
        symbol: 'ln(n!)',
        emoji: '📈',
        category: 'logarithmic',
        description: 'Natural log of factorial',
        addresses: {
            sepolia: '0x1Dc37426c2B777401266129fD8433cE749DFb775',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/ln_factorial.vy',
        abi: 'contracts/build/abis/ln-factorial.json'
    },
    
    'atan': {
        type: 'calculator',
        name: 'Arctangent',
        symbol: 'atan(x)',
        emoji: '📐',
        category: 'trigonometric',
        description: 'Calculate arctangent on-chain',
        addresses: {
            sepolia: '0x3B17Ad5B4BFA9Cf80885406FC03c19A5E00ED769',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/atan.vy',
        abi: 'contracts/build/abis/atan.json'
    },
    
    'sinh': {
        type: 'calculator',
        name: 'Hyperbolic Sine',
        symbol: 'sinh(x)',
        emoji: '〰️',
        category: 'hyperbolic',
        description: 'Calculate hyperbolic sine',
        addresses: {
            sepolia: '0x6cf5f371275297aE5945121fD935Cf2480079540',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/sinh.vy',
        abi: 'contracts/build/abis/sinh.json'
    },
    
    'cosh': {
        type: 'calculator',
        name: 'Hyperbolic Cosine',
        symbol: 'cosh(x)',
        emoji: '〰️',
        category: 'hyperbolic',
        description: 'Calculate hyperbolic cosine',
        addresses: {
            sepolia: '0x4B9Db96269661d277E3C6FF6A91143aF6afa7B14',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/cosh.vy',
        abi: 'contracts/build/abis/cosh.json'
    },
    
    'e-calculator': {
        type: 'calculator',
        name: 'Euler\'s Number',
        symbol: 'e',
        emoji: 'e',
        category: 'constants',
        description: 'Mathematical constant e',
        addresses: {
            sepolia: '0x6476ec7E6AbB0bdb8778554f36Ce72fb1f1af89e',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/constants/e.vy',
        abi: 'contracts/build/abis/e-calculator.json'
    },
    
    'pi-calculator': {
        type: 'calculator',
        name: 'Pi',
        symbol: 'π',
        emoji: 'π',
        category: 'constants',
        description: 'Mathematical constant pi',
        addresses: {
            sepolia: '0x6f7fCc6aB794AeE63a1E04B4810654Eec8D5a22D',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/constants/pi.vy',
        abi: 'contracts/build/abis/pi-calculator.json'
    },
    
    'tau-calculator': {
        type: 'calculator',
        name: 'Tau',
        symbol: 'τ',
        emoji: 'τ',
        category: 'constants',
        description: 'Mathematical constant tau (2π)',
        addresses: {
            sepolia: '0xaeD45577152c0fA4ec52Ef6ce72232e0a1c76fEA',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/constants/tau.vy',
        abi: 'contracts/build/abis/tau-calculator.json'
    },
    
    'sin-calculator': {
        type: 'calculator',
        name: 'Sine',
        symbol: 'sin(x)',
        emoji: '〰️',
        category: 'trigonometric',
        description: 'Calculate sine on-chain',
        addresses: {
            sepolia: '0x6B6163c8540BfeBab10D390E4CC13B31062A30bb',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/trig/sin.vy',
        abi: 'contracts/build/abis/sin-calculator.json'
    },
    
    'cos-calculator': {
        type: 'calculator',
        name: 'Cosine',
        symbol: 'cos(x)',
        emoji: '〰️',
        category: 'trigonometric',
        description: 'Calculate cosine on-chain',
        addresses: {
            sepolia: '0x382EE11b77567a08C9799d4d08D9E1F44Bf34a38',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/trig/cos.vy',
        abi: 'contracts/build/abis/cos-calculator.json'
    },
    
    'tanh-calculator': {
        type: 'calculator',
        name: 'Hyperbolic Tangent',
        symbol: 'tanh(x)',
        emoji: '〰️',
        category: 'hyperbolic',
        description: 'Calculate hyperbolic tangent',
        addresses: {
            sepolia: '0xb26b9E2a65bae3D67c3b11dd193DB4F59CcaB68b',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/trig/tanh.vy',
        abi: 'contracts/build/abis/tanh-calculator.json'
    },
    
    'pow10-calculator': {
        type: 'calculator',
        name: 'Power of 10',
        symbol: '10^x',
        emoji: '📈',
        category: 'exponential',
        description: 'Calculate powers of 10',
        addresses: {
            sepolia: '0x28DA1109e081bc83cEE8A5f921448c3cD7Ac6d02',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/pow10.vy',
        abi: 'contracts/build/abis/pow10-calculator.json'
    },
    
    'pow2-calculator': {
        type: 'calculator',
        name: 'Power of 2',
        symbol: '2^x',
        emoji: '📈',
        category: 'exponential',
        description: 'Calculate powers of 2',
        addresses: {
            sepolia: '0x3916736Ba352B08d1cb7ef57c1d7336924D5E1CD',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/pow2.vy',
        abi: 'contracts/build/abis/pow2-calculator.json'
    },
    
    'ln-calculator': {
        type: 'calculator',
        name: 'Natural Logarithm',
        symbol: 'ln(x)',
        emoji: '📊',
        category: 'logarithmic',
        description: 'Calculate natural logarithm',
        addresses: {
            sepolia: '0xfc4883676333533F053368e27A4038664b9063C2',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/ln.vy',
        abi: 'contracts/build/abis/ln-calculator.json'
    },
    
    'log2-calculator': {
        type: 'calculator',
        name: 'Log Base 2',
        symbol: 'log₂(x)',
        emoji: '📊',
        category: 'logarithmic',
        description: 'Calculate logarithm base 2',
        addresses: {
            sepolia: '0xD628C5420ccdd92DF1dFBf33E854435cA8Fa7350',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/log2.vy',
        abi: 'contracts/build/abis/log2-calculator.json'
    },
    
    'log10-calculator': {
        type: 'calculator',
        name: 'Log Base 10',
        symbol: 'log₁₀(x)',
        emoji: '📊',
        category: 'logarithmic',
        description: 'Calculate logarithm base 10',
        addresses: {
            sepolia: '0x9c44F99C8236FBeb9544406e373CBBABcD42f234',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/log10.vy',
        abi: 'contracts/build/abis/log10-calculator.json'
    },
    
    'sqrt-calculator': {
        type: 'calculator',
        name: 'Square Root',
        symbol: '√x',
        emoji: '√',
        category: 'basic',
        description: 'Calculate square root',
        addresses: {
            sepolia: '0x9e5Fa1afa9047fA095dee3870324480207278024',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/sqrt.vy',
        abi: 'contracts/build/abis/sqrt-calculator.json'
    },
    
    'erf-calculator': {
        type: 'calculator',
        name: 'Error Function',
        symbol: 'erf(x)',
        emoji: '📊',
        category: 'probability',
        description: 'Gaussian error function',
        addresses: {
            sepolia: '0x1f5d453df2c9EBE129A3419A3131ee5c9E39Dc6F',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/erf.vy',
        abi: 'contracts/build/abis/erf-calculator.json'
    },
    
    'zscore': {
        type: 'calculator',
        name: 'Z-Score',
        symbol: 'z',
        emoji: '📏',
        category: 'statistics',
        description: 'Standardized distance from mean',
        addresses: {
            sepolia: '0x35778015b92a3408783ac38a3F3D3edD568A72B5',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/zscore.vy',
        abi: 'contracts/build/abis/zscore.json'
    },
    
    'gaussian-tail': {
        type: 'calculator',
        name: 'Gaussian Tail',
        symbol: 'Tail(z)',
        emoji: '📉',
        category: 'statistics',
        description: 'Gaussian tail probability (Lin 1990)',
        addresses: {
            sepolia: '0xF6D58e7686cEEB619EDBf94522b895Fcc57eEfF5',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/gaussian_tail.vy',
        abi: 'contracts/build/abis/gaussian-tail.json'
    },
    
    'binomial-coeff': {
        type: 'calculator',
        name: 'Binomial Coefficient',
        symbol: 'C(n,k)',
        emoji: '🎲',
        category: 'combinatorics',
        description: 'n choose k - combinations calculator',
        addresses: {
            sepolia: '0xA72776807874Fc2EaD6a1AcC0ee624A59956Bd8a',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/binomial_coeff.vy',
        abi: 'contracts/build/abis/binomial-coeff.json'
    },
    
    'norm-pdf': {
        type: 'calculator',
        name: 'Normal PDF',
        symbol: 'φ(z)',
        emoji: '🔔',
        category: 'statistics',
        description: 'Normal probability density function',
        addresses: {
            sepolia: '0x4C0cBb1C12774d281E2980dB044323B2D424BB47',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/norm_pdf.vy',
        abi: 'contracts/build/abis/norm-pdf.json'
    },
    
    'gcd': {
        type: 'calculator',
        name: 'GCD / LCM',
        symbol: 'GCD(a,b)',
        emoji: '🔢',
        category: 'number-theory',
        description: 'Greatest common divisor and least common multiple',
        addresses: {
            sepolia: '0x182e59b0a7A3bA2F1Fb53e5390e9f01dcCAEFEb6',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/tools/math/gcd.vy',
        abi: 'contracts/build/abis/gcd.json'
    },
    
    // ========== ARITHMETIC (HUFF) ==========
    'fixedpoint127': {
        type: 'arithmetic',
        name: 'BL127',
        symbol: '+−×÷',
        emoji: '0x',
        category: 'huff',
        description: 'Signed 127.128 fixed-point arithmetic with 34 operations: add, sub, mul, div, exp, exp2, exp10, ln, log2, log10, sqrt, pow, abs, neg, inv, min, max, clamp, avg, gavg, dist, zeroFloorSub, hypot, cbrt, lerp, sign, floor, ceil, frac, round, log2Up, gcd, factorial, lambertW0',
        addresses: {
            sepolia: '0xfae694D0c2c44181791F838c54Ed64C3151FfE30',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/archive/huff/src/bl127/bl127.huff',
        abi: 'contracts/build/abis/fixedpoint127.json'
    },
    
    // ========== FUTURES ==========
    'future-factory': {
        type: 'future',
        name: 'Future Factory',
        emoji: '🏭',
        description: 'Eulerian futures marketplace',
        addresses: {
            sepolia: '0xE58f00B5BFc332572986561A6446706F919b8AFa',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/market/future_factory.vy',
        abi: 'contracts/build/abis/future-factory.json'
    },
    
    'uniform-future-blueprint': {
        type: 'future',
        name: 'Uniform Future Blueprint',
        emoji: '📏',
        description: 'Constant payout rate, linear accumulation',
        addresses: {
            sepolia: '0x6b6843660A7306EBe708a4822fd76A0082a162FE',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/market/uniform_future.vy',
        abi: 'contracts/build/abis/uniform-future.json'
    },
    
    'gaussian-future-blueprint': {
        type: 'future',
        name: 'Gaussian Future Blueprint',
        emoji: '🔔',
        description: 'Bell curve distribution, peak at midpoint',
        addresses: {
            sepolia: '0x65948d354Bc30c38a0064AD7ceD7d1DB28C8b6A9',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/market/gaussian_future.vy',
        abi: 'contracts/build/abis/gaussian-future.json'
    },
    
    'exponential-future-blueprint': {
        type: 'future',
        name: 'Exponential Future Blueprint',
        emoji: '📉',
        description: 'Front-loaded or back-loaded payouts',
        addresses: {
            sepolia: '0x2bdBAD0A6Dc7dBAa5CDDc9129eFF58619B90c6F7',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/market/exponential_future.vy',
        abi: 'contracts/build/abis/exponential-future.json'
    },
    
    'linear-future-blueprint': {
        type: 'future',
        name: 'Linear Future Blueprint',
        emoji: '🔺',
        description: 'Triangular distribution, linear growth or decay',
        addresses: {
            sepolia: '0xb7Af3317932D9D4236E64b383D4153FC745C497F',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/market/linear_future.vy',
        abi: 'contracts/build/abis/linear-future.json'
    },
    
    // ========== IDENTITY ==========
    'badge-factory': {
        type: 'identity',
        name: 'Badge Factory',
        emoji: '🏭',
        description: 'Badge creation factory',
        addresses: {
            sepolia: '0x5802f9121018aabC887b9686bA2eB1EFABB70BB7',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/identity/badge_factory.vy',
        abi: 'contracts/build/abis/badge-factory-v2.json'
    },
    
    'badge-blueprint': {
        type: 'identity',
        name: 'Badge Blueprint',
        emoji: '🎖️',
        description: 'Badge contract blueprint',
        addresses: {
            sepolia: '0x906E93e3901C87e0E3158B8eE8D4bF56d887C1D0',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/identity/badge.vy',
        abi: 'contracts/build/abis/badge-v2.json'
    },
    
    // ========== CONTENT ==========
    'content-factory-v4': {
        type: 'content',
        name: 'Content Factory V4',
        emoji: '🏭',
        description: 'Content creation factory',
        addresses: {
            sepolia: '0x4175ed783f344DBA9AE8267880127B0f847F0E35',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/content/content_factory_v4.vy',
        abi: 'contracts/build/abis/content-factory-v4.json'
    },
    
    'image-content-v3-blueprint': {
        type: 'content',
        name: 'Image Content V3 Blueprint',
        emoji: '🖼️',
        description: 'Image content blueprint',
        addresses: {
            sepolia: '0x477c6b74Bf82D6312B35Acd3f93Ee917e7589954',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/content/image_content_v3.vy',
        abi: 'contracts/build/abis/image-content-v3.json'
    },
    
    'text-content-v4-blueprint': {
        type: 'content',
        name: 'Text Content V4 Blueprint',
        emoji: '📝',
        description: 'Text content blueprint',
        addresses: {
            sepolia: '0x06115469c1ecaeDAc722F9C833A6d5866A9EB2Bd',
            mainnet: '0x0000000000000000000000000000000000000000'
        },
        source: 'contracts/src/content/text_content_v4.vy',
        abi: 'contracts/build/abis/text-content-v4.json'
    },
    
};

/**
 * Get contract metadata by name
 * @param {string} contractName - Contract identifier (e.g., 'dice-gods')
 * @param {string} network - Network name (default: current network)
 * @returns {object} Complete contract metadata
 */
export function getContractMetadata(contractName, network = null) {
    const metadata = CONTRACT_REGISTRY[contractName];
    
    if (!metadata) {
        throw new Error(`Unknown contract: ${contractName}`);
    }
    
    // Use current network if not specified
    const targetNetwork = network || getCurrentNetwork();
    
    // Return metadata with resolved address for current network
    return {
        ...metadata,
        contractAddress: metadata.addresses[targetNetwork],
        sourceFile: metadata.source,
        abiFile: metadata.abi
    };
}

/**
 * Get contract address only (backward compatibility helper)
 * @param {string} contractName - Contract identifier
 * @param {string} network - Network name (default: current network)
 * @returns {string} Contract address
 */
export function getContractAddress(contractName, network = null) {
    return getContractMetadata(contractName, network).contractAddress;
}

/**
 * Get all contracts by type
 * @param {string} type - Contract type ('game', 'calculator', etc.)
 * @returns {Array<string>} Array of contract names
 */
export function getContractsByType(type) {
    return Object.keys(CONTRACT_REGISTRY)
        .filter(key => CONTRACT_REGISTRY[key].type === type);
}

/**
 * Check if contract exists in registry
 * @param {string} contractName - Contract identifier
 * @returns {boolean} True if contract exists
 */
export function hasContract(contractName) {
    return contractName in CONTRACT_REGISTRY;
}

// Export lists of contracts by type for convenience
// Note: GAMES is no longer exported - use gameRegistry.getIds() instead
export const CALCULATORS = getContractsByType('calculator');
export const FUTURES = getContractsByType('future');
export const IDENTITY = getContractsByType('identity');


