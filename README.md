# ⚡ VPN Switch - Windows 11 Edition

Aplicativo completo de VPN com navegador de servidores públicos (VPN Gate), medição de latência (ping) em tempo real, suporte para importação de perfis `.ovpn` próprios (ProtonVPN, VPS, etc.) e interface moderna com tema escuro Fluent inspirada no Windows 11.

---

## 🚀 Funcionalidades

1. **Painel Rápido (1-Clique)**:
   - Status visual em tempo real (⚪ Desconectado / 🟢 Conectado / ⏳ Conectando).
   - Detecção automática de IP Público e Geolocalização (País, Cidade, Provedor).
   - Botão grande alternador: `⚡ LIGAR VPN` / `🔴 DESLIGAR VPN`.
   - Log completo colorido com histórico de conexão e diagnóstico em tempo real.

2. **Explorador de Servidores & Ping**:
   - Lista dinâmica de centenas de servidores gratuitos da rede global **VPN Gate**.
   - **Filtros por Região**:
     - 🌎 América Latina (Peru 🇵🇪, Argentina 🇦🇷, Chile 🇨🇱, Colômbia 🇨🇴, etc.)
     - 🗽 Américas (EUA 🇺🇸, Canadá 🇨🇦, América Latina)
     - 🏰 Europa (Alemanha 🇩🇪, França 🇫🇷, Reino Unido 🇬🇧, etc.)
     - ⛩️ Ásia (Japão 🇯🇵, Coreia 🇰🇷, Singapura 🇸🇬, etc.)
     - 🌍 Todas as Regiões
   - **Teste de Latência Real (Ping TCP)** em paralelo:
     - ⚡ `< 130 ms` (Excelente - Verde)
     - 📶 `< 250 ms` (Bom - Azul)
     - 🐢 `> 250 ms` (Alto - Laranja)
   - Tabela ordenável por qualquer coluna (clicando no cabeçalho).
   - Botão para definir servidor favorito como padrão ou conectar imediatamente.

3. **Importação Customizada de `.ovpn`**:
   - Suporte para importar arquivos `.ovpn` próprios (ProtonVPN, NordVPN, VPS particular, etc.).

4. **Gerenciador de Rede no Windows 11**:
   - Execução transparente via `openvpn.exe` em segundo plano (sem janelas pretas de prompt).
   - Elevação automática de privilégios de Administrador (UAC) para configurar rotas de rede com segurança.
   - Encerramento limpo de rotas e conexões ao desligar ou fechar o app.

---

## 📦 Como Usar no Windows 11

### Pré-requisitos
1. **OpenVPN**:
   - É necessário ter o OpenVPN instalado no Windows (ele inclui o driver de rede TAP/Wintun).
   - **Instalação rápida via Terminal/PowerShell**:
     ```powershell
     winget install OpenVPNTechnologies.OpenVPN
     ```
   - Ou baixe o instalador oficial em: [https://openvpn.net/community-downloads/](https://openvpn.net/community-downloads/)

2. **Python 3.10+** (Caso vá rodar via script):
   - Baixe em [https://www.python.org/](https://www.python.org/) e marque a opção **"Add Python to PATH"** na instalação.

---

### ▶️ Como Iniciar

#### Opção A: Execução Direta (Recomendada)
1. Dê dois cliques em **`iniciar.bat`**.
2. O script verificará as dependências automaticamente e abrirá o aplicativo.
3. Se o Windows solicitar permissão de Administrador (UAC), clique em **Sim**.

#### Opção B: Gerar um `.exe` Standalone (Sem precisar de Python depois)
1. Dê dois cliques em **`compilar_exe.bat`**.
2. Aguarde a compilação do PyInstaller.
3. Pronto! O executável portátil será gerado na pasta `dist/VPN-Switch-Portable.exe`. Você pode enviar esse arquivo `.exe` direto para seu amigo!

---

## 📂 Estrutura do Projeto

```text
vpnparaezeky/
├── main.py             # Ponto de entrada com verificação de Admin e inicialização
├── gui.py              # Interface gráfica moderna Windows 11 em PyQt6
├── vpn_engine.py       # Gerenciador OpenVPN, API VPN Gate, medição de Ping e IP
├── requirements.txt    # Dependências Python (PyQt6, requests)
├── iniciar.bat         # Atalho para rodar no Windows 11
├── instalar.bat        # Atalho para instalar dependências
├── compilar_exe.bat    # Gerador de arquivo .exe portátil
└── README.md           # Este manual de instruções
```
