"""Clear threshold alert history and reset for fresh logging"""

import json
from datetime import datetime

state_file = 'lottery_state.json'

# Load current state
with open(state_file, 'r') as f:
    state = json.load(f)

# Clear threshold alert history for all games
for game_id, game_state in state.get('games', {}).items():
    # Clear thresholds_hit array
    game_state['thresholds_hit'] = []
    
    # Reset last_alert_time to null
    game_state['last_alert_time'] = None
    
    # Reset last_threshold to 0 to allow re-alerting
    # This is important - if jackpot is already above threshold,
    # we need last_threshold = 0 to allow alerting when it crosses again
    game_state['last_threshold'] = 0
    
    print(f"Cleared threshold alerts for {game_id}")
    print(f"  - thresholds_hit: {len(game_state.get('thresholds_hit', []))} entries (cleared)")
    print(f"  - last_alert_time: {game_state.get('last_alert_time')}")
    print(f"  - last_threshold: {game_state.get('last_threshold')}")
    print()

# Save updated state
with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)

print(f"[OK] State file updated: {state_file}")
print()
print("The system will now log new threshold alerts when:")
print("  1. Jackpot crosses above the minimum threshold")
print("  2. Jackpot drops below threshold and then crosses back up")
print()
print("Note: If jackpots are already above threshold, alerts will trigger")
print("      when they drop below and cross back up, or on next refresh.")
