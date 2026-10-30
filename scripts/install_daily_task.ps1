# Daily Briefs - (re)install the Windows scheduled task for the morning refresh.
# Run once from an elevated PowerShell:  right-click this file > Run with PowerShell,
# or:  powershell -ExecutionPolicy Bypass -File scripts\install_daily_task.ps1
# Safe to re-run; it replaces the DailyBriefMorningRefresh task in place.

$ErrorActionPreference = "Stop"
$TaskName = "DailyBriefMorningRefresh"
$Runner = Join-Path $PSScriptRoot "daily_refresh_runner.ps1"
$RepoRoot = Split-Path -Parent $PSScriptRoot

If (-not (Test-Path $Runner)) { Throw "Runner not found: $Runner" }

# Show any existing task first, with its last result, so we know why it missed.
$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
If ($Existing) {
    $Info = $Existing | Get-ScheduledTaskInfo
    Write-Host "Existing task: state=$($Existing.State) lastRun=$($Info.LastRunTime) lastResult=$($Info.LastTaskResult) nextRun=$($Info.NextRunTime)"
}

# Windows local time follows GMT/BST, so 04:55 local is always just before 05:00 London.
# The runner waits for 05:00, then publishes only if today's edition is missing.
$Action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`"" `
           -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "04:55"
$Settings = New-ScheduledTaskSettingsSet `
           -WakeToRun `
           -StartWhenAvailable `
           -AllowStartIfOnBatteries `
           -DontStopIfGoingOnBatteries `
           -RunOnlyIfNetworkAvailable `
           -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 15) `
           -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
           -MultipleInstances IgnoreNew
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Principal $Principal -Force `
    -Description "Daily Briefs morning refresh (scripts/daily_refresh_runner.ps1). Publishes at 05:00 Europe/London if today's edition is missing." | Out-Null

# Allow scheduled tasks to wake the PC from sleep, on mains and battery
# (Windows often ships with wake timers off on battery).
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1 | Out-Null
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1 | Out-Null
powercfg /SETACTIVE SCHEME_CURRENT | Out-Null

$Info = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
Write-Host "Installed $TaskName. Next run: $($Info.NextRunTime)"
Write-Host "Note: the PC must be asleep (not shut down or hibernated) and logged in for the task to wake it."
Read-Host "Press Enter to close"
