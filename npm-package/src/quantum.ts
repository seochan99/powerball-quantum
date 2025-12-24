import { Draw, Pick, Scores, WHITE_BALL_RANGE, RED_BALL_RANGE } from './types';

/**
 * Calculate exponential decay momentum scores
 */
export function calculateMomentum(draws: Draw[], decayAlpha = 0.03): { white: Scores; red: Scores } {
  const whiteScores: Scores = {};
  const redScores: Scores = {};

  // Initialize scores
  for (let n = WHITE_BALL_RANGE.min; n <= WHITE_BALL_RANGE.max; n++) {
    whiteScores[n] = 0.1;
  }
  for (let n = RED_BALL_RANGE.min; n <= RED_BALL_RANGE.max; n++) {
    redScores[n] = 0.1;
  }

  // Sort by date ascending
  const sorted = [...draws].sort((a, b) => a.date.getTime() - b.date.getTime());
  const total = sorted.length;

  sorted.forEach((draw, idx) => {
    const t = total - 1 - idx; // t=0 for most recent
    const weight = Math.exp(-decayAlpha * t);

    draw.whiteBalls.forEach(w => {
      if (whiteScores[w] !== undefined) {
        whiteScores[w] += weight;
      }
    });

    if (redScores[draw.powerball] !== undefined) {
      redScores[draw.powerball] += weight;
    }
  });

  return { white: whiteScores, red: redScores };
}

/**
 * Calculate Z-scores for gap analysis (mean reversion)
 */
export function calculateZScores(draws: Draw[]): { white: Scores; red: Scores } {
  const whiteGaps: { [key: number]: number[] } = {};
  const redGaps: { [key: number]: number[] } = {};
  const lastSeenWhite: { [key: number]: number } = {};
  const lastSeenRed: { [key: number]: number } = {};

  // Initialize
  for (let n = WHITE_BALL_RANGE.min; n <= WHITE_BALL_RANGE.max; n++) {
    whiteGaps[n] = [];
    lastSeenWhite[n] = -1;
  }
  for (let n = RED_BALL_RANGE.min; n <= RED_BALL_RANGE.max; n++) {
    redGaps[n] = [];
    lastSeenRed[n] = -1;
  }

  const sorted = [...draws].sort((a, b) => a.date.getTime() - b.date.getTime());

  sorted.forEach((draw, idx) => {
    // White balls
    draw.whiteBalls.forEach(w => {
      if (lastSeenWhite[w] !== -1) {
        whiteGaps[w].push(idx - lastSeenWhite[w]);
      }
      lastSeenWhite[w] = idx;
    });

    // Red ball
    if (lastSeenRed[draw.powerball] !== -1) {
      redGaps[draw.powerball].push(idx - lastSeenRed[draw.powerball]);
    }
    lastSeenRed[draw.powerball] = idx;
  });

  const total = sorted.length;
  const whiteZ: Scores = {};
  const redZ: Scores = {};

  // Calculate Z-scores
  for (let n = WHITE_BALL_RANGE.min; n <= WHITE_BALL_RANGE.max; n++) {
    const currentGap = total - 1 - lastSeenWhite[n];
    const gaps = whiteGaps[n];

    if (gaps.length === 0) {
      whiteZ[n] = 0;
      continue;
    }

    const mean = gaps.reduce((a, b) => a + b, 0) / gaps.length;
    const variance = gaps.reduce((sum, g) => sum + Math.pow(g - mean, 2), 0) / gaps.length;
    const stdev = Math.sqrt(variance) || 1;

    whiteZ[n] = (currentGap - mean) / stdev;
  }

  for (let n = RED_BALL_RANGE.min; n <= RED_BALL_RANGE.max; n++) {
    const currentGap = total - 1 - lastSeenRed[n];
    const gaps = redGaps[n];

    if (gaps.length === 0) {
      redZ[n] = 0;
      continue;
    }

    const mean = gaps.reduce((a, b) => a + b, 0) / gaps.length;
    const variance = gaps.reduce((sum, g) => sum + Math.pow(g - mean, 2), 0) / gaps.length;
    const stdev = Math.sqrt(variance) || 1;

    redZ[n] = (currentGap - mean) / stdev;
  }

  return { white: whiteZ, red: redZ };
}

/**
 * Calculate recent momentum (last N draws)
 */
