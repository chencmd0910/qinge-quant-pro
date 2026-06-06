from dataclasses import dataclass
from datetime import datetime


@dataclass
class Bar:
    symbol: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    change_pct: float = 0.0

    @property
    def is_limit_up(self) -> bool:
        return self.change_pct >= 9.9

    @property
    def is_limit_down(self) -> bool:
        return self.change_pct <= -9.9
