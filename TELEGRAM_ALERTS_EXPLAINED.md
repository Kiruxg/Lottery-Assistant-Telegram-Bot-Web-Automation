# Telegram Alerts Feature - How It Works

## Overview

The Telegram alerts system allows users to receive real-time notifications about lottery jackpots, expected value (EV) calculations, and buy signals directly in their Telegram app.

## How It Currently Works

### 1. **Subscription Methods**

Users can subscribe to game alerts in two ways:

#### A. Via Telegram Bot Commands
- Users send `/subscribe <game_id>` to the bot
- Example: `/subscribe powerball`
- The bot stores the subscription using the user's Telegram `chat_id` as the identifier
- Users immediately receive a confirmation message

#### B. Via Web Dashboard
- Users toggle the "Subscribe" checkbox on the dashboard
- The subscription is stored using a `user_id` (which may be `'web_anonymous'` or a custom ID)
- **NEW**: If the `user_id` is a valid Telegram chat ID (numeric string), a confirmation message is automatically sent to Telegram

### 2. **Alert Types**

Once subscribed, users receive three types of alerts:

#### A. Status Updates
- Sent when jackpot values change
- Includes:
  - Current jackpot amount
  - Net EV calculation
  - Buy signal recommendation (✅ BUY SIGNAL, ⚠️ Near Break-Even, or ❌ NO BUY SIGNAL)
  - Timestamp
- Format example:
  ```
  🎰 Lucky Day Lotto Evening

  💰 Current Jackpot: $450,000.00
  ❌ NO BUY SIGNAL - Net EV: $-0.60 (-59.96%)
  ⏰ Time: 2026-01-27 14:05:27
  ```

#### B. Threshold Alerts
- Sent when jackpot hits configured thresholds
- Only sent near draw time (within 60 minutes)
- Example: Powerball alerts when jackpot exceeds $100M

#### C. Buy Signal Alerts
- Sent when EV becomes positive or near break-even
- Includes detailed EV analysis
- Only sent near draw time

### 3. **Alert Timing**

- **Scheduled Checks**: Alerts are sent automatically based on draw schedules
  - Regular checks: 30 minutes after draw
  - Reminder checks: 3 hours before draw
- **Manual Checks**: Can be triggered via `/status` command or dashboard refresh
- **Near Draw Restriction**: Most alerts only send within 60 minutes of draw time to avoid spam

## Recent Improvements

### ✅ Web Dashboard → Telegram Integration

**What Changed:**
- When a user subscribes via the web dashboard, the system now checks if their `user_id` is a valid Telegram chat ID
- If it is, a confirmation message is automatically sent to their Telegram with:
  - Subscription confirmation
  - Current subscription status (tier, game count)
  - Latest game information (jackpot, EV, buy signal)
  - Next draw time

**How It Works:**
1. User toggles subscribe button on dashboard
2. System checks if `user_id` is numeric (Telegram chat ID format)
3. If yes, fetches latest game data
4. Sends formatted Telegram message with all relevant info
5. User receives notification in Telegram app

**Example Message:**
```
✅ Subscribed to Lucky Day Lotto Evening!

📋 Subscription Status:
• Tier: Free
• Subscribed to: 1/1 games

🎰 Lucky Day Lotto Evening

💰 Current Jackpot: $450,000.00
❌ NO BUY SIGNAL - Net EV: $-0.60 (-59.96%)
⏰ Time: 2026-01-27 14:05:27
```

## Communication Mode Analysis

### Current Approach: Push Notifications via Telegram

**Advantages:**
- ✅ **Proactive**: Users don't need to check - alerts come to them
- ✅ **Real-time**: Instant notifications when conditions are met
- ✅ **Mobile-friendly**: Works on phones, tablets, desktops
- ✅ **Persistent**: Messages stay in chat history for reference
- ✅ **Interactive**: Users can respond with commands (`/status`, `/buysignals`, etc.)
- ✅ **Low friction**: No need to open a separate app/website

**Disadvantages:**
- ⚠️ Requires Telegram app installed
- ⚠️ Users must link their web account to Telegram chat ID (if subscribing via web)

