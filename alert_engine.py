import sys
import time
from colorama import init, Fore, Style
from config import CONFIG

init(autoreset=True)

def beep():
    if sys.platform == "win32":
        import winsound
        winsound.Beep(1000, 200)
    else:
        print("\a", end="", flush=True)

def alert(message: str, alert_type: str = "INFO", sound: bool = True):
    colors = {
        "INFO": Fore.CYAN,
        "BUY": Fore.GREEN,
        "SELL": Fore.RED,
        "ENTRY": Fore.MAGENTA,
    }
    color = colors.get(alert_type.upper(), Fore.WHITE)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{timestamp}] {alert_type.upper():<6} {message}{Style.RESET_ALL}")
    if sound and CONFIG.beep_enabled:
        beep()
