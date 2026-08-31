@echo off
title Instalar Dependencias - VPN Switch
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo      Instalador de Dependencias - VPN Switch
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Instale o Python 3.10+ marcando a opcao "Add to PATH".
    pause
    exit /b 1
)

echo [1/2] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [2/2] Instalando requisitos (PyQt6, requests)...
python -m pip install -r requirements.txt

echo.
echo ========================================================
echo      Instalacao concluida com sucesso!
echo      Agora voce pode rodar "iniciar.bat"
echo ========================================================
echo.
pause
