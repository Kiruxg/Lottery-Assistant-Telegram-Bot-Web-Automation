"""
Lottery Assistant - Main Entry Point
"""

import asyncio
import logging
import os
import sys
import schedule
import time
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from src.lottery_assistant import LotteryAssistant
from src.telegram_bot import TelegramBot

# Load environment variables
load_dotenv()

# Setup logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lottery_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def run_buy_signal_reminder():
    """Check for active buy signals and send reminders"""
    assistant = LotteryAssistant()
    try:
        await assistant.check_buy_signal_reminders()
    finally:
        await assistant.cleanup()


async def run_check(game_id: Optional[str] = None, only_near_draw: bool = True):
    """
    Run a single check cycle
    
    Args:
        game_id: If provided, only check this specific game
        only_near_draw: If True, only send alerts/status if near draw time (default: True)
    """
    assistant = LotteryAssistant()
    try:
        if game_id:
            # Check specific game
            await assistant.check_jackpots(game_id_filter=game_id, only_near_draw=only_near_draw)
        else:
            # Check all games (for manual checks, don't restrict to draw times)
            await assistant.check_jackpots(only_near_draw=False)
    finally:
        await assistant.cleanup()


async def test_system():
    """Test all system components"""
    assistant = LotteryAssistant()
    try:
        results = await assistant.test_components()
        logger.info(f"Test results: {results}")
        
        if all(results.values()):
            logger.info("✅ All components tested successfully!")
        else:
            logger.warning("⚠️ Some components failed tests")
            
    finally:
        await assistant.cleanup()


def schedule_checks():
    """Schedule periodic checks based on draw times from config"""
    from src.scheduler import LotteryScheduler
    
    scheduler = LotteryScheduler()
    schedule_times = scheduler.get_schedule_times(minutes_after=30, reminder_hours_before=3)
    
    # Draw days mapping (0=Monday, 6=Sunday)
    draw_days = {
        'powerball': [0, 2, 5],  # Monday, Wednesday, Saturday
        'mega_millions': [1, 4],  # Tuesday, Friday
        'lucky_day_lotto_midday': list(range(7)),  # Daily
        'lucky_day_lotto_evening': list(range(7))  # Daily
    }
    
    scheduled_count = 0
    
    for game_id, description, check_time in schedule_times:
        time_str = check_time.strftime("%H:%M")
        days = draw_days.get(game_id, list(range(7)))
        
        # Check if this is a reminder check
        is_reminder = "Reminder" in description
        
        if is_reminder:
            # Schedule reminder check
            reminder_func = lambda: asyncio.run(run_buy_signal_reminder())
        else:
            # Create a closure to capture game_id for regular checks
            def make_check_func(gid):
                return lambda: asyncio.run(run_check(game_id=gid, only_near_draw=True))
            reminder_func = make_check_func(game_id)
        
        if len(days) == 7:  # Daily
            schedule.every().day.at(time_str).do(reminder_func)
            logger.info(f"Scheduled daily check at {time_str}: {description} (game: {game_id})")
            scheduled_count += 1
        else:
            # Schedule for specific days
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day_num in days:
                day_name = day_names[day_num]
                getattr(schedule.every(), day_name).at(time_str).do(reminder_func)
                logger.info(f"Scheduled {day_name} check at {time_str}: {description} (game: {game_id})")
                scheduled_count += 1
    
    logger.info(f"✅ Scheduled {scheduled_count} check times based on draw schedules")
    logger.info("📌 Regular checks: 30 minutes after draw | Reminder checks: 3 hours before draw")
    
    # Print summary
    summary = scheduler.get_schedule_summary()
    logger.info(f"\n{summary}")


async def run_scheduled():
    """Run scheduled checks continuously"""
    schedule_checks()
    
    logger.info("Starting scheduled monitoring...")
    
    try:
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Stopping scheduled monitoring...")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            logger.info("Running system tests...")
            asyncio.run(test_system())
        
        elif command == "check":
            # Check if game_id is provided as second argument
            game_id = sys.argv[2] if len(sys.argv) > 2 else None
            if game_id:
                logger.info(f"Running check for {game_id}...")
            else:
                logger.info("Running check for all games...")
            asyncio.run(run_check(game_id=game_id, only_near_draw=False))
        
        elif command == "schedule":
            logger.info("Starting scheduled monitoring...")
            asyncio.run(run_scheduled())
        
        elif command == "bot":
            logger.info("Starting Telegram bot with commands...")
            bot = TelegramBot()
            try:
                bot.start_polling()
            except KeyboardInterrupt:
                logger.info("Stopping bot...")
                try:
                    asyncio.run(bot.stop_polling())
                except:
                    pass
        
        else:
            print("Usage:")
            print("  python main.py test      - Test all components")
            print("  python main.py check     - Run a single check")
            print("  python main.py schedule   - Start scheduled monitoring")
            print("  python main.py bot       - Start Telegram bot with commands")
    else:
        # Default: run a single check
        logger.info("Running single check (default)...")
        asyncio.run(run_check())


if __name__ == "__main__":
    main()
