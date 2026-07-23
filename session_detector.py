from datetime import datetime, time
import pytz

SESSION_DEFINITIONS = {
    "Asia":          (time(0, 0),   time(8, 0)),
    "London":        (time(7, 0),   time(15, 0)),
    "NY":            (time(12, 30), time(20, 30)),
    "NY_Judas":      (time(13, 0),  time(14, 30)),
    "NY_Equity_Open":(time(13, 30), time(14, 0)),
    "Silver_Bullet": (time(14, 0),  time(14, 30))
}

def current_session(tz_name: str = "UTC") -> str:
    now = datetime.now(pytz.timezone(tz_name)).time()
    active = []
    for name, (start, end) in SESSION_DEFINITIONS.items():
        if start <= now < end:
            active.append(name)
    return ", ".join(active) if active else "Off-Session"
