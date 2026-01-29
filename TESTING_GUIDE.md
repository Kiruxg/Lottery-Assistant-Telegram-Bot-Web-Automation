# Testing Guide

## Testing Telegram Subscription Confirmation

### Prerequisites
1. Make sure you have `TELEGRAM_BOT_TOKEN` set in your `.env` file
2. Know your Telegram chat ID (see below)

### Getting Your Telegram Chat ID

**Method 1: From Bot Response**
1. Start a conversation with your bot in Telegram
2. Send `/start` command
3. The bot will respond (this confirms your chat ID is working)

**Method 2: Using get_chat_id.ps1 (Windows)**
```powershell
.\get_chat_id.ps1
```

**Method 3: Using a Test Bot**
1. Message `@userinfobot` on Telegram
2. It will reply with your chat ID

### Testing the Subscription Confirmation

**Option 1: Using the Test Script**
```bash
python test_subscription_telegram.py <your_chat_id> <game_id>
```

Example:
```bash
python test_subscription_telegram.py 123456789 mega_millions
```

**Option 2: Via Web Dashboard**
1. Start the dashboard: `python dashboard.py` or `start_dashboard.bat`
2. Open the dashboard in your browser
3. In browser console, set your user ID to your Telegram chat ID:
   ```javascript
   localStorage.setItem('userId', '123456789'); // Replace with your chat ID
   ```
4. Refresh the page
5. Toggle the subscribe button for any game
6. Check your Telegram for the confirmation message

**Option 3: Direct API Call**
```bash
curl -X POST http://localhost:5000/api/subscriptions/subscribe \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 123456789" \
  -d '{"game_id": "mega_millions"}'
```

### Expected Result

You should receive a Telegram message like:
```
✅ Subscribed to Mega Millions!

📋 Subscription Status:
• Tier: Free
• Subscribed to: 1/1 games

🎰 Mega Millions

💰 Current Jackpot: $285,000,000.00
❌ NO BUY SIGNAL - Net EV: $-0.60 (-59.96%)
⏰ Time: 2026-01-27 14:05:27
```

## Fixing Rollover Count Issues

### Problem
The rollover count may be incorrect if:
- The system was started after a jackpot cycle began
- The jackpot reset detection didn't work correctly
- Historical data wasn't available

### Solution: Manual Fix

Use the fix script to manually set the rollover count:

```bash
python fix_rollover_count.py <game_id> <rollover_count> [cycle_start_jackpot]
```

**Example for Mega Millions:**
Based on the timeline showing:
- Jan 2, 2026: $157M (Rollover 0 - New Cycle)
- Jan 27, 2026: $285M (Rollover 7)

```bash
python fix_rollover_count.py mega_millions 7 157000000
```

This sets:
- Rollover count: 7
- Cycle start jackpot: $157,000,000

### How Rollover Count Works Now

The system now tracks:
1. **cycle_start_jackpot**: The jackpot when the current cycle started (after last win)
2. **rollover_count**: Calculated as `(current_jackpot - cycle_start_jackpot) / rollover_increment`

**Rollover Increments:**
- Lucky Day Lotto: $50,000 per rollover
- Powerball: $2,000,000 per rollover
- Mega Millions: $2,000,000 per rollover

**Automatic Reset Detection:**
- Detects when jackpot drops below 50% of previous jackpot
- For Mega Millions/Powerball: Resets if new jackpot is below $100M
- For LDL: Resets if new jackpot is below $100k

### Verifying Rollover Count

After fixing, run a check to verify:
```bash
python main.py check mega_millions
```

Check the logs or dashboard to confirm the rollover count is correct.

## Testing Full Alert Flow

### 1. Subscribe to a Game
```bash
# Via Telegram
/subscribe mega_millions

# Or via web dashboard (with chat ID set)
```

### 2. Trigger a Manual Check
```bash
python main.py check mega_millions
```

### 3. Check Telegram
You should receive:
- Status update with current jackpot
- EV calculation
- Buy signal recommendation

### 4. Test Threshold Alert
If jackpot is above threshold:
- You'll receive a threshold alert
- Check `lottery_state.json` for threshold tracking

## Troubleshooting

### No Telegram Message Received

1. **Check Bot Token**
   ```bash
   echo $TELEGRAM_BOT_TOKEN  # Linux/Mac
   # or check .env file
   ```

2. **Verify Chat ID**
   - Make sure chat ID is numeric
   - Try sending `/start` to the bot first

3. **Check Logs**
   ```bash
   tail -f lottery_assistant.log
   ```

4. **Test Connection**
   ```python
   from src.telegram_notifier import TelegramNotifier
   import asyncio
   
   async def test():
       notifier = TelegramNotifier(chat_id="YOUR_CHAT_ID")
       await notifier.test_connection()
   
   asyncio.run(test())
   ```

### Rollover Count Still Wrong

1. **Check Current State**
   ```bash
   cat lottery_state.json | grep -A 5 "mega_millions"
   ```

2. **Verify Cycle Start**
   - Check `cycle_start_jackpot` in state
   - Should match the jackpot when cycle began

3. **Manual Override**
   - Use `fix_rollover_count.py` script
   - Or manually edit `lottery_state.json`

### Web Dashboard Not Sending Telegram

1. **Check User ID Format**
   - Must be numeric (Telegram chat ID)
   - Not `'web_anonymous'` or other string

2. **Set User ID in Browser**
   ```javascript
   localStorage.setItem('userId', 'YOUR_TELEGRAM_CHAT_ID');
   ```

3. **Check Dashboard Logs**
   - Look for errors in console
   - Check Flask logs

## Quick Test Checklist

- [ ] Telegram bot token configured
- [ ] Chat ID obtained and verified
- [ ] Test script runs without errors
- [ ] Telegram message received
- [ ] Message contains correct game info
- [ ] Rollover count is accurate (if applicable)
- [ ] Web dashboard subscription works
- [ ] Manual check triggers alerts
