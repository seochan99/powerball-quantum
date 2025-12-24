"""
Powerball Quantum Predictor - Core Algorithm
"""

import os
import math
import random
import statistics
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, Dict
from pathlib import Path

try:
    import requests
    import pandas as pd
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# Constants
DATA_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
WHITE_BALL_RANGE = (1, 69)
RED_BALL_RANGE = (1, 26)


@dataclass
class Pick:
    """A Powerball pick with 5 white balls and 1 red ball."""
    white_balls: List[int]
    powerball: int
    score: float = 0.0

    def __str__(self):
        whites = " - ".join(f"{n:2d}" for n in self.white_balls)
        return f"{whites}  🔴 {self.powerball}"


def _get_data_path() -> Path:
    """Get the path to the data file."""
    return Path(__file__).parent / "powerball_data.csv"


def update_data() -> str:
    """Download latest Powerball data from NY Lottery API."""
    if not HAS_DEPS:
        raise ImportError("requests is required. Install with: pip install requests")

    print("Downloading latest Powerball data...")
    response = requests.get(DATA_URL)
    response.raise_for_status()

    data_path = _get_data_path()
    with open(data_path, 'wb') as f:
        f.write(response.content)

    print("Download complete!")
    return str(data_path)


def load_data() -> pd.DataFrame:
    """Load and preprocess Powerball data."""
    if not HAS_DEPS:
        raise ImportError("pandas is required. Install with: pip install pandas")

    data_path = _get_data_path()

    if not data_path.exists():
        update_data()

    df = pd.read_csv(data_path)

    if 'Winning Numbers' not in df.columns:
        raise ValueError("Column 'Winning Numbers' not found in data.")

    df['numbers_list'] = df['Winning Numbers'].apply(
        lambda x: [int(n) for n in str(x).split()]
    )

    df['Draw Date'] = pd.to_datetime(df['Draw Date'])

    # Filter for current rules (post Oct 7, 2015)
    start_date = '2015-10-07'
    df = df[df['Draw Date'] >= start_date].copy()

    print(f"Loaded {len(df)} draws (current rules since {start_date})")
    return df


