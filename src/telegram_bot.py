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
from .subscription_manager import SubscriptionManager

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
        self.subscription_manager = SubscriptionManager()
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Register command handlers
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("thresholds", self.thresholds_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("buysignals", self.buysignals_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("mysubscriptions", self.mysubscriptions_command))
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
        chat_id = str(update.effective_chat.id)
        
        # Initialize user if new
        if chat_id not in self.subscription_manager.subscriptions:
            self.subscription_manager.set_user_tier(chat_id, 'free')
        
        message = "🎯 *LottoEdge Bot*\n\n"
        message += "I monitor Illinois lottery jackpots and send alerts!\n\n"
        message += "*📋 Available Commands:*\n"
        message += "/subscribe <game> - Subscribe to game alerts\n"
        message += "/unsubscribe <game> - Unsubscribe from a game\n"
        message += "/mysubscriptions - View your subscriptions\n"
        message += "/status - Get current jackpot status\n"
        message += "/thresholds - Show threshold status\n"
        message += "/history - Show threshold alert history\n"
        message += "/buysignals - Show active buy signals\n"
        message += "/help - Show this help message\n\n"
        message += "💡 *Tip:* Free users can subscribe to 1 game. Upgrade to Premium for unlimited subscriptions!\n\n"
        message += "Use /subscribe to start receiving alerts for specific games."
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        # Use plain text to avoid Markdown parsing issues with special characters
        message = "📖 Available Commands\n\n"
        message += "Subscription Commands:\n"
        message += "/subscribe <game> - Subscribe to alerts for a game\n"
        message += "/unsubscribe <game> - Unsubscribe from a game\n"
        message += "/mysubscriptions - View your current subscriptions\n\n"
        message += "Info Commands:\n"
        message += "/status - Get current jackpot status for all games\n"
        message += "/thresholds - Show threshold status and configuration\n"
        message += "/history - Show recent threshold alert history\n"
        message += "/buysignals - Show active buy signals\n\n"
        message += "Available Games:\n"
        message += "• lucky_day_lotto_midday\n"
        message += "• lucky_day_lotto_evening\n"
        message += "• powerball\n"
        message += "• mega_millions\n\n"
        message += "💡 Free Tier: Subscribe to 1 game\n"
        message += "⭐ Premium/Pro: Subscribe to all games"
        
        await update.message.reply_text(message)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            if not self.assistant:
                self.assistant = LotteryAssistant()
            
            # Run a quick check to get latest data (suppress automatic messages)
            results = await self.assistant.check_jackpots(only_near_draw=False, suppress_messages=True)
            
            # Determine which Lucky Day Lotto draw is next (midday or evening)
            midday_result = results.get('lucky_day_lotto_midday')
            evening_result = results.get('lucky_day_lotto_evening')
            next_ldl_game_id = None
            
            if midday_result and evening_result:
                # Compare next draw times to determine which is next
                midday_draw_time = self.assistant._get_next_draw_time('lucky_day_lotto_midday')
                evening_draw_time = self.assistant._get_next_draw_time('lucky_day_lotto_evening')
                
                if midday_draw_time and evening_draw_time:
                    next_ldl_game_id = 'lucky_day_lotto_midday' if midday_draw_time < evening_draw_time else 'lucky_day_lotto_evening'
                elif midday_draw_time:
                    next_ldl_game_id = 'lucky_day_lotto_midday'
                elif evening_draw_time:
                    next_ldl_game_id = 'lucky_day_lotto_evening'
                else:
                    # Fallback: use midday if both exist but no draw times
                    next_ldl_game_id = 'lucky_day_lotto_midday'
            elif midday_result:
                next_ldl_game_id = 'lucky_day_lotto_midday'
            elif evening_result:
                next_ldl_game_id = 'lucky_day_lotto_evening'
            
            # Build status message from results
            status_message = "🎰 *Current Lottery Status*\n\n"
            
            # Define game order: next LDL draw first, then Powerball, then Mega Millions
            game_order = []
            if next_ldl_game_id:
                game_order.append(next_ldl_game_id)
            game_order.extend(['powerball', 'mega_millions'])
            
            for game_id in game_order:
                result = results.get(game_id)
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
                
                # Format: Game Name
                status_message += f"*{game_name}*\n"
                
                # Format: 💰 Jackpot: $X
                status_message += f"💰 Jackpot: ${current_jackpot:,.0f}\n"
                
                # Format: 📊 Net EV: $X (X%)
                status_message += f"📊 Net EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
                
                # Format: Buy signal / recommendation (always show 1-liner)
                if buy_signal_details.get('has_signal'):
                    buy_message = buy_signal_details.get('message', '🟡 Consider Buying')
                else:
                    # Default recommendation when no explicit buy signal
                    if ev_result.get('is_positive_ev', False):
                        buy_message = "🟢 Strong Buy"
                    else:
                        buy_message = "🟠 Not Recommended"
                status_message += f"{buy_message}\n"
                
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
                    message += f"📊 EV: ${signal_info['signal'].get('net_ev', 0):.2f} ({signal_info['signal'].get('ev_percentage', 0):.2f}%)\n\n"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in buysignals command: {e}")
            await update.message.reply_text(
                f"❌ Error getting buy signals: {str(e)}",
                parse_mode="Markdown"
            )
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not context.args or len(context.args) == 0:
                message = "📋 *Subscribe to Game Alerts*\n\n"
                message += "Usage: `/subscribe <game_id>`\n\n"
                message += "*Available games:*\n"
                message += "• `lucky_day_lotto_midday`\n"
                message += "• `lucky_day_lotto_evening`\n"
                message += "• `powerball`\n"
                message += "• `mega_millions`\n\n"
                message += "*Example:* `/subscribe powerball`\n\n"
                
                # Show current subscriptions
                info = self.subscription_manager.get_subscription_info(chat_id)
                if info['subscribed_games']:
                    message += f"*Your subscriptions:* {', '.join(info['subscribed_games'])}\n"
                    message += f"*Tier:* {info['tier'].title()} ({info['subscription_count']}/{info['max_subscriptions']})\n"
                else:
                    message += "*You're not subscribed to any games yet.*\n"
                
                await update.message.reply_text(message, parse_mode="Markdown")
                return
            
            game_id = context.args[0].lower()
            
            # Validate game ID
            valid_games = ['lucky_day_lotto_midday', 'lucky_day_lotto_evening', 'lotto', 'powerball', 'mega_millions', 'pick_3', 'pick_4', 'hot_wins']
            if game_id not in valid_games:
                await update.message.reply_text(
                    f"❌ Invalid game ID: `{game_id}`\n\n"
                    f"Valid games: {', '.join(valid_games)}",
                    parse_mode="Markdown"
                )
                return
            
            # Subscribe
            success, message = self.subscription_manager.subscribe_to_game(chat_id, game_id)
            
            if success:
                info = self.subscription_manager.get_subscription_info(chat_id)
                formatted_message = f"✅ Subscribed to `{game_id}`!\n\n"
                formatted_message += f"*Subscription Status:*\n"
                formatted_message += f"• Tier: {info['tier'].title()}\n"
                formatted_message += f"• Subscribed to: {len(info['subscribed_games'])}/{info['max_subscriptions']} games\n"
                if info['remaining_slots'] > 0:
                    formatted_message += f"• Remaining slots: {info['remaining_slots']}"
                await update.message.reply_text(formatted_message, parse_mode="Markdown")
            else:
                # Send error message without Markdown to avoid parsing issues
                await update.message.reply_text(f"❌ {message}")
            
        except Exception as e:
            logger.error(f"Error in subscribe command: {e}")
            # Send error without Markdown to avoid parsing issues
            await update.message.reply_text(
                f"Error: {str(e)}"
            )
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unsubscribe command"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not context.args or len(context.args) == 0:
                info = self.subscription_manager.get_subscription_info(chat_id)
                if not info['subscribed_games']:
                    await update.message.reply_text(
                        "❌ You're not subscribed to any games.\n\n"
                        "Use `/subscribe <game_id>` to subscribe.",
                        parse_mode="Markdown"
                    )
                    return
                
                message = "📋 *Unsubscribe from Game*\n\n"
                message += "Usage: `/unsubscribe <game_id>`\n\n"
                message += f"*Your current subscriptions:*\n"
                for game_id in info['subscribed_games']:
                    message += f"• `{game_id}`\n"
                message += "\n*Example:* `/unsubscribe powerball`"
                
                await update.message.reply_text(message, parse_mode="Markdown")
                return
            
            game_id = context.args[0].lower()
            success, message = self.subscription_manager.unsubscribe_from_game(chat_id, game_id)
            
            # Format message with proper Markdown escaping
            if success:
                formatted_message = f"✅ Unsubscribed from `{game_id}`."
                await update.message.reply_text(formatted_message, parse_mode="Markdown")
            else:
                # Send error message without Markdown to avoid parsing issues
                await update.message.reply_text(f"❌ {message}")
            
        except Exception as e:
            logger.error(f"Error in unsubscribe command: {e}")
            # Send error without Markdown to avoid parsing issues
            await update.message.reply_text(
                f"Error: {str(e)}"
            )
    
    async def mysubscriptions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mysubscriptions command"""
        try:
            chat_id = str(update.effective_chat.id)
            info = self.subscription_manager.get_subscription_info(chat_id)
            
            message = "📋 *Your Subscriptions*\n\n"
            message += f"*Tier:* {info['tier'].title()}\n"
            message += f"*Subscribed Games:* {info['subscription_count']}/{info['max_subscriptions']}\n\n"
            
            if info['subscribed_games']:
                message += "*Active Subscriptions:*\n"
                for game_id in info['subscribed_games']:
                    message += f"• `{game_id}`\n"
            else:
                message += "*No active subscriptions.*\n"
                message += "Use `/subscribe <game_id>` to subscribe to a game.\n\n"
            
            if info['tier'] == 'free' and info['remaining_slots'] == 0:
                message += "\n💡 *Upgrade to Premium* to subscribe to all games!"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in mysubscriptions command: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
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
