"""QMT券商适配器 - A股实盘

QMT (Quick Market Trading) 是迅投的量化交易客户端。
依赖: xtquant
"""
from ..broker_base import BrokerBase
from typing import Optional
from ...event_engine.core.event import OrderEvent, FillEvent


class QMTBroker(BrokerBase):
    """QMT实盘券商

    TODO: 实现QMT接口
    依赖: pip install xtquant
    """

    def __init__(self, path: str = "", account: str = ""):
        self.path = path      # QMT安装路径
        self.account = account  # 交易账号
        self._connected = False

    def connect(self) -> bool:
        # TODO: 连接QMT
        return False

    def disconnect(self):
        self._connected = False

    def send_order(self, order: OrderEvent) -> Optional[FillEvent]:
        # TODO: QMT下单
        return None

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_position(self, symbol: str) -> dict:
        return {}

    def get_account(self) -> dict:
        return {}

    def get_market_price(self, symbol: str) -> float:
        return 0.0
