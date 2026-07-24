import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLineEdit,
    QPushButton,
    QComboBox,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont

class LiveScannerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Live Scanner")
        self.init_ui()
        self.start_timers()
        self.connected = False
        self.scanning = False

    def init_ui(self):
        main_layout = QVBoxLayout()
        # Connection Box
        conn_frame = QFrame()
        conn_layout = QHBoxLayout()
        conn_frame.setLayout(conn_layout)
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Login ID")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("Server")
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        for w in [self.login_edit, self.password_edit, self.server_edit, self.connect_btn]:
            conn_layout.addWidget(w)
        main_layout.addWidget(conn_frame)
        # Symbol Selector
        symbol_frame = QFrame()
        symbol_layout = QHBoxLayout()
        symbol_frame.setLayout(symbol_layout)
        symbol_label = QLabel("Symbol:")
        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)
        self.symbol_combo.addItems(["USTEC", "XAUUSD"])
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addWidget(self.symbol_combo)
        main_layout.addWidget(symbol_frame)
        # Scanner Controls
        ctrl_frame = QFrame()
        ctrl_layout = QHBoxLayout()
        ctrl_frame.setLayout(ctrl_layout)
        self.start_btn = QPushButton("Start Scanner")
        self.stop_btn = QPushButton("Stop Scanner")
        self.start_btn.clicked.connect(self.start_scanner)
        self.stop_btn.clicked.connect(self.stop_scanner)
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.stop_btn)
        main_layout.addWidget(ctrl_frame)
        # Live Dashboard Banner
        header = QFrame()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        header.setFrameShape(QFrame.StyledPanel)
        # Labels
        self.price_label = QLabel("Live Price: N/A")
        self.session_label = QLabel("Session: N/A")
        self.datetime_label = QLabel("Date/Time: N/A")
        self.status_label = QLabel("Scanner Status: Idle")
        # Make price label big and bold
        price_font = QFont()
        price_font.setPointSize(16)
        price_font.setBold(True)
        self.price_label.setFont(price_font)
        for w in [self.price_label, self.session_label, self.datetime_label, self.status_label]:
            w.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(w)
        main_layout.addWidget(header)
        # Event Log
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumHeight(150)
        main_layout.addWidget(self.event_log)
        self.setLayout(main_layout)

    def start_timers(self):
        # Update date/time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        # Placeholder for live data updates (replace with real MT5 hooks)
        self.fake_update_timer = QTimer(self)
        self.fake_update_timer.timeout.connect(self.fake_update)
        self.fake_update_timer.start(5000)

    def update_datetime(self):
        now = QDateTime.currentDateTime()
        self.datetime_label.setText(f"Date/Time: {now.toString('yyyy-MM-dd HH:mm:ss')}")

    def fake_update(self):
        # Simulate live data; replace with actual MT5 data when connected.
        import random
        symbol = self.symbol_combo.currentText() or "EURUSD"
        self.price_label.setText(f"Live Price ({symbol}): {round(random.uniform(1.0, 2.0),5)}")
        self.session_label.setText("Session: Market Open")
        self.append_event(f"Updated price for {symbol}")

    def toggle_connection(self):
        if not self.connected:
            # Placeholder: insert real MT5 connection logic here.
            self.connected = True
            self.connect_btn.setText("Disconnect")
            self.append_event("Connected to MT5 server")
        else:
            self.connected = False
            self.connect_btn.setText("Connect")
            self.append_event("Disconnected from MT5 server")

    def start_scanner(self):
        if not self.connected:
            self.append_event("Cannot start scanner: not connected")
            return
        if not self.scanning:
            self.scanning = True
            self.status_label.setText("Scanner Status: Running")
            self.append_event("Scanner started")

    def stop_scanner(self):
        if self.scanning:
            self.scanning = False
            self.status_label.setText("Scanner Status: Stopped")
            self.append_event("Scanner stopped")

    def append_event(self, text):
        timestamp = QDateTime.currentDateTime().toString('HH:mm:ss')
        self.event_log.append(f"[{timestamp}] {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = LiveScannerGUI()
    gui.resize(900, 400)
    gui.show()
    sys.exit(app.exec())
