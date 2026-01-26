# 📄 PROJECT SPEC: Lottery Assistant + Telegram Bot + Web Automation

## 1. Project Summary

Build a Lottery Monitoring & Purchase-Assist system that:

- Monitors Illinois lottery jackpots
- Computes alerts and decision logic
- Sends notifications via Telegram bot
- Optionally pre-fills purchase flows on the Illinois Lottery website
- Provides future expansion points (dashboard, EV analysis, multi-game tracking)

## 2. Core Components

### 2.1 Telegram Notification Module

- Use Telegram Bot API for outbound messaging
- Configurable chat_id and bot_token
- Must support:
  - Text messages
  - Status alerts
  - Error alerts
  - Queue or immediate send options

### 2.2 Jackpot Monitoring Module

Fetch jackpot values for:
- Lucky Day Lotto (midday & evening)
- Powerball (optional)
- Mega Millions (optional)

Data sources:
- Scrape official IL Lottery site OR
- Use external APIs if available

Should provide:
- Current jackpot value
- Draw schedule awareness
- Last winning numbers (optional)
- Rollover history (optional)

### 2.3 Threshold Alert Logic

User-defined threshold rules:
- Minimum jackpot (e.g., $500,000)
- Step increments (e.g., +$50,000)

Should maintain state:
- Last threshold hit
- Timestamp of last alert

Should send Telegram message when new threshold is hit

## 3. Advanced Logic / Analytics

### 3.1 Expected Value (EV) Computation

Inputs:
- Jackpot
- Odds of winning
- Ticket cost
- Secondary prize EV (optional)

Output:
- EV per play
- Negative/positive EV indicator

### 3.2 Purchase Decision Logic

Configurable conditions:
- EV threshold (e.g., EV ≥ -$0.20)
- Jackpot threshold
- Rollover count threshold

Sends "Buy Signal" via Telegram when conditions met

## 4. Purchase Assist Features

### 4.1 Web Purchase Automation (Optional)

Use Playwright or Puppeteer for automation

Workflow:
1. Navigate to IL Lottery website
2. Select game (e.g., Lucky Day Lotto)
3. Select quick pick
4. Add to cart
5. Stop at checkout page for manual payment

Legal compliance:
- Do NOT auto-submit payment
- Do NOT bypass geolocation or identity checks

### 4.2 Browser Launch Mode

On "Buy Signal," automation can:
- Auto-open browser in correct game page
- Auto-fill game options
- Wait for user confirmation

Browser should be configurable:
- Chrome / Edge / Chromium / Firefox

## 5. Scheduling & Execution

### 5.1 Task Scheduling

Support:
- Windows Task Scheduler
- Cron (optional)
- Manual run

Suggested schedule:
- Twice per day (around draw times)

### 5.2 State Persistence

Storage options:
- Local file (initial)
- SQLite (upgrade path)
- Redis (future)

Must store:
- Last jackpot value per game
- Last threshold hit
- Historic EV (optional)
- Error logs

## 6. Error Handling & Logging

Error cases:
- Website unreachable
- Parsing failures
- Data format changes
- Telegram API errors
- Web automation timeouts

Logging levels:
- INFO: routine checks
- ALERT: new threshold hit
- ERROR: failures

Output targets:
- Console (initial)
- Log file (optional)
- Telegram error channel (optional)

## 7. Configuration System

### 7.1 .env or Environment Variables

Variables to support:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `MIN_JACKPOT_THRESHOLD`
- `JACKPOT_STEP_INCREMENT`
- `ENABLE_PURCHASE_AUTOMATION`
- `BROWSER_TYPE`
- `RUN_MODE` (production/development)

### 7.2 Config File Support (config.json)

Properties:
- lottery list
- EV settings
- alert schedules
- browser prefs
- legal safety toggles

## 8. Optional Expansion Modules

### 8.1 Dashboard / Web UI

Small Flask/FastAPI API backend
Frontend: React / Next.js / Svelte

Shows:
- Current jackpots
- Last thresholds
- EV metrics
- Rollover history

### 8.2 Multi-Lottery Support

Games to consider:
- Illinois Lucky Day Lotto
- Powerball
- Mega Millions
- Lotto (IL)
- Pick 3 / Pick 4 (optional)

### 8.3 Data Persistence

SQLite or Postgres for:
- Historical jackpots
- EV trends
- Draw outcomes

### 8.4 Mobile App Integration

Use Telegram for push
Or future PWA mobile interface

## 9. Tech Stack Recommendations

### Baseline MVP
- Language: Python or Node.js
- Telegram: direct Telegram Bot API
- Scraping: requests + BeautifulSoup (Python) or axios + cheerio (Node)
- Automation: Playwright (preferred) or Puppeteer

### Upgrade Path
- Persistence: SQLite → Postgres
- Scheduler: cron / cloud scheduler
- Dashboard: FastAPI + React
- Deployment: Docker + Fly.io / Render / Railway

## 10. Deliverables

### MVP deliverables:
- ✅ Telegram bot that alerts on jackpot thresholds
- ✅ Jackpot scraping module
- ✅ State persistence for thresholds
- ✅ Scheduler instructions (Windows + cron)
- ✅ README documentation

### Advanced deliverables:
- ✅ EV calculation engine
- ✅ Buy Signal logic
- ✅ Purchase automation script (browser setup)
- ⏳ Dashboard UI (future)

---

✔️ End of Spec
