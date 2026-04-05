# TEST_DUPLICATE_CLEANUP.ps1
# Script to identify and optionally remove duplicate/outdated documentation files

Write-Host "=== KIRO2 Duplicate Cleanup Test ===" -ForegroundColor Cyan
Write-Host ""

# Change to the repository root
Set-Location "C:\Users\husey\kiro2"

# Check git status
Write-Host "Checking git status for deleted files..." -ForegroundColor Yellow
$deletedFiles = git status --short | Where-Object { $_ -match "^ D " }

if ($deletedFiles) {
    Write-Host ""
    Write-Host "Found $($deletedFiles.Count) deleted files in git:" -ForegroundColor Green
    Write-Host ""

    # Categorize deleted files
    $mdFiles = @()
    $otherFiles = @()

    foreach ($line in $deletedFiles) {
        $file = $line -replace "^ D ", ""
        if ($file -match "\.md$") {
            $mdFiles += $file
        } else {
            $otherFiles += $file
        }
    }

    # Show markdown files
    if ($mdFiles.Count -gt 0) {
        Write-Host "Deleted Markdown Documentation Files ($($mdFiles.Count)):" -ForegroundColor Magenta
        $mdFiles | ForEach-Object { Write-Host "  - $_" }
        Write-Host ""
    }

    # Show other files
    if ($otherFiles.Count -gt 0) {
        Write-Host "Other Deleted Files ($($otherFiles.Count)):" -ForegroundColor Yellow
        $otherFiles | ForEach-Object { Write-Host "  - $_" }
        Write-Host ""
    }

    # Check for uncommitted changes
    Write-Host "Checking for uncommitted changes..." -ForegroundColor Yellow
    $modifiedFiles = git status --short | Where-Object { $_ -match "^[AM]" }

    if ($modifiedFiles) {
        Write-Host ""
        Write-Host "WARNING: You have uncommitted changes:" -ForegroundColor Red
        $modifiedFiles | ForEach-Object { Write-Host "  $_" }
        Write-Host ""
    }

    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  1. Commit all deletions (remove outdated docs from git)"
    Write-Host "  2. Show detailed status"
    Write-Host "  3. Reset deletions (restore files)"
    Write-Host "  4. Exit"
    Write-Host ""

    $choice = Read-Host "Choose an option (1-4)"

    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "Committing deletions..." -ForegroundColor Green
            git add -u
            git commit -m "docs: Remove outdated/duplicate documentation files

- Removed $($mdFiles.Count) outdated markdown documentation files
- Cleanup to reduce repository clutter
- Active documentation retained in key files"
            Write-Host ""
            Write-Host "✅ Deletions committed successfully!" -ForegroundColor Green
        }
        "2" {
            Write-Host ""
            git status
        }
        "3" {
            Write-Host ""
            Write-Host "Restoring deleted files..." -ForegroundColor Yellow
            git restore .
            Write-Host "✅ Files restored!" -ForegroundColor Green
        }
        "4" {
            Write-Host "Exiting..." -ForegroundColor Gray
        }
        default {
            Write-Host "Invalid option. Exiting..." -ForegroundColor Red
        }
    }

} else {
    Write-Host "✅ No deleted files found in git status!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository is clean." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Cleanup Test Complete ===" -ForegroundColor Cyan
