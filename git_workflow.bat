@echo off
echo ========================================
echo FYP Project Git Workflow Automation
echo ========================================
echo.

:: Check if we're in the right directory
if not exist "flashlog" (
    echo ERROR: flashlog directory not found!
    echo Please run this script from the FYP project root directory.
    pause
    exit /b 1
)

:: Check if Git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH!
    pause
    exit /b 1
)

:: Show current status
echo [1/5] Checking Git status...
git status
echo.

:: Ask user for commit message
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg="Auto commit: %date% %time%"

:: Add all files
echo [2/5] Adding files to staging area...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files!
    pause
    exit /b 1
)

:: Commit changes
echo [3/5] Committing changes...
git commit -m %commit_msg%
if errorlevel 1 (
    echo ERROR: Failed to commit changes!
    echo This might be because there are no changes to commit.
    pause
    exit /b 1
)

:: Check if remote exists
echo [4/5] Checking remote repository...
git remote -v >nul 2>&1
if errorlevel 1 (
    echo No remote repository found.
    echo.
    set /p remote_url="Enter GitHub repository URL (e.g., https://github.com/username/repo.git): "
    if not "%remote_url%"=="" (
        git remote add origin %remote_url%
        echo Remote repository added.
    ) else (
        echo No remote URL provided. Skipping push.
        goto :end
    )
)

:: Push to GitHub
echo [5/5] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo WARNING: Push failed. This might be because:
    echo - Remote repository doesn't exist
    echo - You don't have write permissions
    echo - Network issues
    echo.
    echo You can manually push later with: git push origin main
) else (
    echo SUCCESS: Changes pushed to GitHub!
)

:end
echo.
echo ========================================
echo Git workflow completed!
echo ========================================
pause 