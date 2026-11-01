@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title MP3 Binder - buckshot.py

echo ============================================
echo    BIND MP3 INTO buckshot.py
echo ============================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] "python" not found in PATH.
    echo Please install Python or use "py" instead.
    pause
    exit /b 1
)

REM --- Check embed_mp3.py ---
if not exist "embed_mp3.py" (
    echo [ERROR] embed_mp3.py not found in this folder.
    pause
    exit /b 1
)

REM --- List available MP3s ---
echo Available MP3 files in folder:
echo.
set /a i=1
set "mp3_1="
set "mp3_2="
set "mp3_3="
set "mp3_4="
set "mp3_5="
for %%F in (*.mp3) do (
    set "mp3_!i!=%%F"
    echo    !i!. %%F
    set /a i+=1
)
echo    M. Type filename manually
echo    C. Remove embedded MP3 (--clear)
echo    X. Exit
echo.

set "option="
set /p "option=Choose an option (1-5 / M / C / X): "

if /i "%option%"=="X" goto :fin
if /i "%option%"=="C" goto :clear
if /i "%option%"=="M" goto :manual

set "MP3FILE=!mp3_%option%!"
if not defined MP3FILE (
    echo [ERROR] Invalid option.
    pause
    exit /b 1
)
goto :crush

:manual
set /p "MP3FILE=MP3 filename (with extension): "
if not exist "%MP3FILE%" (
    echo [ERROR] "%MP3FILE%" not found.
    pause
    exit /b 1
)
goto :crush

:crush
echo.
echo Selected file: %MP3FILE%
echo.
echo --- BITCRUSHER ---
echo   0    = No effect (recommended for original quality)
echo   1-99 = Progressive effect
echo   100  = Destroyed
echo.
set "CRUSH="
set /p "CRUSH=Bitcrush value [0-100, Enter=0]: "
if "%CRUSH%"=="" set "CRUSH=0"

REM Validate that it is a number
echo %CRUSH%| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo [ERROR] You must enter a number.
    pause
    exit /b 1
)

set "BITRATE="
if not "%CRUSH%"=="0" (
    echo.
    echo Bitrate for resulting MP3 (only if bitcrusher is used):
    echo   128k = Default
    echo   96k  = A bit lighter
    echo   64k  = Very light
    set /p "BITRATE=Bitrate [Enter=128k]: "
    if "!BITRATE!"=="" set "BITRATE=128k"
)

REM --- Confirm ---
echo.
echo ============================================
echo   MP3:      %MP3FILE%
echo   Crush:    %CRUSH%
if not "%CRUSH%"=="0" echo   Bitrate:  %BITRATE%
echo ============================================
set "CONF="
set /p "CONF=Continue? [Y/n]: "
if /i "%CONF%"=="n" goto :fin

echo.
echo Running embed_mp3.py ...
echo.

if "%CRUSH%"=="0" (
    python embed_mp3.py "%MP3FILE%" --crush 0
) else (
    if "%BITRATE%"=="" (
        python embed_mp3.py "%MP3FILE%" --crush %CRUSH%
    ) else (
        python embed_mp3.py "%MP3FILE%" --crush %CRUSH% --bitrate %BITRATE%
    )
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to run embed_mp3.py
) else (
    echo.
    echo [OK] MP3 embedded into buckshot.py
)
echo.
pause
goto :fin

:clear
echo.
set "CONF="
set /p "CONF=Are you sure you want to REMOVE the embedded MP3? [y/N]: "
if /i not "%CONF%"=="y" goto :fin
python embed_mp3.py --clear
echo.
pause

:fin
endlocal
exit /b 0