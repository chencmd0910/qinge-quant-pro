"""Paper Runner - 模拟盘每日运行器

每日收盘后运行:
1. 获取行情
2. 运行策略
3. 生成信号
4. 执行模拟交易
5. 更新持仓
6. 记录净值

使用:
    runner = PaperRunner(broker, strategy, data_engine)
    runner.run_daily()  # 每日调用
    runner.get_history()  # 获取历史净值
"""
from typing import List, Dict, Optional, Callable
from datetime import datetime
import json, os

from ..trading_engine.brokers.paper_broker import PaperBroker
from ..trading_engine.broker_base import Order, OrderSide, OrderStatus
from ..data_engine.providers.provider_base import Market


class PaperRunner:
    """模拟盘运行器

    每日运行策略并执行模拟交易。
    """

    def __init__(self, broker: PaperBroker, strategy_func: Callable = None,
                 data_dir: str = None):
        self.broker = broker
        self.strategy_func = strategy_func
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'paper'
        )
        os.makedirs(self.data_dir, exist_ok=True)

        self.snapshots: List[dict] = []
        self.signal_history: List[dict] = []
        self._snapshot_file = os.path.join(self.data_dir, 'paper_snapshots.json')
        self._load_snapshots()

    def _load_snapshots(self):
        if os.path.exists(self._snapshot_file):
            with open(self._snapshot_file, 'r') as f:
                self.snapshots = json.load(f)

    def _save_snapshots(self):
        with open(self._snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(self.snapshots, f, ensure_ascii=False, indent=2)

    def run_daily(self, date_str: str = None, prices: dict = None,
                  signals: List[dict] = None) -> dict:
        """每日运行

        Args:
            date_str: 日期 (默认今天)
            prices: 当日收盘价 {symbol: price}
            signals: 策略信号 [{"symbol": "510300.SH", "side": "BUY", "quantity": 100, "price": 3.50}, ...]

        Returns:
            当日快照
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # 1. 更新持仓价格
        if prices:
            self.broker.update_prices(prices)

        # 2. 执行信号
        executed = []
        if signals:
            for sig in signals:
                order = Order(
                    symbol=sig["symbol"],
                    market=Market.A_SHARE,
                    side=OrderSide.BUY if sig["side"] == "BUY" else OrderSide.SELL,
                    quantity=sig.get("quantity", 0),
                    price=sig.get("price", 0),
                )
                result = self.broker.send_order(order)
                if result:
                    executed.append({
                        "symbol": result.symbol,
                        "side": result.side.value,
                        "quantity": result.filled_quantity,
                        "price": round(result.filled_price, 4),
                        "commission": round(result.commission, 2),
                        "status": result.status.value,
                    })

        # 3. 记录快照
        snapshot = self.broker.get_snapshot()
        snapshot["date"] = date_str
        snapshot["signals"] = len(signals) if signals else 0
        snapshot["executed"] = len(executed)
        snapshot["trades_today"] = executed

        self.snapshots.append(snapshot)
        self._save_snapshots()

        # 4. 记录信号历史
        if signals:
            for sig in signals:
                self.signal_history.append({
                    "date": date_str,
                    **sig,
                })

        return snapshot

    def get_history(self) -> List[dict]:
        """获取历史净值"""
        return self.snapshots

    def get_equity_curve(self) -> List[dict]:
        """获取权益曲线"""
        return [
            {"date": s["date"], "total": s["total_equity"], "cash": s["cash"], "invested": s["market_value"]}
            for s in self.snapshots
        ]

    def get_latest_snapshot(self) -> Optional[dict]:
        """获取最新快照"""
        return self.snapshots[-1] if self.snapshots else None

    def get_performance_summary(self) -> dict:
        """获取绩效摘要"""
        if not self.snapshots:
            return {}

        first = self.snapshots[0]
        last = self.snapshots[-1]
        days = len(self.snapshots)

        initial = first["total_equity"]
        final = last["total_equity"]
        total_return = (final / initial - 1) * 100 if initial > 0 else 0

        # 最大回撤
        peak = initial
        max_dd = 0
        for s in self.snapshots:
            v = s["total_equity"]
            if v > peak:
                peak = v
            dd = (peak - v) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return {
            "start_date": first["date"],
            "end_date": last["date"],
            "trading_days": days,
            "initial_equity": initial,
            "final_equity": round(final, 2),
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_dd, 2),
            "total_trades": sum(len(s.get("trades_today", [])) for s in self.snapshots),
            "total_commission": last.get("total_commission", 0),
        }
