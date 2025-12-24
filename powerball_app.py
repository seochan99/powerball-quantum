import requests
import pandas as pd
import random
import os
from datetime import datetime
from collections import Counter
import math
import statistics

# Constants
DATA_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
CSV_FILE = "powerball_data.csv"
WHITE_BALL_RANGE = (1, 69)
RED_BALL_RANGE = (1, 26)

def download_data():
    """Downloads the latest Powerball data if not compatible or force update."""
    print(f"Downloading data from {DATA_URL}...")
    try:
        response = requests.get(DATA_URL)
        response.raise_for_status()
        with open(CSV_FILE, 'wb') as f:
            f.write(response.content)
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading data: {e}")

def load_data():
    """Loads data from CSV and preprocesses it."""
    if not os.path.exists(CSV_FILE):
        download_data()
    
    try:
        df = pd.read_csv(CSV_FILE)
        # Ensure 'Winning Numbers' exists
        if 'Winning Numbers' not in df.columns:
            raise ValueError("Column 'Winning Numbers' not found in data.")
        
        # Preprocess: '11 21 27 36 62 24' -> [11, 21, 27, 36, 62, 24]
        # The first 5 are White Balls, the last 1 is the Red Powerball
        df['numbers_list'] = df['Winning Numbers'].apply(lambda x: [int(n) for n in str(x).split()])
        
        # Filter for standard Powerball rules (post-2015 change mostly, but for simplicity we take all reasonable)
        # Actually, let's just analyze what we have. 
        # Note: Powerball rules changed over time. 
        # Current format (since Oct 2015): 5/69 + 1/26.
        # Before that it was different. Analyzing mixed data might skew stats for 'hot' numbers if ranges changed.
        # For a robust 'recent' recommendation, we might want to filter by date.
        # But for this MVP, we'll use all data or maybe just filter for the current rule set if date is available.
        # Let's inspect the date column. 'Draw Date' is usually MM/DD/YYYY.
        
        df['Draw Date'] = pd.to_datetime(df['Draw Date'])
        # Current rules started Oct 7, 2015.
        start_date = '2015-10-07'
        df_current_rules = df[df['Draw Date'] >= start_date].copy()
        
        print(f"Loaded {len(df)} total draws. Using {len(df_current_rules)} draws since {start_date} (Current Rules).")
        return df_current_rules
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def load_historical_combinations(df):
    """Returns a set of all past winning combinations (tuple of 5 sorted whites + red)."""
    history = set()
    for nums in df['numbers_list']:
        if len(nums) >= 6:
            whites = tuple(sorted(nums[:5]))
            red = nums[5]
            history.add((whites, red))
    return history

def check_sum_range(white_balls, min_sum=130, max_sum=220):
    """Checks if the sum of white balls is within the probable range."""
    return min_sum <= sum(white_balls) <= max_sum

def check_odd_even_ratio(white_balls):
    """Checks for 3:2 or 2:3 odd/even ratio."""
    odds = sum(1 for x in white_balls if x % 2 != 0)
    evens = 5 - odds
    return (odds == 3 and evens == 2) or (odds == 2 and evens == 3)

def check_high_low_balance(white_balls, threshold=35):
    """Checks for balanced high/low ratio (1-34 is low, 35-69 is high)."""
    lows = sum(1 for x in white_balls if x < threshold)
    highs = 5 - lows
    # Allow 2:3 or 3:2
    return (lows == 3 and highs == 2) or (lows == 2 and highs == 3)

def recommend_math_strategy(history_set):
    """Generates a number combination using statistical heuristics."""
    max_attempts = 100000
    
    for _ in range(max_attempts):
        # Generate random candidates provided they are unique
        white_balls = sorted(random.sample(range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1), 5))
        red_ball = random.randint(RED_BALL_RANGE[0], RED_BALL_RANGE[1])
        
        # 1. Past Exclusion
        if (tuple(white_balls), red_ball) in history_set:
            continue
            
        # 2. Sum Range Check
        if not check_sum_range(white_balls):
            continue
            
        # 3. Odd/Even Check
        if not check_odd_even_ratio(white_balls):
            continue
            
        # 4. High/Low Check
        if not check_high_low_balance(white_balls):
            continue
            
        # All checks passed
        return white_balls, red_ball
        
    return None, None # Should not happen with 100k attempts

# --- QUANTUM ALPHA STRATEGY MODULE ---

