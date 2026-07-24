import sys
from PySide6 import QtWidgets, QtCore, QtGui
import MetaTrader5 as mt5

# Project modules
from mt5_provider import MT5Provider
from config import Config

class MT5Connector(QtCore.QObject):
    connected = QtCore.Signal()
    connection_failed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.account = None
        self.password = None
        self.server = None
        self.symbol = None

    def login(self, account: str, password: str, server: str, symbol: str):
        """Initialize MT5 connection with credentials and select symbol."""
        self.account = account.strip()
        self.password = password.strip()
        self.server = server.strip()
        self.symbol = symbol.upper().strip()
        if not mt5.initialize(login=self.account, server=self.server, password=self.password):
            self.connection_failed.emit("MT5 initialization failed")
            return
        if not mt5.symbol_select(self.symbol, True):
            self.connection_failed.emit(f"Failed to select symbol {self.symbol}")
            return
        info = mt5.symbol_info(self.symbol)
        if info is None:
            self.connection_failed.emit(f"Symbol {self.symbol} not found in MT5")
            return
        self.connected.emit()

    def shutdown(self):
        mt5.shutdown()

class ScannerThread(QtCore.QThread):
    tick = QtCore.Signal(dict)
    stopped = QtCore.Signal()

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self._running = True
        self.provider = MT5Provider()

    def run(self):
        while self._running:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                try:
                    tick_dict = tick._asdict()
                except Exception:
                    tick_dict = {attr: getattr(tick, attr) for attr in dir(tick) if not attr.startswith('_') and not callable(getattr(tick, attr))}
                self.tick.emit(tick_dict)
            self.msleep(200)
        self.stopped.emit()

    def stop(self):
        self._running = False

