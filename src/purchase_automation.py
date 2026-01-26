"""
Purchase Automation Module
Handles web automation for lottery purchase assistance
"""

import logging
import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import os
import json

logger = logging.getLogger(__name__)


class PurchaseAutomation:
    """Handles web automation for purchase assistance"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize purchase automation
        
        Args:
            config: Configuration dict with automation settings
        """
        self.config = config or {}
        automation_settings = self.config.get('automation_settings', {})
        
        self.headless = automation_settings.get('headless', False)
        self.timeout = automation_settings.get('timeout_seconds', 30) * 1000
        self.wait_for_confirmation = automation_settings.get('wait_for_user_confirmation', True)
        self.stop_at_checkout = automation_settings.get('stop_at_checkout', True)
        
        self.browser_type = os.getenv('BROWSER_TYPE', 'chromium').lower()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def _launch_browser(self):
        """Launch browser instance"""
        playwright = await async_playwright().start()
        
        browser_map = {
            'chromium': playwright.chromium,
            'chrome': playwright.chromium,
            'firefox': playwright.firefox,
            'webkit': playwright.webkit
        }
        
        browser_launcher = browser_map.get(self.browser_type, playwright.chromium)
        
        self.browser = await browser_launcher.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        logger.info(f"Browser launched: {self.browser_type}")
    
    async def _close_browser(self):
        """Close browser instance"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
    
    async def setup_purchase_flow(self, game_name: str, game_url: str) -> bool:
        """
        Set up purchase flow for a game - opens browser, navigates to game page,
        selects Quick Pick, and stops before checkout (legal compliance)
        
        Args:
            game_name: Name of the game
            game_url: URL to the game purchase page
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            if not self.page:
                await self._launch_browser()
            
            # Navigate to game page
            logger.info(f"🌐 Opening browser for {game_name}...")
            logger.info(f"📍 Navigating to {game_url}")
            await self.page.goto(game_url, wait_until='domcontentloaded', timeout=self.timeout)
            
            # Wait for page to fully load
            await asyncio.sleep(2)  # Give page time to render
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            logger.info("✅ Page loaded successfully")
            
            # Try to find and click "Quick Pick" or "Play Now" button
            # Illinois Lottery uses various selectors - try multiple approaches
            quick_pick_selectors = [
                # Common button text variations
                'button:has-text("Quick Pick")',
                'button:has-text("QUICK PICK")',
                'a:has-text("Quick Pick")',
                'a:has-text("QUICK PICK")',
                # Data attributes
                '[data-action="quick-pick"]',
                '[data-testid*="quick-pick"]',
                '[data-testid*="quickpick"]',
                # Class-based selectors
                '.quick-pick',
                '.quick-pick-button',
                '.btn-quick-pick',
                '[class*="quick-pick"]',
                '[class*="quickpick"]',
                # Aria labels
                'button[aria-label*="Quick Pick" i]',
                'button[aria-label*="quick pick" i]',
                # Play Now buttons (often leads to quick pick)
                'button:has-text("Play Now")',
                'a:has-text("Play Now")',
                'button:has-text("PLAY NOW")',
            ]
            
            quick_pick_clicked = False
            for selector in quick_pick_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                    if element:
                        # Scroll element into view
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await element.click()
                        quick_pick_clicked = True
                        logger.info("✅ Quick Pick selected")
                        await asyncio.sleep(2)  # Wait for next page/action
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' not found: {e}")
                    continue
            
            if not quick_pick_clicked:
                logger.warning("⚠️ Could not find Quick Pick button automatically")
                logger.info("💡 Browser is open - please manually select Quick Pick")
                logger.info("🛑 Automation will stop here (legal compliance)")
                return True  # Still return True - browser is open for manual action
            
            # Try to find and click "Add to Cart" or "Add" button
            add_to_cart_selectors = [
                'button:has-text("Add to Cart")',
                'button:has-text("Add")',
                'button:has-text("ADD")',
                'a:has-text("Add to Cart")',
                '[data-action="add-to-cart"]',
                '[data-testid*="add-to-cart"]',
                '.add-to-cart',
                '.btn-add-to-cart',
                '[class*="add-to-cart"]',
                'button[aria-label*="Add" i]',
            ]
            
            add_to_cart_clicked = False
            for selector in add_to_cart_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                    if element:
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await element.click()
                        add_to_cart_clicked = True
                        logger.info("✅ Added to cart")
                        await asyncio.sleep(2)
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' not found: {e}")
                    continue
            
            if not add_to_cart_clicked:
                logger.warning("⚠️ Could not find Add to Cart button automatically")
                logger.info("💡 Please manually add to cart if needed")
            
            # IMPORTANT: Stop before checkout (legal compliance)
            # We do NOT navigate to checkout automatically
            logger.info("")
            logger.info("=" * 60)
            logger.info("🛑 AUTOMATION STOPPED - LEGAL COMPLIANCE")
            logger.info("=" * 60)
            logger.info("✅ Browser is open with Quick Pick selected")
            logger.info("✅ Please review your selection manually")
            logger.info("✅ Complete checkout manually when ready")
            logger.info("=" * 60)
            logger.info("")
            
            # Keep browser open for user interaction
            if self.wait_for_confirmation:
                logger.info("⏳ Browser will remain open for manual completion...")
                logger.info("💡 Close the browser when done")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up purchase flow: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def open_game_page(self, game_url: str) -> bool:
        """
        Simply open the game page in browser
        
        Args:
            game_url: URL to open
            
        Returns:
            True if successful
        """
        try:
            if not self.page:
                await self._launch_browser()
            
            await self.page.goto(game_url, wait_until='networkidle', timeout=self.timeout)
            logger.info(f"Opened game page: {game_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening game page: {e}")
            return False
    
    async def cleanup(self):
        """Clean up browser resources"""
        await self._close_browser()
    
    def get_game_url(self, game_id: str, base_url: str = "https://www.illinoislottery.com") -> str:
        """
        Get purchase URL for a game
        
        Args:
            game_id: Game identifier
            base_url: Base URL for lottery site
            
        Returns:
            Game purchase URL
        """
        url_map = {
            'lucky_day_lotto_midday': f"{base_url}/games/lucky-day-lotto",
            'lucky_day_lotto_evening': f"{base_url}/games/lucky-day-lotto",
            'mega_millions': f"{base_url}/games/mega-millions"
            # Note: Powerball automation is disabled per requirements
        }
        
        return url_map.get(game_id, base_url)
