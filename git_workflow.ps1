# FYP Project Git Workflow Automation (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FYP Project Git Workflow Automation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "flashlog")) {
    Write-Host "ERROR: flashlog directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the FYP project root directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Git is available
try {
    $gitVersion = git --version
    Write-Host "Git version: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not in PATH!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Show current status
Write-Host "[1/5] Checking Git status..." -ForegroundColor Yellow
git status
Write-Host ""

# Ask user for commit message
$commitMsg = Read-Host "Enter commit message (or press Enter for default)"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Auto commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

# Add all files
Write-Host "[2/5] Adding files to staging area..." -ForegroundColor Yellow
try {
    git add .
    Write-Host "Files added successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to add files!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Commit changes
Write-Host "[3/5] Committing changes..." -ForegroundColor Yellow
try {
    git commit -m $commitMsg
    Write-Host "Changes committed successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to commit changes!" -ForegroundColor Red
    Write-Host "This might be because there are no changes to commit." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if remote exists
Write-Host "[4/5] Checking remote repository..." -ForegroundColor Yellow
$remotes = git remote -v 2>$null
if (-not $remotes) {
    Write-Host "No remote repository found." -ForegroundColor Yellow
    Write-Host ""
    $remoteUrl = Read-Host "Enter GitHub repository URL (e.g., https://github.com/username/repo.git)"
    if (-not [string]::IsNullOrWhiteSpace($remoteUrl)) {
        git remote add origin $remoteUrl
        Write-Host "Remote repository added." -ForegroundColor Green
    } else {
        Write-Host "No remote URL provided. Skipping push." -ForegroundColor Yellow
        goto end
    }
}

# Push to GitHub
Write-Host "[5/5] Pushing to GitHub..." -ForegroundColor Yellow
try {
    git push origin main
    Write-Host "SUCCESS: Changes pushed to GitHub!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Push failed. This might be because:" -ForegroundColor Yellow
    Write-Host "- Remote repository doesn't exist" -ForegroundColor Yellow
    Write-Host "- You don't have write permissions" -ForegroundColor Yellow
    Write-Host "- Network issues" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can manually push later with: git push origin main" -ForegroundColor Cyan
}

end:
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git workflow completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit" 