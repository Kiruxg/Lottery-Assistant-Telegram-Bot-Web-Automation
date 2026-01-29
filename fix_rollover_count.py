"""
Fix rollover count for games

This script allows you to manually set the rollover count and cycle start jackpot
for games where the automatic calculation is incorrect.

Usage:
    python fix_rollover_count.py <game_id> <rollover_count> [cycle_start_jackpot]

Example:
    python fix_rollover_count.py mega_millions 7 157000000
"""

import json
import os
import sys
from pathlib import Path

def fix_rollover_count(game_id: str, rollover_count: int, cycle_start_jackpot: float = None):
    """Fix rollover count in state file"""
    state_file = os.getenv('LOTTERY_STATE_FILE', 'lottery_state.json')
    
    if not os.path.exists(state_file):
        print(f"[ERROR] State file not found: {state_file}")
        return False
    
    # Load state
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    if 'games' not in state:
        state['games'] = {}
    
    if game_id not in state['games']:
        print(f"[ERROR] Game {game_id} not found in state")
        return False
    
    game_state = state['games'][game_id]
    
    # Update rollover count
    game_state['rollover_count'] = rollover_count
    
    # Update cycle start jackpot if provided
    if cycle_start_jackpot is not None:
        game_state['cycle_start_jackpot'] = cycle_start_jackpot
        print(f"[OK] Set cycle_start_jackpot to ${cycle_start_jackpot:,.0f}")
    
    # Save state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"[OK] Updated {game_id}:")
    print(f"   Rollover count: {rollover_count}")
    if cycle_start_jackpot:
        print(f"   Cycle start jackpot: ${cycle_start_jackpot:,.0f}")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_rollover_count.py <game_id> <rollover_count> [cycle_start_jackpot]")
        print()
        print("Available game IDs:")
        print("  - lucky_day_lotto_midday")
        print("  - lucky_day_lotto_evening")
        print("  - powerball")
        print("  - mega_millions")
        print()
        print("Example:")
        print("  python fix_rollover_count.py mega_millions 7 157000000")
        sys.exit(1)
    
    game_id = sys.argv[1]
    try:
        rollover_count = int(sys.argv[2])
    except ValueError:
        print(f"[ERROR] Invalid rollover_count: {sys.argv[2]} (must be an integer)")
        sys.exit(1)
    
    cycle_start_jackpot = None
    if len(sys.argv) > 3:
        try:
            cycle_start_jackpot = float(sys.argv[3])
        except ValueError:
            print(f"[ERROR] Invalid cycle_start_jackpot: {sys.argv[3]} (must be a number)")
            sys.exit(1)
    
    # Validate game_id
    valid_games = ['lucky_day_lotto_midday', 'lucky_day_lotto_evening', 'lotto', 'powerball', 'mega_millions', 'pick_3', 'pick_4', 'hot_wins']
    if game_id not in valid_games:
        print(f"[ERROR] Invalid game_id: {game_id}")
        print(f"Valid games: {', '.join(valid_games)}")
        sys.exit(1)
    
    fix_rollover_count(game_id, rollover_count, cycle_start_jackpot)
