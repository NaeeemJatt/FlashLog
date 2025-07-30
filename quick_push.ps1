# Quick Git Push - FYP Project
Write-Host "Quick Git Push - FYP Project" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# Add all files
git add .

# Commit with timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "Auto commit: $timestamp"

# Push to GitHub
git push origin main

Write-Host "Done!" -ForegroundColor Green
Read-Host "Press Enter to exit" 