# Dashboard UI - Lottery Assistant

## Overview

A beautiful, modern web dashboard that visualizes all important lottery data in real-time.

## Features

### Visual Display
- **Current Jackpots** - Large, easy-to-read jackpot amounts
- **EV Indicators** - Color-coded badges (✅ Positive / ⚠️ Warning / ❌ Negative)
- **Change Tracking** - Shows jackpot changes with up/down arrows
- **Threshold Status** - Displays threshold configuration and alert history
- **Recent Alerts** - Shows last 50 threshold alerts

### Key Metrics Per Game
- Current Jackpot
- Change from last check (amount & percentage)
- Net Expected Value (EV)
- EV Percentage
- Ticket Cost
- Odds
- Break-Even Jackpot
- Threshold Information
- Draw Times

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Dashboard
```bash
python dashboard.py
```

### 3. Open in Browser
Navigate to: **http://localhost:5000**

## Configuration

### Environment Variables
- `DASHBOARD_PORT` - Port to run on (default: 5000)
- `DASHBOARD_DEBUG` - Enable debug mode (default: false)
- `LOTTERY_STATE_FILE` - Path to state file (default: lottery_state.json)
- `CONFIG_FILE` - Path to config file (default: config.json)

### Example:
```bash
# Windows PowerShell
$env:DASHBOARD_PORT=8080
$env:DASHBOARD_DEBUG="true"
python dashboard.py
```

## Features

### Real-Time Updates
- Auto-refreshes every 60 seconds
- Manual refresh button
- Live timestamp display

### Responsive Design
- Works on desktop, tablet, and mobile
- Grid layout adapts to screen size
- Modern, clean UI with smooth animations

### Color-Coded Status
- **Green (✅)**: Positive EV - Good to buy
- **Yellow (⚠️)**: Near break-even - Consider buying
- **Red (❌)**: Negative EV - Not recommended

## API Endpoints

### `/api/status`
Returns current status of all games:
```json
{
  "timestamp": "2026-01-26T13:00:00",
  "games": {
    "lucky_day_lotto_midday": {
      "name": "Lucky Day Lotto Midday",
      "current_jackpot": 350000,
      "net_ev": -0.67,
      "is_positive_ev": false,
      ...
    }
  }
}
```

### `/api/history`
Returns recent threshold alerts:
```json
{
  "history": [
    {
      "game_name": "Mega Millions",
      "threshold": 100000000,
      "jackpot": 285000000,
      "timestamp": "2026-01-26T12:57:59"
    }
  ]
}
```

### `/api/config`
Returns current configuration

## Screenshots

The dashboard displays:
- **Game Cards** - One card per game with all key metrics
- **History Section** - Recent threshold alerts
- **Auto-Refresh** - Updates every 60 seconds
- **Responsive** - Works on all screen sizes

## Troubleshooting

### Dashboard won't start
- Check if port 5000 is already in use
- Verify Flask is installed: `pip install flask`
- Check Python version (3.8+)

### No data showing
- Ensure `lottery_state.json` exists
- Run `python main.py check` first to populate data
- Check browser console for errors

### Stale data
- Click refresh button
- Check if backend is running
- Verify state file is being updated

## Development

### Running in Debug Mode
```bash
$env:DASHBOARD_DEBUG="true"
python dashboard.py
```

### Customizing
- Edit `templates/dashboard.html` for UI changes
- Edit `dashboard.py` for API/logic changes
- CSS is embedded in HTML for simplicity

## Future Enhancements

- [ ] Historical jackpot charts
- [ ] EV trend graphs
- [ ] Rollover count tracking
- [ ] Draw time countdown
- [ ] Export data to CSV
- [ ] Dark mode toggle
- [ ] Real-time WebSocket updates

---

**Status**: ✅ Ready to use!
**Port**: 5000 (default)
**URL**: http://localhost:5000
