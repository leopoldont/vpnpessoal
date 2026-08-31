"""
setup_msi.py - Script de compilação para gerar Instalador Nativo do Windows (.msi)
Utiliza cx_Freeze para empacotar o Python + PyQt6 + Dependências em um único pacote MSI.
"""

import sys
import os
from cx_Freeze import setup, Executable

# Arquivos e pastas a incluir no pacote
build_exe_options = {
    "packages": ["os", "sys", "json", "urllib", "socket", "concurrent.futures", "PyQt6", "requests"],
    "include_files": [
        ("vpn_engine.py", "vpn_engine.py"),
        ("gui.py", "gui.py"),
        ("README.md", "README.md"),
        ("LEIA-ME.txt", "LEIA-ME.txt")
    ],
    "excludes": ["tkinter", "unittest", "pydoc", "test"],
    "include_msvcr": True
}

# Configurações do Instalador MSI do Windows
bdist_msi_options = {
    "add_to_path": False,
    "initial_target_dir": r"[LocalAppDataFolder]\VPNSwitch",
    "upgrade_code": "{A3B8C1D2-4E5F-6A7B-8C9D-0E1F2A3B4C5D}",
    "install_icon": None,
    "all_users": False,  # Instalação por usuário (dispensa complicação de permissões)
}

# Executável do aplicativo
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Não abre janela de prompt preta

executables = [
    Executable(
        script="main.py",
        target_name="VPN-Switch.exe",
        base=base,
        shortcut_name="VPN Switch",
        shortcut_dir="DesktopFolder",
        uac_admin=True  # Solicita permissão UAC para gerenciar rotas de rede
    )
]

setup(
    name="VPN Switch",
    version="1.0.0",
    description="VPN Switch & Server Browser para Windows 11",
    author="VPN Switch Team",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=executables
)
