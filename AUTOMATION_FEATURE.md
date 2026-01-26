# 🤖 Purchase Automation Feature

## Overview

The purchase automation feature automatically opens your browser to the Illinois Lottery website when a buy signal is detected, selects Quick Pick, and stops before checkout for legal compliance.

## How It Works

### When It Triggers

The automation triggers automatically when:
1. ✅ A **buy signal** is detected for:
   - Lucky Day Lotto (Midday or Evening)
   - Mega Millions
2. ✅ The buy signal is active and meets all criteria
3. ✅ Automation is enabled in your `.env` file

**Note:** Powerball automation is disabled per requirements.

### What It Does

1. **Opens Browser** - Launches a browser window (non-headless, so you can see it)
2. **Navigates to Game Page** - Goes to the Illinois Lottery website for the specific game
3. **Selects Quick Pick** - Automatically clicks the "Quick Pick" button
4. **Stops Before Checkout** - **Stops here for legal compliance** - you complete checkout manually

### Legal Compliance

⚠️ **IMPORTANT:** The automation **STOPS BEFORE CHECKOUT** to comply with legal requirements. You must:
- Review your selection
- Complete checkout manually
- Make payment yourself

The system will never:
- ❌ Auto-submit payment
- ❌ Auto-complete checkout
- ❌ Store payment information
- ❌ Make purchases without your explicit action

## Setup Instructions

### 1. Enable Automation

Edit your `.env` file and set:
```bash
ENABLE_PURCHASE_AUTOMATION=true
```

### 2. Configure Browser (Optional)

You can choose which browser to use:
```bash
BROWSER_TYPE=chromium  # Options: chromium, chrome, firefox, webkit
```

### 3. Automation Settings in config.json

The automation settings are already configured in `config.json`:
```json
{
  "automation_settings": {
    "headless": false,              // Browser visible (not hidden)
    "timeout_seconds": 30,          // Page load timeout
    "wait_for_user_confirmation": true,  // Keep browser open
    "stop_at_checkout": true        // Stop before checkout (legal)
  }
}
```

## Example Flow

```
1. Buy Signal Detected
   ↓
2. Telegram Alert Sent: "🟡 BUY SIGNAL: Mega Millions"
   ↓
3. Browser Opens: https://www.illinoislottery.com/games/mega-millions
   ↓
4. Quick Pick Selected Automatically
   ↓
5. 🛑 STOPS HERE - Legal Compliance
   ↓
6. You manually:
   - Review selection
   - Add to cart (if needed)
   - Complete checkout
   - Make payment
```

## Troubleshooting

### Browser Doesn't Open

1. **Check if automation is enabled:**
   ```bash
   # In .env file
   ENABLE_PURCHASE_AUTOMATION=true
   ```

2. **Check Playwright installation:**
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

3. **Check logs:**
   Look for automation messages in `lottery_assistant.log`

### Quick Pick Not Selected

The automation tries multiple selectors to find the Quick Pick button. If it can't find it:
- The browser will still open
- You can manually select Quick Pick
- The automation logs will show a warning

### Browser Opens But Nothing Happens

- Check your internet connection
- The Illinois Lottery website may have changed
- Check the browser console for errors
- Review logs for detailed error messages

## Security & Privacy

- ✅ No payment information is stored
- ✅ No login credentials are used
- ✅ Browser opens in a new session
- ✅ You maintain full control
- ✅ Automation stops before any payment step

## Disabling Automation

To disable automation, set in `.env`:
```bash
ENABLE_PURCHASE_AUTOMATION=false
```

Or simply don't set the variable (defaults to `false`).

## Supported Games

- ✅ **Lucky Day Lotto** (Midday & Evening)
- ✅ **Mega Millions**
- ❌ **Powerball** (disabled per requirements)

## Notes

- The browser will remain open after automation completes
- You can close it manually when done
- Multiple buy signals may open multiple browser windows
- Automation only runs when buy signals are detected (not on every check)
