# PowerShell script to compile a distribution bundle
# Usage: .\bundle.ps1

Write-Host "📦 Compiling AI Lighting Agent bundle..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment if present (optional)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "ℹ️  Virtual environment not found, using system Python" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Running bundle compiler..." -ForegroundColor Green
Write-Host ""

# Run the bundle compiler
python compile_bundle.py

# Check if compilation was successful and dist folder exists
if (Test-Path "dist") {
    Write-Host ""
    Write-Host "🔍 Finding newest bundle..." -ForegroundColor Cyan
    
    # Get all directories in dist/ and sort by creation time
    $distFolders = Get-ChildItem -Path "dist" -Directory -ErrorAction SilentlyContinue
    
    if ($distFolders) {
        $newestFolder = $distFolders | Sort-Object CreationTime -Descending | Select-Object -First 1
        
        Write-Host ""
        Write-Host "✅ Bundle created successfully!" -ForegroundColor Green
        Write-Host "📁 Newest bundle: dist\$($newestFolder.Name)" -ForegroundColor Cyan
        Write-Host "📍 Full path: $($newestFolder.FullName)" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "⚠️  dist/ folder exists but contains no bundles" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "⚠️  Bundle compilation may have failed - dist/ folder not found" -ForegroundColor Yellow
}

Write-Host ""

