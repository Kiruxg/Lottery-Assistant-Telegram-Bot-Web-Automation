"""
Jackpot Monitoring Module
Fetches jackpot values from Illinois Lottery website
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from datetime import datetime
import re
import json
import os

logger = logging.getLogger(__name__)


class JackpotMonitor:
    """Monitors Illinois Lottery jackpots"""
    
    BASE_URL = "https://www.illinoislottery.com"
    
    def __init__(self, base_url: Optional[str] = None, use_playwright: bool = False):
        """
        Initialize jackpot monitor
        
        Args:
            base_url: Base URL for Illinois Lottery (defaults to official site)
            use_playwright: Use Playwright for scraping (more robust, handles JS)
        """
        self.base_url = base_url or os.getenv('IL_LOTTERY_URL', self.BASE_URL)
        self.use_playwright = use_playwright
        self.session = requests.Session()
        
        # Enhanced headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Initialize Playwright if requested
        if self.use_playwright:
            try:
                from playwright.sync_api import sync_playwright
                # Just test import, don't store
            except ImportError:
                logger.warning("Playwright not available, falling back to requests")
                self.use_playwright = False
    
    def _parse_currency(self, text: str) -> Optional[float]:
        """
        Parse currency string to float
        
        Args:
            text: Currency string (e.g., "$1,234,567.89" or "$500K")
            
        Returns:
            Float value or None if parsing fails
        """
        if not text:
            return None
        
        # Remove currency symbols and whitespace
        text = text.replace('$', '').replace(',', '').strip()
        
        # Handle K, M, B suffixes
        multiplier = 1
        if text.upper().endswith('K'):
            multiplier = 1000
            text = text[:-1]
        elif text.upper().endswith('M'):
            multiplier = 1000000
            text = text[:-1]
        elif text.upper().endswith('B'):
            multiplier = 1000000000
            text = text[:-1]
        
        try:
            return float(text) * multiplier
        except ValueError:
            logger.warning(f"Failed to parse currency: {text}")
            return None
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage (synchronous method)
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetch fails
        """
        try:
            # Try with requests first
            response = self.session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            logger.warning(f"Requests failed for {url}: {e}")
            return None
    
    async def _fetch_page_async(self, url: str, skip_playwright: bool = False) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage (async version for use in async contexts)
        Tries requests first, falls back to Playwright if needed
        
        Args:
            url: URL to fetch
            skip_playwright: Skip Playwright fallback (faster, but may fail)
            
        Returns:
            BeautifulSoup object or None if fetch fails
        """
        # Try requests first (using asyncio to run in thread pool)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(url, timeout=10, allow_redirects=True)  # Reduced timeout
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            if skip_playwright:
                logger.debug(f"Requests failed for {url}: {e} (skipping Playwright)")
                return None
            logger.debug(f"Requests failed for {url}: {e}. Trying Playwright fallback...")
            # Fallback to Playwright async with shorter timeout
            return await self._fetch_with_playwright_async(url)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def _fetch_with_playwright_async(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch page using Playwright async API (handles JavaScript and anti-bot protection)
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetch fails
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                # Use 'domcontentloaded' instead of 'networkidle' for faster loading
                # Reduced timeout from 30s to 15s
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                content = await page.content()
                await browser.close()
                return BeautifulSoup(content, 'lxml')
            
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright && python -m playwright install")
            return None
        except Exception as e:
            logger.debug(f"Playwright fetch failed for {url}: {e}")
            return None
    
    async def get_lucky_day_lotto_jackpot_async(self, draw_type: str = "evening", shared_soup: Optional[BeautifulSoup] = None) -> Optional[Dict]:
        """
        Get Lucky Day Lotto jackpot (async version)
        
        Args:
            draw_type: "midday" or "evening"
            shared_soup: Pre-fetched soup to use (for performance)
            
        Returns:
            Dict with jackpot info or None
        """
        try:
            # If we have a shared soup (e.g., from homepage), use it
            if shared_soup:
                soup = shared_soup
                url_used = f"{self.base_url}/"
            else:
                # Try direct play page first (usually faster)
                urls_to_try = [
                    f"{self.base_url}/dbg/play/luckydaylotto",  # Direct play page - fastest
                    f"{self.base_url}/",  # Homepage fallback
                ]
                
                soup = None
                url_used = None
                
                for url in urls_to_try:
                    # Skip Playwright for homepage (too slow)
                    skip_playwright = url == f"{self.base_url}/"
                    soup = await self._fetch_page_async(url, skip_playwright=skip_playwright)
                    if soup and soup.title and "not found" not in soup.title.string.lower():
                        url_used = url
                        logger.debug(f"Successfully fetched from: {url}")
                        break
            
            if not soup:
                logger.warning("Could not fetch page for Lucky Day Lotto")
                return None
            
            if not soup:
                return None
            
            jackpot_value = None
            
            # Strategy 1: Look for game card with lucky day lotto
            # Based on HTML structure: mega-menu_game-card--luckydaylotto
            lucky_day_card = soup.find('div', class_=re.compile(r'mega-menu_game-card--luckydaylotto', re.I))
            if lucky_day_card:
                logger.debug("Found Lucky Day Lotto card")
                # Look for jackpot container within the card
                jackpot_container = lucky_day_card.find('div', class_=re.compile(r'jackpot|mega-menu.*jackpot', re.I))
                if jackpot_container:
                    jackpot_text = jackpot_container.get_text()
                    value = self._parse_currency(jackpot_text)
                    # STRICT range for LDL: $10K-$500K (exclude Powerball/Mega Millions)
                    if value and 10000 <= value <= 500000:
                        jackpot_value = value
                        logger.debug(f"Found LDL jackpot in game card container: {value}")
                    else:
                        logger.debug(f"Found value {value} but outside LDL range (likely Powerball/Mega Millions)")
                
                # If no jackpot container, parse entire card text but ONLY values in LDL range
                if not jackpot_value:
                    card_text = lucky_day_card.get_text()
                    # Look for currency values ONLY in Lucky Day Lotto range
                    all_values = re.findall(r'\$[\d,KM]+', card_text)
                    for val_str in all_values:
                        value = self._parse_currency(val_str)
                        # STRICT range for LDL: $10K-$500K
                        if value and 10000 <= value <= 500000:
                            if jackpot_value is None or value > jackpot_value:
                                jackpot_value = value
                                logger.debug(f"Found LDL jackpot in game card text: {value}")
            
            # Strategy 2: Look for common jackpot class names and IDs
            if not jackpot_value:
                jackpot_selectors = [
                    {'class': re.compile(r'jackpot', re.I)},
                    {'class': re.compile(r'prize', re.I)},
                    {'class': re.compile(r'amount', re.I)},
                    {'class': re.compile(r'game.*card', re.I)},
                    {'id': re.compile(r'jackpot', re.I)},
                    {'data-jackpot': True},
                    {'data-amount': True},
                ]
                
                for selector in jackpot_selectors:
                    elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3', 'a'], selector)
                    for elem in elements:
                        text = elem.get_text()
                        value = self._parse_currency(text)
                        # STRICT range for LDL: $10K-$500K
                        if value and 10000 <= value <= 500000:
                            if jackpot_value is None or value > jackpot_value:
                                jackpot_value = value
                                logger.debug(f"Found LDL jackpot via selector: {value}")
            
            # Strategy 3: Look for all currency strings but ONLY in LDL range
            # STRICTLY exclude Powerball/Mega Millions values
            if not jackpot_value:
                all_currency_strings = soup.find_all(string=re.compile(r'\$[\d,KM]+'))
                for currency_str in all_currency_strings:
                    value = self._parse_currency(currency_str)
                    # Lucky Day Lotto jackpots are typically $50K-$500K range
                    # STRICTLY exclude Powerball/Mega Millions values
                    if value and 10000 <= value <= 500000:  # Strict LDL range
                        if jackpot_value is None or value > jackpot_value:
                            jackpot_value = value
                            logger.debug(f"Found LDL jackpot via currency search: {value}")
                    elif value and value > 500000:
                        logger.debug(f"Skipping large value {value} (likely Powerball/Mega Millions)")
            
            # Strategy 4: Look for specific text patterns
            if not jackpot_value:
                # Look for "Next Jackpot" or similar text
                next_jackpot = soup.find(string=re.compile(r'next.*jackpot|jackpot.*amount', re.I))
                if next_jackpot:
                    parent = next_jackpot.find_parent()
                    if parent:
                        text = parent.get_text()
                        value = self._parse_currency(text)
                        if value and value > 1000:
                            jackpot_value = value
                            logger.debug(f"Found jackpot via text pattern: {value}")
            
            # Strategy 5: Look in meta tags or data attributes
            if not jackpot_value:
                meta_jackpot = soup.find('meta', {'property': re.compile(r'jackpot|prize', re.I)})
                if meta_jackpot and meta_jackpot.get('content'):
                    value = self._parse_currency(meta_jackpot.get('content'))
                    if value and value > 1000:
                        jackpot_value = value
                        logger.debug(f"Found jackpot via meta tag: {value}")
            
            if jackpot_value:
                return {
                    'game': f"Lucky Day Lotto {draw_type.title()}",
                    'jackpot': jackpot_value,
                    'draw_type': draw_type,
                    'timestamp': datetime.now().isoformat(),
                    'source': url_used or urls_to_try[0]
                }
            
            # Debug: Save HTML snippet if we can't find jackpot
            logger.warning(f"Could not find jackpot for Lucky Day Lotto {draw_type}")
            logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
            
            # Try to find any large numbers on the page for debugging
            all_numbers = soup.find_all(string=re.compile(r'\$[\d,]+'))
            if all_numbers:
                logger.debug(f"Found {len(all_numbers)} currency strings on page")
                for num in all_numbers[:5]:  # Show first 5
                    logger.debug(f"  Found: {num.strip()}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Lucky Day Lotto jackpot: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def get_powerball_jackpot(self) -> Optional[Dict]:
        """Get Powerball jackpot"""
        try:
            url = f"{self.base_url}/games/powerball"
            soup = self._fetch_page(url)
            
            if not soup:
                return None
            
            # Similar parsing logic as Lucky Day Lotto
            jackpot_value = None
            jackpot_elements = soup.find_all(string=re.compile(r'\$[\d,]+'))
            
            for element in jackpot_elements:
                value = self._parse_currency(element)
                if value and value > 1000000:  # Powerball jackpots are typically large
                    if jackpot_value is None or value > jackpot_value:
                        jackpot_value = value
            
            if jackpot_value:
                return {
                    'game': 'Powerball',
                    'jackpot': jackpot_value,
                    'timestamp': datetime.now().isoformat(),
                    'source': url
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Powerball jackpot: {e}")
            return None
    
    def get_mega_millions_jackpot(self) -> Optional[Dict]:
        """Get Mega Millions jackpot"""
        try:
            url = f"{self.base_url}/games/mega-millions"
            soup = self._fetch_page(url)
            
            if not soup:
                return None
            
            jackpot_value = None
            jackpot_elements = soup.find_all(string=re.compile(r'\$[\d,]+'))
            
            for element in jackpot_elements:
                value = self._parse_currency(element)
                if value and value > 1000000:  # Mega Millions jackpots are typically large
                    if jackpot_value is None or value > jackpot_value:
                        jackpot_value = value
            
            if jackpot_value:
                return {
                    'game': 'Mega Millions',
                    'jackpot': jackpot_value,
                    'timestamp': datetime.now().isoformat(),
                    'source': url
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Mega Millions jackpot: {e}")
            return None
    
    async def get_all_jackpots_async(self, games: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Get jackpots for multiple games (async version)
        Optimized to fetch in parallel and share homepage data
        
        Args:
            games: List of game identifiers
            
        Returns:
            Dict mapping game names to jackpot data
        """
        import asyncio
        
        # Try to fetch homepage once (has all game cards)
        # This is shared across all games for better performance
        homepage_soup = None
        try:
            homepage_soup = await self._fetch_page_async(f"{self.base_url}/", skip_playwright=True)
            if homepage_soup and homepage_soup.title and "not found" not in homepage_soup.title.string.lower():
                logger.debug("Successfully fetched homepage for shared parsing")
        except Exception as e:
            logger.debug(f"Could not fetch homepage: {e}")
        
        # Create tasks for all games to run in parallel
        tasks = []
        game_map = {}
        
        for game in games:
            if game == "lucky_day_lotto_midday":
                task = self.get_lucky_day_lotto_jackpot_async("midday", shared_soup=homepage_soup)
                tasks.append(task)
                game_map[task] = game
            elif game == "lucky_day_lotto_evening":
                task = self.get_lucky_day_lotto_jackpot_async("evening", shared_soup=homepage_soup)
                tasks.append(task)
                game_map[task] = game
            elif game == "powerball":
                task = self.get_powerball_jackpot_async(shared_soup=homepage_soup)
                tasks.append(task)
                game_map[task] = game
            elif game == "mega_millions":
                task = self.get_mega_millions_jackpot_async(shared_soup=homepage_soup)
                tasks.append(task)
                game_map[task] = game
            else:
                logger.warning(f"Unknown game: {game}")
        
        # Run all tasks in parallel
        results = {}
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for task, result in zip(tasks, completed):
                game_id = game_map[task]
                if isinstance(result, Exception):
                    logger.error(f"Error fetching {game_id}: {result}")
                    results[game_id] = None
                else:
                    results[game_id] = result
        
        return results
    
    async def get_powerball_jackpot_async(self, shared_soup: Optional[BeautifulSoup] = None) -> Optional[Dict]:
        """Get Powerball jackpot (async version)"""
        try:
            # If we have a shared soup (e.g., from homepage), use it
            if shared_soup:
                soup = shared_soup
                url_used = f"{self.base_url}/"
            else:
                # Try direct play page first (usually faster)
                urls_to_try = [
                    f"{self.base_url}/dbg/play/powerball",  # Direct play page - fastest
                    f"{self.base_url}/",  # Homepage fallback
                ]
                
                soup = None
                url_used = None
                
                for url in urls_to_try:
                    # Skip Playwright for homepage (too slow)
                    skip_playwright = url == f"{self.base_url}/"
                    soup = await self._fetch_page_async(url, skip_playwright=skip_playwright)
                    if soup and soup.title and "not found" not in soup.title.string.lower():
                        url_used = url
                        logger.debug(f"Successfully fetched Powerball from: {url}")
                        break
            
            if not soup:
                logger.warning("Could not fetch page for Powerball")
                return None
            
            jackpot_value = None
            
            # Strategy 1: Look for Powerball game card
            powerball_card = soup.find('div', class_=re.compile(r'mega-menu_game-card--powerball|powerball.*card', re.I))
            if powerball_card:
                logger.debug("Found Powerball card")
                jackpot_container = powerball_card.find('div', class_=re.compile(r'jackpot', re.I))
                if jackpot_container:
                    jackpot_text = jackpot_container.get_text()
                    value = self._parse_currency(jackpot_text)
                    if value and value > 10000000:  # Powerball jackpots are $10M+
                        jackpot_value = value
                        logger.debug(f"Found Powerball jackpot in card container: {value}")
                else:
                    # Parse entire card
                    card_text = powerball_card.get_text()
                    all_values = re.findall(r'\$[\d,KM]+', card_text)
                    for val_str in all_values:
                        value = self._parse_currency(val_str)
                        if value and value > 10000000:  # Powerball range
                            if jackpot_value is None or value > jackpot_value:
                                jackpot_value = value
                                logger.debug(f"Found Powerball jackpot in card text: {value}")
            
            # Strategy 2: Look for all currency strings in Powerball range
            if not jackpot_value:
                all_currency_strings = soup.find_all(string=re.compile(r'\$[\d,KM]+'))
                for currency_str in all_currency_strings:
                    value = self._parse_currency(currency_str)
                    # Powerball jackpots are typically $20M-$1B+ range
                    if value and value > 10000000:
                        if jackpot_value is None or value > jackpot_value:
                            jackpot_value = value
                            logger.debug(f"Found Powerball jackpot via currency search: {value}")
            
            if jackpot_value:
                return {
                    'game': 'Powerball',
                    'jackpot': jackpot_value,
                    'timestamp': datetime.now().isoformat(),
                    'source': url_used or urls_to_try[0]
                }
            
            logger.warning("Could not find Powerball jackpot")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Powerball jackpot: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    async def get_mega_millions_jackpot_async(self, shared_soup: Optional[BeautifulSoup] = None) -> Optional[Dict]:
        """Get Mega Millions jackpot (async version)"""
        try:
            # If we have a shared soup (e.g., from homepage), use it
            if shared_soup:
                soup = shared_soup
                url_used = f"{self.base_url}/"
            else:
                # Try direct play page first (usually faster)
                urls_to_try = [
                    f"{self.base_url}/dbg/play/megamillions",  # Direct play page - fastest
                    f"{self.base_url}/",  # Homepage fallback
                ]
                
                soup = None
                url_used = None
                
                for url in urls_to_try:
                    # Skip Playwright for homepage (too slow)
                    skip_playwright = url == f"{self.base_url}/"
                    soup = await self._fetch_page_async(url, skip_playwright=skip_playwright)
                    if soup and soup.title and "not found" not in soup.title.string.lower():
                        url_used = url
                        logger.debug(f"Successfully fetched Mega Millions from: {url}")
                        break
            
            if not soup:
                logger.warning("Could not fetch page for Mega Millions")
                return None
            
            jackpot_value = None
            
            # Strategy 1: Look for Mega Millions game card
            mega_card = soup.find('div', class_=re.compile(r'mega-menu_game-card--megamillions|mega.*millions.*card', re.I))
            if mega_card:
                logger.debug("Found Mega Millions card")
                jackpot_container = mega_card.find('div', class_=re.compile(r'jackpot', re.I))
                if jackpot_container:
                    jackpot_text = jackpot_container.get_text()
                    value = self._parse_currency(jackpot_text)
                    if value and value > 10000000:  # Mega Millions jackpots are $10M+
                        jackpot_value = value
                        logger.debug(f"Found Mega Millions jackpot in card container: {value}")
                else:
                    # Parse entire card
                    card_text = mega_card.get_text()
                    all_values = re.findall(r'\$[\d,KM]+', card_text)
                    for val_str in all_values:
                        value = self._parse_currency(val_str)
                        if value and value > 10000000:  # Mega Millions range
                            if jackpot_value is None or value > jackpot_value:
                                jackpot_value = value
                                logger.debug(f"Found Mega Millions jackpot in card text: {value}")
            
            # Strategy 2: Look for all currency strings in Mega Millions range
            if not jackpot_value:
                all_currency_strings = soup.find_all(string=re.compile(r'\$[\d,KM]+'))
                for currency_str in all_currency_strings:
                    value = self._parse_currency(currency_str)
                    # Mega Millions jackpots are typically $20M-$1B+ range
                    if value and value > 10000000:
                        if jackpot_value is None or value > jackpot_value:
                            jackpot_value = value
                            logger.debug(f"Found Mega Millions jackpot via currency search: {value}")
            
            if jackpot_value:
                return {
                    'game': 'Mega Millions',
                    'jackpot': jackpot_value,
                    'timestamp': datetime.now().isoformat(),
                    'source': url_used or urls_to_try[0]
                }
            
            logger.warning("Could not find Mega Millions jackpot")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Mega Millions jackpot: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def test_connection(self) -> bool:
        """Test connection to lottery website"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
