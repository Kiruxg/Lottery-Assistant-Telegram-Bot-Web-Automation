# How to Start the Dashboard

## ⚠️ Important: Don't Open HTML File Directly!

The dashboard **must** be run through Flask. Opening `dashboard.html` directly in a browser will cause 404 errors.

## ✅ Correct Way to Start Dashboard

### Step 1: Start Flask Server

Open a terminal in the project directory and run:

```bash
python dashboard.py
```

You should see:
```
🎰 Starting Lottery Assistant Dashboard on http://localhost:5000
 * Running on http://127.0.0.1:5000
```

### Step 2: Open in Browser

**Do NOT** open the HTML file directly. Instead:

1. Open your web browser
2. Navigate to: **http://localhost:5000**
3. The dashboard should load!

### Step 3: (Optional) Populate Data First

If you see "No game data available", run this in another terminal:

```bash
python main.py check
```

This will fetch current jackpots and populate the state file.

---

## ❌ Common Mistakes

### Wrong: Opening HTML File Directly
- ❌ Double-clicking `dashboard.html`
- ❌ Opening with Live Server (port 5500)
- ❌ Opening with "Open with Browser"

**Result**: 404 errors, API calls fail

### Right: Running Flask Server
- ✅ Run `python dashboard.py` first
- ✅ Then open `http://localhost:5000` in browser

**Result**: Dashboard works perfectly!

---

## 🔧 Troubleshooting

### Error: "HTTP 404: Not Found"
**Cause**: Flask server is not running

**Fix**: 
1. Make sure `python dashboard.py` is running
2. Check terminal for errors
3. Verify you're accessing `http://localhost:5000` (not 5500)

### Error: "ModuleNotFoundError: No module named 'flask'"
**Cause**: Flask not installed

**Fix**:
```bash
pip install flask
```

### Dashboard Shows "No game data available"
**Cause**: State file is empty

**Fix**:
```bash
# In another terminal
python main.py check
```

Then refresh the dashboard.

---

## 📋 Quick Checklist

- [ ] Flask is installed: `pip install flask`
- [ ] Flask server is running: `python dashboard.py`
- [ ] Browser shows: `http://localhost:5000` (not 5500)
- [ ] Data exists: Run `python main.py check` if needed

---

**Remember**: Always run `python dashboard.py` first, then open `http://localhost:5000`!
