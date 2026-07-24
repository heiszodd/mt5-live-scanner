import sys
from PySide6 import QtWidgets, QtCore, QtGui
import MetaTrader5 as mt5

# Project modules
from mt5_provider import MT5Provider
from config import Config
# from session_detector import SessionDetector  # removed

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
        self.provider = MT5Provider()

    def run(self):
        while self._running:
            tick_data = self.provider.get_tick(self.symbol)
            if tick_data:
                self.tick.emit(tick_data)
            self.msleep(200)  # 5 ticks per second approx.
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
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Top controls
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
        layout.addLayout(top_bar)

        # Start/Stop button
        self.start_button = QtWidgets.QPushButton("Start Scanner")
        self.start_button.setEnabled(False)
        layout.addWidget(self.start_button)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        # Live Feed tab
        self.feed_tab = QtWidgets.QWidget()
        self.feed_layout = QtWidgets.QVBoxLayout(self.feed_tab)
        self.feed_view = QtWidgets.QTextEdit()
        self.feed_view.setReadOnly(True)
        self.feed_layout.addWidget(self.feed_view)
        self.tabs.addTab(self.feed_tab, "Live Feed")

        # Strategy Rules tab (placeholder for ZSP Model)
        self.rules_tab = QtWidgets.QWidget()
        self.rules_layout = QtWidgets.QVBoxLayout(self.rules_tab)
        self.rules_label = QtWidgets.QLabel("ZSP Model strategy rules will be displayed here.")
        self.rules_layout.addWidget(self.rules_label)
        self.tabs.addTab(self.rules_tab, "Strategy Rules")

        # Settings tab
        self.settings_tab = QtWidgets.QWidget()
        self.settings_layout = QtWidgets.QFormLayout(self.settings_tab)
        self.audio_checkbox = QtWidgets.QCheckBox("Enable Audio Alerts")
        self.audio_checkbox.setChecked(True)
        self.settings_layout.addRow(self.audio_checkbox)
        self.tabs.addTab(self.settings_tab, "Settings")

    def _connect_signals(self):
        self.connect_button.clicked.connect(self.handle_connect)
        self.start_button.clicked.connect(self.toggle_scanner)
        self.connector.connected.connect(self.on_connected)
        self.connector.connection_failed.connect(self.on_connection_failed)

    def handle_connect(self):
        symbol = self.instrument_input.currentText().strip()
        if not symbol:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid instrument symbol.")
            return
        # Update status before attempting connection
        self.status_label.setText("Connecting...")
        self.status_label.setStyleSheet("color: orange;")
        self.connect_button.setEnabled(False)
        self.connector.connect(symbol)

    def on_connected(self):
        self.status_label.setText("Connected")
        self.status_label.setStyleSheet("color: green;")
        self.start_button.setEnabled(True)
        QtWidgets.QMessageBox.information(self, "MT5", f"Successfully connected to {self.connector.symbol}")

    def on_connection_failed(self, msg: str):
        self.status_label.setText("Connection Failed")
        self.status_label.setStyleSheet("color: red;")
        self.start_button.setEnabled(False)
        QtWidgets.QMessageBox.critical(self, "MT5 Connection Failed", msg)

    def toggle_scanner(self):
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.stop_scanner()
        else:
            self.start_scanner()

    def start_scanner(self):
        symbol = self.connector.symbol
        if not symbol:
            QtWidgets.QMessageBox.warning(self, "Error", "No symbol connected.")
            return
        self.scanner_thread = ScannerThread(symbol)
        self.scanner_thread.tick.connect(self.process_tick)
        self.scanner_thread.finished.connect(self.scanner_finished)
        self.scanner_thread.start()
        self.start_button.setText("Stop Scanner")
        self.feed_view.append("Scanner started for {}...".format(symbol))

    def stop_scanner(self):
        if self.scanner_thread:
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        self.start_button.setText("Start Scanner")
        self.feed_view.append("Scanner stopped.")

    def scanner_finished(self):
        self.start_button.setText("Start Scanner")
        self.feed_view.append("Scanner thread finished.")

    def process_tick(self, tick_data: dict):
        # For demonstration we just stringify the dict.
        self.feed_view.append(str(tick_data))
        # Here you could plug in POIDetector, EntryDetector, AlertEngine, etc.
        # Example placeholder:
        # if EntryDetector.detect(tick_data):
        #     AlertEngine.alert("Entry signal detected", self.audio_checkbox.isChecked())

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
