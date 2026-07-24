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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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
        # Placeholder account data
        self.account_info = {
            "balance": 0.0,
            "equity": 0.0,
            "margin": 0.0,
            "free_margin": 0.0,
            "profit_loss": 0.0,
            "leverage": "",
            "account_number": "",
            "server": "",
        }
        self.open_positions = []  # list of dicts
        self.trade_history = []   # list of dicts

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
        # Account Summary Bar
        account_frame = QFrame()
        account_layout = QHBoxLayout()
        account_frame.setLayout(account_layout)
        self.balance_label = QLabel("Balance: 0.00")
        self.equity_label = QLabel("Equity: 0.00")
        self.margin_label = QLabel("Margin: 0.00")
        self.free_margin_label = QLabel("Free Margin: 0.00")
        self.profit_label = QLabel("P/L: 0.00")
        self.leverage_label = QLabel("Leverage: ")
        self.account_num_label = QLabel("Account #: ")
        self.server_label = QLabel("Server: ")
        for w in [self.balance_label, self.equity_label, self.margin_label, self.free_margin_label,
                  self.profit_label, self.leverage_label, self.account_num_label, self.server_label]:
            w.setAlignment(Qt.AlignCenter)
            account_layout.addWidget(w)
        main_layout.addWidget(account_frame)
        # Live Dashboard Banner (price, session, datetime, status)
        header = QFrame()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        header.setFrameShape(QFrame.StyledPanel)
        self.price_label = QLabel("Live Price: N/A")
        self.session_label = QLabel("Session: N/A")
        self.datetime_label = QLabel("Date/Time: N/A")
        self.status_label = QLabel("Scanner Status: Idle")
        price_font = QFont()
        price_font.setPointSize(16)
        price_font.setBold(True)
        self.price_label.setFont(price_font)
        for w in [self.price_label, self.session_label, self.datetime_label, self.status_label]:
            w.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(w)
        main_layout.addWidget(header)
        # Tabs for Positions and History
        self.tabs = QTabWidget()
        # Open Positions Table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(9)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Volume", "Open Price", "Current Price",
            "SL", "TP", "Profit"
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Trade History Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Ticket", "Time", "Symbol", "Type", "Volume",
            "Open Price", "Close Price", "Profit"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.positions_table, "Open Positions")
        self.tabs.addTab(self.history_table, "Trade History")
        main_layout.addWidget(self.tabs)
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
        import random, time
        symbol = self.symbol_combo.currentText() or "EURUSD"
        price = round(random.uniform(1.0, 2.0), 5)
        self.price_label.setText(f"Live Price ({symbol}): {price}")
        self.session_label.setText("Session: Market Open")
        self.append_event(f"Updated price for {symbol}")
        # Simulated account info
        self.account_info.update({
            "balance": round(random.uniform(1000, 5000), 2),
            "equity": round(random.uniform(1000, 5000), 2),
            "margin": round(random.uniform(100, 500), 2),
            "free_margin": round(random.uniform(500, 2000), 2),
            "profit_loss": round(random.uniform(-200, 200), 2),
            "leverage": "1:100",
            "account_number": "12345678",
            "server": self.server_edit.text() or "DemoServer",
        })
        self.update_account_summary()
        # Simulated positions (randomly add/remove)
        if random.random() < 0.3:
            # add a position
            ticket = random.randint(10000, 99999)
            self.open_positions.append({
                "ticket": ticket,
                "symbol": symbol,
                "type": random.choice(["BUY", "SELL"]),
                "volume": round(random.choice([0.01, 0.1, 1.0]),
                "open_price": price - random.uniform(0.001, 0.005),
                "current_price": price,
                "sl": "-",
                "tp": "-",
                "profit": round(random.uniform(-50, 50), 2),
            })
        if random.random() < 0.2 and self.open_positions:
            # close a random position and move to history
            pos = self.open_positions.pop(random.randrange(len(self.open_positions)))
            pos.update({
                "close_time": QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss'),
                "close_price": price,
                "profit": round(pos["profit"] + random.uniform(-5, 5), 2),
            })
            self.trade_history.append(pos)
        self.update_positions_table()
        self.update_history_table()

    def update_account_summary(self):
        self.balance_label.setText(f"Balance: {self.account_info['balance']:.2f}")
        self.equity_label.setText(f"Equity: {self.account_info['equity']:.2f}")
        self.margin_label.setText(f"Margin: {self.account_info['margin']:.2f}")
        self.free_margin_label.setText(f"Free Margin: {self.account_info['free_margin']:.2f}")
        self.profit_label.setText(f"P/L: {self.account_info['profit_loss']:.2f}")
        self.leverage_label.setText(f"Leverage: {self.account_info['leverage']}")
        self.account_num_label.setText(f"Account #: {self.account_info['account_number']}")
        self.server_label.setText(f"Server: {self.account_info['server']}")

    def update_positions_table(self):
        self.positions_table.setRowCount(len(self.open_positions))
        for row, pos in enumerate(self.open_positions):
            self.positions_table.setItem(row, 0, QTableWidgetItem(str(pos["ticket"])) )
            self.positions_table.setItem(row, 1, QTableWidgetItem(pos["symbol"]))
            self.positions_table.setItem(row, 2, QTableWidgetItem(pos["type"]))
            self.positions_table.setItem(row, 3, QTableWidgetItem(str(pos["volume"])) )
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos['open_price']:.5f}"))
            self.positions_table.setItem(row, 5, QTableWidgetItem(f"{pos['current_price']:.5f}"))
            self.positions_table.setItem(row, 6, QTableWidgetItem(pos["sl"]))
            self.positions_table.setItem(row, 7, QTableWidgetItem(pos["tp"]))
            self.positions_table.setItem(row, 8, QTableWidgetItem(f"{pos['profit']:.2f}"))

    def update_history_table(self):
        self.history_table.setRowCount(len(self.trade_history))
        for row, tr in enumerate(self.trade_history):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(tr["ticket"])) )
            self.history_table.setItem(row, 1, QTableWidgetItem(tr.get("close_time", "")))
            self.history_table.setItem(row, 2, QTableWidgetItem(tr["symbol"]))
            self.history_table.setItem(row, 3, QTableWidgetItem(tr["type"]))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(tr["volume"])) )
            self.history_table.setItem(row, 5, QTableWidgetItem(f"{tr['open_price']:.5f}"))
            self.history_table.setItem(row, 6, QTableWidgetItem(f"{tr.get('close_price', 0):.5f}"))
            self.history_table.setItem(row, 7, QTableWidgetItem(f"{tr['profit']:.2f}"))

    def toggle_connection(self):
        if not self.connected:
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
    gui.resize(1200, 800)
    gui.show()
    sys.exit(app.exec())
