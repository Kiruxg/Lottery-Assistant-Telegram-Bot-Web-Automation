"""Verify EV calculations with corrected values from fact sheet"""

import json
from src.ev_calculator import EVCalculator

config = json.load(open('config.json'))
calc = EVCalculator(config)

print("=" * 80)
print("EV VERIFICATION - CORRECTED VALUES (Jan 27, 2026 Fact Sheet)")
print("=" * 80)
print()

# Mega Millions: $5 ticket, $285M jackpot
mm = calc.calculate_ev(285_000_000, 302_575_350, 5.0, 0.15)
print("Mega Millions:")
print(f"  Jackpot: $285,000,000")
print(f"  Ticket Cost: $5.00 (CORRECTED from $2.00)")
print(f"  Odds: 1 in 302,575,350")
print(f"  After Tax: ${mm['after_tax_jackpot']:,.2f}")
print(f"  Net EV: ${mm['net_ev']:.4f}")
print(f"  EV %: {mm['ev_percentage']:.2f}%")
print(f"  Break-even: ${mm['break_even_jackpot']:,.0f}")
print(f"  Is +EV: {mm['is_positive_ev']}")
print()

# Lucky Day Lotto: Correct odds 1:1,221,759
ldl = calc.calculate_ev(450_000, 1_221_759, 1.0, 0.1)
print("Lucky Day Lotto:")
print(f"  Jackpot: $450,000")
print(f"  Ticket Cost: $1.00")
print(f"  Odds: 1 in 1,221,759 (CORRECTED from 575,757)")
print(f"  After Tax: ${ldl['after_tax_jackpot']:,.2f}")
print(f"  Net EV: ${ldl['net_ev']:.4f}")
print(f"  EV %: {ldl['ev_percentage']:.2f}%")
print(f"  Break-even: ${ldl['break_even_jackpot']:,.0f}")
print(f"  Is +EV: {ldl['is_positive_ev']}")
print()

# Powerball: $2 ticket, $43M jackpot
pb = calc.calculate_ev(43_000_000, 292_201_338, 2.0, 0.15)
print("Powerball:")
print(f"  Jackpot: $43,000,000")
print(f"  Ticket Cost: $2.00")
print(f"  Odds: 1 in 292,201,338")
print(f"  After Tax: ${pb['after_tax_jackpot']:,.2f}")
print(f"  Net EV: ${pb['net_ev']:.4f}")
print(f"  EV %: {pb['ev_percentage']:.2f}%")
print(f"  Break-even: ${pb['break_even_jackpot']:,.0f}")
print(f"  Is +EV: {pb['is_positive_ev']}")
print()

print("=" * 80)
print("CORRECTIONS APPLIED:")
print("  1. Mega Millions ticket cost: $2.00 -> $5.00")
print("  2. Lucky Day Lotto odds: 575,757 -> 1,221,759")
print("=" * 80)
print()
print("All EV calculations now use correct values from official fact sheet.")
