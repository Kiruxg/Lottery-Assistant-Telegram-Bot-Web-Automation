# Windows Task Scheduler Setup - Home Machine

## 📋 Prerequisites

1. Project is located at: `Desktop\Lottery Assistant + Telegram Bot + Web Automation`
2. Python is installed and working
3. `.env` file is configured with Telegram credentials
4. You have Administrator access

---

## 🚀 Method 1: Automatic Setup (Recommended)

### Step 1: Open PowerShell as Administrator

1. Press `Windows Key + X`
2. Select **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**
3. Click **"Yes"** when prompted by User Account Control

### Step 2: Navigate to Project Directory

```powershell
cd "C:\Users\YOUR_USERNAME\Desktop\Lottery Assistant + Telegram Bot + Web Automation"
```

**Replace `YOUR_USERNAME` with your actual Windows username**

Or if you're not sure of your username:
```powershell
cd $env:USERPROFILE\Desktop\"Lottery Assistant + Telegram Bot + Web Automation"
```

### Step 3: Verify Files Exist

```powershell
# Check that these files exist:
Test-Path "main.py"
Test-Path "config.json"
Test-Path ".env"
Test-Path "setup_windows_scheduler.ps1"
```

All should return `True`. If not, check your directory.

### Step 4: Run Setup Script

```powershell
.\setup_windows_scheduler.ps1
```

This will:
- ✅ Detect Python path automatically
- ✅ Create 8 scheduled tasks (one for each check time)
- ✅ Configure tasks to run at correct times
- ✅ Set up daily and weekly schedules

### Step 5: Verify Tasks Created

```powershell
Get-ScheduledTask -TaskName "LotteryCheck_*"
```

You should see 8 tasks listed.

### Step 6: Test One Task Manually

```powershell
# Run a task immediately to test
Start-ScheduledTask -TaskName "LotteryCheck_Lucky_Day_Lotto_Midday_1210"
```

Check Telegram for messages. If you get them, it's working! ✅

---

## 🔧 Method 2: Manual Setup (If Script Fails)

### Step 1: Open Task Scheduler

1. Press `Windows Key + R`
2. Type: `taskschd.msc`
3. Press Enter

### Step 2: Create First Task

1. Click **"Create Basic Task"** in the right panel
2. **Name**: `Lottery Check - LDL Midday - Before Draw`
3. **Description**: `30 minutes before Lucky Day Lotto Midday draw (12:40 PM)`
4. Click **Next**

### Step 3: Set Trigger

