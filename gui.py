# gui.py - Refactored to clean live feed output
import sys
from PySide6 import QtWidgets, QtCore
import MetaTrader5 as mt5

# optional session detector
try:
    from session_detector import SessionDetector
    session_detector = SessionDetector()
except Exception:
    session_detector = None

class MT5Connector(QtCore.QObject):
    connected = QtCore.Signal()
    connection_failed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.symbol = None

    def connect(self, symbol: str):
        self.symbol = symbol.upper()
        if not mt5.initialize():
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

    def run(self):
        while self._running:
            raw = mt5.symbol_info_tick(self.symbol)
            if raw:
                self.tick.emit(raw._asdict())
            self.msleep(200)
        self.stopped.emit()

    def stop(self):
        self._running = False

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Live Scanner")
        self.resize(900, 600)

        self.connector = MT5Connector()
        self.scanner_thread = None
        self.prev_session = ""

        self._setup_ui()
        self._connect_signals()

        # Heartbeat timer for periodic summary every 15 seconds
        self.heartbeat_timer = QtCore.QTimer()
        self.heartbeat_timer.setInterval(15000)
        self.heartbeat_timer.timeout.connect(self._heartbeat)

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vbox = QtWidgets.QVBoxLayout(central)

        # Top control bar
        top_bar = QtWidgets.QHBoxLayout()
        self.instrument_input = QtWidgets.QComboBox()
        self.instrument_input.setEditable(True)
        presets = ["NAS100", "XAUUSD", "US100", "GOLD"]
        self.instrument_input.addItems(presets)
        self.instrument_input.setCurrentText(presets[0])
        top_bar.addWidget(QtWidgets.QLabel("Instrument:"))
        top_bar.addWidget(self.instrument_input)

        self.connect_button = QtWidgets.QPushButton("Connect MT5")
        top_bar.addWidget(self.connect_button)

        self.status_label = QtWidgets.QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red;")
        top_bar.addWidget(self.status_label)

        # Live header label (shows price, session, status)
        self.live_header = QtWidgets.QLabel("Live Price: — | Session: — | Status: —")
        self.live_header.setStyleSheet("font-weight: bold;")
        top_bar.addWidget(self.live_header)

        vbox.addLayout(top_bar)

        # Start/Stop button
        self.start_button = QtWidgets.QPushButton("Start Scanner")
        self.start_button.setEnabled(False)
        vbox.addWidget(self.start_button)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        vbox.addWidget(self.tabs)

        # Live Feed tab (event log only)
        self.feed_tab = QtWidgets.QWidget()
        self.feed_layout = QtWidgets.QVBoxLayout(self.feed_tab)
        self.feed_view = QtWidgets.QTextEdit()
        self.feed_view.setReadOnly(True)
        self.feed_layout.addWidget(self.feed_view)
        self.tabs.addTab(self.feed_tab, "Live Feed")

        # Placeholder tabs
        self.rules_tab = QtWidgets.QWidget()
        self.rules_tab.setLayout(QtWidgets.QVBoxLayout())
        self.rules_tab.layout().addWidget(QtWidgets.QLabel("Strategy rules will be displayed here."))
        self.tabs.addTab(self.rules_tab, "Strategy Rules")

        self.settings_tab = QtWidgets.QWidget()
        self.settings_tab.setLayout(QtWidgets.QFormLayout())
        self.audio_checkbox = QtWidgets.QCheckBox("Enable Audio Alerts")
        self.audio_checkbox.setChecked(True)
        self.settings_tab.layout().addRow(self.audio_checkbox)
        self.tabs.addTab(self.settings_tab, "Settings")

    def _connect_signals(self):
        self.connect_button.clicked.connect(self._handle_connect)
        self.start_button.clicked.connect(self._toggle_scanner)
        self.connector.connected.connect(self._on_connected)
        self.connector.connection_failed.connect(self._on_connection_failed)

    def _handle_connect(self):
        symbol = self.instrument_input.currentText().strip()
        if not symbol:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid instrument symbol.")
            return
        self.status_label.setText("Connecting...")
        self.status_label.setStyleSheet("color: orange;")
        self.connect_button.setEnabled(False)
        self.connector.connect(symbol)

    def _on_connected(self):
        self.status_label.setText("Connected")
        self.status_label.setStyleSheet("color: green;")
        self.start_button.setEnabled(True)
        QtWidgets.QMessageBox.information(self, "MT5", f"Successfully connected to {self.connector.symbol}")

    def _on_connection_failed(self, msg: str):
        self.status_label.setText("Connection Failed")
        self.status_label.setStyleSheet("color: red;")
        self.connect_button.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, "MT5 Connection Failed", msg)

    def _toggle_scanner(self):
        if self.scanner_thread and self.scanner_thread.isRunning():
            self._stop_scanner()
        else:
            self._start_scanner()

    def _start_scanner(self):
        symbol = self.connector.symbol
        if not symbol:
            QtWidgets.QMessageBox.warning(self, "Error", "No symbol connected.")
            return
        self.scanner_thread = ScannerThread(symbol)
        self.scanner_thread.tick.connect(self._process_tick)
        self.scanner_thread.finished.connect(self._scanner_finished)
        self.scanner_thread.start()
        self.start_button.setText("Stop Scanner")
        self._log_event(f"Scanner started for {symbol}")
        self.heartbeat_timer.start()

    def _stop_scanner(self):
        if self.scanner_thread:
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        self.start_button.setText("Start Scanner")
        self._log_event("Scanner stopped.")
        self.heartbeat_timer.stop()
        self.live_header.setText("Live Price: — | Session: — | Status: —")

    def _scanner_finished(self):
        self.start_button.setText("Start Scanner")
        self._log_event("Scanner thread finished.")
        self.heartbeat_timer.stop()

    def _process_tick(self, data: dict):
        # Extract price, prefer bid > ask > last
        price = data.get("bid") or data.get("ask") or data.get("last") or ""
        # Session detection
        session = ""
        if session_detector:
            try:
                session = session_detector.current_session(data) or ""
            except Exception:
                session = ""
        # Update live header
        self.live_header.setText(f"Live Price: {price} | Session: {session or '—'} | Status: Monitoring")
        # Detect session change for logging
        if session and session != self.prev_session:
            self._log_event(f"Session changed to {session}")
            self.prev_session = session
        # TODO: detect POI/FVG/etc. and log when detected

    def _heartbeat(self):
        now = QtCore.QDateTime.currentDateTime().toString("HH:mm:ss")
        header = self.live_header.text()
        self._log_event(f"[{now}] {header}")

    def _log_event(self, message: str):
        timestamp = QtCore.QDateTime.currentDateTime().toString("HH:mm:ss")
        self.feed_view.append(f"{timestamp} {message}")

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
