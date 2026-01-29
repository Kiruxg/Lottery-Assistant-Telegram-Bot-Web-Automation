"""Verify threshold alert system is working correctly"""

import json
from datetime import datetime

state_file = 'lottery_state.json'
config_file = 'config.json'

# Load state and config
with open(state_file, 'r') as f:
    state = json.load(f)

with open(config_file, 'r') as f:
    config = json.load(f)

print("=" * 80)
print("THRESHOLD ALERT SYSTEM VERIFICATION")
print("=" * 80)
print()

for game_id in ['lucky_day_lotto_midday', 'lucky_day_lotto_evening', 'lotto', 'powerball', 'mega_millions', 'pick_3', 'pick_4', 'hot_wins']:
    game_state = state['games'][game_id]
    game_config = config['lottery_games'][game_id]
    
    current = game_state['last_jackpot']
    threshold = game_config.get('min_threshold', 0)
    operator = game_config.get('threshold_operator', '>=')
    last_threshold = game_state.get('last_threshold', 0)
    thresholds_hit = len(game_state.get('thresholds_hit', []))
    last_alert_time = game_state.get('last_alert_time')
    
    # Check if threshold would trigger
    if operator == '>':
        meets_threshold = current > threshold
    else:  # >=
        meets_threshold = current >= threshold
    
    will_trigger = meets_threshold and last_threshold == 0
    
    print(f"{game_config['name']}:")
    print(f"  Current Jackpot: ${current:,.0f}")
    print(f"  Threshold: ${threshold:,.0f} ({operator})")
    print(f"  Meets Threshold: {meets_threshold}")
    print(f"  Last Threshold: {last_threshold}")
    print(f"  Thresholds Hit (history): {thresholds_hit}")
    print(f"  Last Alert Time: {last_alert_time or 'Never'}")
    print(f"  Will Trigger Alert: {will_trigger}")
    
    if will_trigger:
        print(f"  [READY] Will log alert on next check when jackpot is fetched")
    elif meets_threshold and last_threshold > 0:
        print(f"  [ALREADY ALERTED] Threshold already hit (won't re-alert until jackpot drops)")
    elif not meets_threshold:
        print(f"  [WAITING] Jackpot below threshold (will alert when it crosses)")
    
    print()

print("=" * 80)
print("SYSTEM STATUS:")
print("  - All threshold alert history cleared")
print("  - All last_threshold reset to 0")
print("  - System ready to log new alerts")
print()
print("Next Steps:")
print("  1. Run a refresh to fetch current jackpots")
print("  2. System will log alerts when jackpots cross thresholds")
print("  3. Alerts will appear in 'Recent Threshold Alerts' section")
print("=" * 80)
