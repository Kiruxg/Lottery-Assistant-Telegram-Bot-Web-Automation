"""
Telegram Bot Command Handler
Handles interactive commands via Telegram
"""

import logging
import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

from .lottery_assistant import LotteryAssistant

load_dotenv()

logger = logging.getLogger(__name__)


class TelegramBot:
    """Handles Telegram bot commands"""
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token (or from env)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be provided")
        
        self.application = Application.builder().token(self.bot_token).build()
        self.assistant: Optional[LotteryAssistant] = None
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Register command handlers
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("thresholds", self.thresholds_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("buysignals", self.buysignals_command))
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors and send a message to the user"""
        logger.error(f"Exception while handling an update: {context.error}")
        if isinstance(update, Update) and update.message:
            try:
                await update.message.reply_text(
                    f"❌ An error occurred: {str(context.error)}"
                )
            except:
                pass
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        message = "🎰 *Lottery Assistant Bot*\n\n"
        message += "I monitor Illinois lottery jackpots and send alerts!\n\n"
        message += "Available commands:\n"
        message += "/status - Get current jackpot status\n"
        message += "/thresholds - Show threshold status\n"
        message += "/history - Show threshold alert history\n"
        message += "/buysignals - Show active buy signals\n"
        message += "/help - Show this help message\n\n"
        message += "I'll automatically send you updates when jackpots hit thresholds!"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        message = "📖 *Available Commands*\n\n"
        message += "/status - Get current jackpot status for all games\n"
        message += "/thresholds - Show threshold status and configuration\n"
        message += "/history - Show recent threshold alert history\n"
        message += "/buysignals - Show active buy signals\n"
        message += "/help - Show this help message\n"
        message += "/start - Start the bot\n\n"
        message += "The bot automatically monitors:\n"
        message += "• Lucky Day Lotto (Midday & Evening)\n"
        message += "• Powerball\n"
        message += "• Mega Millions\n\n"
        message += "You'll receive alerts when jackpots hit configured thresholds!"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            if not self.assistant:
                self.assistant = LotteryAssistant()
            
            # Run a quick check to get latest data
            await update.message.reply_text("🔄 Checking latest jackpots...", parse_mode="Markdown")
            results = await self.assistant.check_jackpots(only_near_draw=False)
            
            # Build status message from results
            status_message = "🎰 *Current Lottery Status*\n\n"
            
            for game_id, result in results.items():
                if not result:
                    continue
                
                game_config = self.assistant.config.get('lottery_games', {}).get(game_id, {})
                game_name = game_config.get('name', game_id)
                jackpot_data = result.get('jackpot_data', {})
                ev_result = result.get('ev_result', {})
                buy_signal_details = result.get('buy_signal_details', {})
                
                current_jackpot = jackpot_data.get('jackpot', 0)
                net_ev = ev_result.get('net_ev', 0)
                ev_percentage = ev_result.get('ev_percentage', 0)
                
                status_message += f"*{game_name}*\n"
                status_message += f"💰 Jackpot: ${current_jackpot:,.0f}\n"
                
                if buy_signal_details.get('has_signal'):
                    status_message += f"{buy_signal_details.get('message', '🟡 BUY SIGNAL')}\n"
                elif ev_result.get('is_positive_ev', False):
                    status_message += f"✅ Positive EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                else:
                    status_message += f"📊 Net EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                
                status_message += "\n"
            
            await update.message.reply_text(status_message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(
                f"❌ Error getting status: {str(e)}",
                parse_mode="Markdown"
            )
    
    async def thresholds_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /thresholds command"""
        try:
            if not self.assistant:
                self.assistant = LotteryAssistant()
            
            import json
            import os
            state_file = os.getenv('LOTTERY_STATE_FILE', 'lottery_state.json')
            state = {}
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
            
            message = "🎯 *Threshold Status*\n\n"
            
            for game_id, game_config in self.assistant.config.get('lottery_games', {}).items():
                if not game_config.get('enabled', False):
                    continue
                
                game_name = game_config.get('name', game_id)
                game_state = state.get('games', {}).get(game_id, {})
                
                min_threshold = game_config.get('min_threshold')
                last_threshold = game_state.get('last_threshold', 0)
                thresholds_hit = len(game_state.get('thresholds_hit', []))
                
                message += f"*{game_name}*\n"
                if min_threshold:
                    message += f"Minimum: ${min_threshold:,.0f}\n"
                    message += f"Last Hit: ${last_threshold:,.0f}\n" if last_threshold > 0 else "Last Hit: Never\n"
                    message += f"Total Alerts: {thresholds_hit}\n"
                else:
                    message += "Thresholds: Disabled\n"
                message += "\n"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in thresholds command: {e}")
            await update.message.reply_text(
                f"❌ Error getting thresholds: {str(e)}",
                parse_mode="Markdown"
            )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        try:
            if not self.assistant:
                self.assistant = LotteryAssistant()
            
            import json
            import os
            from datetime import datetime
            
            state_file = os.getenv('LOTTERY_STATE_FILE', 'lottery_state.json')
            state = {}
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
            
            history = []
            for game_id, game_state in state.get('games', {}).items():
                game_config = self.assistant.config.get('lottery_games', {}).get(game_id, {})
                game_name = game_config.get('name', game_id)
                
                for threshold_hit in game_state.get('thresholds_hit', []):
                    history.append({
                        'game_name': game_name,
                        'threshold': threshold_hit.get('threshold', 0),
                        'jackpot': threshold_hit.get('jackpot', 0),
                        'timestamp': threshold_hit.get('timestamp', '')
                    })
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            message = "📊 *Threshold Alert History*\n\n"
            
            if not history:
                message += "No threshold alerts yet."
            else:
                for item in history[:10]:  # Show last 10
                    timestamp = item.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            time_str = timestamp
                    else:
                        time_str = "Unknown"
                    
                    message += f"*{item['game_name']}*\n"
                    message += f"Threshold: ${item['threshold']:,.0f}\n"
                    message += f"Jackpot: ${item['jackpot']:,.0f}\n"
                    message += f"Time: {time_str}\n\n"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in history command: {e}")
            await update.message.reply_text(
                f"❌ Error getting history: {str(e)}",
                parse_mode="Markdown"
            )
    
    async def buysignals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /buysignals command"""
        try:
            if not self.assistant:
                self.assistant = LotteryAssistant()
            
            # Run a quick check to get latest buy signals
            await update.message.reply_text("🔄 Checking buy signals...", parse_mode="Markdown")
            results = await self.assistant.check_jackpots(only_near_draw=False)
            
            message = "🟡 *Active Buy Signals*\n\n"
            
            active_signals = []
            for game_id, result in results.items():
                if not result:
                    continue
                
                buy_signal_details = result.get('buy_signal_details', {})
                if buy_signal_details.get('has_signal'):
                    game_config = self.assistant.config.get('lottery_games', {}).get(game_id, {})
                    game_name = game_config.get('name', game_id)
                    jackpot_data = result.get('jackpot_data', {})
                    current_jackpot = jackpot_data.get('jackpot', 0)
                    
                    active_signals.append({
                        'game_name': game_name,
                        'signal': buy_signal_details,
                        'jackpot': current_jackpot
                    })
            
            if not active_signals:
                message += "No active buy signals at this time."
            else:
                for signal_info in active_signals:
                    message += f"*{signal_info['game_name']}*\n"
                    message += f"{signal_info['signal'].get('message', 'BUY SIGNAL')}\n"
                    message += f"💰 Jackpot: ${signal_info['jackpot']:,.0f}\n"
                    message += f"📊 EV: ${signal_info['signal'].get('net_ev', 0):.2f} ({signal_info['signal'].get('ev_percentage', 0):.2f}%)\n"
                    
                    reasons = signal_info['signal'].get('reasons', [])
                    if reasons:
                        message += f"Reasons: {', '.join(reasons)}\n"
                    
                    message += "\n"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in buysignals command: {e}")
            await update.message.reply_text(
                f"❌ Error getting buy signals: {str(e)}",
                parse_mode="Markdown"
            )
    
    def start_polling(self):
        """Start the bot and begin polling for commands"""
        logger.info("Starting Telegram bot polling...")
        logger.info("Telegram bot is running. Send /start to begin!")
        # Don't drop pending updates - we want to process all commands
        self.application.run_polling(drop_pending_updates=False)
    
    async def stop_polling(self):
        """Stop the bot polling"""
        logger.info("Stopping Telegram bot...")
        await self.application.stop()
        await self.application.shutdown()
        if self.assistant:
            await self.assistant.cleanup()