def calculate_momentum(df, decay_alpha=0.03):
    """Calculates Exponential Decay Momentum scores for all balls."""
    # Initialize scores
    white_scores = {n: 0.1 for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    red_scores = {n: 0.1 for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}
    
    # Iterate through draws (recent draws have higher weight)
    # df is chronologically sorted? We should ensure that.
    df_sorted = df.sort_values('Draw Date', ascending=True)
    
    total_draws = len(df_sorted)
    
    for idx, row in enumerate(df_sorted.itertuples()):
        # Calculate time weight: 0 for oldest, increasing for newest
        # Actually simpler: Apply decay to current score and add 1 for hit
        # But let's use the formula: sum(e^(-lambda * t))
        
        t = total_draws - 1 - idx # t=0 for most recent
        weight = math.exp(-decay_alpha * t)
        
        nums = row.numbers_list
        if len(nums) < 6: continue
        
        whites = nums[:5]
        red = nums[5]
        
        for w in whites:
            if w in white_scores:
                white_scores[w] += weight
        
        if red in red_scores:
            red_scores[red] += weight
            
    return white_scores, red_scores

def calculate_gap_z_scores(df):
    """Calculates Z-scores for the current 'Gap' (time since last drawn)."""
    # 1. Calculate gaps for all balls
    white_gaps = {n: [] for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    red_gaps = {n: [] for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}
    
    last_seen_white = {n: -1 for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    last_seen_red = {n: -1 for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}
    
    df_sorted = df.sort_values('Draw Date', ascending=True).reset_index(drop=True)
    total_draws = len(df_sorted)
    
    for idx, row in df_sorted.iterrows():
        nums = row['numbers_list']
        if len(nums) < 6: continue
        
        whites = nums[:5]
        red = nums[5]
        
        # Update Whites
        for w in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1):
            if w in whites:
                if last_seen_white[w] != -1:
                    gap = idx - last_seen_white[w]
                    white_gaps[w].append(gap)
                last_seen_white[w] = idx
                
        # Update Red
        r_range = range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)
        for r in r_range:
            if r == red:
                if last_seen_red[r] != -1:
                    gap = idx - last_seen_red[r]
                    red_gaps[r].append(gap)
                last_seen_red[r] = idx

    # 2. Calculate Current Gap and Stats
    white_z_scores = {}
    red_z_scores = {}
    
    for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1):
        current_gap = total_draws - 1 - last_seen_white[n]
        if not white_gaps[n]:
            # No history gaps? Treat as 0 Z-score or high if never seen
            white_z_scores[n] = 0
            continue
            
        mean_gap = statistics.mean(white_gaps[n])
        stdev_gap = statistics.pstdev(white_gaps[n]) if len(white_gaps[n]) > 1 else 1
        if stdev_gap == 0: stdev_gap = 1
        
        z = (current_gap - mean_gap) / stdev_gap
        white_z_scores[n] = z

    for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1):
        current_gap = total_draws - 1 - last_seen_red[n]
        if not red_gaps[n]:
            red_z_scores[n] = 0
            continue
            
        mean_gap = statistics.mean(red_gaps[n])
        stdev_gap = statistics.pstdev(red_gaps[n]) if len(red_gaps[n]) > 1 else 1
        if stdev_gap == 0: stdev_gap = 1
            
        z = (current_gap - mean_gap) / stdev_gap
        red_z_scores[n] = z
        
    return white_z_scores, red_z_scores

def quantum_selector(momentum, z_scores, n_picks=5):
    """Combines Momentum and Mean Reversion signals to select balls."""
    # Alpha = Momentum Score + (Z-Score * Multiplier)
    # We want positives from both ideally. 
    # High Momentum = Good. High Z-Score (Overdue) = Good.
    
    final_scores = {}
    for n in momentum:
        # Normalize/Scale signals? 
        # Momentum ~ 0-50, Z-Score ~ -1 to 4
        # Let's boost meaningful Z-scores
        z_signal = max(0, z_scores.get(n, 0)) * 5 # Amplify Z-score impact
        score = momentum[n] + z_signal
        final_scores[n] = score
        
    # Valid Selection Simulation (Monte Carlo Lite)
    # Because we need exactly 5 unique, weighted sampling is best
    
    candidates = list(final_scores.keys())
    weights = [final_scores[n] for n in candidates] # Assuming all positive
    
    # Ensure all positive
    min_w = min(weights)
    if min_w <= 0:
        weights = [w - min_w + 0.1 for w in weights]
        
    return get_weighted_sample(candidates, weights, n_picks)

