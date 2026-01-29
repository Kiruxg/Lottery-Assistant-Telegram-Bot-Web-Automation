"""
Buy Signal Logic Module
Determines when to buy tickets based on multiple criteria
Enhanced with multi-factor analysis: EV Tiering, Rollover Momentum, Growth Velocity
"""

import logging
import os
from typing import Dict, Optional, Tuple, List
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
        
        # Historical rollover breakpoints (can be enhanced with actual data)
        # These represent typical rollover patterns for major lotteries
        self.rollover_breakpoints = {
            'mega_millions': {'75p': 8, '95p': 15},  # 75th percentile: 8, 95th: 15
            'powerball': {'75p': 7, '95p': 14},
            'lucky_day_lotto_midday': {'75p': 3, '95p': 6},
            'lucky_day_lotto_evening': {'75p': 3, '95p': 6}
        }
        
        # Composite scoring weights
        self.scoring_weights = {
            'ev': 0.6,
            'momentum': 0.3,
            'growth': 0.1
        }
    
    def get_ev_tier(self, ev_percentage: float) -> Dict[str, str]:
        """
        Classify EV into tiers
        
        Args:
            ev_percentage: Expected value percentage
            
        Returns:
            Dict with tier number, label, and description
        """
        if ev_percentage > -20:
            return {
                'tier': 1,
                'label': 'Value Opportunity',
                'description': 'Approaching reasonable EV'
            }
        elif ev_percentage >= -40:
            return {
                'tier': 2,
                'label': 'Watchlist',
                'description': 'Approaching reasonable EV'
            }
        else:
            return {
                'tier': 3,
                'label': 'Not Recommended',
                'description': 'Poor expected value'
            }
    
    def calculate_rollover_momentum(self, game_id: str, rollover_count: int) -> Dict[str, any]:
        """
        Calculate rollover momentum based on historical breakpoints
        
        Args:
            game_id: Game identifier
            rollover_count: Current rollover count
            
        Returns:
            Dict with momentum strength and score (0-1)
        """
        breakpoints = self.rollover_breakpoints.get(game_id, {'75p': 5, '95p': 10})
        p75 = breakpoints.get('75p', 5)
        p95 = breakpoints.get('95p', 10)
        
        if rollover_count >= p95:
            momentum = 'strong'
            score = 1.0
        elif rollover_count >= p75:
            momentum = 'moderate'
            score = 0.6
        else:
            momentum = 'weak'
            score = 0.2
        
        return {
            'momentum': momentum,
            'score': score,
            'rollover_count': rollover_count,
            'breakpoint_75p': p75,
            'breakpoint_95p': p95
        }
    
    def calculate_growth_velocity(self, current_jackpot: float, previous_jackpot: float) -> Dict[str, any]:
        """
        Calculate jackpot growth velocity
        
        Args:
            current_jackpot: Current jackpot amount
            previous_jackpot: Previous jackpot amount (from last draw)
            
        Returns:
            Dict with growth signal and normalized score (0-1)
        """
        if previous_jackpot <= 0:
            return {
                'growth': 'unknown',
                'score': 0.5,  # Neutral if no previous data
                'growth_amount': 0,
                'growth_percent': 0
            }
        
        growth_amount = current_jackpot - previous_jackpot
        growth_percent = (growth_amount / previous_jackpot * 100) if previous_jackpot > 0 else 0
        
        # Simple heuristic: if growth is positive and significant, it's strong
        # In production, compare against historical mean
        if growth_percent > 5:  # More than 5% growth
            growth = 'strong'
            score = 1.0
        elif growth_percent > 2:  # 2-5% growth
            growth = 'moderate'
            score = 0.6
        elif growth_percent > 0:
            growth = 'weak'
            score = 0.3
        else:
            growth = 'none'
            score = 0.0
        
        return {
            'growth': growth,
            'score': score,
            'growth_amount': growth_amount,
            'growth_percent': growth_percent
        }
    
    def calculate_composite_score(
        self,
        ev_percentage: float,
        momentum_score: float,
        growth_score: float
    ) -> Dict[str, any]:
        """
        Calculate composite BuyScore using weighted factors
        
        Args:
            ev_percentage: EV percentage
            momentum_score: Rollover momentum score (0-1)
            growth_score: Growth velocity score (0-1)
            
        Returns:
            Dict with composite score and signal classification
        """
        # Normalize EV to 0-1 scale
        # EV > -20% = 1.0, EV -20% to -40% = 0.5, EV < -40% = 0.0
        if ev_percentage > -20:
            ev_score = 1.0
        elif ev_percentage >= -40:
            ev_score = 0.5
        else:
            ev_score = 0.0
        
        # Calculate weighted composite score
        buy_score = (
            self.scoring_weights['ev'] * ev_score +
            self.scoring_weights['momentum'] * momentum_score +
            self.scoring_weights['growth'] * growth_score
        )
        
        # Classify signal based on score
        if buy_score >= 0.8:
            signal_class = 'Strong Opportunity'
        elif buy_score >= 0.6:
            signal_class = 'Moderate Opportunity'
        elif buy_score >= 0.4:
            signal_class = 'Watchlist'
        else:
            signal_class = 'Skip / Poor Value'
        
        return {
            'buy_score': buy_score,
            'signal_class': signal_class,
            'ev_score': ev_score,
            'momentum_score': momentum_score,
            'growth_score': growth_score
        }
    
    def calculate_buy_signal(
        self,
        game_id: str,
        current_jackpot: float,
        ev_result: Dict,
        rollover_count: int,
        time_to_draw_minutes: Optional[int] = None,
        game_config: Optional[Dict] = None,
        previous_jackpot: Optional[float] = None
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
        ev_suppression_threshold = self.buy_signal_settings.get('ev_suppression_threshold', -0.50)  # Suppress signals if EV worse than this
        ev_acceptable_threshold = self.buy_signal_settings.get('ev_acceptable_threshold', -0.30)  # Require EV better than this for regular signals
        
        # Default thresholds if not specified
        if jackpot_threshold == 0:
            # Use min_threshold from game config as default
            jackpot_threshold = game_config.get('min_threshold', 0)
        
        reasons = []
        criteria_met = []
        
        # Check each criterion and add user-friendly reasons
        jackpot_met = current_jackpot >= jackpot_threshold if (jackpot_threshold is not None and jackpot_threshold > 0) else True
        if jackpot_met and (jackpot_threshold is not None and jackpot_threshold > 0):
            criteria_met.append('jackpot')
            # User-friendly jackpot reason
            if jackpot_threshold is not None and current_jackpot >= jackpot_threshold * 2:
                reasons.append(f"💰 Massive jackpot: ${current_jackpot:,.0f} (${jackpot_threshold:,.0f}+ threshold)")
            else:
                reasons.append(f"💰 Jackpot reached threshold: ${current_jackpot:,.0f}")
        
        rollover_met = rollover_count >= rollover_threshold if (rollover_threshold is not None and rollover_threshold > 0) else True
        if rollover_met and (rollover_threshold is not None and rollover_threshold > 0):
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
        
        # NEW: Calculate EV Tier
        ev_tier_info = self.get_ev_tier(ev_percentage)
        
        if ev_met:
            criteria_met.append('ev')
            # User-friendly EV reason with tier
            if ev_result.get('is_positive_ev', False):
                reasons.append(f"✅ Tier {ev_tier_info['tier']} - {ev_tier_info['label']}: ${ev_result.get('net_ev', 0):.2f} profit per ticket ({ev_percentage:.1f}%)")
            elif ev_percentage >= -5:
                reasons.append(f"📊 Tier {ev_tier_info['tier']} - {ev_tier_info['label']}: ${ev_result.get('net_ev', 0):.2f} ({ev_percentage:.1f}%)")
            else:
                reasons.append(f"📊 Tier {ev_tier_info['tier']} - {ev_tier_info['label']}: ${ev_result.get('net_ev', 0):.2f} ({ev_percentage:.1f}%)")
        
        # NEW: Calculate Rollover Momentum
        momentum_info = self.calculate_rollover_momentum(game_id, rollover_count)
        if momentum_info['momentum'] == 'strong':
            reasons.append(f"📈 Rollover momentum: Strong ({rollover_count} rollovers, above 95th percentile)")
        elif momentum_info['momentum'] == 'moderate':
            reasons.append(f"📈 Rollover momentum: Moderate ({rollover_count} rollovers, above 75th percentile)")
        
        # NEW: Calculate Growth Velocity
        prev_jackpot = previous_jackpot if previous_jackpot else current_jackpot
        growth_info = self.calculate_growth_velocity(current_jackpot, prev_jackpot)
        if growth_info['growth'] == 'strong':
            reasons.append(f"🚀 Jackpot growing faster than usual: +{growth_info['growth_percent']:.1f}% (${growth_info['growth_amount']:,.0f})")
        elif growth_info['growth'] == 'moderate':
            reasons.append(f"📊 Jackpot growth: +{growth_info['growth_percent']:.1f}% (${growth_info['growth_amount']:,.0f})")
        
        # NEW: Calculate Composite Score
        composite_score = self.calculate_composite_score(
            ev_percentage,
            momentum_info['score'],
            growth_info['score']
        )
        
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
        # Count how many criteria are actually available (not just met)
        available_criteria_count = 0
        if jackpot_threshold is not None and jackpot_threshold > 0:
            available_criteria_count += 1
        if rollover_threshold is not None and rollover_threshold > 0:
            available_criteria_count += 1
        if ev_threshold is not None:
            available_criteria_count += 1
        if time_to_draw_minutes is not None:
            available_criteria_count += 1
        
        # Check for exceptional events first (these override EV requirements)
        is_exceptional_event = (
            (jackpot_threshold is not None and current_jackpot >= jackpot_threshold * 2) or  # Record jackpot (2x+ threshold)
            rollover_count >= 20  # Very high rollovers
        )
        
        # EV-based filtering: if EV is terrible, suppress signal unless it's exceptional
        ev_percentage = ev_result.get('ev_percentage', -999)
        is_positive_ev = ev_result.get('is_positive_ev', False)
        # Convert config thresholds (decimals) to percentages for comparison
        ev_suppression_threshold_pct = ev_suppression_threshold * 100  # e.g., -0.50 -> -50%
        ev_acceptable_threshold_pct = ev_acceptable_threshold * 100  # e.g., -0.30 -> -30%
        ev_is_terrible = ev_percentage < ev_suppression_threshold_pct  # Very negative EV
        ev_is_acceptable = ev_percentage >= ev_acceptable_threshold_pct  # Reasonable EV
        
        # Adaptive threshold: require at least 2 criteria, or 1 if only 2-3 criteria available
        # This helps games like LDL that don't have rollover thresholds
        required_criteria = 2 if available_criteria_count >= 4 else 1
        has_signal = len(criteria_met) >= required_criteria
        
        # Special case: if EV is positive, always show signal (regardless of other criteria)
        if is_positive_ev:
            has_signal = True
            if 'ev' not in criteria_met:
                criteria_met.append('ev')
                reasons.append(f"✅ Positive expected value: ${ev_result.get('net_ev', 0):.2f} profit per ticket ({ev_percentage:.1f}%)")
        
        # Suppress signal if EV is terrible, UNLESS it's an exceptional event
        if ev_is_terrible and not is_exceptional_event:
            has_signal = False
        
        # For regular signals (not exceptional), require EV to be at least acceptable
        # This prevents "Not Recommended" signals for mediocre situations
        if has_signal and not is_exceptional_event and not ev_is_acceptable and not is_positive_ev:
            # Only show if multiple strong criteria are met (3+)
            if len(criteria_met) < 3:
                has_signal = False
        
        if not has_signal:
            return {
                'has_signal': False,
                'signal_type': None,
                'confidence': None,
                'reasons': [],
                'message': None
            }
        
        # Determine signal type and confidence using composite score
        is_recommended = ev_result.get('is_recommended', False)
        buy_score = composite_score['buy_score']
        signal_class = composite_score['signal_class']
        
        # Map composite score to signal type and confidence
        if buy_score >= 0.8:
            signal_type = 'aggressive'
            confidence = 'high'
        elif buy_score >= 0.6:
            signal_type = 'aggressive'
            confidence = 'medium'
        elif buy_score >= 0.4:
            signal_type = 'basic'
            confidence = 'medium'
        else:
            signal_type = 'basic'
            confidence = 'low'
        
        # Override: Positive EV always gets high confidence
        if is_positive_ev:
            signal_type = 'aggressive'
            confidence = 'high'
        
        # Check for event-level signals (record jackpots, high rollovers)
        # But adjust confidence based on EV - don't give high confidence if EV is terrible
        # (is_exceptional_event already set above)
        if is_exceptional_event:
            signal_type = 'event'
            # Add user-friendly event reason (replace generic "Record-range conditions")
            if jackpot_threshold is not None and current_jackpot >= jackpot_threshold * 2:
                reasons = [r for r in reasons if not r.startswith("💰")]  # Remove duplicate jackpot reason
                reasons.insert(0, f"🎯 RECORD JACKPOT: ${current_jackpot:,.0f} (2x+ threshold)")
            if rollover_count >= 20:
                reasons = [r for r in reasons if not r.startswith("🔄")]  # Remove duplicate rollover reason
                reasons.insert(0, f"🎯 RECORD ROLLOVERS: {rollover_count} draws without a winner")
            
            # Adjust confidence based on EV for event signals
            if is_positive_ev:
                confidence = 'high'  # High confidence only if EV is actually positive
            elif ev_percentage >= -20:  # EV better than -20% (at least near break-even)
                confidence = 'medium'  # Medium if EV is reasonable
            else:
                # For exceptional events with terrible EV, still show but mark as "Not Recommended"
                # This is useful info (record jackpot/rollovers) even if EV is bad
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
        
        # Create enhanced message with composite score info
        confidence_label = confidence_labels.get(confidence, confidence.capitalize())
        emoji = confidence_emoji.get(confidence, '🟡')
        
        # Build message with tier and composite score
        if signal_type == 'event':
            message = f"{emoji} {confidence_label} - {signal_class}"
        else:
            # Include EV tier in message
            message = f"{emoji} {confidence_label} - Tier {ev_tier_info['tier']}: {signal_class}"
        
        return {
            'has_signal': True,
            'signal_type': signal_type,
            'confidence': confidence,
            'reasons': reasons,
            'message': message,
            'criteria_met': criteria_met,
            'ev_percentage': ev_result.get('ev_percentage', 0),
            'net_ev': ev_result.get('net_ev', 0),
            # NEW: Enhanced signal data
            'ev_tier': ev_tier_info,
            'rollover_momentum': momentum_info,
            'growth_velocity': growth_info,
            'composite_score': composite_score,
            'buy_score': buy_score,
            'signal_class': signal_class
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
        
        message += f"⏰ Draw: {time_to_draw}"
        
        return message
