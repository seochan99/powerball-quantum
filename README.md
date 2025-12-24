# Powerball Quantum Ultra Predictor

A Python-based Powerball number prediction system using quantitative analysis techniques inspired by Wall Street trading strategies.

## Algorithm Overview

**QUANTUM ULTRA** combines multiple signals:

```
Score[n] = Momentum + Z-Score×5 + RecentTrend×1.5 + PairSynergy×0.5
```

### Signal Components

| Signal | Description |
|--------|-------------|
| **Momentum** | Exponential decay weighting (e^(-0.03×t)) - recent numbers score higher |
| **Z-Score** | Mean reversion analysis - overdue numbers get boosted |
| **Recent Trend** | Last 15 draws with stronger decay (0.15) |
| **Pair Synergy** | Numbers that frequently appear together |

### 7-Stage Filter

All generated picks must pass:

1. No duplicate with historical winning combinations
2. Sum range: 130-220 (covers ~70% of winners)
3. Odd/Even ratio: 2:3 or 3:2
4. High/Low balance: 2:3 or 3:2
5. Decade balance: At least 3 different decades (1-9, 10-19, etc.)
6. Ending digit diversity: At least 4 different last digits
7. No triple consecutive numbers

## Files

| File | Description |
|------|-------------|
| `powerball_app.py` | Main application with all algorithms |
| `generate_csv.py` | Batch generator for millions of picks |
| `generate_tomorrow_picks.py` | Quick generator for next draw |
| `powerball_data.csv` | Historical Powerball data (NY Lottery API) |

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/powerball-quantum-ultra.git
cd powerball-quantum-ultra

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Interactive Mode
```bash
python powerball_app.py
```

### Generate All Strategy Recommendations
```bash
python powerball_app.py --all
```

### Generate 1 Million Picks (QUANTUM ULTRA)
```bash
python generate_csv.py
```

### Quick 100 Picks for Tomorrow
```bash
python generate_tomorrow_picks.py
```

## Data Source

Historical data is sourced from the [NY Open Data Powerball API](https://data.ny.gov/Government-Finance/Lottery-Powerball-Winning-Numbers-Beginning-2010/d6yy-54nr).

Data is automatically downloaded and filtered for current rules (post October 7, 2015: 5/69 + 1/26).

## Disclaimer

This software is for **educational and entertainment purposes only**.

Lottery numbers are randomly drawn, and no algorithm can predict or guarantee winning numbers. Past performance does not indicate future results. Please gamble responsibly.

## License

MIT License - See [LICENSE](LICENSE) for details.

---

Good luck! May the quantum be with you.
