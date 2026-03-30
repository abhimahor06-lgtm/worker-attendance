@echo off
title Contractor Register App
color 0A
echo.
echo  =====================================================
echo    CONTRACTOR REGISTER APP   by Thekedaar Panel
echo  =====================================================
echo.

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [ERROR] Python nahi mila!
    echo  Install karo: https://python.org/downloads
    echo  Install karte waqt "Add to PATH" check karna!
    echo.
    pause
    exit
)

echo  [1/2] Flask install kar raha hai...
pip install Flask --quiet

echo  [2/2] Server start ho raha hai...
echo.
echo  ====================================================
echo   Browser mein kholo:  http://127.0.0.1:5000
echo   Band karne ke liye:  Ctrl+C dabao
echo  ====================================================
echo.

python app.py

echo.
echo  App band ho gaya.
pause
