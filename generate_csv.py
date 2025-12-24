import csv
import random
from powerball_app import (
    load_data, load_historical_combinations, calculate_momentum,
    calculate_gap_z_scores, quantum_selector, check_sum_range,
    check_odd_even_ratio, check_high_low_balance, WHITE_BALL_RANGE, RED_BALL_RANGE,
    # ULTRA imports
    calculate_recent_momentum, analyze_pair_frequency, quantum_ultra_selector,
    check_decade_balance, check_ending_diversity
)
from collections import Counter

def generate_batch_ultra(count, filename, w_mom, r_mom, w_z, r_z, w_recent, r_recent, pair_bonus, history_set):
    """QUANTUM ULTRA batch generator with enhanced filters."""
    print(f"Generating {count} ULTRA picks for {filename}...")
    picks = []
    attempts_per_pick = 150000

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Pick', 'White_1', 'White_2', 'White_3', 'White_4', 'White_5', 'Red_Ball']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, count + 1):
            if i % 10000 == 0:
                print(f"  Progress: {i:,} / {count:,} ({100*i/count:.1f}%)")

            valid_pick = None
            for _ in range(attempts_per_pick):
                # ULTRA selector with all signals
                white_balls = sorted(quantum_ultra_selector(w_mom, w_z, w_recent, pair_bonus, 5))
                red_ball = quantum_ultra_selector(r_mom, r_z, r_recent, {}, 1)[0]

                # FILTER 1: No history duplicates
                if (tuple(white_balls), red_ball) in history_set:
                    continue

                # FILTER 2: Sum range (130-220)
                if not check_sum_range(white_balls):
                    continue

                # FILTER 3: Odd/Even ratio (2:3 or 3:2)
                if not check_odd_even_ratio(white_balls):
                    continue

                # FILTER 4: High/Low balance
                if not check_high_low_balance(white_balls):
                    continue

                # FILTER 5: Decade balance (at least 3 decades)
                if not check_decade_balance(white_balls):
                    continue

                # FILTER 6: Ending digit diversity (at least 4 different)
                if not check_ending_diversity(white_balls):
                    continue

                # FILTER 7: No triple consecutive
                diffs = [white_balls[j+1] - white_balls[j] for j in range(4)]
                consecutive_ones = sum(1 for d in diffs if d == 1)
                if consecutive_ones >= 2:
                    continue

                valid_pick = (white_balls, red_ball)
                break

            if valid_pick:
                w, r = valid_pick
                writer.writerow({
                    'Pick': i,
                    'White_1': w[0], 'White_2': w[1], 'White_3': w[2], 'White_4': w[3], 'White_5': w[4],
                    'Red_Ball': r
                })
                picks.append((w, r))
            else:
                print(f"Warning: Could not generate pick {i}")

    return picks

def main():
    print("=" * 60)
    print("QUANTUM ULTRA GENERATOR - Enhanced Algorithm v2.0")
    print("=" * 60)
    print("\nLoading Data & Calculating All Signals...")

    df = load_data()
    if df is None:
        return

    history_set = load_historical_combinations(df)
    print(f"Loaded {len(history_set)} historical combinations to avoid.")

    # Calculate ALL signals
    print("Calculating Base Momentum...")
    w_mom, r_mom = calculate_momentum(df)

    print("Calculating Z-Scores (Overdue Analysis)...")
    w_z, r_z = calculate_gap_z_scores(df)

    print("Calculating Recent Momentum (Last 15 draws)...")
    w_recent, r_recent = calculate_recent_momentum(df, n_recent=15)

    print("Analyzing Pair Synergy...")
    hot_pairs = analyze_pair_frequency(df, top_n=50)
    pair_bonus = Counter()
    for (a, b), count in hot_pairs:
        pair_bonus[a] += count * 0.1
        pair_bonus[b] += count * 0.1

    print("\nAll signals calculated! Starting generation...\n")

    # Generate 1 million ULTRA picks
    generate_batch_ultra(
        1000000,
        'quantum_ultra_1000000.csv',
        w_mom, r_mom, w_z, r_z, w_recent, r_recent, pair_bonus, history_set
    )

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("File created: quantum_ultra_1000000.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()
