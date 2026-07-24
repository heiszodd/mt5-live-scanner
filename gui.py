import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, QDateTime

class LiveScannerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Live Scanner")
        self.init_ui()
        self.start_timers()

    def init_ui(self):
        # Header dashboard
        header = QFrame()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        header.setFrameShape(QFrame.StyledPanel)

        self.symbol_label = QLabel("Symbol: N/A")
        self.price_label = QLabel("Live Price: N/A")
        self.session_label = QLabel("Session: N/A")
        self.datetime_label = QLabel("Date/Time: N/A")
        self.status_label = QLabel("Scanner Status: Idle")

        for w in [self.symbol_label, self.price_label, self.session_label, self.datetime_label, self.status_label]:
            w.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(w)

        # Compact event log
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumHeight(150)

        main_layout = QVBoxLayout()
        main_layout.addWidget(header)
        main_layout.addWidget(self.event_log)
        self.setLayout(main_layout)

    def start_timers(self):
        # Update date/time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        # Placeholder: update other fields periodically (could be connected to MT5 data source)
        self.fake_update_timer = QTimer(self)
        self.fake_update_timer.timeout.connect(self.fake_update)
        self.fake_update_timer.start(5000)

    def update_datetime(self):
        now = QDateTime.currentDateTime()
        self.datetime_label.setText(f"Date/Time: {now.toString('yyyy-MM-dd HH:mm:ss')}")

    def fake_update(self):
        # This method simulates updates; replace with real MT5 data hooks.
        import random
        self.symbol_label.setText(f"Symbol: EURUSD")
        price = round(1.10 + random.uniform(-0.005, 0.005), 5)
        self.price_label.setText(f"Live Price: {price}")
        self.session_label.setText("Session: Market Open")
        self.status_label.setText("Scanner Status: Running")
        self.append_event(f"Updated price to {price}")

    def append_event(self, text):
        timestamp = QDateTime.currentDateTime().toString('HH:mm:ss')
        self.event_log.append(f"[{timestamp}] {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = LiveScannerGUI()
    gui.resize(800, 300)
    gui.show()
    sys.exit(app.exec())
