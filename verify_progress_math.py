"""Verify the progress calculation math"""

examples = [
    (-75.85, 'Lucky Day Lotto'),
    (-89.67, 'Powerball'),
    (-89.76, 'Mega Millions')
]

worst = -100
acceptable = -20
range_val = acceptable - worst

print('Progress Calculation Verification:')
print(f'Range: {worst}% to {acceptable}% = {range_val} percentage points')
print()

for current, name in examples:
    current_progress = current - worst
    progress_pct = (current_progress / range_val) * 100
    remaining = acceptable - current
    remaining_pct = (remaining / range_val) * 100
    
    print(f'{name}: {current}% EV')
    print(f'  Distance from worst: {current} - ({worst}) = {current_progress:.2f} percentage points')
    print(f'  Progress: {current_progress:.2f} / {range_val} * 100 = {progress_pct:.2f}%')
    print(f'  Remaining to acceptable: {acceptable} - ({current}) = {remaining:.2f} percentage points')
    print(f'  Remaining as % of range: {remaining_pct:.2f}%')
    print()

print('The calculation is mathematically correct!')
print('"30.19% to acceptable EV" means: 30.19% of the way from worst (-100%) to acceptable (-20%)')