### Alternative: "Take Them to Telegram" Approach

**What This Would Mean:**
- Redirect users to Telegram when they subscribe
- Show instructions on how to use the bot
- Require them to complete subscription in Telegram

**Why This Is Less Effective:**
- ❌ **Higher friction**: Extra steps to complete subscription
- ❌ **Abandonment risk**: Users may not complete the flow
- ❌ **Context switching**: Breaks the web experience
- ❌ **No immediate feedback**: Users don't see confirmation right away

### Recommended Approach: Hybrid (Current + Enhanced)

**Best Practice:**
1. **Web Dashboard**: Allow subscription with immediate UI feedback
2. **Auto-Send Telegram**: If user has Telegram linked, send confirmation automatically
3. **Optional Link**: Provide easy way to link Telegram account for web users
4. **Telegram Bot**: Continue to support direct Telegram subscriptions

**Why This Works Best:**
- ✅ **Low friction**: Web users can subscribe instantly
- ✅ **Seamless**: Telegram users get confirmation automatically
- ✅ **Flexible**: Works for both web-only and Telegram users
- ✅ **Progressive**: Can enhance with account linking later

## Technical Implementation

### Key Components

1. **SubscriptionManager** (`src/subscription_manager.py`)
   - Manages user subscriptions
   - Handles tier-based limits (Free: 1 game, Premium/Pro: unlimited)
   - Stores in `user_subscriptions.json`

2. **TelegramNotifier** (`src/telegram_notifier.py`)
   - Sends messages to specific chat IDs
   - Handles message formatting and delivery

3. **LotteryAssistant** (`src/lottery_assistant.py`)
   - Monitors jackpots
   - Calculates EV and buy signals
   - Sends alerts to subscribers via `_send_to_subscribers()`

4. **TelegramBot** (`src/telegram_bot.py`)
   - Handles interactive commands
   - Processes `/subscribe`, `/unsubscribe`, `/status`, etc.

### Subscription Flow

```
User Action (Web Dashboard)
    ↓
API: /api/subscriptions/subscribe
    ↓
SubscriptionManager.subscribe_to_game()
    ↓
Check if user_id is Telegram chat_id
    ↓
If yes: send_subscription_confirmation()
    ├─ Fetch latest game data
    ├─ Format message with jackpot, EV, buy signal
    └─ Send via TelegramNotifier
    ↓
Return success to web UI
```

## Future Enhancements

### Potential Improvements:

1. **Account Linking**
   - Add UI to link web account to Telegram chat ID
   - Store mapping: `web_user_id` → `telegram_chat_id`
   - Enable Telegram alerts for all web users

2. **Rich Notifications**
   - Add inline buttons for quick actions
   - Include charts/graphs in messages
   - Add deep links back to dashboard

3. **Preference Management**
   - Let users choose alert frequency
   - Customize message format
   - Set quiet hours

4. **Multi-Channel Support**
   - Email notifications
   - SMS alerts (Pro tier)
   - Push notifications via web browser

## Usage Tips

### For Users:

1. **Get Started**: Send `/start` to the Telegram bot
2. **Subscribe**: Use `/subscribe <game_id>` or toggle on dashboard
3. **Check Status**: Use `/status` anytime for current jackpots
4. **View Subscriptions**: Use `/mysubscriptions` to see what you're subscribed to
5. **Get Help**: Use `/help` for command list

### For Developers:

1. **Testing**: Use `python main.py check` to trigger manual alerts
2. **Monitoring**: Check `lottery_assistant.log` for delivery status
3. **Configuration**: Adjust thresholds in `config.json`
4. **Debugging**: Set `LOG_LEVEL=DEBUG` for detailed logs

## Conclusion

The Telegram alerts system provides a **proactive, real-time notification system** that keeps users informed about lottery opportunities. The recent enhancement allows web users to seamlessly receive Telegram confirmations when they subscribe, creating a unified experience across platforms.

**Recommendation**: Continue with the current push notification approach via Telegram, as it provides the best user experience with minimal friction and maximum engagement.