export function calculateRecentMomentum(draws: Draw[], nRecent = 15, decay = 0.15): { white: Scores; red: Scores } {
  const whiteScores: Scores = {};
  const redScores: Scores = {};

  for (let n = WHITE_BALL_RANGE.min; n <= WHITE_BALL_RANGE.max; n++) {
    whiteScores[n] = 0.1;
  }
  for (let n = RED_BALL_RANGE.min; n <= RED_BALL_RANGE.max; n++) {
    redScores[n] = 0.1;
  }

  const sorted = [...draws].sort((a, b) => b.date.getTime() - a.date.getTime()).slice(0, nRecent);

  sorted.forEach((draw, idx) => {
    const weight = Math.exp(-decay * idx) * 2;

    draw.whiteBalls.forEach(w => {
      if (whiteScores[w] !== undefined) {
        whiteScores[w] += weight;
      }
    });

    if (redScores[draw.powerball] !== undefined) {
      redScores[draw.powerball] += weight;
    }
  });

  return { white: whiteScores, red: redScores };
}

/**
 * Analyze pair frequency
 */
export function analyzePairFrequency(draws: Draw[], topN = 50): Scores {
  const pairCounts: Map<string, number> = new Map();

  draws.forEach(draw => {
    const whites = [...draw.whiteBalls].sort((a, b) => a - b);
    for (let i = 0; i < whites.length; i++) {
      for (let j = i + 1; j < whites.length; j++) {
        const key = `${whites[i]}-${whites[j]}`;
        pairCounts.set(key, (pairCounts.get(key) || 0) + 1);
      }
    }
  });

  const pairBonus: Scores = {};
  const sorted = [...pairCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN);

  sorted.forEach(([pair, count]) => {
    const [a, b] = pair.split('-').map(Number);
    pairBonus[a] = (pairBonus[a] || 0) + count * 0.1;
    pairBonus[b] = (pairBonus[b] || 0) + count * 0.1;
  });

  return pairBonus;
}

/**
 * Weighted random selection
 */
export function weightedSample(candidates: number[], weights: number[], k: number): number[] {
  const selected = new Set<number>();
  const totalWeight = weights.reduce((a, b) => a + b, 0);

  while (selected.size < k) {
    let r = Math.random() * totalWeight;
    for (let i = 0; i < candidates.length; i++) {
      r -= weights[i];
      if (r <= 0) {
        selected.add(candidates[i]);
        break;
      }
    }
  }

  return [...selected];
}

/**
 * Quantum selector combining all signals
 */
export function quantumSelect(
  momentum: Scores,
  zScores: Scores,
  recentMomentum: Scores,
  pairBonus: Scores,
  nPicks: number
): number[] {
  const candidates = Object.keys(momentum).map(Number);
  const weights = candidates.map(n => {
    const base = momentum[n] || 0;
    const zBoost = Math.max(0, zScores[n] || 0) * 5;
    const recentBoost = (recentMomentum[n] || 0) * 1.5;
    const pairB = (pairBonus[n] || 0) * 0.5;
    return Math.max(0.1, base + zBoost + recentBoost + pairB);
  });

  return weightedSample(candidates, weights, nPicks);
}

// --- FILTERS ---

export function checkSumRange(whiteBalls: number[], min = 130, max = 220): boolean {
  const sum = whiteBalls.reduce((a, b) => a + b, 0);
  return sum >= min && sum <= max;
}

export function checkOddEvenRatio(whiteBalls: number[]): boolean {
  const odds = whiteBalls.filter(x => x % 2 !== 0).length;
  const evens = 5 - odds;
  return (odds === 3 && evens === 2) || (odds === 2 && evens === 3);
}

export function checkHighLowBalance(whiteBalls: number[], threshold = 35): boolean {
  const lows = whiteBalls.filter(x => x < threshold).length;
  const highs = 5 - lows;
  return (lows === 3 && highs === 2) || (lows === 2 && highs === 3);
}

export function checkDecadeBalance(whiteBalls: number[]): boolean {
  const decades = new Set(whiteBalls.map(n => Math.floor(n / 10)));
  return decades.size >= 3;
}

export function checkEndingDiversity(whiteBalls: number[]): boolean {
  const endings = new Set(whiteBalls.map(n => n % 10));
  return endings.size >= 4;
}

export function checkNoTripleConsecutive(whiteBalls: number[]): boolean {
  const sorted = [...whiteBalls].sort((a, b) => a - b);
  const diffs = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    diffs.push(sorted[i + 1] - sorted[i]);
  }
  const consecutiveOnes = diffs.filter(d => d === 1).length;
  return consecutiveOnes < 2;
}

/**
 * Check if combination exists in history
 */
export function isInHistory(whiteBalls: number[], powerball: number, history: Set<string>): boolean {
  const key = [...whiteBalls].sort((a, b) => a - b).join(',') + '-' + powerball;
  return history.has(key);
}

export function buildHistorySet(draws: Draw[]): Set<string> {
  const history = new Set<string>();
  draws.forEach(draw => {
    const key = [...draw.whiteBalls].sort((a, b) => a - b).join(',') + '-' + draw.powerball;
    history.add(key);
  });
  return history;
}
