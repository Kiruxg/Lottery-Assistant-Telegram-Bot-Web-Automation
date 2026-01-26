# Fixing 403 Forbidden Errors

## Problem
The Illinois Lottery website is returning `403 Forbidden` errors when trying to scrape jackpot data.

## Solutions

### Solution 1: Enhanced Headers (Already Applied)
I've updated the scraper with better browser headers to mimic a real browser. This should help in many cases.

### Solution 2: Use Playwright for Scraping
If you're still getting 403 errors, enable Playwright-based scraping:

1. **Edit your `.env` file:**
   ```
   USE_PLAYWRIGHT_SCRAPING=true
   ```

2. **Run the check again:**
   ```powershell
   python main.py check
   ```

Playwright uses a real browser engine and can handle:
- JavaScript-rendered content
- Anti-bot protection
- Cloudflare challenges
- Dynamic content loading

### Solution 3: Manual Testing
Test if the website is accessible:

```powershell
# Test basic connection
python -c "import requests; r = requests.get('https://www.illinoislottery.com'); print(f'Status: {r.status_code}')"
```

### Solution 4: Check Website Structure
The website structure may have changed. You may need to:
1. Visit the website manually in a browser
2. Inspect the page source
3. Update selectors in `src/jackpot_monitor.py`

## Current Status

The scraper now:
- ✅ Uses enhanced browser headers
- ✅ Has Playwright fallback option
- ✅ Automatically falls back to Playwright if requests fails

## Next Steps

1. **Try running the check again** - the enhanced headers might work now
2. **If still getting 403**, enable Playwright in `.env`
3. **If Playwright also fails**, the website structure may need manual inspection

## Alternative: Use Lottery API (if available)

Some states provide official APIs. Check if Illinois Lottery has an API endpoint you can use instead of scraping.
