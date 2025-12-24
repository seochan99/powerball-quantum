"""
Command-line interface for powerball-quantum
"""

import argparse
import sys

from . import predict, quick_pick, update_data, __version__


def main():
    parser = argparse.ArgumentParser(
        prog='powerball-quantum',
        description='Powerball number predictor using quantum-inspired algorithm'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # predict command
    predict_parser = subparsers.add_parser('predict', help='Generate predicted numbers')
    predict_parser.add_argument('-c', '--count', type=int, default=5, help='Number of picks (default: 5)')
    predict_parser.add_argument('-a', '--analysis', action='store_true', help='Show signal analysis')

    # quick command
    subparsers.add_parser('quick', help='Get one quick pick')

    # update command
    subparsers.add_parser('update', help='Update data from NY Lottery API')

    args = parser.parse_args()

    if args.command == 'predict' or args.command is None:
        count = getattr(args, 'count', 5)
        analysis = getattr(args, 'analysis', False)

        print()
        print("🎱 POWERBALL QUANTUM PREDICTOR")
        print("=" * 50)

        picks = predict(count=count, show_analysis=analysis)

        print("\n⭐ RECOMMENDED PICKS:\n")
        for i, pick in enumerate(picks, 1):
            print(f"  #{i}  {pick}  (score: {pick.score:.1f})")

        print("\n" + "=" * 50)
        print("Good luck! 🍀\n")

    elif args.command == 'quick':
        pick = quick_pick()
        if pick:
            print(f"\n🎫 Your lucky numbers:\n\n   {pick}\n")

    elif args.command == 'update':
        print()
        print("📥 Updating Powerball data...")
        print("=" * 50)
        update_data()
        print("✅ Data updated successfully!\n")


if __name__ == '__main__':
    main()
