"""
Centralized Entitlements Configuration
Defines what each subscription tier can access
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


# Plan limits configuration
PLAN_LIMITS = {
    'free': {
        'buy_signals_per_month': float('inf'),  # Unlimited - users get buy signals as long as they're subscribed
        'history_days': 7,
        'alerts_per_game': 3,  # Number of threshold alerts per game subscription
        'can_export': False,
        'can_purchase_automate': False,
        'can_edit_thresholds': False,
        'can_compare_games': False,
        'max_game_subscriptions': 1,
    },
    'premium': {
        'buy_signals_per_month': float('inf'),  # Unlimited
        'history_days': 90,
        'alerts_per_game': float('inf'),  # Unlimited alerts per game
        'can_export': False,
        'can_purchase_automate': False,
        'can_edit_thresholds': True,
        'can_compare_games': True,
        'max_game_subscriptions': 999,  # Practical unlimited
    },
    'pro': {
        'buy_signals_per_month': float('inf'),  # Unlimited
        'history_days': None,  # Unlimited (None means no limit)
        'alerts_per_game': float('inf'),  # Unlimited alerts per game
        'can_export': True,
        'can_purchase_automate': True,
        'can_edit_thresholds': True,
        'can_compare_games': True,
        'max_game_subscriptions': 999,  # Practical unlimited
    },
    'admin': {
        # Admin = superuser for dev/testing. Effectively Pro+everything.
        'buy_signals_per_month': float('inf'),
        'history_days': None,
        'alerts_per_game': float('inf'),
        'can_export': True,
        'can_purchase_automate': True,
        'can_edit_thresholds': True,
        'can_compare_games': True,
        'max_game_subscriptions': 999,
    },
}


def get_plan_limits(plan: str) -> Dict:
    """
    Get limits for a subscription plan
    
    Args:
        plan: Subscription tier ('free', 'premium', 'pro')
        
    Returns:
        Dict with plan limits, defaults to 'free' if plan not found
    """
    return PLAN_LIMITS.get(plan.lower(), PLAN_LIMITS['free'])


def can_access_feature(plan: str, feature: str) -> bool:
    """
    Check if a plan can access a specific feature
    
    Args:
        plan: Subscription tier
        feature: Feature name (e.g., 'can_export', 'can_purchase_automate')
        
    Returns:
        True if plan can access feature, False otherwise
    """
    limits = get_plan_limits(plan)
    return limits.get(feature, False)


def get_history_start_date(plan: str) -> Optional[datetime]:
    """
    Get the earliest date allowed for history queries based on plan
    
    Args:
        plan: Subscription tier
        
    Returns:
        datetime for earliest allowed date, or None if unlimited
    """
    limits = get_plan_limits(plan)
    history_days = limits.get('history_days')
    
    if history_days is None:
        return None  # Unlimited
    
    if not isinstance(history_days, (int, float)) or history_days == float('inf'):
        return None  # Unlimited
    
    return datetime.now() - timedelta(days=int(history_days))


def get_buy_signals_limit(plan: str) -> Optional[int]:
    """
    Get buy signals per month limit for a plan
    
    Args:
        plan: Subscription tier
        
    Returns:
        Number of buy signals allowed per month, or None if unlimited
    """
    limits = get_plan_limits(plan)
    limit = limits.get('buy_signals_per_month')
    
    if limit == float('inf'):
        return None  # Unlimited
    
    return int(limit) if limit is not None else None


def get_alerts_per_game_limit(plan: str) -> Optional[int]:
    """
    Get alerts per game limit for a plan
    
    Args:
        plan: Subscription tier
        
    Returns:
        Number of alerts allowed per game, or None if unlimited
    """
    limits = get_plan_limits(plan)
    limit = limits.get('alerts_per_game')
    
    if limit == float('inf'):
        return None  # Unlimited
    
    return int(limit) if limit is not None else None


def format_history_window(plan: str) -> str:
    """
    Get human-readable history window description
    
    Args:
        plan: Subscription tier
        
    Returns:
        String like "Last 7 days", "Last 90 days", or "All history"
    """
    limits = get_plan_limits(plan)
    history_days = limits.get('history_days')
    
    if history_days is None:
        return "All history"
    
    if history_days == float('inf'):
        return "All history"
    
    return f"Last {int(history_days)} days"
