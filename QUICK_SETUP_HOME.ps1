# Quick Setup Script for Home Machine
# Run this in PowerShell as Administrator

Write-Host "`n🎰 Lottery Assistant - Home Machine Setup`n" -ForegroundColor Cyan

# Get current user's Desktop path
$desktopPath = [Environment]::GetFolderPath("Desktop")
$projectPath = Join-Path $desktopPath "Lottery Assistant + Telegram Bot + Web Automation"

Write-Host "Project Path: $projectPath`n" -ForegroundColor Yellow

# Check if project exists
if (-not (Test-Path $projectPath)) {
    Write-Host "❌ Project not found at: $projectPath" -ForegroundColor Red
    Write-Host "Please update the path in this script or move your project to Desktop.`n" -ForegroundColor Yellow
    exit 1
}

# Change to project directory
Set-Location $projectPath
Write-Host "✅ Changed to project directory`n" -ForegroundColor Green

# Check required files
Write-Host "Checking required files..." -ForegroundColor Yellow
$requiredFiles = @("main.py", "config.json", ".env", "setup_windows_scheduler.ps1")
$allExist = $true

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (MISSING)" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host "`n❌ Some required files are missing. Please check your project.`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ All files found!`n" -ForegroundColor Green

# Find Python
Write-Host "Finding Python..." -ForegroundColor Yellow
$pythonPath = $null

# Try common locations
$pythonLocations = @(
    (Get-Command python -ErrorAction SilentlyContinue).Source,
    "C:\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:PROGRAMFILES\Python312\python.exe",
    "$env:PROGRAMFILES(X86)\Python312\python.exe"
)

foreach ($loc in $pythonLocations) {
    if ($loc -and (Test-Path $loc)) {
        $pythonPath = $loc
        break
    }
}

if (-not $pythonPath) {
    Write-Host "❌ Python not found. Please install Python or update the path.`n" -ForegroundColor Red
    exit 1
}

Write-Host "  ✅ Python found: $pythonPath`n" -ForegroundColor Green

# Test Python
Write-Host "Testing Python..." -ForegroundColor Yellow
try {
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "  ✅ $pythonVersion`n" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python test failed: $_`n" -ForegroundColor Red
    exit 1
}

# Check .env file
Write-Host "Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "TELEGRAM_BOT_TOKEN" -and $envContent -match "TELEGRAM_CHAT_ID") {
        Write-Host "  ✅ .env file looks good`n" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  .env file exists but may be missing credentials`n" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ .env file not found! Please create it from env.example`n" -ForegroundColor Red
    exit 1
}

# Run setup script
Write-Host "Running Windows Task Scheduler setup...`n" -ForegroundColor Cyan
Write-Host "This will create 8 scheduled tasks.`n" -ForegroundColor Yellow

$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Setup cancelled.`n" -ForegroundColor Yellow
    exit 0
}

# Run the setup script
try {
    & ".\setup_windows_scheduler.ps1"
    Write-Host "`n✅ Setup complete!`n" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Setup failed: $_`n" -ForegroundColor Red
    exit 1
}

# Verify tasks
Write-Host "Verifying tasks..." -ForegroundColor Yellow
$tasks = Get-ScheduledTask -TaskName "LotteryCheck_*" -ErrorAction SilentlyContinue

if ($tasks) {
    Write-Host "  ✅ Found $($tasks.Count) tasks`n" -ForegroundColor Green
    
    Write-Host "Task List:" -ForegroundColor Cyan
    $tasks | ForEach-Object {
        $info = Get-ScheduledTaskInfo $_.TaskName
        Write-Host "  • $($_.TaskName)" -ForegroundColor White
        Write-Host "    State: $($_.State) | Next Run: $($info.NextRunTime)`n" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️  No tasks found. Setup may have failed.`n" -ForegroundColor Yellow
}

# Test one task
Write-Host "`nWould you like to test a task now? (Y/N)" -ForegroundColor Yellow
$test = Read-Host
if ($test -eq "Y" -or $test -eq "y") {
    if ($tasks) {
        $testTask = $tasks[0]
        Write-Host "`nTesting: $($testTask.TaskName)..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $testTask.TaskName
        Write-Host "Task started! Check Telegram in 30 seconds for messages.`n" -ForegroundColor Green
    }
}

Write-Host "`n🎉 Setup Complete!`n" -ForegroundColor Green
Write-Host "Your lottery checks will now run automatically at scheduled times.`n" -ForegroundColor Cyan
Write-Host "To view tasks: Get-ScheduledTask -TaskName 'LotteryCheck_*'`n" -ForegroundColor Yellow
