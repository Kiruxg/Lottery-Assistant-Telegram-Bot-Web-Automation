"""Verify dashboard EV values match calculations"""

import json
from src.ev_calculator import EVCalculator

config = json.load(open('config.json'))
calc = EVCalculator(config)

print("=" * 80)
print("DASHBOARD EV VERIFICATION")
print("=" * 80)
print()

# Test cases matching dashboard
test_cases = [
    ('Lucky Day Lotto Evening', 450_000, 1_221_759, 1.0, 0.1),
    ('Powerball', 43_000_000, 292_201_338, 2.0, 0.15),
    ('Mega Millions', 285_000_000, 302_575_350, 5.0, 0.15),
]

for name, jackpot, odds, cost, secondary in test_cases:
    result = calc.calculate_ev(jackpot, odds, cost, secondary)
    
    # Calculate progress
    break_even = result['break_even_jackpot']
    progress_pct = (jackpot / break_even) * 100 if break_even > 0 else 0
    remaining = break_even - jackpot
    
    print(f"{name}:")
    print(f"  Jackpot: ${jackpot:,}")
    print(f"  Net EV: ${result['net_ev']:.4f} (displayed as ${round(result['net_ev']):.0f})")
    print(f"  EV %: {result['ev_percentage']:.2f}%")
    print(f"  Break-even: ${break_even:,.0f}")
    print(f"  Progress: {progress_pct:.2f}% to +EV")
    print(f"  Remaining: ${remaining:,.0f}")
    print()
    
    # Verify against dashboard values
    if name == 'Lucky Day Lotto Evening':
        assert abs(result['ev_percentage'] - (-75.85)) < 0.1, "LDL EV% mismatch"
        assert abs(progress_pct - 15.73) < 0.1, "LDL progress mismatch"
        assert abs(remaining - 2_411_262) < 1000, "LDL remaining mismatch"
        print("  [OK] Matches dashboard: 15.73% to +EV ($2,411,262 remaining)")
    elif name == 'Powerball':
        assert abs(result['ev_percentage'] - (-89.67)) < 0.1, "PB EV% mismatch"
        assert abs(progress_pct - 3.06) < 0.1, "PB progress mismatch"
        assert abs(remaining - 1_363_641_882) < 1000000, "PB remaining mismatch"
        print("  [OK] Matches dashboard: 3.06% to +EV ($1,363,641,882 remaining)")
    elif name == 'Mega Millions':
        assert abs(result['ev_percentage'] - (-89.76)) < 0.1, "MM EV% mismatch"
        assert abs(progress_pct - 7.46) < 0.1, "MM progress mismatch"
        assert abs(remaining - 3_533_606_421) < 1000000, "MM remaining mismatch"
        print("  [OK] Matches dashboard: 7.46% to +EV ($3,533,606,421 remaining)")
    print()

print("=" * 80)
print("[OK] ALL DASHBOARD VALUES VERIFIED - EV CALCULATIONS ARE ACCURATE")
print("=" * 80)
print()
print("Note: Net EV values are rounded for display (-$0.76 -> -$1, -$1.79 -> -$2, -$4.49 -> -$4)")
print("This is intentional for readability. The underlying calculations are precise.")
