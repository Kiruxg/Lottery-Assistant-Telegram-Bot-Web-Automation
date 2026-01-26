"""
Telegram Notification Module
Handles all Telegram bot messaging functionality
"""

import logging
import asyncio
from typing import Optional, List
from telegram import Bot
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handles Telegram bot notifications"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram notifier
        
        Args:
            bot_token: Telegram bot token (or from env)
            chat_id: Telegram chat ID (or from env)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be provided")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID must be provided")
        
        self.bot = Bot(token=self.bot_token)
        self.message_queue: List[str] = []
        
    async def send_message(self, message: str, parse_mode: Optional[str] = None) -> bool:
        """
        Send a message via Telegram
        
        Args:
            message: Message text to send
            parse_mode: Optional parse mode (HTML, Markdown, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info("Telegram message sent successfully")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: Optional[str] = None) -> bool:
        """
        Synchronous wrapper for send_message
        
        Args:
            message: Message text to send
            parse_mode: Optional parse mode
            
        Returns:
            True if successful, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_message(message, parse_mode))
    
    async def send_alert(self, title: str, message: str, alert_type: str = "INFO") -> bool:
        """
        Send a formatted alert message
        
        Args:
            title: Alert title
            message: Alert message body
            alert_type: Type of alert (INFO, ALERT, ERROR)
            
        Returns:
            True if successful, False otherwise
        """
        emoji_map = {
            "INFO": "ℹ️",
            "ALERT": "🚨",
            "ERROR": "❌",
            "SUCCESS": "✅"
        }
        
        emoji = emoji_map.get(alert_type, "ℹ️")
        formatted_message = f"{emoji} *{title}*\n\n{message}"
        
        return await self.send_message(formatted_message, parse_mode="Markdown")
    
    def send_alert_sync(self, title: str, message: str, alert_type: str = "INFO") -> bool:
        """Synchronous wrapper for send_alert"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_alert(title, message, alert_type))
    
    def queue_message(self, message: str):
        """Queue a message for later sending"""
        self.message_queue.append(message)
        logger.debug(f"Message queued. Queue size: {len(self.message_queue)}")
    
    async def send_queued_messages(self) -> int:
        """
        Send all queued messages
        
        Returns:
            Number of messages successfully sent
        """
        sent_count = 0
        while self.message_queue:
            message = self.message_queue.pop(0)
            if await self.send_message(message):
                sent_count += 1
            else:
                # Re-queue failed message
                self.message_queue.insert(0, message)
                break
        
        return sent_count
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            info = await self.bot.get_me()
            logger.info(f"Telegram bot connected: @{info.username}")
            return True
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