def recommend_quantum(df, history_set):
    """Master function for Quantum Alpha Strategy."""
    
    # 1. Calculate Signals
    w_momentum, r_momentum = calculate_momentum(df)
    w_z, r_z = calculate_gap_z_scores(df)
    
    max_attempts = 100000
    for _ in range(max_attempts):
        # 2. Generate Candidate based on Signals
        white_balls = sorted(quantum_selector(w_momentum, w_z, 5))
        red_ball = quantum_selector(r_momentum, r_z, 1)[0]
        
        # 3. Risk Management Filters (Structural Integrity)
        if (tuple(white_balls), red_ball) in history_set:
            continue
        if not check_sum_range(white_balls):
            continue
        if not check_odd_even_ratio(white_balls):
            continue
        if not check_high_low_balance(white_balls):
            continue
            
        # 4. Spacing/Entropy Check (Diversification)
        # Prevent clustering: ensure standard deviation of diffs is healthy
        # or simple check: no 3 consecutive numbers
        diffs = [white_balls[i+1] - white_balls[i] for i in range(len(white_balls)-1)]
        if any(d == 1 for d in diffs):
            # Check for 3 consecutive: d=1 followed by d=1
            consecutive_count = 0
            has_triple = False
            for d in diffs:
                if d == 1:
                    consecutive_count += 1
                    if consecutive_count >= 2: # 1,2,3 has two diffs of 1
                        has_triple = True
                        break
                else:
                    consecutive_count = 0
            if has_triple:
                continue

        return white_balls, red_ball

    return None, None


# --- QUANTUM ULTRA STRATEGY (ENHANCED) ---

def analyze_pair_frequency(df, top_n=20):
    """Analyze which number pairs appear together frequently."""
    from itertools import combinations
    pair_counts = Counter()

    for nums in df['numbers_list']:
        if len(nums) >= 5:
            whites = nums[:5]
            for pair in combinations(sorted(whites), 2):
                pair_counts[pair] += 1

    return pair_counts.most_common(top_n)

def analyze_decade_distribution(df):
    """Analyze distribution across decades (1-9, 10-19, etc.)."""
    decade_counts = {i: 0 for i in range(7)}  # 0-9, 10-19, ..., 60-69

    for nums in df['numbers_list']:
        if len(nums) >= 5:
            for n in nums[:5]:
                decade_counts[n // 10] += 1

    return decade_counts

def analyze_ending_digits(df):
    """Analyze last digit distribution."""
    ending_counts = Counter()

    for nums in df['numbers_list']:
        if len(nums) >= 5:
            for n in nums[:5]:
                ending_counts[n % 10] += 1

    return ending_counts

def analyze_delta_patterns(df):
    """Analyze gaps between consecutive numbers."""
    delta_counts = Counter()

    for nums in df['numbers_list']:
        if len(nums) >= 5:
            sorted_whites = sorted(nums[:5])
            for i in range(4):
                delta = sorted_whites[i+1] - sorted_whites[i]
                delta_counts[delta] += 1

    return delta_counts

def calculate_recent_momentum(df, n_recent=10, decay=0.15):
    """Calculate momentum focusing on most recent N draws."""
    white_scores = {n: 0.1 for n in range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1)}
    red_scores = {n: 0.1 for n in range(RED_BALL_RANGE[0], RED_BALL_RANGE[1] + 1)}

    df_sorted = df.sort_values('Draw Date', ascending=False).head(n_recent)

    for idx, row in enumerate(df_sorted.itertuples()):
        weight = math.exp(-decay * idx)  # Most recent = highest weight
        nums = row.numbers_list
        if len(nums) < 6:
            continue

        for w in nums[:5]:
            if w in white_scores:
                white_scores[w] += weight * 2  # Boost recent

        if nums[5] in red_scores:
            red_scores[nums[5]] += weight * 2

    return white_scores, red_scores

