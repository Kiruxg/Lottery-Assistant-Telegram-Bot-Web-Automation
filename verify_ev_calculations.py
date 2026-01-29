"""
Verify EV calculations are accurate
Double and triple check the math
"""

import json
from src.ev_calculator import EVCalculator

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

calc = EVCalculator(config)

print("=" * 80)
print("EV CALCULATION VERIFICATION")
print("=" * 80)
print()

# Test cases with manual calculations
test_cases = [
    {
        'name': 'Mega Millions',
        'jackpot': 285_000_000,
        'odds': 302_575_350,
        'ticket_cost': 5.0,
        'secondary_ev': 0.15
    },
    {
        'name': 'Lucky Day Lotto',
        'jackpot': 450_000,
        'odds': 575_757,
        'ticket_cost': 1.0,
        'secondary_ev': 0.10
    },
    {
        'name': 'Powerball',
        'jackpot': 43_000_000,
        'odds': 292_201_338,
        'ticket_cost': 2.0,
        'secondary_ev': 0.15
    },
    {
        'name': 'Mega Millions - Break Even Test',
        'jackpot': 1_456_581_831,  # Expected break-even
        'odds': 302_575_350,
        'ticket_cost': 5.0,
        'secondary_ev': 0.15
    }
]

for test in test_cases:
    result = calc.calculate_ev(
        jackpot=test['jackpot'],
        odds=test['odds'],
        ticket_cost=test['ticket_cost'],
        secondary_prize_ev=test['secondary_ev']
    )
    
    # Manual calculation for verification
    tax_rate = 0.37
    lump_sum = 0.61
    
    after_tax_manual = test['jackpot'] * (1 - tax_rate) * lump_sum
    primary_ev_manual = after_tax_manual / test['odds']
    total_ev_manual = primary_ev_manual + test['secondary_ev']
    net_ev_manual = total_ev_manual - test['ticket_cost']
    ev_pct_manual = (net_ev_manual / test['ticket_cost']) * 100
    
    # Break-even calculation
    break_even_manual = (test['ticket_cost'] - test['secondary_ev']) * test['odds'] / ((1 - tax_rate) * lump_sum)
    
    print(f"[TEST] {test['name']}")
    print(f"   Jackpot: ${test['jackpot']:,.0f}")
    print(f"   Ticket Cost: ${test['ticket_cost']:.2f}")
    print(f"   Odds: 1 in {test['odds']:,}")
    print()
    print(f"   Manual Calculation:")
    print(f"   - After Tax (Lump Sum): ${after_tax_manual:,.2f}")
    print(f"   - Primary EV: ${primary_ev_manual:.6f}")
    print(f"   - Secondary EV: ${test['secondary_ev']:.2f}")
    print(f"   - Total EV: ${total_ev_manual:.6f}")
    print(f"   - Net EV: ${net_ev_manual:.6f}")
    print(f"   - EV %: {ev_pct_manual:.2f}%")
    print(f"   - Break-even Jackpot: ${break_even_manual:,.0f}")
    print()
    print(f"   Code Calculation:")
    print(f"   - After Tax (Lump Sum): ${result['after_tax_jackpot']:,.2f}")
    print(f"   - Primary EV: ${result['primary_ev']:.6f}")
    print(f"   - Secondary EV: ${result['secondary_ev']:.2f}")
    print(f"   - Total EV: ${result['total_ev']:.6f}")
    print(f"   - Net EV: ${result['net_ev']:.6f}")
    print(f"   - EV %: {result['ev_percentage']:.2f}%")
    print(f"   - Break-even Jackpot: ${result['break_even_jackpot']:,.0f}")
    print()
    
    # Verify accuracy
    assert abs(result['after_tax_jackpot'] - after_tax_manual) < 0.01, "After tax mismatch!"
    assert abs(result['primary_ev'] - primary_ev_manual) < 0.000001, "Primary EV mismatch!"
    assert abs(result['total_ev'] - total_ev_manual) < 0.000001, "Total EV mismatch!"
    assert abs(result['net_ev'] - net_ev_manual) < 0.000001, "Net EV mismatch!"
    assert abs(result['ev_percentage'] - ev_pct_manual) < 0.01, "EV % mismatch!"
    assert abs(result['break_even_jackpot'] - break_even_manual) < 1000, "Break-even mismatch!"
    
    print(f"   [OK] VERIFIED: All calculations match!")
    print()
    print(f"   Is Positive EV: {result['is_positive_ev']}")
    if result['is_positive_ev']:
        print(f"   [WARNING] This shows as +EV, verify jackpot is correct!")
    print()
    print("-" * 80)
    print()

print("=" * 80)
print("[OK] ALL CALCULATIONS VERIFIED - EV NUMBERS ARE ACCURATE")
print("=" * 80)
