# Daily Briefs - Automated Morning Refresh Runner
# Runs locally at 05:00 AM via Windows Task Scheduler

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$LogFile = Join-Path $RepoRoot "daily-refresh.log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Function Log-Message($msg) {
    $line = "[$Timestamp] $msg"
    Write-Output $line
    Add-Content -Path $LogFile -Value $line
}

Log-Message "=== Starting Daily Morning Refresh ==="

Try {
    # 1. Fetch and fast-forward latest commits
    Log-Message "Syncing with GitHub..."
    & git fetch origin main
    & git pull --rebase origin main

    # 2. Check if today's brief is already published
    $DateStr = Get-Date -Format "yyyy-MM-dd"
    $PeteData = Get-Content -Raw "data/pete.json" | ConvertFrom-Json
    If ($PeteData.worldFact.date -eq $DateStr) {
        Log-Message "Today's brief ($DateStr) is already published. Skipping."
        Exit 0
    }

    # 3. Run refresh pipeline
    $Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    If (-not (Test-Path $Py)) {
        $Py = "python"
    }

    Log-Message "Executing refresh scripts..."
    & $Py scripts/refresh.py
    & $Py scripts/enrich_weather_v2.py
    & $Py scripts/enrich_arsenal.py
    & $Py scripts/finalize_arsenal.py
    & $Py scripts/enrich_next_fixture.py
    & $Py scripts/enrich_tv_picks.py
    & $Py scripts/refresh_story_images.py

    # 4. Run tests
    Log-Message "Running regression suite..."
    & $Py -m unittest discover -s tests

    # 5. Commit and push if changed
    & git add assets/weather-extremes/*.webp data/*.json
    $Diff = & git status --porcelain
    If ($Diff) {
        Log-Message "Committing and pushing refreshed brief for $DateStr..."
        & git commit -m "Morning refresh: $DateStr"
        & git push origin main
        Log-Message "Successfully published $DateStr edition to GitHub Pages."
    } Else {
        Log-Message "No data changes to commit."
    }

    Log-Message "=== Morning Refresh Completed Successfully ==="
} Catch {
    Log-Message "ERROR: $_"
    Exit 1
}
