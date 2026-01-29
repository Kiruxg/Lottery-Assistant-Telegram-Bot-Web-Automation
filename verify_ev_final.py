"""Final verification of EV calculations with correct ticket costs"""

import json
from src.ev_calculator import EVCalculator

config = json.load(open('config.json'))
calc = EVCalculator(config)

print("=" * 80)
print("FINAL EV VERIFICATION - CORRECTED TICKET COSTS")
print("=" * 80)
print()

games = [
    ('Mega Millions', 285_000_000, 302_575_350, 2.0, 0.15),
    ('Lucky Day Lotto', 450_000, 575_757, 1.0, 0.10),
    ('Powerball', 43_000_000, 292_201_338, 2.0, 0.15),
]

for name, jackpot, odds, cost, secondary in games:
    result = calc.calculate_ev(jackpot, odds, cost, secondary)
    
    print(f"{name}:")
    print(f"  Jackpot: ${jackpot:,}")
    print(f"  Ticket Cost: ${cost:.2f}")
    print(f"  Net EV: ${result['net_ev']:.4f}")
    print(f"  EV %: {result['ev_percentage']:.2f}%")
    print(f"  Is +EV: {result['is_positive_ev']}")
    print(f"  Break-even: ${result['break_even_jackpot']:,.0f}")
    print()

print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
