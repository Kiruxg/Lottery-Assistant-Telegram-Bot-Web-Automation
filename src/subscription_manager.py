"""
Subscription Manager Module
Handles user game subscriptions with tier-based limits
"""

import json
import os
import logging
from typing import Dict, List, Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manages user game subscriptions"""
    
    def __init__(self, subscriptions_file: str = "user_subscriptions.json"):
        """
        Initialize subscription manager
        
        Args:
            subscriptions_file: Path to subscriptions storage file
        """
        self.subscriptions_file = subscriptions_file
        self.subscriptions = self._load_subscriptions()
        
        # Subscription limits by tier
        self.tier_limits = {
            'free': 1,       # Free users can subscribe to 1 game
            'premium': 999,  # Premium users can subscribe to all games (practical limit)
            'pro': 999,      # Pro users can subscribe to all games
            'admin': 999,    # Admins effectively unlimited; treated like Pro for subscriptions
        }
    
    def _load_subscriptions(self) -> Dict:
        """Load subscriptions from file"""
        if os.path.exists(self.subscriptions_file):
            try:
                with open(self.subscriptions_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading subscriptions: {e}")
                return {}
        return {}
    
    def _save_subscriptions(self):
        """Save subscriptions to file"""
        try:
            with open(self.subscriptions_file, 'w') as f:
                json.dump(self.subscriptions, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving subscriptions: {e}")
    
    def get_user_tier(self, chat_id: str) -> str:
        """
        Get user subscription tier
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Subscription tier: 'free', 'premium', or 'pro'
        """
        user_data = self.subscriptions.get(chat_id, {})
        return user_data.get('tier', 'free')
    
    def set_user_tier(self, chat_id: str, tier: str):
        """
        Set user subscription tier
        
        Args:
            chat_id: Telegram chat ID
            tier: Subscription tier ('free', 'premium', 'pro')
        """
        if chat_id not in self.subscriptions:
            self.subscriptions[chat_id] = {'games': [], 'tier': tier}
        else:
            self.subscriptions[chat_id]['tier'] = tier
        self._save_subscriptions()
    
    def get_user_subscriptions(self, chat_id: str) -> List[str]:
        """
        Get list of games user is subscribed to
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            List of game IDs user is subscribed to
        """
        user_data = self.subscriptions.get(chat_id, {})
        return user_data.get('games', [])
    
    def subscribe_to_game(self, chat_id: str, game_id: str) -> tuple[bool, str]:
        """
        Subscribe user to a game
        
        Args:
            chat_id: Telegram chat ID
            game_id: Game ID to subscribe to
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        tier = self.get_user_tier(chat_id)
        current_subscriptions = self.get_user_subscriptions(chat_id)
        max_subscriptions = self.tier_limits.get(tier, 1)
        
        # Check if already subscribed
        if game_id in current_subscriptions:
            return False, f"You're already subscribed to this game."
        
        # Check subscription limit
        if len(current_subscriptions) >= max_subscriptions:
            if tier == 'free':
                return False, f"Free tier limit reached. You can only subscribe to {max_subscriptions} game at a time. Upgrade to Premium to subscribe to all games!"
            else:
                return False, f"Subscription limit reached ({max_subscriptions} games)."
        
        # Add subscription
        if chat_id not in self.subscriptions:
            self.subscriptions[chat_id] = {'games': [], 'tier': tier}
        
        self.subscriptions[chat_id]['games'].append(game_id)
        self._save_subscriptions()
        
        return True, f"✅ Subscribed to {game_id}!"
    
    def unsubscribe_from_game(self, chat_id: str, game_id: str) -> tuple[bool, str]:
        """
        Unsubscribe user from a game
        
        Args:
            chat_id: Telegram chat ID
            game_id: Game ID to unsubscribe from
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if chat_id not in self.subscriptions:
            return False, "You're not subscribed to any games."
        
        current_subscriptions = self.subscriptions[chat_id].get('games', [])
        
        if game_id not in current_subscriptions:
            return False, f"You're not subscribed to {game_id}."
        
        # Remove subscription
        self.subscriptions[chat_id]['games'].remove(game_id)
        self._save_subscriptions()
        
        return True, f"✅ Unsubscribed from {game_id}."
    
    def is_subscribed(self, chat_id: str, game_id: str) -> bool:
        """
        Check if user is subscribed to a game
        
        Args:
            chat_id: Telegram chat ID
            game_id: Game ID to check
            
        Returns:
            True if subscribed, False otherwise
        """
        subscriptions = self.get_user_subscriptions(chat_id)
        return game_id in subscriptions
    
    def get_all_subscribers(self, game_id: str) -> List[str]:
        """
        Get all chat IDs subscribed to a game
        
        Args:
            game_id: Game ID
            
        Returns:
            List of chat IDs subscribed to this game
        """
        subscribers = []
        for chat_id, user_data in self.subscriptions.items():
            games = user_data.get('games', [])
            if game_id in games:
                subscribers.append(chat_id)
        return subscribers
    
    def get_subscription_info(self, chat_id: str) -> Dict:
        """
        Get user's subscription information
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Dict with subscription info
        """
        tier = self.get_user_tier(chat_id)
        subscriptions = self.get_user_subscriptions(chat_id)
        max_subscriptions = self.tier_limits.get(tier, 1)
        
        return {
            'tier': tier,
            'subscribed_games': subscriptions,
            'subscription_count': len(subscriptions),
            'max_subscriptions': max_subscriptions,
            'remaining_slots': max_subscriptions - len(subscriptions)
        }
