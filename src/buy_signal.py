"""
Buy Signal Logic Module
Determines when to buy tickets based on multiple criteria
"""

import logging
import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BuySignal:
    """Manages buy signal logic with multiple criteria"""
    
    def __init__(self, config: Dict):
        """
        Initialize buy signal system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.buy_signal_settings = config.get('buy_signal_settings', {})
    
    def calculate_buy_signal(
        self,
        game_id: str,
        current_jackpot: float,
        ev_result: Dict,
        rollover_count: int,
        time_to_draw_minutes: Optional[int] = None,
        game_config: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate buy signal based on multiple criteria
        
        Args:
            game_id: Game identifier
            current_jackpot: Current jackpot amount
            ev_result: EV calculation result
            rollover_count: Number of rollovers
            time_to_draw_minutes: Minutes until next draw
            game_config: Game-specific configuration
            
        Returns:
            Dict with buy signal info:
            {
                'has_signal': bool,
                'signal_type': str,  # 'basic', 'aggressive', 'event'
                'confidence': str,   # 'low', 'medium', 'high'
                'reasons': list,
                'message': str
            }
        """
        if game_config is None:
            game_config = self.config.get('lottery_games', {}).get(game_id, {})
        
        # Get criteria thresholds
        jackpot_threshold = self.buy_signal_settings.get('jackpot_threshold', {}).get(game_id, 0)
        rollover_threshold = self.buy_signal_settings.get('rollover_threshold', {}).get(game_id, 0)
        ev_threshold = self.buy_signal_settings.get('ev_threshold', -0.20)
        draw_window_hours = self.buy_signal_settings.get('draw_window_hours', 24)
        
        # Default thresholds if not specified
        if jackpot_threshold == 0:
            # Use min_threshold from game config as default
            jackpot_threshold = game_config.get('min_threshold', 0)
        
        reasons = []
        criteria_met = []
        
        # Check each criterion and add user-friendly reasons
        jackpot_met = current_jackpot >= jackpot_threshold if jackpot_threshold > 0 else True
        if jackpot_met and jackpot_threshold > 0:
            criteria_met.append('jackpot')
            # User-friendly jackpot reason
            if current_jackpot >= jackpot_threshold * 2:
                reasons.append(f"💰 Massive jackpot: ${current_jackpot:,.0f} (${jackpot_threshold:,.0f}+ threshold)")
            else:
                reasons.append(f"💰 Jackpot reached threshold: ${current_jackpot:,.0f}")
        
        rollover_met = rollover_count >= rollover_threshold if rollover_threshold > 0 else True
        if rollover_met and rollover_threshold > 0:
            criteria_met.append('rollover')
            # User-friendly rollover reason
            if rollover_count >= 20:
                reasons.append(f"🔄 Very high rollover count: {rollover_count} (no winner in {rollover_count} draws)")
            elif rollover_count >= 10:
                reasons.append(f"🔄 High rollover count: {rollover_count} draws without a winner")
            else:
                reasons.append(f"🔄 Rollover count: {rollover_count} (threshold: {rollover_threshold})")
        
        ev_met = ev_result.get('net_ev', -999) >= ev_threshold
        ev_percentage = ev_result.get('ev_percentage', -999)
        if ev_met:
            criteria_met.append('ev')
            # User-friendly EV reason
            if ev_result.get('is_positive_ev', False):
                reasons.append(f"✅ Positive expected value: ${ev_result.get('net_ev', 0):.2f} profit per ticket ({ev_percentage:.1f}%)")
            elif ev_percentage >= -5:
                reasons.append(f"📊 Near break-even EV: ${ev_result.get('net_ev', 0):.2f} ({ev_percentage:.1f}%)")
            else:
                reasons.append(f"📊 Expected value acceptable: ${ev_result.get('net_ev', 0):.2f} ({ev_percentage:.1f}%)")
        
        draw_met = True
        if time_to_draw_minutes is not None:
            draw_met = time_to_draw_minutes <= (draw_window_hours * 60)
            if draw_met:
                criteria_met.append('draw_window')
                hours = time_to_draw_minutes // 60
                minutes = time_to_draw_minutes % 60
                # User-friendly draw time reason
                if hours == 0:
                    reasons.append(f"⏰ Draw is very soon: {minutes} minutes away")
                elif hours < 6:
                    reasons.append(f"⏰ Draw is soon: {hours}h {minutes}m away")
                else:
                    reasons.append(f"⏰ Draw within {hours} hours")
        
        # Determine signal type and confidence
        has_signal = len(criteria_met) >= 2  # Need at least 2 criteria
        
        if not has_signal:
            return {
                'has_signal': False,
                'signal_type': None,
                'confidence': None,
                'reasons': [],
                'message': None
            }
        
        # Determine signal type and confidence based on EV first
        ev_percentage = ev_result.get('ev_percentage', -999)
        is_positive_ev = ev_result.get('is_positive_ev', False)
        is_recommended = ev_result.get('is_recommended', False)
        
        if is_positive_ev:
            signal_type = 'aggressive'
            confidence = 'high'
        elif is_recommended or ev_met:
            if len(criteria_met) >= 3:
                signal_type = 'aggressive'
                confidence = 'medium'
            else:
                signal_type = 'basic'
                confidence = 'medium'
        else:
            signal_type = 'basic'
            confidence = 'low'
        
        # Check for event-level signals (record jackpots, high rollovers)
        # But adjust confidence based on EV - don't give high confidence if EV is terrible
        is_event = current_jackpot >= jackpot_threshold * 2 or rollover_count >= 20
        if is_event:
            signal_type = 'event'
            # Add user-friendly event reason (replace generic "Record-range conditions")
            if current_jackpot >= jackpot_threshold * 2:
                reasons = [r for r in reasons if not r.startswith("💰")]  # Remove duplicate jackpot reason
                reasons.insert(0, f"🎯 RECORD JACKPOT: ${current_jackpot:,.0f} (2x+ threshold)")
            if rollover_count >= 20:
                reasons = [r for r in reasons if not r.startswith("🔄")]  # Remove duplicate rollover reason
                reasons.insert(0, f"🎯 RECORD ROLLOVERS: {rollover_count} draws without a winner")
            
            # Adjust confidence based on EV for event signals
            if is_positive_ev:
                confidence = 'high'  # High confidence only if EV is actually positive
            elif ev_percentage >= -10:  # EV better than -10%
                confidence = 'medium'  # Medium if EV is not terrible
            else:
                confidence = 'low'  # Low confidence if EV is terrible, even for events
        
        # Build message with clearer descriptions
        # High = Positive EV (actually profitable)
        # Medium = Acceptable EV or multiple criteria met
        # Low = Criteria met but EV is terrible (not recommended)
        confidence_labels = {
            'high': 'Strong Buy',
            'medium': 'Consider Buying',
            'low': 'Not Recommended'
        }
        
        signal_labels = {
            'basic': 'Standard Signal',
            'aggressive': 'Strong Signal',
            'event': 'Record Jackpot Alert'
        }
        
        confidence_emoji = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🟠'
        }
        
        signal_emoji = {
            'basic': '📊',
            'aggressive': '⚡',
            'event': '🎯'
        }
        
        # Create simpler, more actionable message
        confidence_label = confidence_labels.get(confidence, confidence.capitalize())
        emoji = confidence_emoji.get(confidence, '🟡')
        
        # For event signals, just show the confidence level (more user-friendly)
        if signal_type == 'event':
            message = f"{emoji} {confidence_label}"
        else:
            message = f"{emoji} {confidence_label}"
        
        return {
            'has_signal': True,
            'signal_type': signal_type,
            'confidence': confidence,
            'reasons': reasons,
            'message': message,
            'criteria_met': criteria_met,
            'ev_percentage': ev_result.get('ev_percentage', 0),
            'net_ev': ev_result.get('net_ev', 0)
        }
    
    def format_buy_signal_message(self, buy_signal: Dict, game_name: str, 
                                  current_jackpot: float, rollover_count: int,
                                  time_to_draw: str) -> str:
        """
        Format buy signal message for Telegram
        
        Args:
            buy_signal: Buy signal dict from calculate_buy_signal
            game_name: Name of the game
            current_jackpot: Current jackpot
            rollover_count: Rollover count
            time_to_draw: Time until draw (formatted string)
            
        Returns:
            Formatted message string
        """
        if not buy_signal.get('has_signal'):
            return None
        
        message = f"🎯 *BUY SIGNAL*\n"
        message += f"*{game_name}*\n\n"
        message += f"{buy_signal['message']}\n\n"
        message += f"💰 Jackpot: ${current_jackpot:,.0f}\n"
        message += f"📊 EV: ${buy_signal.get('net_ev', 0):.2f} ({buy_signal.get('ev_percentage', 0):.2f}%)\n"
        
        if rollover_count > 0:
            message += f"🔄 Rollovers: {rollover_count}\n"
        
        message += f"⏰ Draw: {time_to_draw}\n\n"
        message += f"*Reasons:*\n"
        for reason in buy_signal.get('reasons', []):
            message += f"• {reason}\n"
        
        return message
