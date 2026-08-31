@echo off
title Gerar Executavel (.exe) - VPN Switch
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo      Compilador de Executavel Standalone (.exe)
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

echo [1/3] Garantindo dependencias e PyInstaller...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [2/3] Compilando VPN-Switch.exe (com elevacao UAC embutida)...
pyinstaller --noconfirm --onedir --windowed --uac-admin --name "VPN-Switch" ^
    --add-data "vpn_engine.py;." ^
    --add-data "gui.py;." ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha na compilacao com PyInstaller.
    pause
    exit /b 1
)

echo.
echo [3/3] Compilando versao de arquivo unico (OneFile)...
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "VPN-Switch-Portable" ^
    --add-data "vpn_engine.py;." ^
    --add-data "gui.py;." ^
    main.py

echo.
echo ========================================================
echo      Compilacao Concluida com Sucesso!
echo.
echo      Os executaveis estao na pasta 'dist/':
echo      - dist/VPN-Switch-Portable.exe (Executavel unico)
echo      - dist/VPN-Switch/VPN-Switch.exe (Pasta com app)
echo ========================================================
echo.
pause
