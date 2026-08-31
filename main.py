"""
main.py - Ponto de Entrada do VPN Switch para Windows 11
"""

import sys
import os
import ctypes

def is_admin() -> bool:
    """Verifica se o processo possui privilégios de Administrador no Windows."""
    if os.name == 'nt':
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return True


def run_as_admin():
    """Solicita elevação de UAC no Windows e reexecuta o script como Administrador."""
    if os.name == 'nt':
        try:
            # Reexecuta via ShellExecute com verbo 'runas'
            params = " ".join([f'"{arg}"' for arg in sys.argv])
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                params,
                None,
                1  # SW_SHOWNORMAL
            )
            if ret > 32:
                sys.exit(0)
        except Exception as e:
            print(f"[Aviso] Não foi possível solicitar elevação automática: {e}")


def main():
    # 1. Checar privilégios de Administrador no Windows
    if os.name == 'nt' and not is_admin():
        print("Solicitando privilégios de Administrador no Windows...")
        run_as_admin()

    # 2. Verificar dependências de GUI (PyQt6 ou PySide6)
    try:
        from gui import MainWindow, QApplication, QT_LIB
        if QT_LIB is None:
            raise ImportError("Nenhuma biblioteca Qt compatível encontrada (PyQt6 ou PySide6).")
    except ImportError as e:
        print("\n=======================================================")
        print("   [ERRO] Dependências não encontradas!")
        print(f"   {e}")
        print("=======================================================")
        print("Por favor, instale os requisitos executando:")
        print("   pip install -r requirements.txt")
        print("ou dê dois cliques no arquivo 'instalar.bat'")
        print("=======================================================\n")
        input("Pressione Enter para fechar...")
        sys.exit(1)

    # 3. Iniciar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("VPN Switch")
    app.setOrganizationName("VPNSwitchTeam")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