class HeaderCard(QtWidgets.QGroupBox):
    """Top dashboard card showing live price, session, datetime, status and balances."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Live Dashboard")
        layout = QtWidgets.QGridLayout(self)
        # Labels placeholders
        self.price_label = QtWidgets.QLabel("Price: --")
        self.session_label = QtWidgets.QLabel("Session: --")
        self.datetime_label = QtWidgets.QLabel("Date/Time (WAT): --")
        self.status_label = QtWidgets.QLabel("Status: Disconnected")
        self.balance_label = QtWidgets.QLabel("Balance: --")
        self.equity_label = QtWidgets.QLabel("Equity: --")
        self.margin_label = QtWidgets.QLabel("Free Margin: --")
        self.pl_label = QtWidgets.QLabel("Floating P/L: --")
        # Arrange in grid
        layout.addWidget(self.price_label, 0, 0)
        layout.addWidget(self.session_label, 0, 1)
        layout.addWidget(self.datetime_label, 0, 2)
        layout.addWidget(self.status_label, 1, 0)
        layout.addWidget(self.balance_label, 1, 1)
        layout.addWidget(self.equity_label, 1, 2)
        layout.addWidget(self.margin_label, 2, 0)
        layout.addWidget(self.pl_label, 2, 1)

    def update_datetime(self):
        now = QtCore.QDateTime.currentDateTime()
        self.datetime_label.setText(f"Date/Time (WAT): {now.toString('yyyy-MM-dd HH:mm:ss')}")

class LoginControls(QtWidgets.QGroupBox):
    """MT5 login fields and control buttons."""
    login_requested = QtCore.Signal(str, str, str, str)
    start_scanner = QtCore.Signal()
    stop_scanner = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("MT5 Connection")
        form = QtWidgets.QFormLayout(self)
        self.account_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.server_edit = QtWidgets.QLineEdit()
        self.symbol_edit = QtWidgets.QComboBox()
        self.symbol_edit.setEditable(True)
        self.symbol_edit.addItems(["XAUUSD", "NAS100", "US100", "EURUSD"])
        form.addRow("Account #", self.account_edit)
        form.addRow("Password", self.password_edit)
        form.addRow("Server", self.server_edit)
        form.addRow("Symbol", self.symbol_edit)
        btn_layout = QtWidgets.QHBoxLayout()
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.start_btn = QtWidgets.QPushButton("Start Scanner")
        self.start_btn.setEnabled(False)
        self.stop_btn = QtWidgets.QPushButton("Stop Scanner")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        form.addRow(btn_layout)
        self.connect_btn.clicked.connect(self._on_connect)
        self.start_btn.clicked.connect(lambda: self.start_scanner.emit())
        self.stop_btn.clicked.connect(lambda: self.stop_scanner.emit())

    def _on_connect(self):
        account = self.account_edit.text()
        password = self.password_edit.text()
        server = self.server_edit.text()
        symbol = self.symbol_edit.currentText()
        self.login_requested.emit(account, password, server, symbol)

    def set_connected(self, ok: bool):
        self.start_btn.setEnabled(ok)
        self.stop_btn.setEnabled(False)
        self.connect_btn.setEnabled(not ok)

    def set_scanning(self, scanning: bool):
        self.start_btn.setEnabled(not scanning)
        self.stop_btn.setEnabled(scanning)
        self.connect_btn.setEnabled(not scanning)

class PositionsTable(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Open Positions")
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Ticket", "Symbol", "Type", "Lots", "Open Price", "Current Price", "SL", "TP", "Profit"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_positions(self, positions):
        self.table.setRowCount(len(positions))
        for row, pos in enumerate(positions):
            for col, key in enumerate(["ticket", "symbol", "type", "lots", "price_open", "price_current", "sl", "tp", "profit"]):
                item = QtWidgets.QTableWidgetItem(str(pos.get(key, "")))
                self.table.setItem(row, col, item)

class HistoryTable(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Trade History")
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Ticket", "Symbol", "Type", "Lots", "Close Price", "Profit"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_history(self, history):
        self.table.setRowCount(len(history))
        for row, tr in enumerate(history):
            for col, key in enumerate(["ticket", "symbol", "type", "lots", "price_close", "profit"]):
                item = QtWidgets.QTableWidgetItem(str(tr.get(key, "")))
                self.table.setItem(row, col, item)

class EventLog(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Event Log")
        layout = QtWidgets.QVBoxLayout(self)
        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

    def append(self, text: str):
        timestamp = QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        self.log_view.append(f"[{timestamp}] {text}")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Live Scanner – Modern Dashboard")
        self.resize(1200, 800)
        self.connector = MT5Connector()
        self.scanner_thread = None
        self._setup_ui()
        self._connect_signals()
        # Timer for datetime updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.header.update_datetime)
        self.timer.start(1000)

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        # Header
        self.header = HeaderCard()
        main_layout.addWidget(self.header)
        # Controls
        self.controls = LoginControls()
        main_layout.addWidget(self.controls)
        # Splitter for tables and log
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.positions = PositionsTable()
        self.history = HistoryTable()
        self.log = EventLog()
        upper = QtWidgets.QWidget()
        upper_layout = QtWidgets.QHBoxLayout(upper)
        upper_layout.addWidget(self.positions)
        upper_layout.addWidget(self.history)
        splitter.addWidget(upper)
        splitter.addWidget(self.log)
        main_layout.addWidget(splitter)

    def _connect_signals(self):
        self.controls.login_requested.connect(self.handle_login)
        self.controls.start_scanner.connect(self.start_scanner)
        self.controls.stop_scanner.connect(self.stop_scanner)
        self.connector.connected.connect(self.on_connected)
        self.connector.connection_failed.connect(self.on_connection_failed)

    def handle_login(self, account, password, server, symbol):
        self.log.append("Attempting MT5 connection...")
        self.controls.connect_btn.setEnabled(False)
        self.connector.login(account, password, server, symbol)

    def on_connected(self):
        self.log.append("MT5 connected successfully.")
        self.header.status_label.setText("Status: Connected")
        self.header.status_label.setStyleSheet("color: green;")
        self.controls.set_connected(True)
        # Populate live price placeholder
        self.update_price_placeholder()

    def on_connection_failed(self, msg: str):
        self.log.append(f"Connection failed: {msg}")
        self.header.status_label.setText("Status: Connection Failed")
        self.header.status_label.setStyleSheet("color: red;")
        self.controls.set_connected(False)
        QtWidgets.QMessageBox.critical(self, "MT5 Connection Failed", msg)

    def start_scanner(self):
        if not self.connector.symbol:
            QtWidgets.QMessageBox.warning(self, "Error", "No symbol connected.")
            return
        self.scanner_thread = ScannerThread(self.connector.symbol)
        self.scanner_thread.tick.connect(self.process_tick)
        self.scanner_thread.finished.connect(self.scanner_finished)
        self.scanner_thread.start()
        self.log.append("Scanner started.")
        self.header.status_label.setText("Status: Scanning")
        self.header.status_label.setStyleSheet("color: blue;")
        self.controls.set_scanning(True)

    def stop_scanner(self):
        if self.scanner_thread:
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        self.log.append("Scanner stopped.")
        self.header.status_label.setText("Status: Connected")
        self.header.status_label.setStyleSheet("color: green;")
        self.controls.set_scanning(False)

    def scanner_finished(self):
        self.log.append("Scanner thread finished.")
        self.controls.set_scanning(False)
        self.header.status_label.setText("Status: Connected")
        self.header.status_label.setStyleSheet("color: green;")

    def process_tick(self, tick_data: dict):
        # Update price in header
        price = tick_data.get('last') or tick_data.get('bid')
        if isinstance(price, (int, float)):
            self.header.price_label.setText(f"Price: {price:.5f}")
        else:
            self.header.price_label.setText(f"Price: {price}")
        # Simple session inference based on time (placeholder)
        hour = QtCore.QTime.currentTime().hour()
        if 0 <= hour < 8:
            session = "Asian"
        elif 8 <= hour < 16:
            session = "London"
        else:
            session = "NY"
        self.header.session_label.setText(f"Session: {session}")
        # Log tick
        self.log.append(f"Tick received: {price}")
        # Here you would query MT5 for account balances and positions; placeholders:
        self.header.balance_label.setText("Balance: --")
        self.header.equity_label.setText("Equity: --")
        self.header.margin_label.setText("Free Margin: --")
        self.header.pl_label.setText("Floating P/L: --")
        # Update positions table (placeholder empty list)
        # self.positions.update_positions([])
        # Update history table (placeholder)
        # self.history.update_history([])

    def update_price_placeholder(self):
        # Pull initial price once after connection
        tick = mt5.symbol_info_tick(self.connector.symbol)
        if tick:
            try:
                price = tick.last if hasattr(tick, 'last') else tick.bid
                self.header.price_label.setText(f"Price: {price:.5f}")
            except Exception:
                pass

    def closeEvent(self, event):
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        self.connector.shutdown()
        super().closeEvent(event)

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
