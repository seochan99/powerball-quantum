import csv
import random
from powerball_app import (
    load_data, load_historical_combinations, calculate_momentum,
    calculate_gap_z_scores, quantum_selector, check_sum_range,
    check_odd_even_ratio, check_high_low_balance, WHITE_BALL_RANGE, RED_BALL_RANGE
)

def generate_tomorrow_picks(count=100, filename='tomorrow_picks.csv'):
    print(f"Generating {count} picks for tomorrow's draw...")
    df = load_data()
    if df is None:
        return

    history_set = load_historical_combinations(df)

    # Calculate signals once
    w_mom, r_mom = calculate_momentum(df)
    w_z, r_z = calculate_gap_z_scores(df)

    picks = []

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Pick', 'White_1', 'White_2', 'White_3', 'White_4', 'White_5', 'Red_Ball']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, count + 1):
            # Try to find a valid pick
            valid_pick = None
            for _ in range(10000):  # Reasonable attempts per pick
                white_balls = sorted(quantum_selector(w_mom, w_z, 5))
                red_ball = quantum_selector(r_mom, r_z, 1)[0]

                # Apply filters
                if (tuple(white_balls), red_ball) in history_set:
                    continue
                if not check_sum_range(white_balls):
                    continue
                if not check_odd_even_ratio(white_balls):
                    continue
                if not check_high_low_balance(white_balls):
                    continue

                # Spacing check
                diffs = [white_balls[j+1] - white_balls[j] for j in range(len(white_balls)-1)]
                if any(d == 1 for d in diffs):
                    consecutive_count = 0
                    has_triple = False
                    for d in diffs:
                        if d == 1:
                            consecutive_count += 1
                            if consecutive_count >= 2:
                                has_triple = True
                                break
                        else:
                            consecutive_count = 0
                    if has_triple:
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
                picks.append(f"{w} + {r}")

    print(f"Generated {len(picks)} picks in {filename}")
    print("\nFirst 10 picks:")
    for i, pick in enumerate(picks[:10], 1):
        print(f"{i:2d}. {pick}")

    return picks

if __name__ == "__main__":
    generate_tomorrow_picks(1000000, 'quantum_alpha_1000000.csv')