def check_decade_balance(white_balls):
    """Ensure numbers span at least 3 different decades."""
    decades = set(n // 10 for n in white_balls)
    return len(decades) >= 3

def check_ending_diversity(white_balls):
    """Ensure at least 4 different ending digits."""
    endings = set(n % 10 for n in white_balls)
    return len(endings) >= 4

def quantum_ultra_selector(momentum, z_scores, recent_momentum, pair_bonus, n_picks=5):
    """Enhanced selector combining multiple signals."""
    final_scores = {}

    for n in momentum:
        # Base momentum
        base = momentum[n]
        # Z-score boost (overdue numbers)
        z_boost = max(0, z_scores.get(n, 0)) * 5
        # Recent trend boost
        recent_boost = recent_momentum.get(n, 0) * 1.5
        # Pair synergy (numbers that appear with hot numbers)
        pair_boost = pair_bonus.get(n, 0) * 0.5

        final_scores[n] = base + z_boost + recent_boost + pair_boost

    candidates = list(final_scores.keys())
    weights = [max(0.1, final_scores[n]) for n in candidates]

    return get_weighted_sample(candidates, weights, n_picks)

def recommend_quantum_ultra(df, history_set):
    """QUANTUM ULTRA - Enhanced prediction algorithm."""

    # Calculate all signals
    w_momentum, r_momentum = calculate_momentum(df)
    w_z, r_z = calculate_gap_z_scores(df)
    w_recent, r_recent = calculate_recent_momentum(df, n_recent=15)

    # Get hot pairs for synergy scoring
    hot_pairs = analyze_pair_frequency(df, top_n=50)
    pair_bonus = Counter()
    for (a, b), count in hot_pairs:
        pair_bonus[a] += count * 0.1
        pair_bonus[b] += count * 0.1

    max_attempts = 150000
    for _ in range(max_attempts):
        # Generate with ultra selector
        white_balls = sorted(quantum_ultra_selector(w_momentum, w_z, w_recent, pair_bonus, 5))
        red_ball = quantum_ultra_selector(r_momentum, r_z, r_recent, {}, 1)[0]

        # FILTERS
        # 1. No duplicates from history
        if (tuple(white_balls), red_ball) in history_set:
            continue

        # 2. Sum range (130-220)
        if not check_sum_range(white_balls):
            continue

        # 3. Odd/Even ratio (2:3 or 3:2)
        if not check_odd_even_ratio(white_balls):
            continue

        # 4. High/Low balance
        if not check_high_low_balance(white_balls):
            continue

        # 5. Decade balance (at least 3 decades)
        if not check_decade_balance(white_balls):
            continue

        # 6. Ending digit diversity (at least 4 different)
        if not check_ending_diversity(white_balls):
            continue

        # 7. No triple consecutive
        diffs = [white_balls[i+1] - white_balls[i] for i in range(4)]
        consecutive_ones = sum(1 for d in diffs if d == 1)
        if consecutive_ones >= 2:
            continue

        return white_balls, red_ball

    return None, None


def analyze_frequencies(df):
    """Calculates frequencies for White and Red balls."""
    white_balls = []
    red_balls = []
    
    for nums in df['numbers_list']:
        if len(nums) >= 6:
            white_balls.extend(nums[:5])
            red_balls.append(nums[5])
            
    white_counts = Counter(white_balls)
    red_counts = Counter(red_balls)
    
    return white_counts, red_counts

def get_hot_numbers(counter, top_n=10):
    return [num for num, count in counter.most_common(top_n)]

def get_cold_numbers(counter, range_min, range_max, bottom_n=10):
    # Get all possible numbers
    all_nums = set(range(range_min, range_max + 1))
    # Count observed
    observed = set(counter.keys())
    # Zero frequency numbers
    never_drawn = list(all_nums - observed)
    
    # Sort by frequency (ascending)
    sorted_by_freq = sorted(counter.items(), key=lambda x: x[1])
    least_frequent = [num for num, count in sorted_by_freq[:bottom_n]]
    
    # Combine never drawn and least frequent
    cold_candidates = never_drawn + least_frequent
    return cold_candidates[:bottom_n] # Return top bottom candidates

def recommend(strategy, white_counts, red_counts):
    """Generates a recommendation based on strategy."""
    
    # White Balls Selection (Need 5 unique)
    white_recs = []
    if strategy == 'hot':
        # Pick from top 50% frequent numbers to maintain some randomness but favor hot
        # Or simple: Weighted choice based on frequency
        population = list(white_counts.keys())
        weights = list(white_counts.values())
        white_recs = get_weighted_sample(population, weights, 5)
        
        # Red Ball
        population_r = list(red_counts.keys())
        weights_r = list(red_counts.values())
        red_rec = get_weighted_sample(population_r, weights_r, 1)[0]
        
    elif strategy == 'cold':
        # Inverse weights? Or just pick from cold list
        # detailed implementation:
        # We want numbers that haven't appeared lately or have low overall count.
        # Simple approach: Inverse probability weighting is tricky if count is 0.
        # Let's just pick randomly from the bottom 50% of frequency.
        
        sorted_white = sorted(white_counts.items(), key=lambda x: x[1])
        bottom_half_white = [x[0] for x in sorted_white[:len(sorted_white)//2]]
        # If not enough, take more
        if len(bottom_half_white) < 5:
            bottom_half_white = list(white_counts.keys())
            
        white_recs = random.sample(bottom_half_white, 5)
        
        sorted_red = sorted(red_counts.items(), key=lambda x: x[1])
        bottom_half_red = [x[0] for x in sorted_red[:len(sorted_red)//2]]
        if not bottom_half_red:
             bottom_half_red = list(red_counts.keys())
        red_rec = random.choice(bottom_half_red)

    elif strategy == 'math':
        # NOTE: This requires history_set to be passed too, but to keep signature simple 
        # we might need to change how we call this or do it inside main.
        # Let's adjust main to call specific function, or handle it here if we pass history.
        # For minimal disruption, we'll return None here and handle in main, or pass history in kwargs if we refactor.
        # Actually, let's just make `recommend` take *args or handle it outside.
        pass # Handle in main for clarity

    elif strategy == 'random':
        white_recs = random.sample(range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1), 5)
        red_rec = random.randint(RED_BALL_RANGE[0], RED_BALL_RANGE[1])
        
    else: # Balanced or Default
        # A mix? Let's just do fully random but valid
        white_recs = random.sample(range(WHITE_BALL_RANGE[0], WHITE_BALL_RANGE[1] + 1), 5)
        red_rec = random.randint(RED_BALL_RANGE[0], RED_BALL_RANGE[1])

    return sorted(white_recs), red_rec

def get_weighted_sample(population, weights, k):
    # random.choices is with replacement, we need without replacement for white balls
    # But for a simple weighted sample without replacement:
    # We can use numpy but want to avoid extra deps if possible, though we have pandas (which implies numpy usually).
    # Let's use a simple loop
    selected = set()
    while len(selected) < k:
        choice = random.choices(population, weights=weights, k=1)[0]
        selected.add(choice)
    return list(selected)

def main():
    print("--- Powerball Number Recommender ---")
    df = load_data()
    if df is None:
        return

    white_counts, red_counts = analyze_frequencies(df)
    
    print("\nTop 5 Hot White Balls:", get_hot_numbers(white_counts, 5))
    print("Top 3 Hot Red Balls:", get_hot_numbers(red_counts, 3))
    
    while True:
        print("\nSelect Strategy:")
        print("1. Hot Numbers (High Frequency based)")
        print("2. Cold Numbers (Low Frequency based)")
        print("3. Random Luck")
        print("4. Smart Math Strategy (Statistical Probability)")
        print("5. Quantum Alpha (Wall Street Momentum + Mean Reversion)")
        print("q. Quit")
        
        choice = input("Enter choice: ").strip().lower()
        
        if choice == 'q':
            break
        
        strategy = 'random'
        if choice == '1':
            strategy = 'hot'
        elif choice == '2':
            strategy = 'cold'
        elif choice == '3':
            strategy = 'random'
        elif choice == '4':
            strategy = 'math'
        elif choice == '5':
            strategy = 'quantum'
            
        if strategy == 'math':
            # Need history for this one
            history_set = load_historical_combinations(df)
            w, r = recommend_math_strategy(history_set)
            if w is None:
                print("Could not generate a number satisfying all criteria.")
                continue
        elif strategy == 'quantum':
            history_set = load_historical_combinations(df)
            print("Running Quantum Alpha Simulation...")
            w, r = recommend_quantum(df, history_set)
            if w is None:
                print("Market Volatility too high. No stable Alpha found.")
                continue
        else:
            w, r = recommend(strategy, white_counts, red_counts)

        print(f"\n[{strategy.upper()} Recommendation]")
        print(f"White Balls: {w}")
        print(f"Powerball:   {r}")

def generate_all_recommendations():
    """Generate recommendations for all strategies."""
    print("--- Powerball Number Recommender - All Strategies ---")
    df = load_data()
    if df is None:
        return

    white_counts, red_counts = analyze_frequencies(df)
    history_set = load_historical_combinations(df)

    strategies = [
        ('hot', 'Hot Numbers'),
        ('cold', 'Cold Numbers'),
        ('random', 'Random Luck'),
        ('math', 'Smart Math Strategy'),
        ('quantum', 'Quantum Alpha')
    ]

    print("\nGenerating recommendations for tomorrow's draw:\n")

    for strategy_key, strategy_name in strategies:
        print(f"=== {strategy_name} ===")

        if strategy_key == 'math':
            w, r = recommend_math_strategy(history_set)
        elif strategy_key == 'quantum':
            print("Running Quantum Alpha Simulation...")
            w, r = recommend_quantum(df, history_set)
        else:
            w, r = recommend(strategy_key, white_counts, red_counts)

        if w is None or r is None:
            print("Could not generate recommendation for this strategy.")
            continue

        print(f"White Balls: {w}")
        print(f"Powerball:   {r}")
        print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        generate_all_recommendations()
    else:
        main()
