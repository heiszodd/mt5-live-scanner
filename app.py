import time
from mt5_provider import MT5Provider
from session_detector import current_session
from poi_detectors import run_poi_detection
from entry_detectors import confirm_entry
from alert_engine import alert
from config import CONFIG

def main():
    provider = MT5Provider()
    if not provider.connect():
        alert("Failed to connect to MT5", "INFO")
        return
    print("MT5 Scanner Engine initialized successfully.")

if __name__ == "__main__":
    main()
