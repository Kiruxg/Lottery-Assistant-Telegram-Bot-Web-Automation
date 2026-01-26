# Dashboard Troubleshooting

## Issue: No Data Appears on First Load

### Solution 1: Run a Check First (Recommended)

The dashboard loads data from `lottery_state.json`. If this file is empty or doesn't exist, you need to populate it first:

```bash
python main.py check
```

This will:
- Fetch current jackpots
- Update the state file
- Send Telegram messages

Then refresh the dashboard - data should appear!

### Solution 2: Use Refresh Button

Click the **"Refresh (Fetch Latest)"** button in the dashboard. This will:
- Run a full check (takes 10-20 seconds)
- Update the state file
- Display the latest data

### Solution 3: Check State File

Verify `lottery_state.json` exists and has data:

```powershell
# Check if file exists
Test-Path "lottery_state.json"

# View contents
Get-Content "lottery_state.json" | ConvertFrom-Json | ConvertTo-Json
```

---

## Common Issues

### Dashboard Shows "Loading..." Forever

**Cause**: API endpoint is failing or taking too long

**Fix**:
1. Check browser console (F12) for errors
2. Check Flask server logs for errors
3. Verify `.env` file exists with Telegram credentials
4. Try the refresh button

### Dashboard Shows "No game data available"

**Cause**: State file is empty or no games are enabled

**Fix**:
1. Run `python main.py check` to populate data
2. Check `config.json` - ensure games have `"enabled": true`
3. Click "Refresh (Fetch Latest)" button

### Dashboard Loads But Shows $0.00 for All Games

**Cause**: State file exists but has no jackpot data

**Fix**:
1. Run `python main.py check` to fetch current jackpots
2. This will update `lottery_state.json` with real data

### Error: "Error loading data: ..."

**Cause**: Backend error (missing config, API failure, etc.)

**Fix**:
1. Check Flask terminal for error messages
2. Verify `config.json` exists and is valid JSON
3. Verify `.env` file exists
4. Check `lottery_assistant.log` for details

---

## Quick Fix Checklist

1. ✅ Run `python main.py check` first
2. ✅ Verify `lottery_state.json` has data
3. ✅ Check `config.json` has games enabled
4. ✅ Verify Flask server is running
5. ✅ Check browser console (F12) for errors
6. ✅ Try refresh button

---

## How Dashboard Works

### Fast Load (Default)
- Reads from `lottery_state.json` (instant)
- Shows last known jackpot values
- Calculates EV from stored data
- No web scraping (fast!)

### Refresh (Button Click)
- Runs full check (`python main.py check`)
- Fetches latest jackpots from website
- Updates state file
- Takes 10-20 seconds (web scraping)

### Auto-Refresh
- Every 60 seconds, reloads from state file
- Fast (no web scraping)
- Use refresh button to get latest data

---

## First Time Setup

1. **Start Flask server:**
   ```bash
   python dashboard.py
   ```

2. **In another terminal, populate data:**
   ```bash
   python main.py check
   ```

3. **Open dashboard:**
   Navigate to http://localhost:5000

4. **Data should appear!** ✅

---

## Still Not Working?

1. Check Flask terminal output for errors
2. Check browser console (F12 → Console tab)
3. Verify files exist:
   - `config.json`
   - `lottery_state.json`
   - `.env`
4. Test API directly:
   ```bash
   curl http://localhost:5000/api/status
   ```
