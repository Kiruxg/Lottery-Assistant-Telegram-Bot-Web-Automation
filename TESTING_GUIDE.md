# Testing Guide - Alert Scheduling & Buy Signals

## ✅ What Should Happen Now

### 1. **Status Messages Include EV/Buy Signal**
Every status message should now show:
- **If buy signal (positive EV or near break-even):**
  ```
  🎰 Powerball
  
  💰 Current Jackpot: $1,500,000,000.00
  ✅ BUY SIGNAL - Positive EV: $0.50 (25.00%)
  ⏰ Time: 2026-01-26 21:29:00
  ```

- **If not a buy signal:**
  ```
  🎰 Lucky Day Lotto Midday
  
  💰 Current Jackpot: $350,000.00
  📊 Net EV: $-0.67 (-66.64%)
  ⏰ Time: 2026-01-26 12:10:00
  ```

### 2. **Alerts Only Near Draw Times**
When scheduled tasks run:
- ✅ Checks only the specific game
- ✅ Only sends alerts/status if within 60 minutes of draw time
- ✅ Includes buy signal in status message

### 3. **Manual Checks Show All Data**
When you run `python main.py check`:
- ✅ Checks all games
- ✅ Sends status messages regardless of draw time
- ✅ Always includes EV/buy signal info

## 🧪 How to Test

### Test 1: Manual Check (Should Show EV Info)
```bash
python main.py check
```
**Expected:** 4 status messages, each with EV/buy signal info

### Test 2: Game-Specific Check
```bash
python main.py check powerball
```
**Expected:** 1 status message for Powerball with EV info

### Test 3: Scheduled Check (Near Draw Time)
If you run a scheduled check within 60 minutes of draw time:
- ✅ Should send status message with EV info
- ✅ Should send threshold alert if threshold met
- ✅ Should send buy signal alert if EV threshold met

### Test 4: Scheduled Check (Far From Draw Time)
If you run a scheduled check more than 60 minutes from draw time:
- ❌ Should NOT send status message
- ❌ Should NOT send alerts
- ✅ Still updates state file (for tracking)

## 🔍 Troubleshooting

### Issue: Messages Don't Show EV Info
**Possible causes:**
1. Code changes not saved/reloaded
2. Running old version of code
3. Error in EV calculation

**Fix:**
- Verify code changes are saved
- Restart Python if running continuously
- Check logs for errors

### Issue: Alerts Sending When Not Near Draw Time
**Possible causes:**
1. `only_near_draw=False` being used
2. Draw time calculation error
3. Time zone issues

**Fix:**
- Check `main.py` - scheduled checks should use `only_near_draw=True`
- Verify draw times in `config.json` are correct
- Check system time zone

### Issue: No Alerts at All
**Possible causes:**
1. Not near draw time (if scheduled)
2. Thresholds not met
3. Telegram connection issue

**Fix:**
- Run manual check: `python main.py check` (should always send)
- Check thresholds in `config.json`
- Test Telegram: `python main.py test`

## 📋 Verification Checklist

- [ ] Status messages include EV/buy signal info
- [ ] Buy signals show for positive EV or near break-even
- [ ] Scheduled checks only send near draw times
- [ ] Manual checks always send (regardless of time)
- [ ] Game-specific checks work correctly
- [ ] Threshold alerts only send near draw times
- [ ] Buy signal alerts only send near draw times

## 🎯 Expected Behavior Summary

| Scenario | Status Message | Threshold Alert | Buy Signal Alert |
|----------|---------------|-----------------|------------------|
| **Scheduled (near draw)** | ✅ With EV | ✅ If threshold met | ✅ If EV threshold met |
| **Scheduled (far from draw)** | ❌ Not sent | ❌ Not sent | ❌ Not sent |
| **Manual check** | ✅ With EV | ✅ If threshold met | ✅ If EV threshold met |

---

**If messages in your screenshot don't match this, please run a fresh test:**
```bash
python main.py check
```

This should show the new format with EV/buy signal information!
