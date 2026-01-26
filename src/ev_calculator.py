"""
Expected Value (EV) Computation Module
Calculates expected value for lottery tickets
"""

import logging
from typing import Dict, Optional
import json
import os

logger = logging.getLogger(__name__)


class EVCalculator:
    """Calculates expected value for lottery games"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize EV calculator
        
        Args:
            config: Configuration dict with EV settings
        """
        self.config = config or {}
        ev_settings = self.config.get('ev_settings', {})
        
        self.include_secondary = ev_settings.get('include_secondary_prizes', True)
        self.tax_rate = ev_settings.get('tax_rate', 0.37)  # Federal tax rate
        self.lump_sum_factor = ev_settings.get('lump_sum_factor', 0.61)  # Lump sum vs annuity
    
    def calculate_ev(self, jackpot: float, odds: int, ticket_cost: float,
                    secondary_prize_ev: Optional[float] = None) -> Dict:
        """
        Calculate expected value for a lottery ticket
        
        Args:
            jackpot: Current jackpot amount
            odds: Odds of winning (e.g., 1 in 575757)
            ticket_cost: Cost of one ticket
            secondary_prize_ev: Expected value from secondary prizes (optional)
            
        Returns:
            Dict with EV calculations and metrics
        """
        # Adjust jackpot for taxes and lump sum
        after_tax_jackpot = jackpot * (1 - self.tax_rate) * self.lump_sum_factor
        
        # Primary prize EV
        primary_ev = after_tax_jackpot / odds
        
        # Secondary prize EV
        secondary_ev = secondary_prize_ev if (self.include_secondary and secondary_prize_ev) else 0
        
        # Total EV
        total_ev = primary_ev + secondary_ev
        
        # Net EV (after ticket cost)
        net_ev = total_ev - ticket_cost
        
        # EV percentage
        ev_percentage = (net_ev / ticket_cost) * 100 if ticket_cost > 0 else 0
        
        # Break-even analysis
        break_even_jackpot = (ticket_cost - secondary_ev) * odds / ((1 - self.tax_rate) * self.lump_sum_factor)
        
        result = {
            'jackpot': jackpot,
            'after_tax_jackpot': after_tax_jackpot,
            'odds': odds,
            'ticket_cost': ticket_cost,
            'primary_ev': primary_ev,
            'secondary_ev': secondary_ev,
            'total_ev': total_ev,
            'net_ev': net_ev,
            'ev_percentage': ev_percentage,
            'break_even_jackpot': break_even_jackpot,
            'is_positive_ev': net_ev > 0,
            'is_recommended': net_ev >= float(os.getenv('EV_THRESHOLD', '-0.20'))
        }
        
        logger.debug(f"EV calculated: Net EV = ${net_ev:.4f}")
        
        return result
    
    def format_ev_message(self, ev_result: Dict, game_name: str) -> str:
        """
        Format EV calculation results as a message
        
        Args:
            ev_result: Result dict from calculate_ev
            game_name: Name of the game
            
        Returns:
            Formatted message string
        """
        message = f"📊 *EV Analysis: {game_name}*\n\n"
        message += f"💰 Jackpot: ${ev_result['jackpot']:,.2f}\n"
        message += f"💵 After Tax (Lump Sum): ${ev_result['after_tax_jackpot']:,.2f}\n"
        message += f"🎫 Ticket Cost: ${ev_result['ticket_cost']:.2f}\n\n"
        
        message += f"📈 Expected Value:\n"
        message += f"  • Primary Prize EV: ${ev_result['primary_ev']:.4f}\n"
        if ev_result['secondary_ev'] > 0:
            message += f"  • Secondary Prizes EV: ${ev_result['secondary_ev']:.4f}\n"
        message += f"  • Total EV: ${ev_result['total_ev']:.4f}\n"
        message += f"  • Net EV: ${ev_result['net_ev']:.4f}\n"
        message += f"  • EV %: {ev_result['ev_percentage']:.2f}%\n\n"
        
        if ev_result['is_positive_ev']:
            message += "✅ *Positive EV - Consider buying!*\n"
        elif ev_result['is_recommended']:
            message += "⚠️ *Near break-even - Consider buying*\n"
        else:
            message += "❌ *Negative EV - Not recommended*\n"
        
        message += f"\n🎯 Break-even jackpot: ${ev_result['break_even_jackpot']:,.2f}"
        
        return message
    
    def should_buy(self, ev_result: Dict, ev_threshold: Optional[float] = None) -> bool:
        """
        Determine if ticket should be purchased based on EV
        
        Args:
            ev_result: Result dict from calculate_ev
            ev_threshold: Minimum EV threshold (or from env)
            
        Returns:
            True if purchase is recommended
        """
        if ev_threshold is None:
            ev_threshold = float(os.getenv('EV_THRESHOLD', '-0.20'))
        
        return ev_result['net_ev'] >= ev_threshold
