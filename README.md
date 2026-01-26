# Lottery Assistant + Telegram Bot + Web Automation

A comprehensive lottery monitoring and purchase-assist system for Illinois Lottery games. Monitors jackpots, calculates expected value, sends Telegram alerts, and optionally assists with purchase automation.

## Features

### Core Functionality
- ✅ **Jackpot Monitoring**: Automatically monitors Illinois Lottery jackpots (Lucky Day Lotto, Powerball, Mega Millions)
- ✅ **Threshold Alerts**: Per-game configurable threshold-based alerts via Telegram
- ✅ **Expected Value Calculation**: Computes EV for lottery tickets with tax and lump sum adjustments
- ✅ **Buy Signal Logic**: Sends alerts when EV thresholds are met
- ✅ **Telegram Integration**: Full Telegram bot support with interactive commands (`/status`, `/help`)
- ✅ **State Persistence**: Tracks jackpot history and threshold states
- ✅ **Web Automation**: Optional Playwright-based purchase assistance
- ✅ **Web Dashboard**: Beautiful visual dashboard for monitoring jackpots and EV

### Advanced Features
- 📊 EV analysis with secondary prize consideration
- 🎯 Break-even jackpot calculations
- 📈 Historical threshold tracking
- 🔄 Automated scheduling (Windows Task Scheduler support)
- 🛒 Purchase flow automation (stops at checkout for manual payment)
- 🎨 Modern web dashboard with real-time updates
- 📱 Interactive Telegram bot commands

## Installation

### Prerequisites
- Python 3.8+
- Node.js (for Playwright browser binaries)

### Setup Steps

1. **Clone or download the project**

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers** (if using automation)
   ```bash
   python -m playwright install
   ```

4. **Configure environment variables**
   ```bash
   # Windows PowerShell
   Copy-Item env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```
   
   Edit `.env` and add your Telegram bot credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

5. **Configure game settings** (optional)
   Edit `config.json` to enable/disable games and adjust settings.

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token (required) | - |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID (required) | - |
| `MIN_JACKPOT_THRESHOLD` | Minimum jackpot to monitor | 500000 |
| `JACKPOT_STEP_INCREMENT` | Increment for threshold alerts | 50000 |
| `EV_THRESHOLD` | Minimum EV to trigger buy signal | -0.20 |
| `ENABLE_PURCHASE_AUTOMATION` | Enable web automation | false |
| `BROWSER_TYPE` | Browser for automation (chromium/firefox/webkit) | chromium |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |

### Config File (config.json)

The `config.json` file contains:
- **lottery_games**: Game configurations (odds, costs, draw times)
- **alert_settings**: Alert frequency and cooldown settings
- **ev_settings**: Tax rates and lump sum factors
- **automation_settings**: Browser automation preferences
- **persistence**: File paths for state and logs

## Usage

### Running Tests
Test all components (Telegram, web scraping, etc.):
```bash
python main.py test
```

### Single Check
Run a one-time jackpot check:
```bash
python main.py check
```

### Telegram Bot Commands
Start interactive Telegram bot with command support:
```bash
python main.py bot
```

Then in Telegram, send:
- `/status` - Get current jackpot status for all games
- `/help` - Show available commands
- `/start` - Start the bot

### Web Dashboard
Start the web dashboard:
```bash
python dashboard.py
```

Then open http://localhost:5000 in your browser to see:
- Current jackpots for all games
- EV calculations and indicators
- Threshold status
- Recent alerts history

### Scheduled Monitoring
Start continuous monitoring with Python scheduler:
```bash
python main.py schedule
```

**Recommended**: Use Windows Task Scheduler instead (see below)

### Windows Task Scheduler Setup (Recommended)

**Automatic Setup:**
```powershell
# Run PowerShell as Administrator
.\setup_windows_scheduler.ps1
```

**Manual Setup:**
See `HOME_MACHINE_SETUP.md` or `SCHEDULER_SETUP.md` for detailed instructions.

The scheduler automatically creates tasks for:
- LDL Midday: 12:10 PM, 12:50 PM (Daily)
- LDL Evening: 8:52 PM, 9:32 PM (Daily)
- Powerball: 9:29 PM, 10:09 PM (Mon/Wed/Sat)
- Mega Millions: 9:30 PM, 10:10 PM (Tue/Fri)

### Linux/Mac Cron Setup

Add to crontab (`crontab -e`):
```
30 12 * * * cd /path/to/project && python main.py check
10 21 * * * cd /path/to/project && python main.py check
```

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── telegram_notifier.py      # Telegram bot messaging
│   ├── jackpot_monitor.py        # Web scraping for jackpots
│   ├── threshold_alert.py        # Threshold logic and alerts
│   ├── ev_calculator.py          # Expected value calculations
│   ├── purchase_automation.py    # Playwright automation
│   └── lottery_assistant.py      # Main orchestrator
├── main.py                        # Entry point
├── config.json                    # Configuration file
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## How It Works

1. **Monitoring**: The system periodically checks Illinois Lottery website for current jackpot values
2. **Threshold Detection**: Compares current jackpot to configured thresholds
3. **EV Calculation**: Computes expected value considering taxes, lump sum, and secondary prizes
4. **Alerting**: Sends Telegram notifications when thresholds are hit or buy signals are triggered
5. **Automation** (optional): Opens browser and pre-fills purchase flow, stopping at checkout

## Legal & Compliance

⚠️ **Important**: This tool is for informational purposes only. The purchase automation feature:
- Does NOT auto-submit payments
- Does NOT bypass geolocation or identity verification
- Requires manual confirmation at checkout
- Stops before payment submission

Always comply with local laws and lottery regulations. Use at your own risk.

## Troubleshooting

### Telegram Bot Not Working
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Test bot token with: `curl https://api.telegram.org/bot<TOKEN>/getMe`
- Ensure bot is started: Send `/start` to your bot

### Jackpot Scraping Fails
- Illinois Lottery website structure may have changed
- Check `lottery_assistant.log` for errors
- May need to update selectors in `jackpot_monitor.py`

### Browser Automation Issues
- Ensure Playwright browsers are installed: `playwright install`
- Check browser type setting in `.env`
- Verify website is accessible

## Future Enhancements

- [x] Dashboard web UI ✅ (Flask-based, complete!)
- [ ] SQLite/Postgres database for historical data
- [ ] Multi-state lottery support
- [ ] Advanced analytics and trends (charts, graphs)
- [ ] Mobile app integration
- [ ] Rollover count tracking
- [ ] Draw outcome tracking
- [ ] Historical jackpot charts in dashboard

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - Use at your own discretion and comply with all applicable laws.

## Support

For issues or questions:
1. Check the logs: `lottery_assistant.log`
2. Review configuration files
3. Test individual components: `python main.py test`

---

**Disclaimer**: This software is provided as-is for educational and informational purposes. Always gamble responsibly and within your means.
