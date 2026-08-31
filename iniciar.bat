@echo off
title VPN Switch - Windows 11
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo       ⚡ VPN Switch - Versao Windows 11
echo ========================================================
echo.

:: Verificar se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado no sistema!
    echo Por favor, instale o Python em https://www.python.org/
    echo Certifique-se de marcar a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

:: Verificar se as dependencias estao instaladas
python -c "import PyQt6, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependencias necessarias (PyQt6, requests)...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependencias via pip.
        pause
        exit /b 1
    )
)

:: Executar o programa
echo [INFO] Iniciando VPN Switch...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [AVISO] O aplicativo encerrou com codigo %errorlevel%.
    pause
)
