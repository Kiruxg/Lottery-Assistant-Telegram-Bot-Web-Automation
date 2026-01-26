"""
Main Lottery Assistant Module
Orchestrates all components
"""

import logging
import json
import os
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from .telegram_notifier import TelegramNotifier
from .jackpot_monitor import JackpotMonitor
from .threshold_alert import ThresholdAlert
from .ev_calculator import EVCalculator
from .purchase_automation import PurchaseAutomation
from .buy_signal import BuySignal

logger = logging.getLogger(__name__)


class LotteryAssistant:
    """Main Lottery Assistant class"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize Lottery Assistant
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.notifier = TelegramNotifier()
        # Use Playwright if requests fail (can be enabled via env var)
        use_playwright = os.getenv('USE_PLAYWRIGHT_SCRAPING', 'false').lower() == 'true'
        self.monitor = JackpotMonitor(use_playwright=use_playwright)
        self.threshold_alert = ThresholdAlert(
            state_file=self.config.get('persistence', {}).get('data_file', 'lottery_state.json')
        )
        self.ev_calculator = EVCalculator(self.config)
        self.buy_signal = BuySignal(self.config)
        
        # Initialize automation only if enabled
        self.automation = None
        if os.getenv('ENABLE_PURCHASE_AUTOMATION', 'false').lower() == 'true':
            self.automation = PurchaseAutomation(self.config)
        
        # Get enabled games
        self.enabled_games = [
            game_id for game_id, game_config in self.config.get('lottery_games', {}).items()
            if game_config.get('enabled', False)
        ]
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}
    
    def _setup_logging(self, log_level: str = "INFO"):
        """Setup logging configuration"""
        log_file = self.config.get('persistence', {}).get('log_file', 'lottery_assistant.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def _get_next_draw_time(self, game_id: str) -> Optional[datetime]:
        """
        Calculate the next draw time for a game
        
        Args:
            game_id: Game identifier
            
        Returns:
            datetime object for next draw, or None if error
        """
        from datetime import datetime, time, timedelta
        
        game_config = self.config.get('lottery_games', {}).get(game_id, {})
        draw_time_str = game_config.get('draw_time', '12:00')
        
        try:
            parts = draw_time_str.split(':')
            draw_hour = int(parts[0])
            draw_minute = int(parts[1])
            draw_time = time(draw_hour, draw_minute)
        except (ValueError, IndexError):
            return None
        
        now = datetime.now()
        draw_datetime = datetime.combine(now.date(), draw_time)
        
        # If draw time has passed today, move to next draw
        if draw_datetime <= now:
            # Check draw days for this game
            draw_days = self._get_draw_days(game_id)
            if len(draw_days) == 7:  # Daily
                draw_datetime += timedelta(days=1)
            else:
                # Find next draw day
                current_weekday = now.weekday()  # 0=Monday, 6=Sunday
                days_ahead = 1
                while True:
                    next_date = now.date() + timedelta(days=days_ahead)
                    next_weekday = next_date.weekday()
                    if next_weekday in draw_days:
                        draw_datetime = datetime.combine(next_date, draw_time)
                        break
                    days_ahead += 1
                    if days_ahead > 7:  # Safety check
                        draw_datetime += timedelta(days=1)
                        break
        
        return draw_datetime
    
    def _get_draw_days(self, game_id: str) -> list:
        """Get draw days for a game (0=Monday, 6=Sunday)"""
        draw_days_map = {
            'powerball': [0, 2, 5],  # Monday, Wednesday, Saturday
            'mega_millions': [1, 4],  # Tuesday, Friday
            'lucky_day_lotto_midday': list(range(7)),  # Daily
            'lucky_day_lotto_evening': list(range(7))  # Daily
        }
        return draw_days_map.get(game_id, list(range(7)))
    
    def _format_time_to_draw(self, game_id: str) -> str:
        """
        Format time until next draw as "Xh Ym" or "Xm" or "Less than 1m"
        
        Args:
            game_id: Game identifier
            
        Returns:
            Formatted string like "7h 12m" or "45m" or "Less than 1m"
        """
        from datetime import datetime
        
        next_draw = self._get_next_draw_time(game_id)
        if not next_draw:
            return "Unknown"
        
        now = datetime.now()
        time_diff = next_draw - now
        
        if time_diff.total_seconds() < 0:
            return "Draw passed"
        
        total_minutes = int(time_diff.total_seconds() / 60)
        
        if total_minutes < 1:
            return "Less than 1m"
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def _is_near_draw_time(self, game_id: str, window_minutes: int = 60) -> bool:
        """
        Check if current time is near the draw time for a specific game
        
        Args:
            game_id: Game identifier
            window_minutes: Minutes before/after draw time to consider "near" (default 60)
            
        Returns:
            True if within window of draw time
        """
        from datetime import datetime, time, timedelta
        
        game_config = self.config.get('lottery_games', {}).get(game_id, {})
        draw_time_str = game_config.get('draw_time', '12:00')
        
        try:
            parts = draw_time_str.split(':')
            draw_hour = int(parts[0])
            draw_minute = int(parts[1])
            draw_time = time(draw_hour, draw_minute)
        except (ValueError, IndexError):
            return True  # If can't parse, assume always near (fallback)
        
        now = datetime.now().time()
        draw_datetime = datetime.combine(datetime.today(), draw_time)
        now_datetime = datetime.combine(datetime.today(), now)
        
        # Calculate time difference
        time_diff = abs((now_datetime - draw_datetime).total_seconds() / 60)
        
        # Also check if draw was yesterday (for late night draws)
        yesterday_draw = draw_datetime - timedelta(days=1)
        time_diff_yesterday = abs((now_datetime - yesterday_draw).total_seconds() / 60)
        
        return min(time_diff, time_diff_yesterday) <= window_minutes
    
    async def check_jackpots(self, game_id_filter: Optional[str] = None, only_near_draw: bool = False) -> Dict:
        """
        Check enabled games for jackpot updates
        
        Args:
            game_id_filter: If provided, only check this specific game
            only_near_draw: If True, only send alerts/status messages if near draw time
            
        Returns:
            Dict with jackpot data for all games
        """
        if game_id_filter:
            logger.info(f"Checking jackpot for {game_id_filter}...")
            games_to_check = [game_id_filter] if game_id_filter in self.enabled_games else []
        else:
            logger.info("Checking jackpots for enabled games...")
            games_to_check = self.enabled_games
        
        if not games_to_check:
            logger.warning("No games to check")
            return {}
        
        jackpots = await self.monitor.get_all_jackpots_async(games_to_check)
        
        results = {}
        
        # Process games in order: LDL midday, LDL evening, Powerball, Mega Millions
        game_order = [
            'lucky_day_lotto_midday',
            'lucky_day_lotto_evening',
            'powerball',
            'mega_millions'
        ]
        
        for game_id in game_order:
            if game_id not in games_to_check:
                continue
                
            jackpot_data = jackpots.get(game_id)
            if jackpot_data:
                game_config = self.config.get('lottery_games', {}).get(game_id, {})
                game_name = game_config.get('name', game_id)
                
                current_jackpot = jackpot_data.get('jackpot', 0)
                
                # Calculate EV first (needed for status message)
                odds = game_config.get('odds', 1)
                ticket_cost = game_config.get('ticket_cost', 1.0)
                secondary_ev = game_config.get('secondary_prize_ev', 0)
                
                ev_result = self.ev_calculator.calculate_ev(
                    current_jackpot,
                    odds,
                    ticket_cost,
                    secondary_ev
                )
                
                # Get rollover count from state (now tracked for all games)
                game_state = self.threshold_alert._get_game_state(game_id)
                rollover_count = game_state.get('rollover_count', 0)
                
                # Calculate time to draw in minutes
                next_draw = self._get_next_draw_time(game_id)
                time_to_draw_minutes = None
                time_to_draw_str = "Unknown"
                if next_draw:
                    time_diff = next_draw - datetime.now()
                    time_to_draw_minutes = int(time_diff.total_seconds() / 60)
                    time_to_draw_str = self._format_time_to_draw(game_id)
                
                # Calculate buy signal using new logic
                buy_signal = self.buy_signal.calculate_buy_signal(
                    game_id=game_id,
                    current_jackpot=current_jackpot,
                    ev_result=ev_result,
                    rollover_count=rollover_count,
                    time_to_draw_minutes=time_to_draw_minutes,
                    game_config=game_config
                )
                
                # Track active buy signal in state
                game_state = self.threshold_alert._get_game_state(game_id)
                if buy_signal.get('has_signal'):
                    game_state['active_buy_signal'] = True
                    game_state['buy_signal_last_seen'] = datetime.now().isoformat()
                    game_state['buy_signal_reminder_sent'] = False  # Reset reminder flag
                else:
                    game_state['active_buy_signal'] = False
                self.threshold_alert._save_state()
                
                # Legacy buy signal check (for backward compatibility)
                ev_threshold = float(os.getenv('EV_THRESHOLD', '-0.20'))
                is_buy_signal_legacy = self.ev_calculator.should_buy(ev_result, ev_threshold)
                
                # Check if we should send messages (only near draw time if only_near_draw is True)
                should_send = not only_near_draw or self._is_near_draw_time(game_id, window_minutes=60)
                
                if should_send:
                    # Build status message with buy signal info
                    status_message = f"🎰 *{game_name}*\n\n"
                    status_message += f"💰 Current Jackpot: ${current_jackpot:,.2f}\n"
                    
                    # Add EV and buy signal info
                    net_ev = ev_result.get('net_ev', 0)
                    ev_percentage = ev_result.get('ev_percentage', 0)
                    
                    # Use new buy signal if available, otherwise fall back to legacy
                    if buy_signal.get('has_signal'):
                        status_message += f"{buy_signal['message']}\n"
                        status_message += f"Net EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                    elif ev_result.get('is_positive_ev', False):
                        status_message += f"✅ *BUY SIGNAL* - Positive EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                    elif is_buy_signal_legacy:
                        status_message += f"⚠️ *BUY SIGNAL* - Near Break-Even: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                    else:
                        status_message += f"❌ *NO BUY SIGNAL* - Net EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                    
                    status_message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    await self.notifier.send_message(status_message, parse_mode="Markdown")
                
                # Get game-specific threshold settings
                game_min_threshold = game_config.get('min_threshold')
                game_step_increment = game_config.get('step_increment')
                threshold_operator = game_config.get('threshold_operator', '>=')
                
                # Check threshold (only if configured for this game)
                alert_info = self.threshold_alert.check_threshold(
                    game_id, 
                    current_jackpot,
                    min_threshold=game_min_threshold,
                    step_increment=game_step_increment,
                    threshold_operator=threshold_operator
                )
                
                # Only send threshold alert if near draw time (if only_near_draw is True)
                if alert_info and (not only_near_draw or self._is_near_draw_time(game_id, window_minutes=60)):
                    # Send threshold alert (separate from status message)
                    message = self.threshold_alert.get_alert_message(alert_info, game_name)
                    await self.notifier.send_alert(
                        "Jackpot Threshold Alert",
                        message,
                        "ALERT"
                    )
                
                # Send buy signal alert if new buy signal logic triggers (only if near draw time)
                if buy_signal.get('has_signal') and (not only_near_draw or self._is_near_draw_time(game_id, window_minutes=60)):
                    buy_message = self.buy_signal.format_buy_signal_message(
                        buy_signal, game_name, current_jackpot, rollover_count, time_to_draw_str
                    )
                    
                    if buy_message:
                        await self.notifier.send_alert(
                            "Buy Signal",
                            buy_message,
                            "ALERT"
                        )
                    
                    # Trigger automation if enabled (only for Lucky Day Lotto and Mega Millions)
                    if self.automation and game_id in ['lucky_day_lotto_midday', 'lucky_day_lotto_evening', 'mega_millions']:
                        game_url = self.automation.get_game_url(game_id)
                        logger.info(f"🤖 Triggering purchase automation for {game_name}")
                        await self.automation.setup_purchase_flow(game_name, game_url)
                # Fallback to legacy buy signal
                elif is_buy_signal_legacy and (not only_near_draw or self._is_near_draw_time(game_id, window_minutes=60)):
                    buy_message = f"🛒 *Buy Signal: {game_name}*\n\n"
                    buy_message += self.ev_calculator.format_ev_message(ev_result, game_name)
                    
                    await self.notifier.send_alert(
                        "Buy Signal",
                        buy_message,
                        "ALERT"
                    )
                    
                    # Trigger automation if enabled (only for Lucky Day Lotto and Mega Millions)
                    if self.automation and game_id in ['lucky_day_lotto_midday', 'lucky_day_lotto_evening', 'mega_millions']:
                        game_url = self.automation.get_game_url(game_id)
                        logger.info(f"🤖 Triggering purchase automation for {game_name}")
                        await self.automation.setup_purchase_flow(game_name, game_url)
                
                results[game_id] = {
                    'jackpot_data': jackpot_data,
                    'ev_result': ev_result,
                    'alert_sent': alert_info is not None,
                    'buy_signal': buy_signal.get('has_signal', False),
                    'buy_signal_details': buy_signal
                }
            else:
                logger.warning(f"Could not fetch jackpot for {game_id}")
                results[game_id] = None
        
        return results
    
    async def check_buy_signal_reminders(self) -> Dict:
        """
        Check for active buy signals and send reminders 3 hours before draw
        
        Returns:
            Dict with reminder results
        """
        results = {}
        
        for game_id in self.enabled_games:
            game_config = self.config.get('lottery_games', {}).get(game_id, {})
            game_state = self.threshold_alert._get_game_state(game_id)
            
            # Check if buy signal is active
            if not game_state.get('active_buy_signal', False):
                continue
            
            # Check if we're 3 hours before draw
            next_draw = self._get_next_draw_time(game_id)
            if not next_draw:
                continue
            
            now = datetime.now()
            time_diff = next_draw - now
            minutes_to_draw = int(time_diff.total_seconds() / 60)
            
            # Send reminder if within 175-185 minutes before draw (3 hour window, ±5 min tolerance)
            if 175 <= minutes_to_draw <= 185 and not game_state.get('buy_signal_reminder_sent', False):
                game_name = game_config.get('name', game_id)
                
                # Get current jackpot from state
                current_jackpot = game_state.get('last_jackpot', 0)
                
                # Recalculate EV for reminder
                odds = game_config.get('odds', 1)
                ticket_cost = game_config.get('ticket_cost', 1.0)
                secondary_ev = game_config.get('secondary_prize_ev', 0)
                
                ev_result = self.ev_calculator.calculate_ev(
                    current_jackpot,
                    odds,
                    ticket_cost,
                    secondary_ev
                )
                
                # Recalculate buy signal
                rollover_count = game_state.get('rollover_count', 0) if game_id in ['powerball', 'mega_millions'] else 0
                buy_signal = self.buy_signal.calculate_buy_signal(
                    game_id=game_id,
                    current_jackpot=current_jackpot,
                    ev_result=ev_result,
                    rollover_count=rollover_count,
                    time_to_draw_minutes=minutes_to_draw,
                    game_config=game_config
                )
                
                # Only send if buy signal is still active
                if buy_signal.get('has_signal'):
                    time_to_draw_str = self._format_time_to_draw(game_id)
                    reminder_message = f"⏰ *Buy Signal Reminder*\n\n"
                    reminder_message += f"*{game_name}*\n\n"
                    reminder_message += f"{buy_signal['message']}\n\n"
                    reminder_message += f"💰 Jackpot: ${current_jackpot:,.0f}\n"
                    reminder_message += f"📊 EV: ${buy_signal.get('net_ev', 0):.2f} ({buy_signal.get('ev_percentage', 0):.2f}%)\n"
                    reminder_message += f"⏰ Draw in: {time_to_draw_str}\n\n"
                    reminder_message += f"*Buy signal still active! Consider purchasing.*"
                    
                    await self.notifier.send_alert(
                        "Buy Signal Reminder",
                        reminder_message,
                        "ALERT"
                    )
                    
                    # Mark reminder as sent
                    game_state['buy_signal_reminder_sent'] = True
                    self.threshold_alert._save_state()
                    
                    results[game_id] = {'reminder_sent': True}
                else:
                    # Buy signal no longer active, clear it
                    game_state['active_buy_signal'] = False
                    game_state['buy_signal_reminder_sent'] = False
                    self.threshold_alert._save_state()
                    results[game_id] = {'reminder_sent': False, 'reason': 'Buy signal no longer active'}
            else:
                results[game_id] = {'reminder_sent': False, 'reason': 'Not in reminder window or already sent'}
        
        return results
    
    async def test_components(self) -> Dict:
        """
        Test all components
        
        Returns:
            Dict with test results
        """
        results = {
            'telegram': False,
            'monitor': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test Telegram
        try:
            results['telegram'] = await self.notifier.test_connection()
            if results['telegram']:
                await self.notifier.send_message("🧪 Test message from Lottery Assistant")
        except Exception as e:
            logger.error(f"Telegram test failed: {e}")
        
        # Test Monitor
        try:
            results['monitor'] = self.monitor.test_connection()
        except Exception as e:
            logger.error(f"Monitor test failed: {e}")
        
        return results
    
    async def run_once(self):
        """Run a single check cycle"""
        try:
            results = await self.check_jackpots()
            logger.info("Check cycle completed")
            return results
        except Exception as e:
            logger.error(f"Error in check cycle: {e}")
            await self.notifier.send_alert(
                "Error",
                f"An error occurred during jackpot check: {str(e)}",
                "ERROR"
            )
            raise
    
    async def get_status(self) -> str:
        """
        Get current status of all enabled games
        
        Returns:
            Formatted status message string
        """
        logger.info("Getting current status...")
        
        jackpots = await self.monitor.get_all_jackpots_async(self.enabled_games)
        
        status_lines = ["📊 *Current Jackpot Status*\n"]
        
        # Process games in order: LDL midday, LDL evening, Powerball, Mega Millions
        game_order = [
            'lucky_day_lotto_midday',
            'lucky_day_lotto_evening',
            'powerball',
            'mega_millions'
        ]
        
        for game_id in game_order:
            if game_id not in self.enabled_games:
                continue
                
            jackpot_data = jackpots.get(game_id)
            game_config = self.config.get('lottery_games', {}).get(game_id, {})
            game_name = game_config.get('name', game_id)
            
            if jackpot_data:
                current_jackpot = jackpot_data.get('jackpot', 0)
                last_jackpot = self.threshold_alert.get_last_jackpot(game_id)
                
                # Calculate change
                if last_jackpot > 0:
                    change = current_jackpot - last_jackpot
                    change_str = f"${change:+,.2f}" if change != 0 else "$0.00"
                    change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                else:
                    change_str = "N/A"
                    change_emoji = "🆕"
                
                # Calculate EV for quick indicator
                odds = game_config.get('odds', 1)
                ticket_cost = game_config.get('ticket_cost', 1.0)
                secondary_ev = game_config.get('secondary_prize_ev', 0)
                
                ev_result = self.ev_calculator.calculate_ev(
                    current_jackpot,
                    odds,
                    ticket_cost,
                    secondary_ev
                )
                
                ev_indicator = "✅" if ev_result['is_positive_ev'] else "⚠️" if ev_result['is_recommended'] else "❌"
                
                status_lines.append(f"\n🎰 *{game_name}*")
                status_lines.append(f"💰 Jackpot: ${current_jackpot:,.2f}")
                status_lines.append(f"{change_emoji} Change: {change_str}")
                status_lines.append(f"📊 Net EV: ${ev_result['net_ev']:.4f} {ev_indicator}")
            else:
                status_lines.append(f"\n🎰 *{game_name}*")
                status_lines.append("❌ Unable to fetch jackpot")
        
        status_lines.append(f"\n⏰ Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(status_lines)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.automation:
            await self.automation.cleanup()
