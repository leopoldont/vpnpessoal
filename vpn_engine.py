"""
vpn_engine.py - Mecanismo de Gerenciamento OpenVPN, API VPN Gate e Conexões (Windows 11 / Multiplataforma)
"""

import os
import sys
import time
import json
import base64
import csv
import socket
import re
import shutil
import subprocess
import threading
import urllib.request
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable

# Códigos de Regiões para Filtro
LATAM_CODES = {'PE', 'AR', 'CL', 'CO', 'MX', 'UY', 'PY', 'BO', 'EC', 'VE', 'CR', 'PA', 'GT', 'HN', 'SV', 'NI', 'BR'}
AMERICAS_CODES = {'US', 'CA', 'MX'}.union(LATAM_CODES)
EUROPE_CODES = {'DE', 'FR', 'GB', 'NL', 'RO', 'IT', 'ES', 'CH', 'SE', 'NO', 'PL', 'UA', 'CZ', 'AT', 'FI', 'PT', 'BE', 'DK', 'IE', 'NO', 'SE'}
ASIA_CODES = {'JP', 'KR', 'SG', 'TH', 'ID', 'VN', 'IN', 'MY', 'PH', 'TW', 'HK'}

FLAGS = {
    'PE': '🇵🇪', 'AR': '🇦🇷', 'CL': '🇨🇱', 'CO': '🇨🇴', 'MX': '🇲🇽', 'UY': '🇺🇾', 'PY': '🇵🇾', 'BO': '🇧🇴',
    'EC': '🇪🇨', 'VE': '🇻🇪', 'CR': '🇨🇷', 'PA': '🇵🇦', 'BR': '🇧🇷', 'GT': '🇬🇹', 'HN': '🇭🇳', 'SV': '🇸🇻',
    'US': '🇺🇸', 'CA': '🇨🇦',
    'DE': '🇩🇪', 'FR': '🇫🇷', 'GB': '🇬🇧', 'NL': '🇳🇱', 'RO': '🇷🇴', 'IT': '🇮🇹', 'ES': '🇪🇸', 'CH': '🇨🇭',
    'SE': '🇸🇪', 'NO': '🇳🇴', 'PL': '🇵🇱', 'UA': '🇺🇦', 'PT': '🇵🇹', 'BE': '🇧🇪', 'DK': '🇩🇰', 'IE': '🇮🇪',
    'JP': '🇯🇵', 'KR': '🇰🇷', 'SG': '🇸🇬', 'TH': '🇹🇭', 'ID': '🇮🇩', 'VN': '🇻🇳', 'IN': '🇮🇳', 'AU': '🇦🇺',
    'RU': '🇷🇺', 'MY': '🇲🇾', 'PH': '🇵🇭', 'TW': '🇹🇼', 'HK': '🇭🇰'
}


def get_app_dir() -> Path:
    """Retorna o diretório padrão de configurações do app no Windows / SO atual."""
    if os.name == 'nt':
        base = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA') or str(Path.home() / "AppData" / "Roaming")
        app_dir = Path(base) / "VPNSwitch"
    else:
        app_dir = Path.home() / ".config" / "vpn-switch"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def find_openvpn_executable() -> Optional[str]:
    """
    Localiza o executável do OpenVPN no Windows 11 ou Linux.
    Procura em locais padrão do Windows, no diretório local do app ou no PATH.
    """
    if os.name == 'nt':
        # 1. Caminhos clássicos de instalação do OpenVPN no Windows
        candidatos = [
            r"C:\Program Files\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files\OpenVPN Technologies\OpenVPN Client\core\openvpn.exe",
            r"C:\Program Files\OpenVPNConnect\OpenVPNConnect.exe",
            # Caminho relativo ao executável ou script atual
            str(Path(__file__).resolve().parent / "bin" / "openvpn.exe"),
            str(Path(__file__).resolve().parent / "openvpn.exe"),
        ]
        for c in candidatos:
            if os.path.isfile(c):
                return c

        # 2. Busca no PATH do sistema
        which_path = shutil.which("openvpn.exe") or shutil.which("openvpn")
        if which_path:
            return which_path

        return None
    else:
        # Linux / Unix
        return shutil.which("openvpn")