1. **Trigger**: Select **"Daily"**
2. Click **Next**
3. **Start**: `12:10 PM` (or today's date)
4. **Recur every**: `1 days`
5. Click **Next**

### Step 4: Set Action

1. **Action**: Select **"Start a program"**
2. Click **Next**
3. **Program/script**: Find your Python executable
   - Usually: `C:\Python312\python.exe` or `C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python312\python.exe`
   - Or type: `python` (if in PATH)
4. **Add arguments**: `"C:\Users\YOUR_USERNAME\Desktop\Lottery Assistant + Telegram Bot + Web Automation\main.py" check`
5. **Start in**: `C:\Users\YOUR_USERNAME\Desktop\Lottery Assistant + Telegram Bot + Web Automation`
6. Click **Next**

### Step 5: Configure Settings

1. Check **"Open the Properties dialog..."**
2. Click **Finish**
3. In Properties dialog:
   - **General tab**: Check **"Run whether user is logged on or not"**
   - **General tab**: Check **"Run with highest privileges"**
   - **Conditions tab**: Uncheck **"Start the task only if the computer is on AC power"** (if you want it to run on battery)
   - Click **OK**

### Step 6: Repeat for All Times

Create tasks for all these times:

| Game | Time | Days | Description |
|------|------|------|-------------|
| LDL Midday - Before | 12:10 PM | Daily | 30min before 12:40 draw |
| LDL Midday - After | 12:50 PM | Daily | 10min after 12:40 draw |
| LDL Evening - Before | 8:52 PM | Daily | 30min before 9:22 draw |
| LDL Evening - After | 9:32 PM | Daily | 10min after 9:22 draw |
| Powerball - Before | 9:29 PM | Mon, Wed, Sat | 30min before 9:59 draw |
| Powerball - After | 10:09 PM | Mon, Wed, Sat | 10min after 9:59 draw |
| Mega Millions - Before | 9:30 PM | Tue, Fri | 30min before 10:00 draw |
| Mega Millions - After | 10:10 PM | Tue, Fri | 10min after 10:00 draw |

**For weekly tasks (Powerball, Mega Millions):**
- Use **"Weekly"** trigger instead of Daily
- Select specific days (Monday/Wednesday/Saturday for Powerball, Tuesday/Friday for Mega Millions)

---

## ✅ Verification Checklist

After setup, verify:

### 1. Check Tasks Exist
```powershell
Get-ScheduledTask -TaskName "LotteryCheck_*" | Format-Table TaskName, State, LastRunTime
```

### 2. Check Next Run Time
```powershell
Get-ScheduledTask -TaskName "LotteryCheck_*" | ForEach-Object {
    $info = Get-ScheduledTaskInfo $_.TaskName
    [PSCustomObject]@{
        Task = $_.TaskName
        NextRun = $info.NextRunTime
        LastRun = $info.LastRunTime
    }
}
```

### 3. Test Manually
```powershell
# Test one task
Start-ScheduledTask -TaskName "LotteryCheck_Lucky_Day_Lotto_Midday_1210"

# Wait 30 seconds, then check Telegram
```

### 4. Check Task History
1. Open Task Scheduler
2. Click on a task
3. Click **"History"** tab at bottom
4. Look for recent runs and any errors

---

## 🔍 Finding Your Python Path

If you're not sure where Python is installed:

```powershell
# Method 1: Check PATH
where.exe python

# Method 2: Check common locations
Test-Path "C:\Python312\python.exe"
Test-Path "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
Test-Path "$env:PROGRAMFILES\Python312\python.exe"

# Method 3: Get from Python itself
python -c "import sys; print(sys.executable)"
```

---

## 📝 Quick Reference: All Scheduled Times

Copy-paste these into Task Scheduler:

### Daily Tasks (Lucky Day Lotto)
- **12:10 PM** - LDL Midday (30min before)
- **12:50 PM** - LDL Midday (10min after)
- **8:52 PM** - LDL Evening (30min before)
- **9:32 PM** - LDL Evening (10min after)

### Weekly Tasks

**Powerball (Mon, Wed, Sat):**
- **9:29 PM** - Powerball (30min before)
- **10:09 PM** - Powerball (10min after)

**Mega Millions (Tue, Fri):**
- **9:30 PM** - Mega Millions (30min before)
- **10:10 PM** - Mega Millions (10min after)

---

## 🛠️ Troubleshooting

### Task Not Running

1. **Check Task is Enabled:**
   ```powershell
   Get-ScheduledTask -TaskName "LotteryCheck_*" | Where-Object {$_.State -ne "Ready"}
   ```

2. **Check Last Run Result:**
   - Open Task Scheduler
   - Click on task → History tab
   - Look for error codes

3. **Common Issues:**
   - ❌ Python path incorrect → Fix in task properties
   - ❌ Working directory wrong → Fix in task properties
   - ❌ Missing `.env` file → Ensure `.env` exists in project folder
   - ❌ Permission denied → Run task with "highest privileges"

### Task Runs But No Messages

1. **Check Logs:**
   ```powershell
   Get-Content "lottery_assistant.log" -Tail 50
   ```

2. **Test Manually:**
   ```powershell
   cd "C:\Users\YOUR_USERNAME\Desktop\Lottery Assistant + Telegram Bot + Web Automation"
   python main.py check
   ```

3. **Verify `.env` file:**
   - Check `TELEGRAM_BOT_TOKEN` is set
   - Check `TELEGRAM_CHAT_ID` is set

### Task Shows "Last Run: Never"

- Task might not have triggered yet
- Check if current time is before scheduled time
- Manually trigger to test: `Start-ScheduledTask -TaskName "TASK_NAME"`

---

## 🗑️ Removing Tasks (If Needed)

To remove all scheduled tasks:

```powershell
Get-ScheduledTask -TaskName "LotteryCheck_*" | Unregister-ScheduledTask
```

To remove a specific task:

```powershell
Unregister-ScheduledTask -TaskName "LotteryCheck_Lucky_Day_Lotto_Midday_1210" -Confirm:$false
```

---

## 📋 Final Checklist

Before you're done, verify:

- [ ] All 8 tasks created
- [ ] Tasks are enabled (State = "Ready")
- [ ] Python path is correct
- [ ] Working directory is correct
- [ ] `.env` file exists and has credentials
- [ ] Tested one task manually
- [ ] Received Telegram message from test
- [ ] Next run times look correct

---

## 🎯 Expected Behavior

Once set up correctly:

1. **Tasks run automatically** at scheduled times
2. **Telegram messages sent** for each game
3. **No Python process needed** to be running
4. **Works after reboot** (Windows handles it)
5. **Runs in background** (no terminal needed)

---

## 💡 Pro Tips

1. **Test First**: Always test one task manually before relying on automation
2. **Check Logs**: Review `lottery_assistant.log` if something goes wrong
3. **Backup `.env`**: Keep a backup of your `.env` file (it's not in git)
4. **Monitor First Week**: Check that tasks run correctly for the first few days
5. **Set Email Alerts**: In Task Scheduler, you can configure tasks to send emails on failure

---

**Ready to set up?** Follow Method 1 (Automatic) for easiest setup, or Method 2 (Manual) if you prefer more control!
