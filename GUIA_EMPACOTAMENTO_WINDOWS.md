# 📘 Guia de Aprendizados: Empacotamento e Distribuição Windows a partir do Linux

Este documento registra a arquitetura, lições aprendidas e o fluxo padrão definitivo para desenvolver aplicações desktop em Python no Linux e distribuí-las para usuários finais não-técnicos no **Windows 11**.

---

## 🎯 1. O Desafio do Usuário Final no Windows 11

Quando o usuário final não possui conhecimento técnico:
- Ele **não tem Python, pip nem Git instalados**.
- Arquivos `.bat` soltos ou scripts `.py` causam confusão e exigem configuração de ambiente.
- Arquivos `.exe` portáteis sem assinatura digital acionam o **Windows SmartScreen** (*"O Windows protegeu o seu computador"*) e são frequentemente bloqueados por navegadores ou mensageiros (WhatsApp/Discord).

---

## 💡 2. A Solução Tradicional de Alta Aceitação: Instalador Nativo (`.MSI`)

A melhor experiência para o usuário Windows é o pacote **`.MSI` (Microsoft Windows Installer)**:
1. **Instalação com 2 cliques:** Padrão familiar de instalação do Windows.
2. **Escopo por Usuário (`LocalAppDataFolder`):**
   - Instala em `C:\Users\<Usuario>\AppData\Local\Programs\<NomeDoApp>`.
   - **Vantagem crítica:** Não requer privilégios de Administrador durante a instalação, evitando erros de permissão de pasta em ambientes corporativos ou restritos.
3. **Criação Automática de Atalhos:** Coloca ícone com nome limpo na Área de Trabalho e no Menu Iniciar.
4. **Desinstalador Integrado:** Registra automaticamente no *"Adicionar ou Remover Programas"* do Windows.

---

## 🏗️ 3. Arquitetura de Empacotamento

### A. Geração do `.MSI` com `cx_Freeze` ([`setup_msi.py`](setup_msi.py))
```python
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os", "sys", "json", "urllib", "socket", "PyQt6", "requests"],
    "include_files": [("vpn_engine.py", "vpn_engine.py"), ("gui.py", "gui.py")],
    "include_msvcr": True  # Inclui as bibliotecas de C Runtime da Microsoft
}

bdist_msi_options = {
    "initial_target_dir": r"[LocalAppDataFolder]\VPNSwitch",
    "upgrade_code": "{A3B8C1D2-4E5F-6A7B-8C9D-0E1F2A3B4C5D}",
    "all_users": False  # Escopo do usuário local
}
```

### B. Geração do `.EXE` Portátil com `PyInstaller`
Para casos onde um executável único sem instalação é preferido:
```bash
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "NomeApp" main.py
```
- `--windowed` (ou `-w`): Não abre a janela preta de prompt (CMD).
- `--uac-admin`: Solicita permissão de administrador no Windows ao iniciar para tarefas que exigem privilégios de rede/sistema.

---

## ☁️ 4. Fluxo de Cross-Compilation Linux ➔ Windows via GitHub Actions

Como bibliotecas gráficas (PyQt6) e executáveis Windows dependem de DLLs nativas do Windows, a melhor prática não é usar emuladores pesados locais, mas sim **máquinas virtuais Windows reais na nuvem**:

### Pipeline de Build ([`.github/workflows/build_windows.yml`](.github/workflows/build_windows.yml))
1. **Runner:** `runs-on: windows-latest`
2. **Ambiente:** `actions/setup-python@v5` (Python 3.11 x64)
3. **Compilação:**
   - Executa `python setup_msi.py bdist_msi` para gerar o `.msi`.
   - Executa `pyinstaller` para gerar o `.exe`.
4. **Publicação:** `actions/upload-artifact@v4` disponibiliza o ZIP com os instaladores prontos para download.

---

## ⚡ 5. Automação Completa via Terminal Linux (Playbook)

Com o **GitHub CLI (`gh`)**, todo o ciclo é automatizado direto do terminal:

```bash
# 1. Inicializar repositório Git local
git init -b main
git add .
git commit -m "feat: setup windows installer pipeline"

# 2. Criar repositório privado no GitHub e subir o código
gh repo create nome-do-projeto --private --source=. --remote=origin --push

# 3. Disparar e acompanhar a compilação no Windows Actions
gh workflow run build_windows.yml
gh run watch

# 4. Baixar os instaladores prontos direto para o Linux
gh run download --name "VPN-Switch-Windows-Installers" --dir "./dist_windows"
```

---

## 🛡️ 6. Boas Práticas para Drivers e Dependências Externas (OpenVPN / TAP)

Em aplicativos que exigem drivers de terceiros no Windows:
1. **Detecção Graciosa no Código:**
   - O aplicativo verifica se o executável/driver existe (`C:\Program Files\OpenVPN\bin\openvpn.exe`, `PATH`, etc.).
2. **Popup Orientado à Ação:**
   - Se ausente, exibe uma janela amigável com botão de 1 clique para abrir o instalador oficial ou sugere o comando oficial do Windows Package Manager:
     ```powershell
     winget install OpenVPNTechnologies.OpenVPN
     ```
3. **Gerenciamento de Processos no Windows:**
   - Sempre usar `CREATE_NO_WINDOW` (`0x08000000`) no `subprocess.Popen`.
   - Ao fechar o app, garantir o encerramento do processo em árvore com `taskkill /F /IM openvpn.exe`.
