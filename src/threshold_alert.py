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
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
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
                'buy_signal_reminder_sent': False
            }
        
        return self.state['games'][game_id]
    
    def check_threshold(self, game_id: str, current_jackpot: float, 
                       min_threshold: Optional[float] = None,
                       step_increment: Optional[float] = None,
                       threshold_operator: str = ">=") -> Optional[Dict]:
        """
        Check if current jackpot hits a new threshold
        
        Args:
            game_id: Game identifier
            current_jackpot: Current jackpot value
            min_threshold: Minimum threshold for this game (overrides default)
            step_increment: Step increment for this game (overrides default)
            threshold_operator: Comparison operator (">=" or ">") for minimum threshold
            
        Returns:
            Alert info dict if threshold hit, None otherwise
        """
        game_state = self._get_game_state(game_id)
        last_jackpot = game_state.get('last_jackpot', 0)
        last_threshold = game_state.get('last_threshold', 0)
        
        # Use game-specific thresholds if provided, otherwise use defaults
        game_min_threshold = min_threshold if min_threshold is not None else self.min_threshold
        game_step_increment = step_increment if step_increment is not None else self.step_increment
        
        # If no threshold configured for this game, skip threshold checking
        if game_min_threshold is None or game_step_increment is None:
            game_state['last_jackpot'] = current_jackpot
            self._save_state()
            return None
        
        # Track rollovers for all games
        last_jackpot = game_state.get('last_jackpot', 0)
        
        # Calculate rollover count based on current jackpot vs starting jackpot
        # Starting jackpots: LDL = $50k, Powerball/Mega = $20M
        starting_jackpots = {
            'lucky_day_lotto_midday': 50000,
            'lucky_day_lotto_evening': 50000,
            'powerball': 20000000,
            'mega_millions': 20000000
        }
        
        rollover_increments = {
            'lucky_day_lotto_midday': 50000,
            'lucky_day_lotto_evening': 50000,
            'powerball': 2000000,
            'mega_millions': 2000000
        }
        
        starting_jackpot = starting_jackpots.get(game_id, 0)
        rollover_increment = rollover_increments.get(game_id, 0)
        
        if starting_jackpot > 0 and rollover_increment > 0:
            # Check if jackpot reset (someone won) - jackpot dropped significantly
            if last_jackpot > 0 and current_jackpot < last_jackpot * 0.5 and current_jackpot <= starting_jackpot * 1.5:
                # Jackpot reset - someone won!
                game_state['rollover_count'] = 0
                game_state['last_won_date'] = datetime.now().isoformat()
                logger.info(f"Jackpot reset detected for {game_id} - rollover count reset to 0")
            else:
                # Calculate rollover count based on current jackpot
                if current_jackpot >= starting_jackpot:
                    # Calculate how many rollovers based on jackpot increase
                    jackpot_increase = current_jackpot - starting_jackpot
                    calculated_rollovers = int(jackpot_increase / rollover_increment)
                    
                    # Only update if calculated rollovers is higher than stored (or if not set)
                    stored_rollovers = game_state.get('rollover_count', 0)
                    if calculated_rollovers > stored_rollovers:
                        game_state['rollover_count'] = calculated_rollovers
                        logger.debug(f"Rollover count for {game_id}: {calculated_rollovers} (calculated from jackpot ${current_jackpot:,.0f})")
                    elif stored_rollovers == 0 and calculated_rollovers > 0:
                        # Initialize rollover count if not set
                        game_state['rollover_count'] = calculated_rollovers
                        logger.info(f"Initialized rollover count for {game_id}: {calculated_rollovers}")
                else:
                    # Jackpot below starting amount (shouldn't happen, but handle it)
                    game_state['rollover_count'] = 0
        
        # Update last jackpot
        game_state['last_jackpot'] = current_jackpot
        
        # Check if we've crossed a new threshold based on operator
        if threshold_operator == ">":
            # For ">", only trigger if strictly greater than threshold
            if current_jackpot <= game_min_threshold:
                self._save_state()
                return None
        else:
            # Default ">=" behavior
            if current_jackpot < game_min_threshold:
                self._save_state()
                return None
        
        # Calculate the next threshold
        if last_threshold == 0:
            # First threshold: minimum threshold
            next_threshold = game_min_threshold
        else:
            # Next threshold: last threshold + step increment
            next_threshold = last_threshold + game_step_increment
        
        # Check if we've crossed the threshold
        if current_jackpot >= next_threshold and last_jackpot < next_threshold:
            # New threshold hit!
            alert_info = {
                'game_id': game_id,
                'current_jackpot': current_jackpot,
                'threshold': next_threshold,
                'previous_jackpot': last_jackpot,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update state
            game_state['last_threshold'] = next_threshold
            game_state['last_alert_time'] = datetime.now().isoformat()
            game_state['thresholds_hit'].append({
                'threshold': next_threshold,
                'jackpot': current_jackpot,
                'timestamp': datetime.now().isoformat()
            })
            
            self._save_state()
            logger.info(f"Threshold hit for {game_id}: ${next_threshold:,.2f}")
            
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
