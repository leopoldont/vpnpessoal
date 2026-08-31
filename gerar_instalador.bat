@echo off
title Gerador de Instaladores Windows (.msi / Setup) - VPN Switch
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo       Gerador de Instaladores - VPN Switch Windows 11
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado neste computador!
    echo Para gerar o instalador, instale o Python 3.10+ com a opcao "Add to PATH".
    pause
    exit /b 1
)

echo [1/3] Instalando ferramentas de empacotamento (cx_Freeze, PyInstaller)...
python -m pip install -r requirements.txt
python -m pip install cx_Freeze pyinstaller

echo.
echo ========================================================
echo   Escolha o tipo de instalador que deseja gerar:
echo.
echo   [1] Gerar Instalador Nativo do Windows (.MSI)
echo   [2] Gerar Executavel Portatil Unico (.EXE)
echo   [3] Gerar Todos (MSI + EXE)
echo ========================================================
set /p opcao="Digite a opcao desejada (1, 2 ou 3): "

if "%opcao%"=="1" goto GERAR_MSI
if "%opcao%"=="2" goto GERAR_EXE
if "%opcao%"=="3" goto GERAR_TODOS
goto GERAR_MSI

:GERAR_MSI
echo.
echo [2/3] Gerando pacote de instalacao .MSI via cx_Freeze...
python setup_msi.py bdist_msi
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao gerar o arquivo .MSI
    pause
    exit /b 1
)
goto CONCLUIDO

:GERAR_EXE
echo.
echo [2/3] Gerando executavel unico (.EXE) via PyInstaller...
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "VPN-Switch-Portable" ^
    --add-data "vpn_engine.py;." ^
    --add-data "gui.py;." ^
    main.py
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao gerar o executavel .EXE
    pause
    exit /b 1
)
goto CONCLUIDO

:GERAR_TODOS
echo.
echo [2/3] Gerando pacote .MSI e executavel .EXE...
python setup_msi.py bdist_msi
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "VPN-Switch-Portable" ^
    --add-data "vpn_engine.py;." ^
    --add-data "gui.py;." ^
    main.py
goto CONCLUIDO

:CONCLUIDO
echo.
echo ========================================================
echo      SUCESSO! O Instalador foi criado com exito.
echo.
echo      Verifique a pasta "dist/":
echo      - Arquivo de instalacao .msi (Pronto para enviar ao seu amigo!)
echo.
echo      Seu amigo so precisara dar 2 cliques no .msi para
echo      instalar o VPN Switch normalmente no Windows 11.
echo ========================================================
echo.
pause
