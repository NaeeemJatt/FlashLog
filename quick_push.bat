@echo off
echo Quick Git Push - FYP Project
echo ============================

:: Add all files
git add .

:: Commit with timestamp
git commit -m "Auto commit: %date% %time%"

:: Push to GitHub
git push origin main

echo Done!
pause 