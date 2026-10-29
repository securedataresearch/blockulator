/**
 * Network Configuration
 * Infrastructure layer - centralizes network-specific settings
 * 
 * Sepolia only: the archived apps are testnet history, and nothing here may point a
 * wallet at mainnet. A stored preference for any other network falls back to Sepolia.
 */

import { eventBus, EVENTS } from '../events/event-bus.js';

const NETWORKS = {
    sepolia: {
        chainId: 11155111,
        chainIdHex: '0xaa36a7',
        // Using PublicNode RPC - free, reliable, no API key required
        rpcUrl: 'https://ethereum-sepolia-rpc.publicnode.com',
        name: 'Sepolia Testnet',
        displayName: 'TESTNET',
        blockExplorer: 'https://sepolia.etherscan.io',
        nativeCurrency: {
            name: 'Sepolia ETH',
            symbol: 'ETH',
            decimals: 18
        }
    }
};

function readStoredNetwork() {
    try {
        if (typeof localStorage === 'undefined') return 'sepolia';
        return localStorage.getItem('preferred_network') || 'sepolia';
    } catch {
        return 'sepolia';
    }
}

// Current network - defaults to testnet, persisted in localStorage
let CURRENT_NETWORK = readStoredNetwork();

// Validate stored network
if (!NETWORKS[CURRENT_NETWORK]) {
    console.warn(`Invalid stored network: ${CURRENT_NETWORK}, defaulting to sepolia`);
    CURRENT_NETWORK = 'sepolia';
}

/**
 * Get the current network identifier
 */
export function getCurrentNetwork() {
    return CURRENT_NETWORK;
}

/**
 * Get the current network configuration
 */
export function getConfig() {
    return NETWORKS[CURRENT_NETWORK];
}

/**
 * Get all available networks
 */
export function getNetworks() {
    return NETWORKS;
}

/**
 * Switch to a different network
 * This will emit an event that all components should listen to
 */
export function switchNetwork(network) {
    if (!NETWORKS[network]) {
        console.error(`Invalid network: ${network}`);
        return false;
    }
    
    if (network === CURRENT_NETWORK) {
        console.log(`Already on ${network}`);
        return false;
    }
    
    console.log(`🔄 Switching network from ${CURRENT_NETWORK} to ${network}...`);
    
    CURRENT_NETWORK = network;
    try {
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('preferred_network', network);
        }
    } catch {
        /* ignore (e.g. private mode / non-browser) */
    }
    
    // Emit event - all components should listen and reinitialize
    eventBus.emit(EVENTS.NETWORK_CHANGED, {
        network: CURRENT_NETWORK,
        config: NETWORKS[CURRENT_NETWORK]
    });
    
    console.log(`✅ Switched to ${NETWORKS[network].name}`);
    return true;
}

// Helper function to get block explorer URL for an address
export function getExplorerUrl(address) {
    const currentConfig = getConfig();
    return `${currentConfig.blockExplorer}/address/${address}`;
}

// Helper function to get block explorer URL for a transaction
export function getTransactionUrl(txHash) {
    const currentConfig = getConfig();
    return `${currentConfig.blockExplorer}/tx/${txHash}`;
}

// Log initial network on load
console.log(`🌐 Network initialized: ${NETWORKS[CURRENT_NETWORK].name}`);

