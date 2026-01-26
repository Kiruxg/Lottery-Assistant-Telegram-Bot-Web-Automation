# PowerShell script to set up Windows Task Scheduler for Lottery Assistant
# Run this script as Administrator

param(
    [string]$PythonPath = "",
    [string]$ScriptPath = ""
)

Write-Host "`n🎰 Lottery Assistant - Windows Task Scheduler Setup`n" -ForegroundColor Cyan

# Get Python path if not provided
if ([string]::IsNullOrEmpty($PythonPath)) {
    $PythonPath = (Get-Command python).Source
    if ([string]::IsNullOrEmpty($PythonPath)) {
        Write-Host "❌ Python not found in PATH. Please provide Python path." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Python: $PythonPath" -ForegroundColor Green

# Get script path if not provided
if ([string]::IsNullOrEmpty($ScriptPath)) {
    $ScriptPath = Join-Path $PSScriptRoot "main.py"
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Script: $ScriptPath`n" -ForegroundColor Green

# Import scheduler module to get schedule times
Write-Host "📅 Generating schedule from config.json...`n" -ForegroundColor Yellow

$scheduleTimes = @(
    @{Game="Lucky Day Lotto Midday"; GameId="lucky_day_lotto_midday"; Time="12:10"; Days="Daily"; Desc="30min before 12:40 draw"},
    @{Game="Lucky Day Lotto Midday"; GameId="lucky_day_lotto_midday"; Time="12:50"; Days="Daily"; Desc="10min after 12:40 draw"},
    @{Game="Lucky Day Lotto Evening"; GameId="lucky_day_lotto_evening"; Time="20:52"; Days="Daily"; Desc="30min before 21:22 draw"},
    @{Game="Lucky Day Lotto Evening"; GameId="lucky_day_lotto_evening"; Time="21:32"; Days="Daily"; Desc="10min after 21:22 draw"},
    @{Game="Powerball"; GameId="powerball"; Time="21:29"; Days="Mon,Wed,Sat"; Desc="30min before 21:59 draw"},
    @{Game="Powerball"; GameId="powerball"; Time="22:09"; Days="Mon,Wed,Sat"; Desc="10min after 21:59 draw"},
    @{Game="Mega Millions"; GameId="mega_millions"; Time="21:30"; Days="Tue,Fri"; Desc="30min before 22:00 draw"},
    @{Game="Mega Millions"; GameId="mega_millions"; Time="22:10"; Days="Tue,Fri"; Desc="10min after 22:00 draw"}
)

$taskCount = 0

foreach ($schedule in $scheduleTimes) {
    $taskName = "LotteryCheck_$($schedule.Game.Replace(' ', '_'))_$($schedule.Time.Replace(':', ''))"
    $taskName = $taskName -replace '[^a-zA-Z0-9_]', '_'
    
    # Parse days
    $days = $schedule.Days
    if ($days -eq "Daily") {
        $trigger = New-ScheduledTaskTrigger -Daily -At $schedule.Time
    } elseif ($days -eq "Mon,Wed,Sat") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Wednesday,Saturday -At $schedule.Time
    } elseif ($days -eq "Tue,Fri") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday,Friday -At $schedule.Time
    }
    
    # Pass game_id to check command so only that game is checked
    $action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`" check $($schedule.GameId)" -WorkingDirectory (Split-Path $ScriptPath)
    
    try {
        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-Host "⚠️  Task exists: $taskName (skipping)" -ForegroundColor Yellow
            continue
        }
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description $schedule.Desc -RunLevel Highest
        
        Write-Host "✅ Created: $taskName ($($schedule.Time) - $($schedule.Days))" -ForegroundColor Green
        $taskCount++
    } catch {
        Write-Host "❌ Failed to create task: $taskName - $_" -ForegroundColor Red
    }
}

Write-Host "`n✅ Setup complete! Created $taskCount scheduled tasks.`n" -ForegroundColor Green
Write-Host "To view tasks: Get-ScheduledTask -TaskName 'LotteryCheck_*'" -ForegroundColor Cyan
Write-Host "To remove tasks: Get-ScheduledTask -TaskName 'LotteryCheck_*' | Unregister-ScheduledTask`n" -ForegroundColor Cyan
