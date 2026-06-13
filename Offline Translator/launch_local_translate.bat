@echo off
title Local Translate App

echo ══════════════════════════════════════════════════════
echo   Local Translate (LM Studio + Gemma 4 2B)
echo ══════════════════════════════════════════════════════
echo.
echo Make sure LM Studio is open and your Local Server is 
echo running on port 1234 before clicking Start!
echo.

python "%~dp0live_translate_local.py"
pause
