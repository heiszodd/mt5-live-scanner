# download_history.py
"""
Script to download 1-minute historical data for XAUUSD and USTEC (or NQ) using MetaTrader5 API.
Exports CSV and Parquet files in a data/ folder.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# Configuration
SYMBOLS = ["XAUUSD", "USTEC"]  # replace "USTEC" with "NQ" if preferred
TIMEFRAME = mt5.TIMEFRAME_M1
# Number of minutes of data to fetch (e.g., last 1 day = 1440 minutes)
MINUTES = 1440

def ensure_data_folder():
    os.makedirs("data", exist_ok=True)

def fetch_rates(symbol: str, minutes: int) -> pd.DataFrame:
    if not mt5.initialize():
        raise RuntimeError(f"MetaTrader5 initialization failed: {mt5.last_error()}")
    # Ensure symbol is available
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Failed to select symbol {symbol}")
    utc_to = datetime.utcnow()
    utc_from = utc_to - timedelta(minutes=minutes)
    rates = mt5.copy_rates_range(symbol, TIMEFRAME, utc_from, utc_to)
    mt5.shutdown()
    if rates is None:
        raise RuntimeError(f"No rates returned for {symbol}")
    df = pd.DataFrame(rates)
    # Convert time column from seconds since epoch to readable datetime
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

def export_df(df: pd.DataFrame, symbol: str):
    csv_path = os.path.join("data", f"{symbol}_m1.csv")
    parquet_path = os.path.join("data", f"{symbol}_m1.parquet")
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"Exported {symbol} data to {csv_path} and {parquet_path}")

def main():
    ensure_data_folder()
    for sym in SYMBOLS:
        print(f"Fetching {sym}...")
        df = fetch_rates(sym, MINUTES)
        export_df(df, sym)

if __name__ == "__main__":
    main()
