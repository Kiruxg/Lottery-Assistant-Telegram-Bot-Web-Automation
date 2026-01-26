# Alert Scheduling Update

## ✅ Changes Made

### 1. **Game-Specific Scheduling**
- Alerts now only send around the time of draws per game (when thresholds are met)
- Each scheduled task checks only its specific game
- Alerts are restricted to within 60 minutes of draw time

### 2. **Buy Signal in Status Messages**
- Status messages now include EV information and buy signals
- Format:
  - ✅ **BUY SIGNAL** - Positive EV: $X.XX (XX.XX%)
  - ⚠️ **BUY SIGNAL** - Near Break-Even: $X.XX (XX.XX%)
  - 📊 Net EV: $X.XX (XX.XX%) (if not a buy signal)

### 3. **Smart Alert Timing**
- `only_near_draw` parameter controls whether alerts are sent only near draw times
- Scheduled checks (via scheduler) use `only_near_draw=True` by default
- Manual checks (`python main.py check`) use `only_near_draw=False` to show all data

## 📋 How It Works

### Scheduled Checks (Automated)
When tasks run via scheduler:
1. **Checks specific game** at its scheduled time (30min before or 10min after draw)
2. **Only sends alerts/status** if within 60 minutes of draw time
3. **Includes buy signal** in status message if EV threshold is met

### Manual Checks
When you run `python main.py check`:
- Checks all enabled games
- Sends status messages regardless of draw time
- Useful for testing or manual updates

### Game-Specific Manual Check
When you run `python main.py check <game_id>`:
- Checks only the specified game
- Example: `python main.py check powerball`

## 🎯 Example Status Messages

### With Buy Signal (Positive EV)
```
🎰 Powerball

💰 Current Jackpot: $1,500,000,000.00
✅ BUY SIGNAL - Positive EV: $0.50 (25.00%)
⏰ Time: 2026-01-26 21:29:00
```

### With Buy Signal (Near Break-Even)
```
🎰 Mega Millions

💰 Current Jackpot: $1,400,000,000.00
⚠️ BUY SIGNAL - Near Break-Even: $-0.15 (-7.50%)
⏰ Time: 2026-01-26 21:30:00
```

### Without Buy Signal
```
🎰 Lucky Day Lotto Midday

💰 Current Jackpot: $350,000.00
📊 Net EV: $-0.67 (-66.64%)
⏰ Time: 2026-01-26 12:10:00
```

## ⚙️ Configuration

### Draw Time Window
The `_is_near_draw_time()` method checks if current time is within 60 minutes of draw time. This can be adjusted by modifying the `window_minutes` parameter.

### EV Threshold
Buy signals are triggered when:
- Net EV >= `EV_THRESHOLD` (default: -$0.20)
- Or Net EV > 0 (positive EV)

Configure via `.env`:
```
EV_THRESHOLD=-0.20
```

## 📅 Scheduled Check Times

Based on draw times in `config.json`:

| Game | Draw Time | Check Times | Alert Window |
|------|-----------|-------------|--------------|
| **Lucky Day Lotto Midday** | 12:40 PM | 12:10 PM, 12:50 PM | 11:40 AM - 1:40 PM |
| **Lucky Day Lotto Evening** | 9:22 PM | 8:52 PM, 9:32 PM | 8:22 PM - 10:22 PM |
| **Powerball** | 9:59 PM | 9:29 PM, 10:09 PM | 8:59 PM - 10:59 PM |
| **Mega Millions** | 10:00 PM | 9:30 PM, 10:10 PM | 9:00 PM - 11:00 PM |

**Note:** Alerts only send if:
1. Scheduled check runs at the scheduled time
2. Current time is within 60 minutes of draw time
3. Threshold is met (for threshold alerts)
4. EV threshold is met (for buy signals)

## 🔧 Technical Details

### Modified Files
1. **`src/lottery_assistant.py`**
   - Added `_is_near_draw_time()` method
   - Updated `check_jackpots()` to accept `game_id_filter` and `only_near_draw` parameters
   - Enhanced status messages with EV and buy signal info

2. **`main.py`**
   - Updated `run_check()` to accept `game_id` and `only_near_draw` parameters
   - Modified scheduler to pass `game_id` to each scheduled check
   - Updated command-line handling for game-specific checks

### Key Methods

#### `_is_near_draw_time(game_id, window_minutes=60)`
Checks if current time is within the specified window of the game's draw time.

#### `check_jackpots(game_id_filter=None, only_near_draw=False)`
- `game_id_filter`: If provided, only check this game
- `only_near_draw`: If True, only send alerts/status if near draw time

## 🚀 Usage

### Automated (Scheduled)
```bash
python main.py schedule
```
Runs continuously, checking games at their scheduled times. Alerts only sent near draw times.

### Manual (All Games)
```bash
python main.py check
```
Checks all games and sends status messages regardless of draw time.

### Manual (Specific Game)
```bash
python main.py check powerball
```
Checks only Powerball and sends status message.

## ✅ Benefits

1. **Reduced Noise**: Alerts only sent when relevant (near draw times)
2. **Better Information**: Status messages include EV and buy signals
3. **Game-Specific**: Each game checked independently at its draw time
4. **Flexible**: Manual checks still work for testing/updates
