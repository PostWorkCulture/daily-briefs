# Daily Briefs - Automated Morning Refresh Runner
# Runs locally via Windows Task Scheduler. Publishes only at or after 05:00
# Europe/London and only after the same tests and protected-rule validator
# used by the GitHub Actions Morning refresh have passed.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Python must read the UTF-8 JSON data as UTF-8 on Windows.
$env:PYTHONUTF8 = "1"

$LogFile = Join-Path $RepoRoot "daily-refresh.log"
$London = [System.TimeZoneInfo]::FindSystemTimeZoneById("GMT Standard Time")

Function London-Now {
    [System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $London)
}

Function Log-Message($msg) {
    $line = "[$((London-Now).ToString('yyyy-MM-dd HH:mm:ss'))] $msg"
    Write-Output $line
    Add-Content -Path $LogFile -Value $line
}

# Native commands do not stop the script on failure, so check every exit code.
Function Invoke-Step($label, [scriptblock]$cmd) {
    & $cmd
    If ($LASTEXITCODE -ne 0) {
        Throw "$label failed (exit code $LASTEXITCODE)"
    }
}

Function Stale-Profiles($DateStr) {
    $stale = @()
    ForEach ($p in @("pete", "sofia")) {
        $data = Get-Content -Raw -Encoding UTF8 "data/$p.json" | ConvertFrom-Json
        If ($data.worldFact.date -ne $DateStr) { $stale += $p }
    }
    return $stale
}

Log-Message "=== Starting Daily Morning Refresh ==="

Try {
    # 1. Never publish before 05:00 London. If the task fires early (for
    #    example a UTC-pinned trigger after the clocks change), wait for 05:00.
    $Now = London-Now
    $Five = $Now.Date.AddHours(5)
    If ($Now -lt $Five) {
        $Wait = $Five - $Now
        If ($Wait.TotalMinutes -gt 90) {
            Log-Message "Before 05:00 Europe/London ($($Now.ToString('HH:mm'))). Skipping."
            Exit 0
        }
        Log-Message "Before 05:00 Europe/London ($($Now.ToString('HH:mm'))). Waiting $([int][math]::Ceiling($Wait.TotalMinutes)) min."
        Start-Sleep -Seconds ([int][math]::Ceiling($Wait.TotalSeconds) + 60)
    }
    $DateStr = (London-Now).ToString("yyyy-MM-dd")

    # 2. Sync with GitHub (the Actions refresh may already have published).
    Log-Message "Syncing with GitHub..."
    Invoke-Step "git fetch" { git fetch origin main }
    Invoke-Step "git pull" { git pull --rebase origin main }

    # 3. Skip when both profiles already carry today's edition.
    $Stale = Stale-Profiles $DateStr
    If ($Stale.Count -eq 0) {
        Log-Message "Today's brief ($DateStr) is already published. Skipping."
        Exit 0
    }
    Log-Message "Stale profiles for ${DateStr}: $($Stale -join ', ')"

    $Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    If (-not (Test-Path $Py)) { $Py = "python" }

    # 4. Regression tests before refreshing (same order as GitHub Actions).
    Log-Message "Running regression suite..."
    Invoke-Step "Regression tests" { & $Py -m unittest discover -s tests -p "test_*.py" }

    # 5. Refresh pipeline. Any failing step stops publication.
    Log-Message "Executing refresh scripts..."
    ForEach ($s in @("refresh.py", "enrich_weather_v2.py", "enrich_arsenal.py", "finalize_arsenal.py",
                     "enrich_next_fixture.py", "enrich_tv_picks.py", "refresh_story_images.py")) {
        Invoke-Step $s { & $Py "scripts/$s" }
    }

    # 6. Protected-rule validator shared with GitHub Actions.
    Log-Message "Validating protected brief rules..."
    Invoke-Step "Protected-rule validation" { & $Py scripts/validate_brief.py }

    # 7. Commit and push only the refreshed data.
    Invoke-Step "git add" { git add data/*.json assets/weather-extremes/*.webp assets/scenery/*.webp assets/news-images/*.webp }
    git diff --cached --quiet
    If ($LASTEXITCODE -eq 0) {
        Log-Message "No data changes to commit."
    } Else {
        Log-Message "Committing and pushing refreshed brief for $DateStr..."
        Invoke-Step "git commit" { git commit -m "Morning refresh: $DateStr" }
        Invoke-Step "git pull" { git pull --rebase origin main }
        Invoke-Step "git push" { git push origin main }
        Log-Message "Published $DateStr edition to GitHub Pages."
    }

    Log-Message "=== Morning Refresh Completed Successfully ==="
} Catch {
    Log-Message "ERROR: $_"
    # Leave the working tree on the last published edition so a failed local
    # run never lingers as unpublished half-refreshed data.
    Try { git checkout -- data assets 2>&1 | Out-Null } Catch { }
    Exit 1
}