class VpnEngine:
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        self.log_callback = log_callback
        self.app_dir = get_app_dir()
        self.profile_path = self.app_dir / "vpn_profile.ovpn"
        
        self.openvpn_proc: Optional[subprocess.Popen] = None
        self.is_connected = False
        self.is_connecting = False
        self._stop_monitor = threading.Event()
        
        self.raw_servers: List[Dict] = []
        self.tested_servers: Dict[str, int] = {}  # IP -> ping_ms
        self.active_server_desc = "Automático (Melhor Latência LatAm / Global)"

    def log(self, message: str, tag: str = "info"):
        if self.log_callback:
            self.log_callback(message, tag)
        else:
            print(f"[{tag.upper()}] {message}")

    def query_public_ip(self) -> Optional[Dict]:
        """Consulta o IP público atual e detalhes de geolocalização."""
        urls = [
            ("https://ipinfo.io/json", lambda d: d),
            ("https://api.ipify.org?format=json", lambda d: {"ip": d.get("ip"), "country": "N/A", "city": "", "org": ""}),
            ("https://ifconfig.me/all.json", lambda d: {"ip": d.get("ip_addr"), "country": d.get("country_code", "N/A"), "city": "", "org": ""})
        ]
        
        for url, parser in urls:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "VPNSwitch-Windows/1.0 (curl/7.68.0)"}
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    raw = response.read().decode('utf-8', errors='ignore')
                    data = json.loads(raw)
                    return parser(data)
            except Exception:
                continue
        return None

    def fetch_vpngate_servers(self) -> List[Dict]:
        """Baixa a lista de servidores públicos da API do VPN Gate."""
        url = "http://www.vpngate.net/api/iphone/"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("*")]
        if not lines:
            raise ValueError("Resposta da API VPN Gate veio vazia ou corrompida.")
        
        reader = csv.DictReader(lines)
        servers = [s for s in reader if s.get("OpenVPN_ConfigData_Base64")]
        self.raw_servers = servers
        return servers

    def test_single_server_ping(self, server_dict: Dict) -> int:
        """Mede a latência TCP real para as portas declaradas no arquivo .ovpn."""
        ovpn_raw = base64.b64decode(server_dict.get('OpenVPN_ConfigData_Base64', '')).decode('utf-8', errors='ignore')
        remotes = re.findall(r'^\s*remote\s+([^\s]+)\s+(\d+)', ovpn_raw, re.MULTILINE)
        
        best_ping = 9999
        for host, port_str in remotes:
            t0 = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect((host, int(port_str)))
                sock.close()
                ms = int((time.time() - t0) * 1000)
                if ms < best_ping:
                    best_ping = ms
            except Exception:
                continue
        
        server_dict['measured_ping'] = best_ping
        return best_ping

    def test_all_servers_latency(self, servers: List[Dict], progress_callback: Optional[Callable[[Dict[str, int]], None]] = None) -> Dict[str, int]:
        """Mede a latência de múltiplos servidores em paralelo."""
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            future_to_server = {executor.submit(self.test_single_server_ping, s): s for s in servers}
            for future in concurrent.futures.as_completed(future_to_server):
                s = future_to_server[future]
                try:
                    ping = future.result()
                    ip = s.get('IP')
                    if ip:
                        results[ip] = ping
                        self.tested_servers[ip] = ping
                except Exception:
                    pass
                
                if progress_callback:
                    progress_callback(results)
                    
        return results

    def save_ovpn_profile(self, ovpn_content: str, description: str = ""):
        """Salva a configuração .ovpn ativa no disco."""
        with open(self.profile_path, "w", encoding="utf-8") as f:
            f.write(ovpn_content)
        if description:
            self.active_server_desc = description

    def test_ovpn_text_reachability(self, ovpn_text: str) -> Tuple[bool, str, int]:
        """Testa se os remotes em uma configuração .ovpn estão acessíveis."""
        remotes = re.findall(r'^\s*remote\s+([^\s]+)\s+(\d+)', ovpn_text, re.MULTILINE)
        for host, port in remotes:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.5)
                sock.connect((host, int(port)))
                sock.close()
                return True, host, int(port)
            except Exception:
                continue
        return False, "", 0

    def select_best_auto_ovpn(self) -> Tuple[Optional[str], Optional[str]]:
        """Seleciona a melhor configuração disponível (salva local, LatAm, Américas ou Menor Latência Global)."""
        # 1. Se já tem perfil salvo válido
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8", errors="ignore") as f:
                    ovpn = f.read()
                alive, host, _ = self.test_ovpn_text_reachability(ovpn)
                if alive:
                    return ovpn, f"Perfil Padrão Salvo ({host})"
            except Exception:
                pass

        if not self.raw_servers:
            return None, None

        # 2. Priorizar América Latina com boa latência
        latam_candidates = [
            s for s in self.raw_servers 
            if s.get('CountryShort') in LATAM_CODES and s.get('measured_ping', 9999) < 500
        ]
        if latam_candidates:
            best_latam = min(latam_candidates, key=lambda x: x.get('measured_ping', 9999))
            ovpn = base64.b64decode(best_latam.get('OpenVPN_ConfigData_Base64')).decode('utf-8', errors='ignore')
            return ovpn, f"{FLAGS.get(best_latam.get('CountryShort'), '🌐')} {best_latam.get('CountryLong')} ({best_latam.get('IP')})"

        # 3. Priorizar Américas (EUA / Canadá)
        americas_candidates = [
            s for s in self.raw_servers 
            if s.get('CountryShort') in AMERICAS_CODES and s.get('measured_ping', 9999) < 300
        ]
        if americas_candidates:
            best_am = min(americas_candidates, key=lambda x: x.get('measured_ping', 9999))
            ovpn = base64.b64decode(best_am.get('OpenVPN_ConfigData_Base64')).decode('utf-8', errors='ignore')
            return ovpn, f"{FLAGS.get(best_am.get('CountryShort'), '🌐')} {best_am.get('CountryLong')} ({best_am.get('IP')})"

        # 4. Servidor global com menor ping
        valid_pings = [s for s in self.raw_servers if s.get('measured_ping', 9999) < 400]
        if valid_pings:
            best_global = min(valid_pings, key=lambda x: x.get('measured_ping', 9999))
            ovpn = base64.b64decode(best_global.get('OpenVPN_ConfigData_Base64')).decode('utf-8', errors='ignore')
            return ovpn, f"{FLAGS.get(best_global.get('CountryShort'), '🌐')} {best_global.get('CountryLong')} ({best_global.get('IP')})"

        # 5. Qualquer um da lista como fallback
        first = self.raw_servers[0]
        ovpn = base64.b64decode(first.get('OpenVPN_ConfigData_Base64')).decode('utf-8', errors='ignore')
        return ovpn, f"{FLAGS.get(first.get('CountryShort'), '🌐')} {first.get('CountryLong')} ({first.get('IP')})"

    def start_vpn(self, ovpn_content: Optional[str] = None, on_connected_callback: Optional[Callable[[Dict], None]] = None, on_failure_callback: Optional[Callable[[str], None]] = None):
        """Inicia a conexão OpenVPN em segundo plano e monitora o log em tempo real."""
        openvpn_bin = find_openvpn_executable()
        if not openvpn_bin:
            err = (
                "OpenVPN não encontrado no Windows.\n"
                "Por favor, instale o OpenVPN Community ou certifique-se de que openvpn.exe está instalado em:\n"
                "C:\\Program Files\\OpenVPN\\bin\\openvpn.exe"
            )
            self.log(f"❌ {err}", tag="error")
            if on_failure_callback:
                on_failure_callback(err)
            return

        if not ovpn_content:
            ovpn_content, desc = self.select_best_auto_ovpn()
            if not ovpn_content:
                err = "Nenhum servidor disponível para conexão. Atualize a lista na aba Servidores."
                self.log(f"❌ {err}", tag="error")
                if on_failure_callback:
                    on_failure_callback(err)
                return
            if desc:
                self.active_server_desc = desc

        # Salva o arquivo .ovpn
        self.save_ovpn_profile(ovpn_content)

        # Ajuste de compatibilidade para Windows no .ovpn se necessário
        prepared_ovpn = self._prepare_ovpn_for_windows(ovpn_content)
        with open(self.profile_path, "w", encoding="utf-8") as f:
            f.write(prepared_ovpn)

        self.is_connecting = True
        self._stop_monitor.clear()

        def worker():
            self.log(f"🚀 Iniciando OpenVPN com: {openvpn_bin}", tag="info")
            self.log(f"📁 Carregando perfil: {self.profile_path}", tag="info")
            
            # Flags para Windows (sem janela preta de console popup)
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0x08000000

            cmd = [openvpn_bin, "--config", str(self.profile_path)]

            try:
                self.openvpn_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=creationflags
                )
            except PermissionError:
                msg = "Permissão negada ao executar o OpenVPN. Execute o aplicativo como Administrador no Windows."
                self.log(f"❌ {msg}", tag="error")
                self.is_connecting = False
                if on_failure_callback:
                    on_failure_callback(msg)
                return
            except Exception as e:
                msg = f"Erro ao iniciar processo OpenVPN: {e}"
                self.log(f"❌ {msg}", tag="error")
                self.is_connecting = False
                if on_failure_callback:
                    on_failure_callback(msg)
                return

            connected = False
            fail_reason = ""

            # Loop de leitura contínua de stdout
            while self.openvpn_proc and self.openvpn_proc.poll() is None:
                line = self.openvpn_proc.stdout.readline()
                if not line:
                    if self._stop_monitor.is_set():
                        break
                    time.sleep(0.05)
                    continue

                clean_line = line.strip()
                if not clean_line:
                    continue

                # Filtrar ruídos desnecessários e logar
                if any(x in clean_line for x in ["MANAGEMENT:", "TAP-WIN32", "Route addition", "netsh"]):
                    self.log(f"⚙️ {clean_line}", tag="info")
                elif "WARNING" in clean_line:
                    self.log(f"⚠️ {clean_line}", tag="warning")
                elif "ERROR" in clean_line or "AUTH_FAILED" in clean_line or "TLS Error" in clean_line:
                    self.log(f"❌ {clean_line}", tag="error")
                    fail_reason = clean_line
                else:
                    self.log(f"📡 {clean_line}", tag="info")

                # Detectar sucesso de inicialização
                if "Initialization Sequence Completed" in clean_line or "Peer Connection Initiated" in clean_line:
                    connected = True
                    self.is_connected = True
                    self.is_connecting = False
                    self.log("🛡️ TÚNEL SEGURO ESTABELECIDO COM SUCESSO!", tag="success")
                    
                    # Checar novo IP
                    time.sleep(1.5)
                    new_ip_info = self.query_public_ip()
                    if new_ip_info:
                        self.log(f"🌐 Novo IP Público: {new_ip_info.get('ip')}", tag="bold")
                        self.log(f"📍 Região: {new_ip_info.get('country')} - {new_ip_info.get('city')} ({new_ip_info.get('org')})", tag="bold")
                    
                    if on_connected_callback:
                        on_connected_callback(new_ip_info or {})
                    break

            # Se o processo encerrou antes de conectar
            if not connected and not self._stop_monitor.is_set():
                self.is_connected = False
                self.is_connecting = False
                msg = fail_reason or "Conexão encerrada antes de completar a inicialização."
                self.log(f"❌ Falha na conexão: {msg}", tag="error")
                if on_failure_callback:
                    on_failure_callback(msg)

        threading.Thread(target=worker, daemon=True).start()

    def _prepare_ovpn_for_windows(self, ovpn_text: str) -> str:
        """Garante diretivas recomendadas para Windows (ignorar certificados locais se embutidos, etc.)."""
        lines = ovpn_text.splitlines()
        filtered = []
        for l in lines:
            # Remover diretivas incompatíveis com Windows ou já gerenciadas
            if l.strip().startswith("dev-type") or l.strip().startswith("group") or l.strip().startswith("user"):
                if os.name == 'nt':
                    continue
            filtered.append(l)
        
        # Adiciona flag para desabilitar prompt de credenciais se não requerido
        final_text = "\n".join(filtered)
        if "auth-nocache" not in final_text:
            final_text += "\nauth-nocache\n"
        if "verb" not in final_text:
            final_text += "\nverb 3\n"
        return final_text

    def stop_vpn(self, on_disconnected_callback: Optional[Callable[[Optional[Dict]], None]] = None):
        """Desconecta a VPN e restaura a rota direta."""
        self._stop_monitor.set()
        self.is_connected = False
        self.is_connecting = False

        def worker():
            self.log("🔌 Encerrando conexão VPN...", tag="warning")
            if self.openvpn_proc:
                try:
                    self.openvpn_proc.terminate()
                    self.openvpn_proc.wait(timeout=2.5)
                except Exception:
                    try:
                        self.openvpn_proc.kill()
                    except Exception:
                        pass
                self.openvpn_proc = None

            # No Windows, garantir que nenhum processo órfão de openvpn permaneça
            if os.name == 'nt':
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "openvpn.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

            time.sleep(1.0)
            self.log("✅ VPN Desconectada. Tráfego direto restabelecido.", tag="success")
            
            ip_info = self.query_public_ip()
            if ip_info:
                self.log(f"🌐 IP Atual: {ip_info.get('ip')} ({ip_info.get('country')})", tag="info")

            if on_disconnected_callback:
                on_disconnected_callback(ip_info)

        threading.Thread(target=worker, daemon=True).start()
