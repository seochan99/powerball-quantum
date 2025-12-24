import { Draw, Pick, PredictOptions } from './types';
import { loadData, updateData } from './data';
import {
  calculateMomentum,
  calculateZScores,
  calculateRecentMomentum,
  analyzePairFrequency,
  quantumSelect,
  checkSumRange,
  checkOddEvenRatio,
  checkHighLowBalance,
  checkDecadeBalance,
  checkEndingDiversity,
  checkNoTripleConsecutive,
  isInHistory,
  buildHistorySet
} from './quantum';

export { Draw, Pick, PredictOptions } from './types';
export { loadData, updateData } from './data';

/**
 * Generate a single quantum-powered pick
 */
export function generatePick(
  draws: Draw[],
  historySet: Set<string>,
  whiteMomentum: Record<number, number>,
  redMomentum: Record<number, number>,
  whiteZ: Record<number, number>,
  redZ: Record<number, number>,
  whiteRecent: Record<number, number>,
  redRecent: Record<number, number>,
  pairBonus: Record<number, number>
): Pick | null {
  const maxAttempts = 150000;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const whiteBalls = quantumSelect(whiteMomentum, whiteZ, whiteRecent, pairBonus, 5).sort((a, b) => a - b);
    const powerball = quantumSelect(redMomentum, redZ, redRecent, {}, 1)[0];

    // Apply all filters
    if (isInHistory(whiteBalls, powerball, historySet)) continue;
    if (!checkSumRange(whiteBalls)) continue;
    if (!checkOddEvenRatio(whiteBalls)) continue;
    if (!checkHighLowBalance(whiteBalls)) continue;
    if (!checkDecadeBalance(whiteBalls)) continue;
    if (!checkEndingDiversity(whiteBalls)) continue;
    if (!checkNoTripleConsecutive(whiteBalls)) continue;

    // Calculate score
    let score = 0;
    whiteBalls.forEach(n => {
      score += (whiteMomentum[n] || 0) * 1.0;
      score += Math.max(0, whiteZ[n] || 0) * 3.0;
      score += (whiteRecent[n] || 0) * 2.0;
      score += (pairBonus[n] || 0) * 0.5;
    });
    score += (redMomentum[powerball] || 0) * 2.0;
    score += Math.max(0, redZ[powerball] || 0) * 4.0;

    return { whiteBalls, powerball, score };
  }

  return null;
}

/**
 * Main prediction function - call this to get picks!
 *
 * @example
 * ```typescript
 * import { predict } from 'powerball-quantum';
 *
 * const picks = await predict({ count: 5 });
 * console.log(picks);
 * ```
 */
export async function predict(options: PredictOptions = {}): Promise<Pick[]> {
  const { count = 5, showAnalysis = false } = options;

  // Load data
  const draws = await loadData();
  const historySet = buildHistorySet(draws);

  // Calculate all signals
  const { white: wMom, red: rMom } = calculateMomentum(draws);
  const { white: wZ, red: rZ } = calculateZScores(draws);
  const { white: wRecent, red: rRecent } = calculateRecentMomentum(draws, 15);
  const pairBonus = analyzePairFrequency(draws, 50);

  if (showAnalysis) {
    console.log('\n📊 Signal Analysis:');
    const topMom = Object.entries(wMom).sort((a, b) => b[1] - a[1]).slice(0, 10);
    console.log('🔥 Hot Numbers:', topMom.map(([n]) => n));
    const topZ = Object.entries(wZ).sort((a, b) => b[1] - a[1]).slice(0, 10);
    console.log('⏰ Overdue Numbers:', topZ.filter(([, z]) => z > 1).map(([n]) => n));
  }

  // Generate picks
  const picks: Pick[] = [];
  const seen = new Set<string>();

  for (let i = 0; i < count * 10 && picks.length < count; i++) {
    const pick = generatePick(
      draws, historySet,
      wMom, rMom, wZ, rZ, wRecent, rRecent, pairBonus
    );

    if (pick) {
      const key = pick.whiteBalls.join(',') + '-' + pick.powerball;
      if (!seen.has(key)) {
        seen.add(key);
        picks.push(pick);
      }
    }
  }

  // Sort by score
  picks.sort((a, b) => (b.score || 0) - (a.score || 0));

  return picks;
}

/**
 * Quick function to get a single best pick
 */
export async function quickPick(): Promise<Pick | null> {
  const picks = await predict({ count: 1 });
  return picks[0] || null;
}

/**
 * Format pick for display
 */
export function formatPick(pick: Pick): string {
  const whites = pick.whiteBalls.map(n => n.toString().padStart(2, ' ')).join(' - ');
  return `${whites}  🔴 ${pick.powerball}`;
}

// Default export
export default { predict, quickPick, updateData, loadData, formatPick };
