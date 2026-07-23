import pandas as pd
from typing import List, Dict
from config import CONFIG

def detect_fvg(df: pd.DataFrame, **params) -> List[Dict]:
    gaps = []
    for i in range(2, len(df)):
        prev_high = df.iloc[i-2]["high"]
        prev_low  = df.iloc[i-2]["low"]
        cur_high  = df.iloc[i]["high"]
        cur_low   = df.iloc[i]["low"]
        if cur_low > prev_high:
            gaps.append({"type": "FVG_BULL", "index": i, "price": cur_low, "status": "active"})
        elif cur_high < prev_low:
            gaps.append({"type": "FVG_BEAR", "index": i, "price": cur_high, "status": "active"})
    return gaps

def detect_ifvg(df: pd.DataFrame, **params) -> List[Dict]:
    return []

def detect_order_block(df: pd.DataFrame, **params) -> List[Dict]:
    blocks = []
    for i in range(1, len(df)-1):
        body = abs(df.iloc[i]["close"] - df.iloc[i]["open"])
        prev_body = abs(df.iloc[i-1]["close"] - df.iloc[i-1]["open"])
        if body > prev_body * 1.5:
            blocks.append({"type": "OrderBlock", "index": i, "price": df.iloc[i]["close"], "status": "active"})
    return blocks

def detect_breaker_block(df: pd.DataFrame, **params) -> List[Dict]:
    return []

def detect_liquidity_pool(df: pd.DataFrame, **params) -> List[Dict]:
    return []

DETECTORS = {
    "FVG": detect_fvg,
    "IFVG": detect_ifvg,
    "OrderBlock": detect_order_block,
    "BreakerBlock": detect_breaker_block,
    "LiquidityPool": detect_liquidity_pool
}

def run_poi_detection(df: pd.DataFrame) -> List[Dict]:
    results = []
    for rule in CONFIG.poi_rules:
        if not rule.enabled:
            continue
        detector = DETECTORS.get(rule.name)
        if detector:
            results.extend(detector(df, **rule.params))
    return results
