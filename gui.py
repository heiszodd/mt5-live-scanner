import sys
import threading
from PySide6 import QtCore, QtWidgets, QtGui

# Import MT5 related modules (assumed to be in the repository)
import mt5_provider
import config
import session_detector
import poi_detectors
import entry_detectors
import alert_engine

class ScannerWorker(QtCore.QThread):
    update_signal = QtCore.Signal(dict)  # Emitted with event data
    status_signal = QtCore.Signal(str)   # Emitted with status messages

    def __init__(self, instrument, htf, ltf, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.htf = htf
        self.ltf = ltf
        self._running = threading.Event()
        self._running.clear()

    def run(self):
        self._running.set()
        self.status_signal.emit("Scanner started")
        # Initialize MT5 connection and detectors
        try:
            provider = mt5_provider.MT5Provider()
            provider.connect()
            self.status_signal.emit("MT5 connected")
        except Exception as e:
            self.status_signal.emit(f"MT5 connection error: {e}")
            return

        while self._running.is_set():
            try:
                # Example placeholder logic – replace with real scanning
                data = provider.fetch_latest(self.instrument, self.htf, self.ltf)
                # Process data through detectors (simplified)
                poi = poi_detectors.detect_poi(data)
                entry = entry_detectors.detect_entry(data)
                alert = alert_engine.evaluate(poi, entry)
                event = {
                    "timestamp": QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate),
                    "symbol": self.instrument,
                    "timeframe": self.ltf,
                    "event": alert.get("type", "N/A"),
                    "price": alert.get("price", 0.0),
                    "status": "Live" if alert.get("active", False) else "Idle",
                }
                self.update_signal.emit(event)
            except Exception as e:
                self.status_signal.emit(f"Scanning error: {e}")
            self.msleep(500)  # 0.5 s pause between loops
        self.status_signal.emit("Scanner stopped")
        provider.disconnect()

    def stop(self):
        self._running.clear()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Live Scanner")
        self.resize(1200, 800)
        self._setup_ui()
        self.scanner = None

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # Top controls
        controls_layout = QtWidgets.QHBoxLayout()
        self.instrument_cb = QtWidgets.QComboBox()
        self.instrument_cb.addItems(["NAS100", "XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"])
        self.htf_cb = QtWidgets.QComboBox()
        self.htf_cb.addItems(["4H", "1H", "15M"])
        self.ltf_cb = QtWidgets.QComboBox()
        self.ltf_cb.addItems(["5M", "1M"])
        self.start_btn = QtWidgets.QPushButton("Start Scanner")
        self.stop_btn = QtWidgets.QPushButton("Stop Scanner")
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(QtWidgets.QLabel("Instrument:"))
        controls_layout.addWidget(self.instrument_cb)
        controls_layout.addWidget(QtWidgets.QLabel("HTF:"))
        controls_layout.addWidget(self.htf_cb)
        controls_layout.addWidget(QtWidgets.QLabel("LTF:"))
        controls_layout.addWidget(self.ltf_cb)
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        main_layout.addLayout(controls_layout)

        # Status bar area (using a QGroupBox as a card)
        status_group = QtWidgets.QGroupBox("Status")
        status_layout = QtWidgets.QHBoxLayout(status_group)
        self.conn_status_lbl = QtWidgets.QLabel("MT5: Disconnected")
        self.session_status_lbl = QtWidgets.QLabel("Session: —")
        status_layout.addWidget(self.conn_status_lbl)
        status_layout.addStretch()
        status_layout.addWidget(self.session_status_lbl)
        main_layout.addWidget(status_group)

        # Main splitter with tabs
        self.tabs = QtWidgets.QTabWidget()
        self._create_live_feed_tab()
        self._create_strategy_tab()
        self._create_settings_tab()
        main_layout.addWidget(self.tabs)

        # Connections
        self.start_btn.clicked.connect(self.start_scanner)
        self.stop_btn.clicked.connect(self.stop_scanner)

        # Apply dark style
        self.apply_dark_style()

    def _create_live_feed_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        self.feed_table = QtWidgets.QTableWidget()
        self.feed_table.setColumnCount(6)
        self.feed_table.setHorizontalHeaderLabels(["Timestamp", "Symbol", "Timeframe", "Event", "Price", "Status"])
        self.feed_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.feed_table)
        self.tabs.addTab(tab, "Live POI & Liquidity Feed")

    def _create_strategy_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        strategy_text = (
            "ZSP Model Criteria:\n"
            "- HTF DoL (4H)\n"
            "- 1M Sweep + MSS\n"
            "- FVG Entry\n\n"
            "Risk Management Rules:\n"
            "- Body Closure Rule\n"
            "- 1:1 Break‑Even\n"
            "- 2:1 Target"
        )
        self.strategy_label = QtWidgets.QLabel(strategy_text)
        self.strategy_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        layout.addWidget(self.strategy_label)
        self.tabs.addTab(tab, "Active Strategy & Rules")

    def _create_settings_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        self.audio_checkbox = QtWidgets.QCheckBox("Enable audio alerts")
        self.beep_spin = QtWidgets.QSpinBox()
        self.beep_spin.setRange(1, 10)
        self.beep_spin.setValue(3)
        self.threshold_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(50)
        layout.addRow(self.audio_checkbox)
        layout.addRow("Beep frequency (per alert):", self.beep_spin)
        layout.addRow("Alert threshold (%):", self.threshold_slider)
        self.tabs.addTab(tab, "Settings")

    def apply_dark_style(self):
        # Simple dark stylesheet with accent color
        dark_style = """
            QMainWindow { background-color: #2b2b2b; color: #dddddd; }
            QWidget { background-color: #2b2b2b; color: #dddddd; }
            QComboBox, QSpinBox, QSlider, QCheckBox, QPushButton { background-color: #3c3f41; color: #ffffff; }
            QTableWidget { background-color: #1e1e1e; gridline-color: #555555; }
            QHeaderView::section { background-color: #3c3f41; color: #ffffff; }
            QGroupBox { border: 1px solid #555555; margin-top: 6px; }
            QGroupBox:title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
        """
        self.setStyleSheet(dark_style)

    def start_scanner(self):
        if self.scanner and self.scanner.isRunning():
            return
        instrument = self.instrument_cb.currentText()
        htf = self.htf_cb.currentText()
        ltf = self.ltf_cb.currentText()
        self.scanner = ScannerWorker(instrument, htf, ltf)
        self.scanner.update_signal.connect(self.add_feed_row)
        self.scanner.status_signal.connect(self.update_status)
        self.scanner.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.conn_status_lbl.setText("MT5: Connecting…")

    def stop_scanner(self):
        if self.scanner:
            self.scanner.stop()
            self.scanner.wait()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.conn_status_lbl.setText("MT5: Disconnected")

    @QtCore.Slot(dict)
    def add_feed_row(self, event):
        row = self.feed_table.rowCount()
        self.feed_table.insertRow(row)
        self.feed_table.setItem(row, 0, QtWidgets.QTableWidgetItem(event.get("timestamp", "")))
        self.feed_table.setItem(row, 1, QtWidgets.QTableWidgetItem(event.get("symbol", "")))
        self.feed_table.setItem(row, 2, QtWidgets.QTableWidgetItem(event.get("timeframe", "")))
        self.feed_table.setItem(row, 3, QtWidgets.QTableWidgetItem(event.get("event", "")))
        self.feed_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(event.get("price", ""))))
        self.feed_table.setItem(row, 5, QtWidgets.QTableWidgetItem(event.get("status", "")))
        self.feed_table.scrollToBottom()

    @QtCore.Slot(str)
    def update_status(self, msg):
        # Update connection or generic status based on message content
        if "connected" in msg.lower():
            self.conn_status_lbl.setText("MT5: Connected")
        elif "error" in msg.lower() or "stopped" in msg.lower():
            self.conn_status_lbl.setText("MT5: Disconnected")
        # Session indicator placeholder – could be expanded with real logic
        self.session_status_lbl.setText("Session: Active")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
