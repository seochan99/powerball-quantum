# powerball-quantum

Powerball number predictor using quantum-inspired algorithm with momentum, mean reversion, and statistical filters.

## Installation

**Python (pip):**
```bash
pip install powerball-quantum
```

**Node.js (npm):**
```bash
npm install powerball-quantum
```

## Python Usage

### CLI
```bash
# Get 5 recommended picks
powerball-quantum predict

# Get 10 picks with analysis
powerball-quantum predict -c 10 -a

# Quick single pick
powerball-quantum quick

# Update data from NY Lottery API
powerball-quantum update
```

### Python API
```python
from powerball_quantum import predict, quick_pick, update_data

# Get 5 picks
picks = predict(count=5)
for pick in picks:
    print(pick)
# Output: 21 - 26 - 34 - 57 - 61  🔴 1

# Quick single pick
my_pick = quick_pick()
print(my_pick.white_balls, my_pick.powerball)
# [5, 7, 28, 38, 66], 23

# Update data
update_data()
```

## Node.js Usage

### CLI
```bash
npx powerball-quantum predict
npx powerball-quantum quick
npx powerball-quantum update
```

### JavaScript API
```javascript
const { predict, quickPick } = require('powerball-quantum');

const picks = await predict({ count: 5 });
const myPick = await quickPick();
```

## Algorithm

**QUANTUM** combines Wall Street quant-inspired signals:

| Signal | Description |
|--------|-------------|
| **Momentum** | Exponential decay weighting - recent numbers score higher |
| **Z-Score** | Mean reversion - overdue numbers get boosted |
| **Recent Trend** | Last 15 draws with stronger emphasis |
| **Pair Synergy** | Numbers that frequently appear together |

### 7-Stage Filter

1. No duplicate with historical combinations
2. Sum range: 130-220
3. Odd/Even ratio: 2:3 or 3:2
4. High/Low balance: 2:3 or 3:2
5. Decade balance: At least 3 different decades
6. Ending diversity: At least 4 different last digits
7. No triple consecutive numbers

## Data Source

Historical data from [NY Open Data Powerball API](https://data.ny.gov/Government-Finance/Lottery-Powerball-Winning-Numbers-Beginning-2010/d6yy-54nr).

## Disclaimer

**For educational and entertainment purposes only.** Lottery numbers are randomly drawn. No algorithm can predict or guarantee winning numbers. Gamble responsibly.

## License

MIT
