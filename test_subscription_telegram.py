"""
Test script for Telegram subscription confirmation feature

This script allows you to test the subscription confirmation message
that gets sent when a user subscribes via the web dashboard.

Usage:
    python test_subscription_telegram.py <chat_id> <game_id>

Example:
    python test_subscription_telegram.py 123456789 mega_millions
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard import send_subscription_confirmation, is_telegram_chat_id

load_dotenv()


async def test_subscription_confirmation(chat_id: str, game_id: str):
    """Test sending subscription confirmation"""
    print(f"Testing subscription confirmation...")
    print(f"Chat ID: {chat_id}")
    print(f"Is valid Telegram chat ID: {is_telegram_chat_id(chat_id)}")
    print(f"Game ID: {game_id}")
    print()
    
    if not is_telegram_chat_id(chat_id):
        print("⚠️  Warning: Chat ID doesn't look like a valid Telegram chat ID")
        print("   (Should be a numeric string)")
        print()
    
    try:
        await send_subscription_confirmation(chat_id, game_id)
        print("✅ Subscription confirmation sent successfully!")
        print("   Check your Telegram app for the message.")
    except Exception as e:
        print(f"❌ Error sending confirmation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_subscription_telegram.py <chat_id> <game_id>")
        print()
        print("Available game IDs:")
        print("  - lucky_day_lotto_midday")
        print("  - lucky_day_lotto_evening")
        print("  - powerball")
        print("  - mega_millions")
        print()
        print("Example:")
        print("  python test_subscription_telegram.py 123456789 mega_millions")
        sys.exit(1)
    
    chat_id = sys.argv[1]
    game_id = sys.argv[2]
    
    # Validate game_id
    valid_games = ['lucky_day_lotto_midday', 'lucky_day_lotto_evening', 'lotto', 'powerball', 'mega_millions', 'pick_3', 'pick_4', 'hot_wins']
    if game_id not in valid_games:
        print(f"❌ Invalid game_id: {game_id}")
        print(f"Valid games: {', '.join(valid_games)}")
        sys.exit(1)
    
    # Check for Telegram bot token
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment")
        print("   Make sure your .env file has TELEGRAM_BOT_TOKEN set")
        sys.exit(1)
    
    asyncio.run(test_subscription_confirmation(chat_id, game_id))
