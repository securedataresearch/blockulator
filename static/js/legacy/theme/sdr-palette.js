/**
 * Blockulator legacy palette: the previous SDR design tokens and particle
 * palette, inlined here when vendor/sdr was retired. The archived apps are
 * drawn against these. This file and css/legacy/tokens.css are the only
 * places colour literals are allowed (scripts/check-sdr-colors.mjs).
 */

const colors = {
  primary: '#737373',
  secondary: '#525252',
  accent: '#a3a3a3',
  bgDarker: '#000000',
  bgDark: '#0a0a0a',
  bgLight: '#171717',
  bgCard: '#171717',
  textDark: '#e5e5e5',
  textLight: '#a3a3a3',
  textWhite: '#f5f5f5',
  border: '#262626',
  link: '#a8a8a8',
  linkVisited: '#a8a8a8',
};


const palette = [
  '#00694e',  // 0:  deep emerald (Pantone 341 C)
  '#407050',  // 1:  emerald→red (forest olive)
  '#509060',  // 2:  emerald→gold (moss)
  '#306878',  // 3:  emerald→sapphire (teal)
  '#705040',  // 4:  emerald↔red (brown-green)
  '#708050',  // 5:  emerald↔gold (olive)
  '#407080',  // 6:  emerald↔sapphire (deep teal)
  '#d09050',  // 7:  gold↔red (burnt orange)
  '#e4002b',  // 8:  warm red (Pantone 185 C)
  '#c06030',  // 9:  red→gold (rust)
  '#a04870',  // 10: red→sapphire (plum)
  '#a09860',  // 11: gold
  '#805088',  // 12: red↔sapphire (deep violet)
  '#7888a0',  // 13: gold↔sapphire
  '#5878a0',  // 14: sapphire (light)
  '#4070a0',  // 15: sapphire
];


const EXTRA = {
    outlineVariant: '#1a1a1a',
    error: '#ef4444',
    warning: '#f59e0b',
    chartTrack: 'rgba(255, 255, 255, 0.14)',
    pixelPaper: '#ffffff',
};

/**
 * @param {string} hex - "#RRGGBB"
 * @param {number} alpha - 0..1
 * @returns {string} rgba(...)
 */
export function rgbaFromHex(hex, alpha) {
    const h = hex.replace('#', '');
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

/**
 * Lerp two #RRGGBB colors (t = 0 → fg, t = 1 → bg). For calmer chart ink on dark fields.
 */
export function blendHex(fg, bg, t) {
    const h = (x) => x.replace('#', '');
    const pa = h(fg);
    const pb = h(bg);
    const ar = parseInt(pa.slice(0, 2), 16);
    const ag = parseInt(pa.slice(2, 4), 16);
    const ab = parseInt(pa.slice(4, 6), 16);
    const br = parseInt(pb.slice(0, 2), 16);
    const bg_ = parseInt(pb.slice(2, 4), 16);
    const bb = parseInt(pb.slice(4, 6), 16);
    const u = Math.min(1, Math.max(0, t));
    const r = Math.round(ar + (br - ar) * u);
    const g = Math.round(ag + (bg_ - ag) * u);
    const b = Math.round(ab + (bb - ab) * u);
    return `#${[r, g, b].map((x) => x.toString(16).padStart(2, '0')).join('')}`;
}

export const SDR_PALETTE = {
    bgDarker: colors.bgDarker,
    bgDark: colors.bgDark,
    bgCard: colors.bgCard,
    border: colors.border,
    text: colors.textDark,
    textMuted: colors.textLight,
    textWhite: colors.textWhite,
    primary: colors.primary,
    secondary: colors.secondary,
    accent: colors.accent,
    link: colors.link,
    outlineVariant: EXTRA.outlineVariant,
    success: palette[0],
    error: EXTRA.error,
    warning: EXTRA.warning,
    particleEmerald: palette[0],
    particleRed: palette[8],
    particleGold: palette[11],
    particleSapphire: palette[15],
    chartTrack: EXTRA.chartTrack,
    pixelPaper: EXTRA.pixelPaper,
};

/**
 * Ordered particle bases (same sequence as frame.js indices 0, 8, 11, 15).
 */
export const PARTICLE_BASES_HEX = [
    SDR_PALETTE.particleEmerald,
    SDR_PALETTE.particleRed,
    SDR_PALETTE.particleGold,
    SDR_PALETTE.particleSapphire,
];

/**
 * @param {number} index
 * @returns {string} hex
 */
export function particleHexAt(index) {
    return PARTICLE_BASES_HEX[index % PARTICLE_BASES_HEX.length];
}

/**
 * Library trace colors — identical mapping to About precision chart.
 */
export const LIBRARY_TRACE_COLORS = {
    bl127: SDR_PALETTE.particleEmerald,
    abdk: SDR_PALETTE.particleSapphire,
    solady: SDR_PALETTE.particleGold,
    prb: SDR_PALETTE.particleRed,
};

/** Plotly / chart chrome on black field */
export const CHART_THEME = {
    fontColor: SDR_PALETTE.textMuted,
    gridColor: SDR_PALETTE.outlineVariant,
    gridColorMinor: rgbaFromHex(SDR_PALETTE.textMuted, 0.14),
    zeroLine: SDR_PALETTE.border,
};

/**
 * Default `--panel-color` / status-card accent per game (particle bases only).
 * @type {Record<string, string>}
 */
export const GAME_PANEL_COLOR_HEX = {
    'pissing-contest': SDR_PALETTE.particleSapphire,
    'pay-it-forward': SDR_PALETTE.particleEmerald,
    'pay-it-backward': SDR_PALETTE.particleSapphire,
    'message-board': SDR_PALETTE.particleSapphire,
    'king-of-the-hill': SDR_PALETTE.particleSapphire,
    'last-call': SDR_PALETTE.particleRed,
    'time-to-make-the-donuts': SDR_PALETTE.particleGold,
    'dice-gods': SDR_PALETTE.particleSapphire,
    'satan-moloch-baal': SDR_PALETTE.particleRed,
};

/**
 * @param {string} gameId
 * @returns {string} hex
 */
export function gamePanelColor(gameId) {
    return GAME_PANEL_COLOR_HEX[gameId] ?? SDR_PALETTE.particleSapphire;
}

const DISTRIBUTION_CHART_NAMES = [
    'Uniform - Constant Rate',
    'Gaussian - Bell Curve',
    'Exponential Decay',
    'Exponential Growth',
    'Linear Decay',
    'Linear Growth',
];

/**
 * Six distribution preview traces — cycles the four particle bases, then repeats with lower alpha feel via same hues.
 */
export function distributionPreviewChartColors() {
    return DISTRIBUTION_CHART_NAMES.map((name, i) => {
        const border = particleHexAt(i);
        return { border, bg: rgbaFromHex(border, i < 4 ? 0.2 : 0.14), name };
    });
}
