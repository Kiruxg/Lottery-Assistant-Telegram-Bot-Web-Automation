"""
Buy Signal Logger
Tracks when buy signals are shown to users for entitlement enforcement
"""

import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class BuySignalLogger:
    """Tracks buy signal usage for entitlement enforcement"""
    
    def __init__(self, log_file: str = "buy_signals_log.json"):
        """
        Initialize buy signal logger
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self.logs = self._load_logs()
    
    def _load_logs(self) -> Dict:
        """Load logs from file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading buy signal logs: {e}")
                return {}
        return {}
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Error saving buy signal logs: {e}")
    
    def log_buy_signal(self, user_id: str, game_id: str, signal_type: str, 
                      draw_id: Optional[str] = None) -> None:
        """
        Log a buy signal shown to a user
        
        Args:
            user_id: User identifier
            game_id: Game identifier
            signal_type: Type of signal ('strong_buy', 'weak_buy', etc.)
            draw_id: Optional draw identifier
        """
        if user_id not in self.logs:
            self.logs[user_id] = []
        
        log_entry = {
            'game_id': game_id,
            'signal_type': signal_type,
            'draw_id': draw_id,
            'created_at': datetime.now().isoformat()
        }
        
        self.logs[user_id].append(log_entry)
        self._save_logs()
    
    def get_used_signals_this_month(self, user_id: str) -> int:
        """
        Count buy signals used by user in current month
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of buy signals used this month
        """
        if user_id not in self.logs:
            return 0
        
        # Get start of current month
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Count logs from this month
        count = 0
        for log_entry in self.logs[user_id]:
            try:
                created_at = datetime.fromisoformat(log_entry['created_at'])
                if created_at >= start_of_month:
                    count += 1
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing log entry: {e}")
                continue
        
        return count
    
    def get_remaining_signals(self, user_id: str, plan_limit: Optional[int]) -> Optional[int]:
        """
        Get remaining buy signals for user this month
        
        Args:
            user_id: User identifier
            plan_limit: Plan limit (None if unlimited)
            
        Returns:
            Remaining signals, or None if unlimited
        """
        if plan_limit is None:
            return None  # Unlimited
        
        used = self.get_used_signals_this_month(user_id)
        remaining = max(0, plan_limit - used)
        return remaining
    
    def can_show_buy_signal(self, user_id: str, plan_limit: Optional[int]) -> tuple[bool, Optional[int]]:
        """
        Check if buy signal can be shown to user
        
        Args:
            user_id: User identifier
            plan_limit: Plan limit (None if unlimited)
            
        Returns:
            Tuple of (can_show: bool, remaining: Optional[int])
        """
        if plan_limit is None:
            return True, None  # Unlimited
        
        remaining = self.get_remaining_signals(user_id, plan_limit)
        can_show = remaining is not None and remaining > 0
        
        return can_show, remaining
