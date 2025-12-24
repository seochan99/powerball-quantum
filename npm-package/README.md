# powerball-quantum

Powerball number predictor using quantum-inspired algorithm with momentum, mean reversion, and statistical filters.

## Installation

```bash
npm install powerball-quantum
```

## CLI Usage

```bash
# Get 5 recommended picks
npx powerball-quantum predict

# Get 10 picks with analysis
npx powerball-quantum predict -c 10 -a

# Quick single pick
npx powerball-quantum quick

# Update data from NY Lottery API
npx powerball-quantum update
```

## Programmatic Usage

```typescript
import { predict, quickPick, formatPick, updateData } from 'powerball-quantum';

// Get 5 picks
const picks = await predict({ count: 5 });
picks.forEach(pick => {
  console.log(formatPick(pick));
  // Output: 21 - 26 - 34 - 57 - 61  🔴 1
});

// Quick single pick
const myPick = await quickPick();
console.log(myPick);
// { whiteBalls: [5, 7, 28, 38, 66], powerball: 23, score: 46.5 }

// Update data
await updateData();
```

## Algorithm

**QUANTUM** combines multiple Wall Street quant-inspired signals:

| Signal | Description |
|--------|-------------|
| **Momentum** | Exponential decay weighting - recent numbers score higher |
| **Z-Score** | Mean reversion - overdue numbers get boosted |
| **Recent Trend** | Last 15 draws with stronger emphasis |
| **Pair Synergy** | Numbers that frequently appear together |

### 7-Stage Filter

All picks must pass:
1. ❌ No duplicate with historical combinations
2. ✅ Sum range: 130-220
3. ✅ Odd/Even ratio: 2:3 or 3:2
4. ✅ High/Low balance: 2:3 or 3:2
5. ✅ Decade balance: At least 3 different decades
6. ✅ Ending diversity: At least 4 different last digits
7. ❌ No triple consecutive numbers

## Data Source

Historical data from [NY Open Data Powerball API](https://data.ny.gov/Government-Finance/Lottery-Powerball-Winning-Numbers-Beginning-2010/d6yy-54nr).

## Disclaimer

**For educational and entertainment purposes only.** Lottery numbers are randomly drawn. No algorithm can predict or guarantee winning numbers. Gamble responsibly.

## License

MIT
