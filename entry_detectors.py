import pandas as pd
from typing import Dict

def confirm_entry(df_ltf: pd.DataFrame, selected_poi: Dict, **params) -> bool:
    if not selected_poi:
        return False
    last = df_ltf.iloc[-1]
    tolerance = params.get("tolerance", 0.001)
    price = selected_poi["price"]
    diff = abs(last["close"] - price) / price

    if selected_poi["type"].endswith("_BULL"):
        direction_ok = last["close"] > last["open"]
    elif selected_poi["type"].endswith("_BEAR"):
        direction_ok = last["close"] < last["open"]
    else:
        direction_ok = True

    return direction_ok and diff <= tolerance
