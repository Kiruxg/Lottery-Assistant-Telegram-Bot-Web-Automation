# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install
```

### Step 2: Get Telegram Bot Credentials

1. **Create a Telegram Bot:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` and follow instructions
   - Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get Your Chat ID:**
   - Search for your bot on Telegram
   - Send `/start` to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat.id` in the response (usually a number like `123456789`)

### Step 3: Configure Environment

```bash
# Copy the example file
cp env.example .env

# Edit .env and add your credentials
# Windows: notepad .env
# Linux/Mac: nano .env
```

Edit `.env`:
```
TELEGRAM_BOT_TOKEN=your_actual_token_here
TELEGRAM_CHAT_ID=your_actual_chat_id_here
```

### Step 4: Test the System

```bash
python main.py test
```

You should receive a test message on Telegram!

### Step 5: Run Your First Check

```bash
python main.py check
```

This will check current jackpots and send alerts if thresholds are met.

### Step 6: Set Up Scheduled Monitoring

**Option A: Use Built-in Scheduler**
```bash
python main.py schedule
```

**Option B: Windows Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 12:30 PM and 9:10 PM
4. Action: Start program
   - Program: `python`
   - Arguments: `main.py check`
   - Start in: `C:\path\to\project`

**Option C: Linux/Mac Cron**
```bash
crontab -e
```

Add:
```
30 12 * * * cd /path/to/project && python main.py check
10 21 * * * cd /path/to/project && python main.py check
```

## 📋 Configuration Tips

### Adjust Thresholds

Edit `.env`:
```
MIN_JACKPOT_THRESHOLD=1000000    # Only alert if jackpot >= $1M
JACKPOT_STEP_INCREMENT=100000     # Alert every $100K increase
EV_THRESHOLD=-0.10                # Buy signal when EV >= -$0.10
```

### Enable/Disable Games

Edit `config.json`:
```json
{
  "lottery_games": {
    "lucky_day_lotto_evening": {
      "enabled": true,
      ...
    },
    "powerball": {
      "enabled": false,  // Disable Powerball
      ...
    }
  }
}
```

### Enable Purchase Automation

⚠️ **Warning**: This opens a browser and navigates to purchase pages. Always review before purchasing!

Edit `.env`:
```
ENABLE_PURCHASE_AUTOMATION=true
BROWSER_TYPE=chromium
```

## 🐛 Troubleshooting

### "TELEGRAM_BOT_TOKEN must be provided"
- Make sure `.env` file exists and contains your token
- Check that token doesn't have extra spaces

### "Failed to fetch jackpot"
- Illinois Lottery website may have changed structure
- Check `lottery_assistant.log` for details
- You may need to update selectors in `src/jackpot_monitor.py`

### Browser automation not working
- Run: `python -m playwright install`
- Check browser type in `.env` (chromium/firefox/webkit)

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [PROJECT_SPEC.md](PROJECT_SPEC.md) for feature details
- Customize `config.json` for your preferences
- Check logs in `lottery_assistant.log`

## ⚠️ Important Notes

- This tool is for informational purposes only
- Always gamble responsibly
- Purchase automation stops at checkout - manual payment required
- Comply with all local laws and regulations

---

**Need Help?** Check the logs: `lottery_assistant.log`
