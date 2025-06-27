from dataclasses import dataclass
from typing import List

@dataclass
class Company:
    ticker: str
    name: str
    market_cap: str
    currency: str
    price: str
    high_price: str
    drop_from_high: str
    pe: str
    daily_change: str
    eps: str
    sector: str
    moat: str
    price_history: List[float]