def _calculate_momentum(df: pd.DataFrame, decay_alpha: float = 0.03) -> Tuple[Dict, Dict]:
    """Calculate exponential decay momentum scores."""
    white_scores = {n: 0.1 for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    red_scores = {n: 0.1 for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}

    df_sorted = df.sort_values('Draw Date', ascending=True)
    total_draws = len(df_sorted)

    for idx, row in enumerate(df_sorted.itertuples()):
        t = total_draws - 1 - idx
        weight = math.exp(-decay_alpha * t)

        nums = row.numbers_list
        if len(nums) < 6:
            continue

        for w in nums[:5]:
            if w in white_scores:
                white_scores[w] += weight

        if nums[5] in red_scores:
            red_scores[nums[5]] += weight

    return white_scores, red_scores


def _calculate_z_scores(df: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Calculate Z-scores for gap analysis (mean reversion)."""
    white_gaps = {n: [] for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    red_gaps = {n: [] for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}
    last_seen_white = {n: -1 for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    last_seen_red = {n: -1 for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}

    df_sorted = df.sort_values('Draw Date', ascending=True).reset_index(drop=True)
    total_draws = len(df_sorted)

    for idx, row in df_sorted.iterrows():
        nums = row['numbers_list']
        if len(nums) < 6:
            continue

        whites = nums[:5]
        red = nums[5]

        for w in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1):
            if w in whites:
                if last_seen_white[w] != -1:
                    white_gaps[w].append(idx - last_seen_white[w])
                last_seen_white[w] = idx

        for r in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1):
            if r == red:
                if last_seen_red[r] != -1:
                    red_gaps[r].append(idx - last_seen_red[r])
                last_seen_red[r] = idx

    white_z = {}
    red_z = {}

    for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1):
        current_gap = total_draws - 1 - last_seen_white[n]
        if not white_gaps[n]:
            white_z[n] = 0
            continue
        mean_gap = statistics.mean(white_gaps[n])
        stdev = statistics.pstdev(white_gaps[n]) if len(white_gaps[n]) > 1 else 1
        if stdev == 0:
            stdev = 1
        white_z[n] = (current_gap - mean_gap) / stdev

    for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1):
        current_gap = total_draws - 1 - last_seen_red[n]
        if not red_gaps[n]:
            red_z[n] = 0
            continue
        mean_gap = statistics.mean(red_gaps[n])
        stdev = statistics.pstdev(red_gaps[n]) if len(red_gaps[n]) > 1 else 1
        if stdev == 0:
            stdev = 1
        red_z[n] = (current_gap - mean_gap) / stdev

    return white_z, red_z


def _calculate_recent_momentum(df: pd.DataFrame, n_recent: int = 15, decay: float = 0.15) -> Tuple[Dict, Dict]:
    """Calculate momentum focusing on most recent N draws."""
    white_scores = {n: 0.1 for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    red_scores = {n: 0.1 for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}

    df_sorted = df.sort_values('Draw Date', ascending=False).head(n_recent)

    for idx, row in enumerate(df_sorted.itertuples()):
        weight = math.exp(-decay * idx) * 2
        nums = row.numbers_list
        if len(nums) < 6:
            continue

        for w in nums[:5]:
            if w in white_scores:
                white_scores[w] += weight

        if nums[5] in red_scores:
            red_scores[nums[5]] += weight

    return white_scores, red_scores


def _analyze_pair_frequency(df: pd.DataFrame, top_n: int = 50) -> Dict:
    """Analyze which number pairs appear together frequently."""
    from itertools import combinations
    pair_counts = Counter()

    for nums in df['numbers_list']:
        if len(nums) >= 5:
            whites = nums[:5]
            for pair in combinations(sorted(whites), 2):
                pair_counts[pair] += 1

    pair_bonus = {}
    for (a, b), count in pair_counts.most_common(top_n):
        pair_bonus[a] = pair_bonus.get(a, 0) + count * 0.1
        pair_bonus[b] = pair_bonus.get(b, 0) + count * 0.1

    return pair_bonus


def _get_weighted_sample(population: List[int], weights: List[float], k: int) -> List[int]:
    """Weighted random sample without replacement."""
    selected = set()
    while len(selected) < k:
        choice = random.choices(population, weights=weights, k=1)[0]
        selected.add(choice)
    return list(selected)


def _quantum_selector(momentum: Dict, z_scores: Dict, recent: Dict, pair_bonus: Dict, n_picks: int) -> List[int]:
    """Select numbers using combined signals."""
    final_scores = {}
    for n in momentum:
        base = momentum[n]
        z_boost = max(0, z_scores.get(n, 0)) * 5
        recent_boost = recent.get(n, 0) * 1.5
        pair_b = pair_bonus.get(n, 0) * 0.5
        final_scores[n] = base + z_boost + recent_boost + pair_b

    candidates = list(final_scores.keys())
    weights = [max(0.1, final_scores[n]) for n in candidates]

    return _get_weighted_sample(candidates, weights, n_picks)


# Filters
def _check_sum_range(white_balls: List[int], min_sum: int = 130, max_sum: int = 220) -> bool:
    return min_sum <= sum(white_balls) <= max_sum


def _check_odd_even_ratio(white_balls: List[int]) -> bool:
    odds = sum(1 for x in white_balls if x % 2 != 0)
    evens = 5 - odds
    return (odds == 3 and evens == 2) or (odds == 2 and evens == 3)


def _check_high_low_balance(white_balls: List[int], threshold: int = 35) -> bool:
    lows = sum(1 for x in white_balls if x < threshold)
    highs = 5 - lows
    return (lows == 3 and highs == 2) or (lows == 2 and highs == 3)


def _check_decade_balance(white_balls: List[int]) -> bool:
    decades = set(n // 10 for n in white_balls)
    return len(decades) >= 3


def _check_ending_diversity(white_balls: List[int]) -> bool:
    endings = set(n % 10 for n in white_balls)
    return len(endings) >= 4


def _check_no_triple_consecutive(white_balls: List[int]) -> bool:
    sorted_balls = sorted(white_balls)
    diffs = [sorted_balls[i+1] - sorted_balls[i] for i in range(4)]
    consecutive_ones = sum(1 for d in diffs if d == 1)
    return consecutive_ones < 2


def _build_history_set(df: pd.DataFrame) -> Set[Tuple]:
    """Build set of historical combinations."""
    history = set()
    for nums in df['numbers_list']:
        if len(nums) >= 6:
            whites = tuple(sorted(nums[:5]))
            red = nums[5]
            history.add((whites, red))
    return history


def predict(count: int = 5, show_analysis: bool = False) -> List[Pick]:
    """
    Generate predicted Powerball numbers.

    Args:
        count: Number of picks to generate (default: 5)
        show_analysis: Show signal analysis (default: False)

    Returns:
        List of Pick objects sorted by score

    Example:
        >>> from powerball_quantum import predict
        >>> picks = predict(count=5)
        >>> for pick in picks:
        ...     print(pick)
    """
    df = load_data()
    history_set = _build_history_set(df)

    # Calculate all signals
    w_mom, r_mom = _calculate_momentum(df)
    w_z, r_z = _calculate_z_scores(df)
    w_recent, r_recent = _calculate_recent_momentum(df, n_recent=15)
    pair_bonus = _analyze_pair_frequency(df, top_n=50)

    if show_analysis:
        print("\n📊 Signal Analysis:")
        top_mom = sorted(w_mom.items(), key=lambda x: x[1], reverse=True)[:10]
        print("🔥 Hot Numbers:", [x[0] for x in top_mom])
        top_z = sorted(w_z.items(), key=lambda x: x[1], reverse=True)[:10]
        print("⏰ Overdue:", [x[0] for x in top_z if x[1] > 1])

    picks = []
    seen = set()

    for _ in range(count * 100):
        if len(picks) >= count:
            break

        # Generate candidate
        white_balls = sorted(_quantum_selector(w_mom, w_z, w_recent, pair_bonus, 5))
        red_ball = _quantum_selector(r_mom, r_z, r_recent, {}, 1)[0]

        # Apply filters
        if (tuple(white_balls), red_ball) in history_set:
            continue
        if not _check_sum_range(white_balls):
            continue
        if not _check_odd_even_ratio(white_balls):
            continue
        if not _check_high_low_balance(white_balls):
            continue
        if not _check_decade_balance(white_balls):
            continue
        if not _check_ending_diversity(white_balls):
            continue
        if not _check_no_triple_consecutive(white_balls):
            continue

        key = (tuple(white_balls), red_ball)
        if key in seen:
            continue
        seen.add(key)

        # Calculate score
        score = 0.0
        for n in white_balls:
            score += w_mom.get(n, 0) * 1.0
            score += max(0, w_z.get(n, 0)) * 3.0
            score += w_recent.get(n, 0) * 2.0
            score += pair_bonus.get(n, 0) * 0.5
        score += r_mom.get(red_ball, 0) * 2.0
        score += max(0, r_z.get(red_ball, 0)) * 4.0

        picks.append(Pick(white_balls=white_balls, powerball=red_ball, score=score))

    # Sort by score
    picks.sort(key=lambda x: x.score, reverse=True)

    return picks[:count]


def quick_pick() -> Optional[Pick]:
    """
    Get a single best pick quickly.

    Returns:
        A single Pick object or None

    Example:
        >>> from powerball_quantum import quick_pick
        >>> pick = quick_pick()
        >>> print(pick)
    """
    picks = predict(count=1)
    return picks[0] if picks else None


def format_pick(pick: Pick) -> str:
    """Format a pick for display."""
    return str(pick)
