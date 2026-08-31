"""
gui.py - Interface Gráfica Moderna Estilo Windows 11 (PyQt6 / PySide6) para o VPN Switch
"""

import sys
import os
import time
import base64
import re
import webbrowser
from datetime import datetime
from typing import Optional, Dict, List

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
        QHeaderView, QComboBox, QTabWidget, QFrame, QFileDialog,
        QMessageBox, QLineEdit, QAbstractItemView
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon
    QT_LIB = "PyQt6"
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
            QHeaderView, QComboBox, QTabWidget, QFrame, QFileDialog,
            QMessageBox, QLineEdit, QAbstractItemView
        )
        from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal, QTimer
        from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon
        QT_LIB = "PySide6"
    except ImportError:
        QT_LIB = None

from vpn_engine import (
    VpnEngine, FLAGS, LATAM_CODES, AMERICAS_CODES, EUROPE_CODES, ASIA_CODES,
    find_openvpn_executable
)


WIN11_DARK_STYLESHEET = """
QWidget {
    background-color: #12131a;
    color: #e2e8f0;
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #2d3748;
    background-color: #1a1b26;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #161722;
    color: #94a3b8;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #1a1b26;
    color: #38bdf8;
    border-bottom: 2px solid #38bdf8;
}

QTabBar::tab:hover:!selected {
    background-color: #232538;
    color: #f1f5f9;
}

QFrame.card {
    background-color: #1e2030;
    border: 1px solid #2e344e;
    border-radius: 10px;
    padding: 14px;
}

QLabel {
    background-color: transparent;
}

QPushButton {
    background-color: #2e344e;
    color: #f8fafc;
    border: 1px solid #3b4261;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3d4566;
    border-color: #4f5882;
}

QPushButton:pressed {
    background-color: #222638;
}

QPushButton:disabled {
    background-color: #1a1b26;
    color: #4b5563;
    border-color: #24283b;
}

QPushButton.primary-connect {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #0284c7);
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 12px;
}

QPushButton.primary-connect:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #0369a1);
}

QPushButton.primary-disconnect {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #b91c1c);
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 12px;
}

QPushButton.primary-disconnect:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #991b1b);
}

QTextEdit {
    background-color: #0f1017;
    color: #cbd5e1;
    border: 1px solid #282d42;
    border-radius: 6px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
}

QTableWidget {
    background-color: #141520;
    alternate-background-color: #1a1b2b;
    border: 1px solid #2a2f45;
    border-radius: 6px;
    gridline-color: #24283b;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 4px;
}

QHeaderView::section {
    background-color: #1a1b2b;
    color: #94a3b8;
    padding: 6px;
    border: none;
    border-right: 1px solid #2a2f45;
    border-bottom: 1px solid #2a2f45;
    font-weight: bold;
}

QComboBox, QLineEdit {
    background-color: #1c1e2d;
    border: 1px solid #2d334d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f1f5f9;
}

QComboBox:hover, QLineEdit:hover {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QScrollBar:vertical {
    background: #141520;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2e344e;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4a547d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class FetchServersWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, engine: VpnEngine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            servers = self.engine.fetch_vpngate_servers()
            self.finished.emit(servers)
        except Exception as e:
            self.error.emit(str(e))


class TestLatencyWorker(QThread):
    progress = pyqtSignal(dict)
    completed = pyqtSignal()

    def __init__(self, engine: VpnEngine, servers: list):
        super().__init__()
        self.engine = engine
        self.servers = servers

    def run(self):
        def on_prog(tested_map):
            self.progress.emit(tested_map)
        
        self.engine.test_all_servers_latency(self.servers, progress_callback=on_prog)
        self.completed.emit()


class NumericTableWidgetItem(QTableWidgetItem):
    """Permite ordenação numérica correta nas colunas de Ping, Velocidade e Sessões."""
    def __init__(self, text, sort_val):
        super().__init__(text)
        self.sort_val = sort_val

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.sort_val < other.sort_val
        return super().__lt__(other)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPN Switch & Server Browser - Windows 11 Edition")
        self.resize(840, 720)
        self.setMinimumSize(760, 600)

        self.engine = VpnEngine(log_callback=self.on_engine_log)
        self.selected_server: Optional[Dict] = None
        self.is_busy = False

        self.init_ui()
        self.apply_styles()

        # Checagem inicial de IP e OpenVPN
        QTimer.singleShot(100, self.initial_startup_tasks)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # TAB 1: Painel Rápido & Log
        self.tab1 = QWidget()
        self.setup_tab1()
        self.tabs.addTab(self.tab1, "⚡ Painel Rápido")

        # TAB 2: Explorador de Servidores & Ping
        self.tab2 = QWidget()
        self.setup_tab2()
        self.tabs.addTab(self.tab2, "🌐 Lista de Servidores & Ping")

    def setup_tab1(self):
        layout = QVBoxLayout(self.tab1)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Card de Status
        card_status = QFrame()
        card_status.setProperty("class", "card")
        status_layout = QVBoxLayout(card_status)
        status_layout.setSpacing(6)

        self.lbl_status = QLabel("⚪ DESCONECTADO (Conexão Direta)")
        self.lbl_status.setStyleSheet("font-size: 18px; font-weight: bold; color: #94a3b8;")
        status_layout.addWidget(self.lbl_status)

        self.lbl_ip = QLabel("🌐 IP Público: Consultando...")
        self.lbl_ip.setStyleSheet("font-size: 13px; color: #e2e8f0;")
        status_layout.addWidget(self.lbl_ip)

        self.lbl_loc = QLabel("📍 Localização: Consultando...")
        self.lbl_loc.setStyleSheet("font-size: 13px; color: #cbd5e1;")
        status_layout.addWidget(self.lbl_loc)

        self.lbl_target_server = QLabel(f"🎯 Servidor Alvo: <span style='color: #38bdf8;'><b>{self.engine.active_server_desc}</b></span>")
        self.lbl_target_server.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_target_server.setStyleSheet("font-size: 13px;")
        status_layout.addWidget(self.lbl_target_server)

        layout.addWidget(card_status)

        # Botão Grande de Conexão (Toggle)
        self.btn_toggle = QPushButton("⚡ LIGAR VPN")
        self.btn_toggle.setProperty("class", "primary-connect")
        self.btn_toggle.setFixedHeight(50)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.on_toggle_vpn_clicked)
        layout.addWidget(self.btn_toggle)

        # Card do Log em Tempo Real
        card_log = QFrame()
        card_log.setProperty("class", "card")
        log_layout = QVBoxLayout(card_log)
        log_layout.setSpacing(8)

        lbl_log_title = QLabel("📄 Log da Conexão em Tempo Real:")
        lbl_log_title.setStyleSheet("font-weight: bold; color: #94a3b8;")
        log_layout.addWidget(lbl_log_title)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)

        # Botões inferiores do log
        log_btn_layout = QHBoxLayout()
        self.btn_clear_log = QPushButton("🗑️ Limpar Log")
        self.btn_clear_log.clicked.connect(self.txt_log.clear)
        log_btn_layout.addWidget(self.btn_clear_log)

        log_btn_layout.addStretch()

        self.btn_goto_servers = QPushButton("🌐 Explorar Lista de Servidores ➔")
        self.btn_goto_servers.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        log_btn_layout.addWidget(self.btn_goto_servers)

        log_layout.addLayout(log_btn_layout)
        layout.addWidget(card_log, stretch=1)

    def setup_tab2(self):
        layout = QVBoxLayout(self.tab2)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Barra Superior de Filtros e Busca
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        filter_bar.addWidget(QLabel("Região:"))
        self.combo_region = QComboBox()
        self.combo_region.addItem("🌍 Todas as Regiões", "ALL")
        self.combo_region.addItem("🌎 América Latina (Peru, AR, CL, CO...)", "LATAM")
        self.combo_region.addItem("🗽 Américas (EUA, Canadá, LatAm)", "AMERICAS")
        self.combo_region.addItem("🏰 Europa (Alemanha, França, UK...)", "EUROPE")
        self.combo_region.addItem("⛩️ Ásia (Japão, Coreia, Singapura)", "ASIA")
        self.combo_region.currentIndexChanged.connect(self.apply_table_filters)
        filter_bar.addWidget(self.combo_region)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Filtrar por país ou IP...")
        self.input_search.textChanged.connect(self.apply_table_filters)
        filter_bar.addWidget(self.input_search, stretch=1)

        self.btn_refresh = QPushButton("🔄 Atualizar Lista & Ping")
        self.btn_refresh.clicked.connect(self.start_fetch_and_test_servers)
        filter_bar.addWidget(self.btn_refresh)

        layout.addLayout(filter_bar)

        # Status contagem
        self.lbl_server_count = QLabel("Carregando servidores...")
        self.lbl_server_count.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.lbl_server_count)

        # Tabela de Servidores
        self.table_servers = QTableWidget()
        self.table_servers.setColumnCount(7)
        self.table_servers.setHorizontalHeaderLabels([
            "País / Região", "IP / Host", "Latência (Ping)", "Velocidade",
            "Criptografia / Proto", "Sessões", "Qualidade"
        ])
        self.table_servers.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_servers.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_servers.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_servers.setAlternatingRowColors(True)
        self.table_servers.setSortingEnabled(True)
        self.table_servers.verticalHeader().setVisible(False)
        self.table_servers.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_servers.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_servers.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_servers.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_servers.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_servers.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_servers.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table_servers.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.table_servers.doubleClicked.connect(self.on_connect_selected_clicked)
        layout.addWidget(self.table_servers, stretch=1)

        # Barra de Ações Inferior
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.btn_connect_selected = QPushButton("🚀 Conectar Neste Servidor")
        self.btn_connect_selected.setEnabled(False)
        self.btn_connect_selected.clicked.connect(self.on_connect_selected_clicked)
        action_bar.addWidget(self.btn_connect_selected)

        self.btn_set_default = QPushButton("⭐ Salvar como Padrão do Toggle")
        self.btn_set_default.setEnabled(False)
        self.btn_set_default.clicked.connect(self.on_set_default_clicked)
        action_bar.addWidget(self.btn_set_default)

        action_bar.addStretch()

        self.btn_import_ovpn = QPushButton("📁 Importar .ovpn Próprio (Proton / VPS)")
        self.btn_import_ovpn.clicked.connect(self.on_import_custom_ovpn_clicked)
        action_bar.addWidget(self.btn_import_ovpn)

        layout.addLayout(action_bar)

    def apply_styles(self):
        self.setStyleSheet(WIN11_DARK_STYLESHEET)

    def append_log(self, text: str, tag: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "info": "#60a5fa",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "error": "#f87171",
            "bold": "#f1f5f9"
        }
        color = color_map.get(tag, "#cbd5e1")
        font_weight = "bold" if tag in ["success", "error", "bold"] else "normal"

        html_line = f"<span style='color: #64748b;'>[{timestamp}]</span> <span style='color: {color}; font-weight: {font_weight};'>{text}</span><br>"
        
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)
        self.txt_log.insertHtml(html_line)
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)

    def on_engine_log(self, text: str, tag: str):
        # Thread-safe via QTimer se necessário
        QTimer.singleShot(0, lambda: self.append_log(text, tag))

    def initial_startup_tasks(self):
        self.append_log("✨ VPN Switch Windows 11 iniciado com sucesso!", "info")
        
        # Verificar openvpn.exe
        openvpn_bin = find_openvpn_executable()
        if openvpn_bin:
            self.append_log(f"✅ OpenVPN detectado no sistema: {openvpn_bin}", "success")
        else:
            self.append_log("⚠️ OpenVPN executável não encontrado automaticamente no Windows.", "warning")
            self.show_openvpn_missing_dialog()

        # Atualizar IP inicial
        self.refresh_ip_async()

        # Baixar lista de servidores
        self.start_fetch_and_test_servers()

    def show_openvpn_missing_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("OpenVPN Necessário")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "<h3>OpenVPN não encontrado no Windows</h3>"
            "<p>Para que o VPN Switch possa criar os túneis de rede no Windows 11, é necessário ter o OpenVPN instalado com o driver TAP/Wintun.</p>"
            "<p><b>Como resolver facilmente:</b></p>"
            "<ul>"
            "<li>Baixe e instale o <a href='https://openvpn.net/community-downloads/'>OpenVPN Community Installer</a></li>"
            "<li>Ou abra o Terminal / PowerShell e execute:<br><code>winget install OpenVPNTechnologies.OpenVPN</code></li>"
            "</ul>"
        )
        btn_download = msg.addButton("🌐 Abrir Site de Download", QMessageBox.ButtonRole.AcceptRole)
        btn_close = msg.addButton("OK, Entendi", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() == btn_download:
            webbrowser.open("https://openvpn.net/community-downloads/")

    def refresh_ip_async(self):
        def worker():
            info = self.engine.query_public_ip()
            QTimer.singleShot(0, lambda: self.update_ip_display(info))

        threading_thread = threading.Thread(target=worker, daemon=True)
        threading_thread.start()

    def update_ip_display(self, ip_info: Optional[Dict]):
        if ip_info:
            ip = ip_info.get('ip', 'N/A')
            city = ip_info.get('city', '')
            country = ip_info.get('country', '')
            org = ip_info.get('org', '')
            self.lbl_ip.setText(f"🌐 IP Público: <b>{ip}</b>")
            loc_str = f"{country} - {city} ({org})" if city else f"{country} ({org})"
            self.lbl_loc.setText(f"📍 Localização: <b>{loc_str}</b>")
        else:
            self.lbl_ip.setText("🌐 IP Público: Indisponível")
            self.lbl_loc.setText("📍 Localização: N/A")

    def update_connection_ui(self, is_connected: bool, is_connecting: bool = False):
        self.is_busy = is_connecting
        self.btn_toggle.setEnabled(not is_connecting)

        if is_connecting:
            self.lbl_status.setText("⏳ CONECTANDO... (Configurando túnel seguro)")
            self.lbl_status.setStyleSheet("font-size: 18px; font-weight: bold; color: #f59e0b;")
            self.btn_toggle.setText("⏳ Aguarde...")
            self.btn_toggle.setProperty("class", "primary-connect")
        elif is_connected:
            self.lbl_status.setText("🟢 CONECTADO (VPN Ativa e Protegida)")
            self.lbl_status.setStyleSheet("font-size: 18px; font-weight: bold; color: #22c55e;")
            self.btn_toggle.setText("🔴 DESLIGAR VPN")
            self.btn_toggle.setProperty("class", "primary-disconnect")
        else:
            self.lbl_status.setText("⚪ DESCONECTADO (Conexão Direta)")
            self.lbl_status.setStyleSheet("font-size: 18px; font-weight: bold; color: #94a3b8;")
            self.btn_toggle.setText("⚡ LIGAR VPN")
            self.btn_toggle.setProperty("class", "primary-connect")

        self.apply_styles()

    def on_toggle_vpn_clicked(self):
        if self.is_busy:
            return

        if self.engine.is_connected:
            # Desconectar
            self.update_connection_ui(False, is_connecting=True)
            self.engine.stop_vpn(on_disconnected_callback=self.on_vpn_disconnected)
        else:
            # Conectar
            self.update_connection_ui(False, is_connecting=True)
            self.engine.start_vpn(
                ovpn_content=None,
                on_connected_callback=self.on_vpn_connected,
                on_failure_callback=self.on_vpn_failure
            )

    def on_vpn_connected(self, ip_info: Dict):
        QTimer.singleShot(0, lambda: self.update_connection_ui(True))
        QTimer.singleShot(0, lambda: self.update_ip_display(ip_info))

    def on_vpn_failure(self, error_msg: str):
        QTimer.singleShot(0, lambda: self.update_connection_ui(False))
        QTimer.singleShot(0, self.refresh_ip_async)

    def on_vpn_disconnected(self, ip_info: Optional[Dict]):
        QTimer.singleShot(0, lambda: self.update_connection_ui(False))
        QTimer.singleShot(0, lambda: self.update_ip_display(ip_info))

    def start_fetch_and_test_servers(self):
        self.btn_refresh.setEnabled(False)
        self.lbl_server_count.setText("📡 Baixando lista de servidores públicos...")
        self.append_log("📡 Consultando API do VPN Gate...", "info")

        self.fetch_worker = FetchServersWorker(self.engine)
        self.fetch_worker.finished.connect(self.on_servers_fetched)
        self.fetch_worker.error.connect(self.on_servers_fetch_error)
        self.fetch_worker.start()

    def on_servers_fetched(self, servers: list):
        self.append_log(f"📋 {len(servers)} servidores recebidos da rede.", "info")
        self.populate_server_table(servers)
        self.btn_refresh.setEnabled(True)

        # Iniciar medição de ping em background
        self.append_log("⚡ Medindo latência (ping) real dos servidores...", "info")
        self.test_worker = TestLatencyWorker(self.engine, servers)
        self.test_worker.progress.connect(self.on_latency_progress)
        self.test_worker.completed.connect(self.on_latency_completed)
        self.test_worker.start()

    def on_servers_fetch_error(self, err_msg: str):
        self.append_log(f"❌ Erro ao buscar lista de servidores: {err_msg}", "error")
        self.lbl_server_count.setText("Erro ao baixar servidores.")
        self.btn_refresh.setEnabled(True)

    def populate_server_table(self, servers: list):
        self.table_servers.setSortingEnabled(False)
        self.table_servers.setRowCount(len(servers))

        for row, s in enumerate(servers):
            c_short = s.get('CountryShort', '??')
            c_long = s.get('CountryLong', 'Unknown')
            flag = FLAGS.get(c_short, '🌐')
            country_text = f"{flag} {c_long} ({c_short})"
            ip_str = s.get('IP', 'N/A')

            # Ping
            ping_val = s.get('measured_ping', 0)
            ping_item = self.create_ping_item(ping_val)

            # Velocidade
            speed_bps = float(s.get('Speed', 0) or 0)
            speed_mbps = speed_bps / 1_000_000.0
            speed_item = NumericTableWidgetItem(f"{speed_mbps:.1f} Mbps", speed_mbps)

            # Criptografia / Proto
            ovpn_raw = base64.b64decode(s.get('OpenVPN_ConfigData_Base64', '')).decode('utf-8', errors='ignore')
            cipher_match = re.search(r'cipher\s+([^\s]+)', ovpn_raw, re.IGNORECASE)
            proto_match = re.search(r'proto\s+([^\s]+)', ovpn_raw, re.IGNORECASE)
            ciph = cipher_match.group(1) if cipher_match else "AES-128"
            prot = proto_match.group(1).upper() if proto_match else "UDP"
            sec_text = f"{ciph} / {prot}"

            # Usuários
            users_int = int(s.get('NumVpnSessions', 0) or 0)
            users_item = NumericTableWidgetItem(f"{users_int} conexões", users_int)

            # Qualidade
            score = float(s.get('Score', 0) or 0)
            qual_str = "⭐⭐⭐⭐⭐" if score > 1000000 else ("⭐⭐⭐⭐" if score > 500000 else "⭐⭐⭐")

            # Inserir itens
            item_country = QTableWidgetItem(country_text)
            item_country.setData(Qt.ItemDataRole.UserRole, s)  # Guardar dicionário do servidor

            self.table_servers.setItem(row, 0, item_country)
            self.table_servers.setItem(row, 1, QTableWidgetItem(ip_str))
            self.table_servers.setItem(row, 2, ping_item)
            self.table_servers.setItem(row, 3, speed_item)
            self.table_servers.setItem(row, 4, QTableWidgetItem(sec_text))
            self.table_servers.setItem(row, 5, users_item)
            self.table_servers.setItem(row, 6, QTableWidgetItem(qual_str))

        self.table_servers.setSortingEnabled(True)
        self.apply_table_filters()

    def create_ping_item(self, ping_ms: int) -> NumericTableWidgetItem:
        if ping_ms <= 0:
            item = NumericTableWidgetItem("⏳ Testando...", 9998)
            item.setForeground(QColor("#94a3b8"))
        elif ping_ms >= 9000:
            item = NumericTableWidgetItem("❌ Sem resposta", 9999)
            item.setForeground(QColor("#f87171"))
        elif ping_ms < 130:
            item = NumericTableWidgetItem(f"⚡ {ping_ms} ms (Excelente)", ping_ms)
            item.setForeground(QColor("#4ade80"))
        elif ping_ms < 250:
            item = NumericTableWidgetItem(f"📶 {ping_ms} ms (Bom)", ping_ms)
            item.setForeground(QColor("#38bdf8"))
        else:
            item = NumericTableWidgetItem(f"🐢 {ping_ms} ms (Alto)", ping_ms)
            item.setForeground(QColor("#fb923c"))
        return item

    def on_latency_progress(self, tested_map: dict):
        for row in range(self.table_servers.rowCount()):
            ip_item = self.table_servers.item(row, 1)
            if ip_item and ip_item.text() in tested_map:
                ping_ms = tested_map[ip_item.text()]
                new_ping_item = self.create_ping_item(ping_ms)
                self.table_servers.setItem(row, 2, new_ping_item)

    def on_latency_completed(self):
        self.append_log("✅ Testes de latência concluídos com sucesso.", "success")
        self.apply_table_filters()

    def apply_table_filters(self):
        selected_region = self.combo_region.currentData() or "ALL"
        search_query = self.input_search.text().strip().lower()

        visible_count = 0
        for row in range(self.table_servers.rowCount()):
            item_country = self.table_servers.item(row, 0)
            if not item_country:
                continue

            s_dict = item_country.data(Qt.ItemDataRole.UserRole)
            if not s_dict:
                continue

            c_short = s_dict.get('CountryShort', '')
            c_long = s_dict.get('CountryLong', '').lower()
            ip = s_dict.get('IP', '').lower()

            # Filtro por Região
            match_region = True
            if selected_region == "LATAM":
                match_region = c_short in LATAM_CODES
            elif selected_region == "AMERICAS":
                match_region = c_short in AMERICAS_CODES
            elif selected_region == "EUROPE":
                match_region = c_short in EUROPE_CODES
            elif selected_region == "ASIA":
                match_region = c_short in ASIA_CODES

            # Filtro por Texto de Busca
            match_search = True
            if search_query:
                match_search = (search_query in c_long) or (search_query in c_short.lower()) or (search_query in ip)

            should_show = match_region and match_search
            self.table_servers.setRowHidden(row, not should_show)
            if should_show:
                visible_count += 1

        self.lbl_server_count.setText(f"{visible_count} servidores visíveis na listagem")

    def on_table_selection_changed(self):
        selected_items = self.table_servers.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            item_country = self.table_servers.item(row, 0)
            if item_country:
                self.selected_server = item_country.data(Qt.ItemDataRole.UserRole)
                self.btn_connect_selected.setEnabled(True)
                self.btn_set_default.setEnabled(True)
                return

        self.selected_server = None
        self.btn_connect_selected.setEnabled(False)
        self.btn_set_default.setEnabled(False)

    def on_set_default_clicked(self):
        if not self.selected_server:
            return

        c_long = self.selected_server.get('CountryLong')
        c_short = self.selected_server.get('CountryShort')
        flag = FLAGS.get(c_short, '🌐')
        ip = self.selected_server.get('IP')
        ping = self.selected_server.get('measured_ping', 'N/A')

        desc = f"{flag} {c_long} ({ip}) - Ping: {ping}ms"
        self.lbl_target_server.setText(f"🎯 Servidor Alvo: <span style='color: #4ade80;'><b>{desc}</b></span>")
        self.append_log(f"⭐ Servidor salvo como padrão: {flag} {c_long} ({ip})", "info")

        ovpn_data = base64.b64decode(self.selected_server.get('OpenVPN_ConfigData_Base64')).decode('utf-8', errors='ignore')
        self.engine.save_ovpn_profile(ovpn_data, description=desc)

    def on_connect_selected_clicked(self):
        if not self.selected_server:
            return

        self.on_set_default_clicked()
        self.tabs.setCurrentIndex(0)

        if self.engine.is_connected:
            self.engine.stop_vpn()
            time.sleep(0.5)

        self.update_connection_ui(False, is_connecting=True)
        ovpn_data = base64.b64decode(self.selected_server.get('OpenVPN_ConfigData_Base64')).decode('utf-8', errors='ignore')
        self.engine.start_vpn(
            ovpn_content=ovpn_data,
            on_connected_callback=self.on_vpn_connected,
            on_failure_callback=self.on_vpn_failure
        )

    def on_import_custom_ovpn_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o arquivo .ovpn (Peru / ProtonVPN / VPS / Servidor Próprio)",
            "",
            "Arquivos OpenVPN (*.ovpn);;Todos os Arquivos (*.*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    ovpn_content = f.read()

                file_name = os.path.basename(file_path)
                desc = f"📁 Arquivo Local ({file_name})"
                self.engine.save_ovpn_profile(ovpn_content, description=desc)
                
                self.lbl_target_server.setText(f"🎯 Servidor Alvo: <span style='color: #c084fc;'><b>{desc}</b></span>")
                self.append_log(f"📁 Arquivo .ovpn importado com sucesso: {file_name}", "success")
                self.append_log("💾 Perfil salvo como padrão! Clique em 'LIGAR VPN' no Painel Rápido.", "info")
                self.tabs.setCurrentIndex(0)
            except Exception as e:
                self.append_log(f"❌ Erro ao importar arquivo: {e}", "error")
                QMessageBox.critical(self, "Erro ao Abrir Arquivo", f"Não foi possível ler o arquivo:\n{e}")

    def closeEvent(self, event):
        """Ao fechar a aplicação, desliga o túnel OpenVPN para não travar a rota do Windows."""
        if self.engine.is_connected or self.engine.openvpn_proc:
            reply = QMessageBox.question(
                self,
                "VPN Ativa",
                "A VPN ainda está conectada. Deseja desligar a VPN e fechar o aplicativo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.engine.stop_vpn()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
