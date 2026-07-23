import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from typing import Optional
from config import CONFIG

class MT5Provider:
    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        if not mt5.initialize():
            print(f"[MT5] Initialization failed, error {mt5.last_error()}")
            self.connected = False
        else:
            self.connected = True
        return self.connected

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def verify_symbol(self, symbol: str) -> bool:
        info = mt5.symbol_info(symbol)
        return info is not None and info.visible

    def get_rate_series(self, symbol: str, timeframe: str, n: int = 500) -> pd.DataFrame:
        tf = self._map_timeframe(timeframe)
        now = datetime.utcnow()
        rates = mt5.copy_rates_from(symbol, tf, now, n)
        if rates is None:
            raise RuntimeError(f"Failed to fetch rates for {symbol} {timeframe}")
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    @staticmethod
    def _map_timeframe(tf_str: str) -> int:
        mapping = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        if tf_str not in mapping:
            raise ValueError(f"Unsupported timeframe {tf_str}")
        return mapping[tf_str]