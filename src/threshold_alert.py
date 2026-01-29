"""
Threshold Alert Logic Module
Manages jackpot thresholds and alert triggering
"""

import logging
import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class ThresholdAlert:
    """Manages threshold-based alerts"""
    
    def __init__(self, state_file: str = "lottery_state.json", 
                 min_threshold: Optional[float] = None,
                 step_increment: Optional[float] = None):
        """
        Initialize threshold alert system
        
        Args:
            state_file: Path to state persistence file
            min_threshold: Minimum jackpot threshold (or from env)
            step_increment: Step increment for alerts (or from env)
        """
        self.state_file = state_file
        self.min_threshold = min_threshold or float(os.getenv('MIN_JACKPOT_THRESHOLD', '500000'))
        self.step_increment = step_increment or float(os.getenv('JACKPOT_STEP_INCREMENT', '50000'))
        
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """Save state to file"""
        try:
            # Debug logging for pick_4 and hot_wins
            if 'games' in self.state:
                pick_4_state = self.state['games'].get('pick_4', {})
                hot_wins_state = self.state['games'].get('hot_wins', {})
                if pick_4_state:
                    logger.info(f"[PICK_4] _save_state: About to save last_jackpot = {pick_4_state.get('last_jackpot')}")
                if hot_wins_state:
                    logger.info(f"[HOT_WINS] _save_state: About to save last_jackpot = {hot_wins_state.get('last_jackpot')}")
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            # Verify after save
            if 'games' in self.state:
                pick_4_state = self.state['games'].get('pick_4', {})
                hot_wins_state = self.state['games'].get('hot_wins', {})
                if pick_4_state:
                    logger.info(f"[PICK_4] _save_state: Successfully saved, last_jackpot = {pick_4_state.get('last_jackpot')}")
                if hot_wins_state:
                    logger.info(f"[HOT_WINS] _save_state: Successfully saved, last_jackpot = {hot_wins_state.get('last_jackpot')}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            import traceback
            logger.error(f"State save error traceback: {traceback.format_exc()}")
    
    def _get_game_state(self, game_id: str) -> Dict:
        """Get or create state for a game"""
        if 'games' not in self.state:
            self.state['games'] = {}
        
        if game_id not in self.state['games']:
            self.state['games'][game_id] = {
                'last_jackpot': 0,
                'last_threshold': 0,
                'last_alert_time': None,
                'thresholds_hit': [],
                'active_buy_signal': False,
                'buy_signal_last_seen': None,
                'buy_signal_reminder_sent': False,
                'cycle_start_jackpot': None,  # Track jackpot when current cycle started
                'rollover_count': 0
            }
        
        return self.state['games'][game_id]
    
    def check_threshold(self, game_id: str, current_jackpot: float, 
                       min_threshold: Optional[float] = None,
                       threshold_operator: str = ">=") -> Optional[Dict]:
        """
        Check if current jackpot hits the threshold
        
        Args:
            game_id: Game identifier
            current_jackpot: Current jackpot value
            min_threshold: Minimum threshold for this game (overrides default)
            threshold_operator: Comparison operator (">=" or ">") for minimum threshold
            
        Returns:
            Alert info dict if threshold hit, None otherwise
        """
        game_state = self._get_game_state(game_id)
        # Get the PREVIOUS jackpot value (before updating)
        last_jackpot = game_state.get('last_jackpot', 0)
        last_threshold = game_state.get('last_threshold', 0)
        
        # Use game-specific threshold if provided, otherwise use default
        # NOTE: If min_threshold parameter is None, it means the game has no threshold configured
        # and we should use None (not fall back to default). This allows games like pick_3, pick_4, hot_wins
        # to skip threshold checking entirely.
        if min_threshold is None:
            # Explicitly None from config - don't use default threshold
            game_min_threshold = None
        else:
            # Use the provided threshold value
            game_min_threshold = min_threshold
        
        # If no threshold configured for this game, skip threshold checking
        if game_min_threshold is None:
            # Update jackpot tracking: move current to previous, then update current
            if 'last_jackpot' in game_state and game_state['last_jackpot'] != current_jackpot:
                game_state['previous_jackpot'] = game_state['last_jackpot']
            
            # Debug logging for pick_4 and hot_wins
            if game_id in ['pick_4', 'hot_wins']:
                logger.info(f"[{game_id.upper()}] check_threshold (no threshold): Updating last_jackpot from {game_state.get('last_jackpot')} to {current_jackpot}")
            
            game_state['last_jackpot'] = current_jackpot
            
            # Verify the update
            if game_id in ['pick_4', 'hot_wins']:
                logger.info(f"[{game_id.upper()}] check_threshold (no threshold): After update, game_state['last_jackpot'] = {game_state['last_jackpot']}")
                logger.info(f"[{game_id.upper()}] check_threshold (no threshold): self.state['games']['{game_id}']['last_jackpot'] = {self.state['games'][game_id]['last_jackpot']}")
            
            self._save_state()
            return None
        
        # Calculate rollover count based on cycle start jackpot
        # Track the jackpot when the current cycle started (after last win)
        rollover_increments = {
            'lucky_day_lotto_midday': 50000,
            'lucky_day_lotto_evening': 50000,
            'powerball': 2000000,
            'mega_millions': 2000000
        }
        
        rollover_increment = rollover_increments.get(game_id, 0)
        cycle_start_jackpot = game_state.get('cycle_start_jackpot')
        
        if rollover_increment > 0:
            # Check if jackpot reset (someone won) - jackpot dropped significantly
            # For Mega Millions: reset if drops below 50% of last jackpot AND is below $100M (new starting jackpot is $50M)
            # For Powerball: reset if drops below 50% of last jackpot AND is below $100M (starting jackpot is $20M)
            # For LDL: reset if drops below 50% of last jackpot AND is below $100k
            reset_thresholds = {
                'lucky_day_lotto_midday': 100000,
                'lucky_day_lotto_evening': 100000,
                'powerball': 100000000,
                'mega_millions': 100000000  # Still $100M threshold, but new cycles start at $50M
            }
            reset_threshold = reset_thresholds.get(game_id, 0)
            
            jackpot_reset = False
            if last_jackpot > 0 and current_jackpot < last_jackpot * 0.5 and current_jackpot <= reset_threshold:
                # Jackpot reset - someone won!
                jackpot_reset = True
                game_state['rollover_count'] = 0
                game_state['cycle_start_jackpot'] = current_jackpot
                game_state['last_won_date'] = datetime.now().isoformat()
                logger.info(f"Jackpot reset detected for {game_id} - rollover count reset to 0, cycle starts at ${current_jackpot:,.0f}")
            elif cycle_start_jackpot is None:
                # First time tracking - initialize cycle start
                game_state['cycle_start_jackpot'] = current_jackpot
                game_state['rollover_count'] = 0
                logger.info(f"Initialized cycle start jackpot for {game_id}: ${current_jackpot:,.0f}")
            elif not jackpot_reset and cycle_start_jackpot:
                # Calculate rollover count from cycle start
                if current_jackpot >= cycle_start_jackpot:
                    jackpot_increase = current_jackpot - cycle_start_jackpot
                    calculated_rollovers = max(0, int(jackpot_increase / rollover_increment))
                    
                    # Update rollover count (always use calculated value for accuracy)
                    game_state['rollover_count'] = calculated_rollovers
                    if calculated_rollovers > 0:
                        logger.debug(f"Rollover count for {game_id}: {calculated_rollovers} (from ${cycle_start_jackpot:,.0f} to ${current_jackpot:,.0f})")
                else:
                    # Jackpot somehow below cycle start (shouldn't happen, but reset cycle)
                    logger.warning(f"Jackpot ${current_jackpot:,.0f} below cycle start ${cycle_start_jackpot:,.0f} for {game_id} - resetting cycle")
                    game_state['cycle_start_jackpot'] = current_jackpot
                    game_state['rollover_count'] = 0
        
        # Update jackpot tracking: move current to previous, then update current
        # This allows dashboard to show change between checks
        if 'last_jackpot' in game_state and game_state['last_jackpot'] != current_jackpot:
            game_state['previous_jackpot'] = game_state['last_jackpot']
        
        # Debug logging for pick_4 and hot_wins
        if game_id in ['pick_4', 'hot_wins']:
            logger.info(f"[{game_id.upper()}] check_threshold: Updating last_jackpot from {game_state.get('last_jackpot')} to {current_jackpot}")
        
        game_state['last_jackpot'] = current_jackpot
        
        # Verify the update
        if game_id in ['pick_4', 'hot_wins']:
            logger.info(f"[{game_id.upper()}] check_threshold: After update, game_state['last_jackpot'] = {game_state['last_jackpot']}")
        
        # Reset threshold tracking if jackpot drops below threshold (allows re-alerting)
        if current_jackpot < game_min_threshold:
            if last_threshold > 0:
                # Reset threshold tracking when jackpot drops below
                game_state['last_threshold'] = 0
                self._save_state()
            return None
        
        # Simple threshold check: only alert when crossing min_threshold
        # Alert once when threshold is reached
        threshold_hit = None
        
        # Check if we've crossed the minimum threshold
        # Only trigger if we haven't already alerted for this threshold level
        if current_jackpot >= game_min_threshold and last_threshold == 0:
            threshold_hit = game_min_threshold
        
        if threshold_hit:
            # New threshold hit!
            alert_info = {
                'game_id': game_id,
                'current_jackpot': current_jackpot,
                'threshold': threshold_hit,
                'previous_jackpot': last_jackpot,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update state to the threshold that was hit
            game_state['last_threshold'] = threshold_hit
            game_state['last_alert_time'] = datetime.now().isoformat()
            game_state['thresholds_hit'].append({
                'threshold': threshold_hit,
                'jackpot': current_jackpot,
                'timestamp': datetime.now().isoformat()
            })
            
            self._save_state()
            logger.info(f"Threshold hit for {game_id}: ${threshold_hit:,.2f} (jackpot: ${current_jackpot:,.2f}, previous: ${last_jackpot:,.2f})")
            
            return alert_info
        
        self._save_state()
        return None
    
    def get_last_threshold(self, game_id: str) -> float:
        """Get the last threshold hit for a game"""
        game_state = self._get_game_state(game_id)
        return game_state.get('last_threshold', 0)
    
    def get_last_jackpot(self, game_id: str) -> float:
        """Get the last recorded jackpot for a game"""
        game_state = self._get_game_state(game_id)
        return game_state.get('last_jackpot', 0)
    
    def reset_thresholds(self, game_id: Optional[str] = None):
        """
        Reset thresholds for a game or all games
        
        Args:
            game_id: Game to reset, or None for all games
        """
        if game_id:
            if 'games' in self.state and game_id in self.state['games']:
                self.state['games'][game_id]['last_threshold'] = 0
                self._save_state()
        else:
            if 'games' in self.state:
                for game in self.state['games'].values():
                    game['last_threshold'] = 0
            self._save_state()
    
    def get_alert_message(self, alert_info: Dict, game_name: str) -> str:
        """
        Format alert message for Telegram
        
        Args:
            alert_info: Alert info dict from check_threshold
            game_name: Display name of the game
            
        Returns:
            Formatted message string
        """
        jackpot = alert_info['current_jackpot']
        threshold = alert_info['threshold']
        
        message = f"🎰 *Jackpot Alert: {game_name}*\n\n"
        message += f"💰 Current Jackpot: ${jackpot:,.2f}\n"
        message += f"🎯 Threshold Hit: ${threshold:,.2f}\n"
        message += f"📈 Previous Value: ${alert_info['previous_jackpot']:,.2f}\n"
        message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
