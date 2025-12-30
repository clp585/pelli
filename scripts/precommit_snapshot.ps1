$ErrorActionPreference = "Stop"

try {
    $repo = git rev-parse --show-toplevel
    Set-Location $repo

    Write-Host "[pre-commit] Running snapshot generator..."
    python export_agent_snapshot.py --out PROJECT_SNAPSHOT.md
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[pre-commit] Snapshot generation failed."
        exit 1
    }

    Write-Host "[pre-commit] Staging PROJECT_SNAPSHOT.md..."
    git add PROJECT_SNAPSHOT.md | Out-Null

    Write-Host "[pre-commit] Snapshot generated and staged."
    exit 0
}
catch {
    Write-Host "[pre-commit] Snapshot generation failed: $($_.Exception.Message)"
    exit 1
}
