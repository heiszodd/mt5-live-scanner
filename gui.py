# -*- coding: utf-8 -*-
"""
MT5 Live Scanner GUI

A clean PySide6 based user interface for interacting with MetaTrader5.
It provides login controls, connection handling, live positions, history, and an event log.
"""

import sys
from PySide6 import QtWidgets, QtCore, QtGui
import MetaTrader5 as mt5

class MT5Connector(QtCore.QObject):
    connection_success = QtCore.Signal()
    connection_failed = QtCore.Signal(str)
    disconnected = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False

    def connect(self, login: int, password: str, server: str):
        if not mt5.initialize(login=login, password=password, server=server):
            err = mt5.last_error()
            self.connection_failed.emit(f"MT5 initialization failed: Code {err[0]} - {err[1]}")
            return
        self.connected = True
        self.connection_success.emit()

    def disconnect(self):
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.disconnected.emit()

class HeaderCard(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        title = QtWidgets.QLabel("MT5 Live Scanner")
        title.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Weight.Bold))
        layout.addWidget(title, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

class LoginControls(QtWidgets.QGroupBox):
    def __init__(self, connector: MT5Connector, parent=None):
        super().__init__("Login Controls", parent)
        self.connector = connector
        layout = QtWidgets.QFormLayout(self)
        self.account_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.server_edit = QtWidgets.QLineEdit()
        self.symbol_edit = QtWidgets.QLineEdit()
        layout.addRow("Account:", self.account_edit)
        layout.addRow("Password:", self.password_edit)
        layout.addRow("Server:", self.server_edit)
        layout.addRow("Symbol:", self.symbol_edit)
        btn_layout = QtWidgets.QHBoxLayout()
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addRow(btn_layout)
        self.connect_btn.clicked.connect(self.on_connect)
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.connector.connection_success.connect(self.on_connected)
        self.connector.connection_failed.connect(self.on_failed)
        self.connector.disconnected.connect(self.on_disconnected)

    def on_connect(self):
        try:
            login = int(self.account_edit.text())
        except ValueError:
            self.parent().log_event("Invalid account number.")
            return
        password = self.password_edit.text()
        server = self.server_edit.text()
        self.connector.connect(login, password, server)
        self.parent().log_event("Attempting MT5 connection...")

    def on_connected(self):
        self.parent().log_event("MT5 connected successfully.")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.connect_btn.setEnabled(False)

    def on_failed(self, msg):
        self.parent().log_event(f"Connection failed: {msg}")

    def on_disconnected(self):
        self.parent().log_event("MT5 disconnected.")
        self.connect_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def on_start(self):
        self.parent().log_event("Start scanning (placeholder).")
        # TODO: implement live scanning logic

    def on_stop(self):
        self.parent().log_event("Stop scanning (placeholder).")
        # TODO: implement stop logic

class PositionsTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setHorizontalHeaderLabels(["Ticket", "Symbol", "Volume", "Price", "Profit"])
        self.horizontalHeader().setStretchLastSection(True)
        # Placeholder: you can populate this table with live data from MT5

class HistoryTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setHorizontalHeaderLabels(["Time", "Ticket", "Symbol", "Action", "Profit"])
        self.horizontalHeader().setStretchLastSection(True)

class EventLog(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(150)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Live Scanner")
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        self.header = HeaderCard()
        layout.addWidget(self.header)
        self.connector = MT5Connector()
        self.login = LoginControls(self.connector)
        layout.addWidget(self.login)
        self.positions = PositionsTable()
        layout.addWidget(QtWidgets.QLabel("Live Positions"))
        layout.addWidget(self.positions)
        self.history = HistoryTable()
        layout.addWidget(QtWidgets.QLabel("History"))
        layout.addWidget(self.history)
        self.log = EventLog()
        layout.addWidget(QtWidgets.QLabel("Event Log"))
        layout.addWidget(self.log)

    def log_event(self, text: str):
        self.log.append(f"{QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')} - {text}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
