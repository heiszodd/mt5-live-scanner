# MT5 Live Scanner Engine

A modular decision-support scanner engine built for MT5 (MetaTrader 5) trading, implementing high-timeframe (4H) POI detection and low-timeframe (1M) entry confirmation.

## Architecture

- `config.py`: Central configuration for timeframes, POI rules, and risk management.
- `mt5_provider.py`: Handles MetaTrader 5 API connection and rate streaming.
- `session_detector.py`: Detects active trading sessions (Asia, London, NY, Judas, Equity Open, Silver Bullet).
- `poi_detectors.py`: HTF POI detectors (FVG, IFVG, Order Block, Breaker Block, Liquidity Pools).
- `entry_detectors.py`: Execution timeframe entry confirmation logic.
- `alert_engine.py`: Real-time visual and audio alerts with low latency.
- `app.py`: Main application workflow loop.

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install MetaTrader5 pandas colorama pytz
   ```
2. Open MT5 desktop terminal on PC and log in to your account.
3. Run the scanner:
   ```bash
   python app.py
   ```
