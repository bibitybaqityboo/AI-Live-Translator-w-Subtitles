@echo off
title Gemini Live Translate
color 0B

echo.
echo  ============================================================
echo       Gemini Live Translate - Real-Time Voice Translation
echo  ============================================================
echo.

:: ── Set your API key here (one-time setup) ─────────────────────
:: Replace YOUR_KEY_HERE with your actual Gemini API key.
:: Get one at: https://aistudio.google.com/apikey
if not defined GEMINI_API_KEY (
    set "GEMINI_API_KEY=YOUR_GEMINI_API_KEY"
)

if "%GEMINI_API_KEY%"=="YOUR_GEMINI_API_KEY" (
    echo  [!] You need to set your API key first!
    echo      Open this file in Notepad and replace YOUR_GEMINI_API_KEY
    echo      on the line that says: set "GEMINI_API_KEY=YOUR_GEMINI_API_KEY"
    echo.
    echo      Get a free key at: https://aistudio.google.com/apikey
    echo.
    pause
    exit /b
)

:: ── Choose target language ─────────────────────────────────────
echo  Popular language codes:
echo    es = Spanish       fr = French        de = German
echo    ar = Arabic        zh = Chinese       ja = Japanese
echo    ko = Korean        hi = Hindi         pt = Portuguese
echo    it = Italian       ru = Russian       pl = Polish
echo    tr = Turkish       nl = Dutch         sv = Swedish
echo.

set "TARGET=es"
set /p TARGET="  Enter target language code [es]: "

echo.
echo  Starting translation to: %TARGET%
echo  (Use headphones to avoid echo! Press Ctrl+C to stop.)
echo  ============================================================
echo.

python "%~dp0live_translate.py" --target %TARGET%

echo.
pause
