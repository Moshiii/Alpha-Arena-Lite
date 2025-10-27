"""
Tests for add_order function in simple_portfolio
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_portfolio import SimplePortfolio


class TestAddOrder(unittest.TestCase):
    """Test add_order function with dummy price data"""
    
    def setUp(self):
        """Set up dummy price data for testing"""
        self.dummy_prices = {
            "BTC": 45000.0,
            "ETH": 3000.0,
            "SOL": 100.0,
            "SOLUSDT": 1.05,
            "INJ": 12.5
        }
    
    def test_add_order_with_leverage(self):
        """Test adding an order with leverage"""
        portfolio = SimplePortfolio()
        
        # Add BTC order with 10x leverage
        result = portfolio.add_order("BTC", quantity=0.5, price=self.dummy_prices["BTC"], leverage=10.0)
        self.assertTrue(result)
        
        self.assertIn("BTC", portfolio.positions)
        position = portfolio.positions["BTC"]
        
        # Check position attributes
        self.assertEqual(position.symbol, "BTC")
        self.assertEqual(position.quantity, 0.5)
        self.assertEqual(position.entry_price, self.dummy_prices["BTC"])
        self.assertEqual(position.current_price, self.dummy_prices["BTC"])
        self.assertEqual(position.leverage, 10.0)
        
        # Check liquidation price calculation: price * (1 - 1/leverage)
        # 45000 * (1 - 1/10) = 45000 * 0.9 = 40500
        self.assertAlmostEqual(position.liquidation_price, 40500.0, places=2)
    
    def test_add_order_without_leverage(self):
        """Test adding an order without leverage (leverage=1)"""
        portfolio = SimplePortfolio()
        
        # Add SOL order with 1x leverage
        result = portfolio.add_order("SOL", quantity=10.0, price=self.dummy_prices["SOL"], leverage=1.0)
        self.assertTrue(result)
        
        self.assertIn("SOL", portfolio.positions)
        position = portfolio.positions["SOL"]
        
        self.assertEqual(position.symbol, "SOL")
        self.assertEqual(position.quantity, 10.0)
        self.assertEqual(position.leverage, 1.0)
        self.assertIsNone(position.liquidation_price)
    
    def test_add_order_short_position(self):
        """Test adding a short order (negative quantity)"""
        portfolio = SimplePortfolio()
        
        # Add short ETH position
        result = portfolio.add_order("ETH", quantity=-5.0, price=self.dummy_prices["ETH"], leverage=5.0)
        self.assertTrue(result)
        
        self.assertIn("ETH", portfolio.positions)
        position = portfolio.positions["ETH"]
        
        self.assertEqual(position.quantity, -5.0)
        self.assertEqual(position.leverage, 5.0)
        
        # Check liquidation price for short: 3000 * (1 - 1/5) = 3000 * 0.8 = 2400
        self.assertAlmostEqual(position.liquidation_price, 2400.0, places=2)
    
    def test_add_order_multiple_symbols(self):
        """Test adding orders for multiple symbols"""
        portfolio = SimplePortfolio()
        
        # Add BTC order
        result1 = portfolio.add_order("BTC", quantity=0.5, price=self.dummy_prices["BTC"], leverage=10.0)
        self.assertTrue(result1)
        
        # Add ETH order
        result2 = portfolio.add_order("ETH", quantity=10.0, price=self.dummy_prices["ETH"], leverage=5.0)
        self.assertTrue(result2)
        
        # Add SOL order
        result3 = portfolio.add_order("SOL", quantity=100.0, price=self.dummy_prices["SOL"], leverage=1.0)
        self.assertTrue(result3)
        
        self.assertEqual(len(portfolio.get_all_positions()), 3)
        self.assertIn("BTC", portfolio.positions)
        self.assertIn("ETH", portfolio.positions)
        self.assertIn("SOL", portfolio.positions)
    
    def test_add_order_updates_price_and_calculates_pnl(self):
        """Test that add_order creates position that can calculate PnL"""
        portfolio = SimplePortfolio()
        
        # Add BTC order at 45000
        result = portfolio.add_order("BTC", quantity=0.5, price=self.dummy_prices["BTC"], leverage=10.0)
        self.assertTrue(result)
        
        # Update price to 46000 (profit)
        portfolio.update_price("BTC", 46000.0)
        
        position = portfolio.positions["BTC"]
        pnl = position.calculate_unrealized_pnl()
        
        # Expected: (46000 - 45000) * 0.5 * 10 = 5000
        self.assertEqual(pnl, 5000.0)
    
    def test_add_order_rejects_duplicate_symbol(self):
        """Test that add_order returns False when position already exists"""
        portfolio = SimplePortfolio()
        
        # Add initial BTC order - should succeed
        result1 = portfolio.add_order("BTC", quantity=0.5, price=self.dummy_prices["BTC"], leverage=10.0)
        self.assertTrue(result1)
        
        # Try to add another BTC order - should fail
        result2 = portfolio.add_order("BTC", quantity=1.0, price=50000.0, leverage=5.0)
        self.assertFalse(result2)
        
        # Should still have only one position
        self.assertEqual(len(portfolio.get_all_positions()), 1)
        
        # Position should still have original values, not updated
        position = portfolio.positions["BTC"]
        self.assertEqual(position.quantity, 0.5)
        self.assertEqual(position.entry_price, self.dummy_prices["BTC"])
        self.assertEqual(position.leverage, 10.0)
    
    def test_add_order_with_fractional_prices(self):
        """Test add_order with fractional prices (like stablecoins)"""
        portfolio = SimplePortfolio()
        
        # Add SOLUSDT order
        result = portfolio.add_order("SOLUSDT", quantity=1000.0, price=self.dummy_prices["SOLUSDT"], leverage=1.0)
        self.assertTrue(result)
        
        position = portfolio.positions["SOLUSDT"]
        self.assertEqual(position.entry_price, self.dummy_prices["SOLUSDT"])
        self.assertIsNone(position.liquidation_price)  # leverage = 1
    
    def test_add_order_total_pnl(self):
        """Test that portfolio calculates total PnL correctly after add_order"""
        portfolio = SimplePortfolio()
        
        # Add profitable BTC position
        result1 = portfolio.add_order("BTC", quantity=0.5, price=45000.0, leverage=10.0)
        self.assertTrue(result1)
        portfolio.update_price("BTC", 46000.0)  # $10k price increase
        
        # Add losing ETH position
        result2 = portfolio.add_order("ETH", quantity=-10.0, price=3000.0, leverage=5.0)
        self.assertTrue(result2)
        portfolio.update_price("ETH", 3100.0)  # $100 price increase (bad for short)
        
        # Total PnL: BTC profit + ETH loss
        total_pnl = portfolio.total_pnl()
        # BTC: (46000 - 45000) * 0.5 * 10 = 5000
        # ETH: (3100 - 3000) * 10 * 5 * (-1) = -5000
        self.assertEqual(total_pnl, 0.0)
    
    def test_add_order_entry_time(self):
        """Test that add_order sets entry_time correctly"""
        portfolio = SimplePortfolio()
        
        result = portfolio.add_order("BTC", quantity=0.5, price=self.dummy_prices["BTC"], leverage=10.0)
        self.assertTrue(result)
        
        position = portfolio.positions["BTC"]
        self.assertIsNotNone(position.entry_time)
        self.assertIsInstance(position.entry_time, str)
    
    def test_add_order_with_various_leverage_levels(self):
        """Test add_order with different leverage levels"""
        portfolio = SimplePortfolio()
        
        # 2x leverage
        result1 = portfolio.add_order("BTC", quantity=1.0, price=10000.0, leverage=2.0)
        self.assertTrue(result1)
        self.assertAlmostEqual(portfolio.positions["BTC"].liquidation_price, 5000.0, places=2)
        
        # 5x leverage
        result2 = portfolio.add_order("ETH", quantity=1.0, price=1000.0, leverage=5.0)
        self.assertTrue(result2)
        self.assertAlmostEqual(portfolio.positions["ETH"].liquidation_price, 800.0, places=2)
        
        # 20x leverage
        result3 = portfolio.add_order("SOL", quantity=1.0, price=100.0, leverage=20.0)
        self.assertTrue(result3)
        self.assertAlmostEqual(portfolio.positions["SOL"].liquidation_price, 95.0, places=2)
    
    def test_add_order_default_leverage(self):
        """Test add_order with default leverage (1.0)"""
        portfolio = SimplePortfolio()
        
        # Add order without specifying leverage
        result = portfolio.add_order("BTC", quantity=0.5, price=self.dummy_prices["BTC"])
        self.assertTrue(result)
        
        position = portfolio.positions["BTC"]
        self.assertEqual(position.leverage, 1.0)
        self.assertIsNone(position.liquidation_price)


if __name__ == "__main__":
    unittest.main()
