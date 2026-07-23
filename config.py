from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class POIRule:
    name: str
    enabled: bool = True
    params: Dict = field(default_factory=dict)

@dataclass
class RiskRule:
    max_risk_percent: float = 1.0
    sl_multiplier: float = 1.5
    tp_multiplier: float = 3.0
    rr_min: float = 1.5

@dataclass
class Config:
    htf: str = "H4"
    ltf: str = "M1"
    poi_rules: List[POIRule] = field(default_factory=lambda: [
        POIRule(name="FVG"),
        POIRule(name="IFVG"),
        POIRule(name="OrderBlock"),
        POIRule(name="BreakerBlock"),
        POIRule(name="LiquidityPool")
    ])
    session_filters: List[str] = field(default_factory=lambda: [
        "Asia", "London", "NY", "NY_Judas", "NY_Equity_Open", "Silver_Bullet"
    ])
    risk: RiskRule = RiskRule()
    beep_enabled: bool = True
    sound_file: str = ""

CONFIG = Config()