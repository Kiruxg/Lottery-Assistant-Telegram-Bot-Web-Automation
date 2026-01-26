# Automated Scheduling Setup Guide

## Overview

The Lottery Assistant can be scheduled to automatically check jackpots and send Telegram messages at strategic times around draw schedules.

## Draw Times

Based on your `config.json`:
- **Lucky Day Lotto Midday**: 12:40 PM (Daily)
- **Lucky Day Lotto Evening**: 9:22 PM (Daily)
- **Powerball**: 9:59 PM (Monday, Wednesday, Saturday)
- **Mega Millions**: 10:00 PM (Tuesday, Friday)

## Scheduling Strategy

Checks are scheduled at:
- **30 minutes before draw** - Final check before draw closes
- **10 minutes after draw** - Check updated jackpot after draw

## Implementation Options

### Option 1: Windows Task Scheduler (Recommended for Windows)

**Best for:**
- ✅ Runs even when Python script isn't running
- ✅ Survives reboots automatically
- ✅ Built into Windows (no dependencies)
- ✅ Can run in background without terminal

**Setup:**

1. **Automatic Setup (PowerShell as Administrator):**
   ```powershell
   .\setup_windows_scheduler.ps1
   ```

2. **Manual Setup:**
   - Open Task Scheduler (`taskschd.msc`)
   - Create Basic Task
   - Name: "Lottery Check - [Game] - [Time]"
   - Trigger: Daily/Weekly at specific time
   - Action: Start a program
   - Program: `python` (or full path to Python.exe)
   - Arguments: `"C:\path\to\main.py" check`
   - Start in: `C:\path\to\project\`

**View Scheduled Tasks:**
```powershell
Get-ScheduledTask -TaskName "LotteryCheck_*"
```

**Remove Tasks:**
```powershell
Get-ScheduledTask -TaskName "LotteryCheck_*" | Unregister-ScheduledTask
```

---

### Option 2: Python Scheduler (Development/Testing)

**Best for:**
- ✅ Easy to test and modify
- ✅ No admin rights needed
- ✅ Good for development

**Limitations:**
- ❌ Requires Python script to be running continuously
- ❌ Stops if computer sleeps/reboots
- ❌ Needs terminal/background process

**Usage:**
```bash
python main.py schedule
```

This starts a Python scheduler that runs checks at configured times. Keep the terminal open or run as a background service.

**Run as Background Service (Windows):**
```powershell
# Create a scheduled task to start the scheduler on boot
$action = New-ScheduledTaskAction -Execute "python" -Argument "`"$PWD\main.py`" schedule" -WorkingDirectory $PWD
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "LotteryAssistantScheduler" -Action $action -Trigger $trigger -Description "Lottery Assistant Python Scheduler"
```

---

### Option 3: Cron (Linux/Mac)

**Best for:**
- ✅ Linux/Mac systems
- ✅ Standard Unix tool
- ✅ Very reliable

**Setup:**

1. Edit crontab:
   ```bash
   crontab -e
   ```

2. Add entries (adjust paths):
   ```
   # Lucky Day Lotto Midday - 30min before (12:10) and 10min after (12:50)
   10 12 * * * cd /path/to/project && /usr/bin/python3 main.py check
   50 12 * * * cd /path/to/project && /usr/bin/python3 main.py check

   # Lucky Day Lotto Evening - 30min before (20:52) and 10min after (21:32)
   52 20 * * * cd /path/to/project && /usr/bin/python3 main.py check
   32 21 * * * cd /path/to/project && /usr/bin/python3 main.py check

   # Powerball - 30min before (21:29) and 10min after (22:09) - Mon, Wed, Sat
   29 21 * * 1,3,6 cd /path/to/project && /usr/bin/python3 main.py check
   9 22 * * 1,3,6 cd /path/to/project && /usr/bin/python3 main.py check

   # Mega Millions - 30min before (21:30) and 10min after (22:10) - Tue, Fri
   30 21 * * 2,5 cd /path/to/project && /usr/bin/python3 main.py check
   10 22 * * 2,5 cd /path/to/project && /usr/bin/python3 main.py check
   ```

---

## Recommended Schedule Times

Based on draw times, here are the recommended check times:

| Game | Draw Time | Check 1 (Before) | Check 2 (After) |
|------|-----------|------------------|-----------------|
| LDL Midday | 12:40 PM | 12:10 PM | 12:50 PM |
| LDL Evening | 9:22 PM | 8:52 PM | 9:32 PM |
| Powerball | 9:59 PM (Mon/Wed/Sat) | 9:29 PM | 10:09 PM |
| Mega Millions | 10:00 PM (Tue/Fri) | 9:30 PM | 10:10 PM |

## Verification

After setup, verify scheduling:

1. **Check next scheduled run:**
   - Windows: Task Scheduler → View scheduled tasks
   - Python: Check logs when `schedule` command runs
   - Cron: `crontab -l`

2. **Test manually:**
   ```bash
   python main.py check
   ```

3. **Check logs:**
   - View `lottery_assistant.log` for scheduled check results
   - Check Telegram for received messages

## Troubleshooting

### Windows Task Scheduler Issues

**Task not running:**
- Check task is enabled
- Verify Python path is correct
- Check "Run whether user is logged on or not"
- Check task history for errors

**Permission errors:**
- Run PowerShell as Administrator
- Check task "Run with highest privileges"

### Python Scheduler Issues

**Script stops:**
- Ensure terminal stays open
- Use `nohup` (Linux) or background service (Windows)
- Check for errors in logs

**Time zone issues:**
- Verify system time zone is correct
- Python scheduler uses system time

## Best Practice Recommendation

**For Production (Windows):**
👉 Use **Windows Task Scheduler** - Most reliable, runs independently

**For Development:**
👉 Use **Python Scheduler** - Easy to test and modify

**For Linux/Mac:**
👉 Use **Cron** - Standard and reliable

---

## Quick Start

**Windows (Recommended):**
```powershell
# Run as Administrator
.\setup_windows_scheduler.ps1
```

**Python Scheduler:**
```bash
python main.py schedule
```

**View Schedule:**
```bash
python -c "from src.scheduler import LotteryScheduler; s = LotteryScheduler(); print(s.get_schedule_summary())"
```
