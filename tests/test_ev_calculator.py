"""
Comprehensive tests for EV Calculator
Tests expected value calculations rigorously
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ev_calculator import EVCalculator


class TestEVCalculator(unittest.TestCase):
    """Test EV calculation logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'ev_settings': {
                'include_secondary_prizes': True,
                'tax_rate': 0.37,
                'lump_sum_factor': 0.61
            }
        }
        self.calculator = EVCalculator(self.config)
    
    def test_basic_ev_calculation(self):
        """Test basic EV calculation"""
        # Test case: $1M jackpot, 1:575757 odds, $1 ticket
        result = self.calculator.calculate_ev(
            jackpot=1_000_000,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0.10
        )
        
        # After tax and lump sum: 1M * 0.63 * 0.61 = 384,300
        expected_after_tax = 1_000_000 * 0.63 * 0.61
        self.assertAlmostEqual(result['after_tax_jackpot'], expected_after_tax, places=2)
        
        # Primary EV = 384,300 / 575,757 ≈ 0.6677
        expected_primary_ev = expected_after_tax / 575757
        self.assertAlmostEqual(result['primary_ev'], expected_primary_ev, places=4)
        
        # Total EV = primary + secondary = 0.6677 + 0.10 = 0.7677
        expected_total_ev = expected_primary_ev + 0.10
        self.assertAlmostEqual(result['total_ev'], expected_total_ev, places=4)
        
        # Net EV = 0.7677 - 1.0 = -0.2323
        expected_net_ev = expected_total_ev - 1.0
        self.assertAlmostEqual(result['net_ev'], expected_net_ev, places=4)
        
        # Should be negative EV
        self.assertFalse(result['is_positive_ev'])
    
    def test_positive_ev_scenario(self):
        """Test scenario where EV becomes positive"""
        # Very high jackpot: $500M, 1:292M odds (Powerball-like), $2 ticket
        result = self.calculator.calculate_ev(
            jackpot=500_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # After tax and lump sum: 500M * 0.63 * 0.61 = 192,150,000
        expected_after_tax = 500_000_000 * 0.63 * 0.61
        self.assertAlmostEqual(result['after_tax_jackpot'], expected_after_tax, places=2)
        
        # Primary EV = 192,150,000 / 292,201,338 ≈ 0.6579
        expected_primary_ev = expected_after_tax / 292_201_338
        self.assertAlmostEqual(result['primary_ev'], expected_primary_ev, places=4)
        
        # Total EV = 0.6579 + 0.15 = 0.8079
        # Net EV = 0.8079 - 2.0 = -1.1921 (still negative!)
        # Need even higher jackpot for positive EV
        
        # Test with $1B jackpot
        result_billion = self.calculator.calculate_ev(
            jackpot=1_000_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # After tax: 1B * 0.63 * 0.61 = 384,300,000
        # Primary EV = 384,300,000 / 292,201,338 ≈ 1.3158
        # Total EV = 1.3158 + 0.15 = 1.4658
        # Net EV = 1.4658 - 2.0 = -0.5342 (still negative!)
        
        # Test with $2B jackpot (realistic mega jackpot)
        result_2b = self.calculator.calculate_ev(
            jackpot=2_000_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # After tax: 2B * 0.63 * 0.61 = 768,600,000
        # Primary EV = 768,600,000 / 292,201,338 ≈ 2.6316
        # Total EV = 2.6316 + 0.15 = 2.7816
        # Net EV = 2.7816 - 2.0 = 0.7816 (POSITIVE!)
        self.assertTrue(result_2b['is_positive_ev'])
        self.assertGreater(result_2b['net_ev'], 0)
    
    def test_break_even_calculation(self):
        """Test break-even jackpot calculation"""
        # For $2 ticket, 292M odds, $0.15 secondary EV
        # Break-even: (2.0 - 0.15) * 292,201,338 / (0.63 * 0.61)
        # = 1.85 * 292,201,338 / 0.3843
        # ≈ 1,410,000,000
        
        result = self.calculator.calculate_ev(
            jackpot=1_410_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # Net EV should be close to 0
        self.assertAlmostEqual(result['net_ev'], 0, places=2)
        
        # Break-even jackpot should match
        self.assertAlmostEqual(result['break_even_jackpot'], 1_410_000_000, delta=10_000_000)
    
    def test_should_buy_logic(self):
        """Test should_buy decision logic"""
        # Default threshold is -0.20
        
        # Negative EV but above threshold
        result1 = self.calculator.calculate_ev(
            jackpot=1_000_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        # Net EV ≈ -0.53, which is < -0.20, so should NOT buy
        self.assertFalse(self.calculator.should_buy(result1, -0.20))
        
        # Negative EV but close to threshold
        result2 = self.calculator.calculate_ev(
            jackpot=1_200_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        # Net EV might be around -0.20, should buy
        should_buy = self.calculator.should_buy(result2, -0.20)
        # This depends on exact calculation, but should be True if net_ev >= -0.20
        if result2['net_ev'] >= -0.20:
            self.assertTrue(should_buy)
        else:
            self.assertFalse(should_buy)
        
        # Positive EV - definitely should buy
        result3 = self.calculator.calculate_ev(
            jackpot=2_000_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        self.assertTrue(self.calculator.should_buy(result3, -0.20))
    
    def test_lucky_day_lotto_scenarios(self):
        """Test realistic Lucky Day Lotto scenarios"""
        # LDL: $350k jackpot, 1:575757 odds, $1 ticket
        result = self.calculator.calculate_ev(
            jackpot=350_000,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0.10
        )
        
        # After tax: 350k * 0.63 * 0.61 = 134,505
        expected_after_tax = 350_000 * 0.63 * 0.61
        self.assertAlmostEqual(result['after_tax_jackpot'], expected_after_tax, places=2)
        
        # Primary EV = 134,505 / 575,757 ≈ 0.2337
        # Total EV = 0.2337 + 0.10 = 0.3337
        # Net EV = 0.3337 - 1.0 = -0.6663
        
        self.assertAlmostEqual(result['net_ev'], -0.6663, places=2)
        self.assertFalse(result['is_positive_ev'])
        
        # Test at $500k threshold
        result_500k = self.calculator.calculate_ev(
            jackpot=500_000,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0.10
        )
        
        # Net EV should be better but still negative
        self.assertGreater(result_500k['net_ev'], result['net_ev'])
        self.assertFalse(result_500k['is_positive_ev'])
    
    def test_powerball_scenarios(self):
        """Test realistic Powerball scenarios"""
        # Powerball: $30M jackpot, 1:292M odds, $2 ticket
        result = self.calculator.calculate_ev(
            jackpot=30_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # After tax: 30M * 0.63 * 0.61 = 11,529,000
        expected_after_tax = 30_000_000 * 0.63 * 0.61
        self.assertAlmostEqual(result['after_tax_jackpot'], expected_after_tax, places=2)
        
        # Primary EV = 11,529,000 / 292,201,338 ≈ 0.0395
        # Total EV = 0.0395 + 0.15 = 0.1895
        # Net EV = 0.1895 - 2.0 = -1.8105
        
        self.assertAlmostEqual(result['net_ev'], -1.8105, places=2)
        self.assertFalse(result['is_positive_ev'])
        
        # Test at $100M threshold
        result_100m = self.calculator.calculate_ev(
            jackpot=100_000_000,
            odds=292_201_338,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # Net EV should be better
        self.assertGreater(result_100m['net_ev'], result['net_ev'])
    
    def test_mega_millions_scenarios(self):
        """Test realistic Mega Millions scenarios"""
        # Mega Millions: $285M jackpot, 1:302M odds, $2 ticket
        result = self.calculator.calculate_ev(
            jackpot=285_000_000,
            odds=302_575_350,
            ticket_cost=2.0,
            secondary_prize_ev=0.15
        )
        
        # After tax: 285M * 0.63 * 0.61 = 109,525,500
        expected_after_tax = 285_000_000 * 0.63 * 0.61
        self.assertAlmostEqual(result['after_tax_jackpot'], expected_after_tax, places=2)
        
        # Primary EV = 109,525,500 / 302,575,350 ≈ 0.3618
        # Total EV = 0.3618 + 0.15 = 0.5118
        # Net EV = 0.5118 - 2.0 = -1.4882
        
        self.assertAlmostEqual(result['net_ev'], -1.4882, places=2)
        self.assertFalse(result['is_positive_ev'])
    
    def test_edge_cases(self):
        """Test edge cases"""
        # Zero jackpot
        result = self.calculator.calculate_ev(
            jackpot=0,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0.10
        )
        self.assertEqual(result['after_tax_jackpot'], 0)
        self.assertEqual(result['primary_ev'], 0)
        self.assertEqual(result['net_ev'], -0.90)  # Only secondary EV - ticket cost
        
        # Very small jackpot
        result = self.calculator.calculate_ev(
            jackpot=1000,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0.10
        )
        self.assertLess(result['net_ev'], 0)
        
        # No secondary prizes
        result = self.calculator.calculate_ev(
            jackpot=1_000_000,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0
        )
        self.assertEqual(result['secondary_ev'], 0)
    
    def test_ev_percentage(self):
        """Test EV percentage calculation"""
        result = self.calculator.calculate_ev(
            jackpot=1_000_000,
            odds=575757,
            ticket_cost=1.0,
            secondary_prize_ev=0.10
        )
        
        # EV % = (net_ev / ticket_cost) * 100
        expected_percentage = (result['net_ev'] / 1.0) * 100
        self.assertAlmostEqual(result['ev_percentage'], expected_percentage, places=2)


if __name__ == '__main__':
    unittest.main()
