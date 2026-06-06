"""Strategy Registry - 策略注册表

所有策略的回测结果统一存储、评分、排名。

评分公式（0-100）:
    score = 年化收益权重 * 30
          + 夏普比率权重 * 30
          + 回撤控制权重 * 20
          + 胜率权重 * 10
          + Alpha权重 * 10

支持策略类型:
    - etf_rotation:    ETF轮动
    - multi_factor:    多因子
    - industry_rotation: 行业轮动
    - dividend:        红利策略
    - trend:           趋势策略
"""
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass, field
import json, os

STRATEGY_TYPES = [
    "etf_rotation", "multi_factor", "industry_rotation",
    "dividend", "trend", "momentum", "mean_reversion",
]


@dataclass
class StrategyRecord:
    """策略回测记录"""
    strategy_id: str        # 唯一ID
    strategy_name: str      # 策略名称
    strategy_type: str      # 策略类型
    version: str            # 版本号
    market: str             # 市场: A股/港股/美股/加密
    period: str             # 回测区间
    params: dict            # 策略参数

    # 收益指标
    annual_return: float    # 年化收益 %
    total_return: float     # 总收益 %
    max_drawdown: float     # 最大回撤 %
    sharpe_ratio: float     # 夏普比率
    sortino_ratio: float    # Sortino比率
    win_rate: float         # 胜率 %
    trade_count: int        # 交易次数

    # 基准对比
    benchmark_return: float = 0     # 基准年化收益 %
    alpha: float = 0                # Alpha
    excess_return: float = 0        # 超额收益 %

    # 元数据
    created_at: str = ""
    score: float = 0                # 综合评分 0-100
    rank: int = 0                   # 排名
    tags: List[str] = field(default_factory=list)


class StrategyRegistry:
    """策略注册表

    管理所有策略的回测结果，提供评分和排名。
    数据持久化到 JSON 文件。
    """

    def __init__(self, data_dir: str = None):
        self.records: Dict[str, StrategyRecord] = {}
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data'
        )
        self._registry_file = os.path.join(self.data_dir, 'strategy_registry.json')
        self._load()

    def _load(self):
        """从文件加载"""
        if os.path.exists(self._registry_file):
            with open(self._registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    record = StrategyRecord(**item)
                    self.records[record.strategy_id] = record

    def _save(self):
        """保存到文件"""
        os.makedirs(self.data_dir, exist_ok=True)
        data = []
        for r in self.records.values():
            d = {
                'strategy_id': r.strategy_id, 'strategy_name': r.strategy_name,
                'strategy_type': r.strategy_type, 'version': r.version,
                'market': r.market, 'period': r.period, 'params': r.params,
                'annual_return': r.annual_return, 'total_return': r.total_return,
                'max_drawdown': r.max_drawdown, 'sharpe_ratio': r.sharpe_ratio,
                'sortino_ratio': r.sortino_ratio, 'win_rate': r.win_rate,
                'trade_count': r.trade_count,
                'benchmark_return': r.benchmark_return, 'alpha': r.alpha,
                'excess_return': r.excess_return,
                'created_at': r.created_at, 'score': r.score,
                'rank': r.rank, 'tags': r.tags,
            }
            data.append(d)
        with open(self._registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register(self, record: StrategyRecord) -> StrategyRecord:
        """注册策略回测结果"""
        if not record.created_at:
            record.created_at = datetime.now().isoformat()
        record.score = self._calculate_score(record)
        self.records[record.strategy_id] = record
        self._update_ranks()
        self._save()
        return record

    def _calculate_score(self, r: StrategyRecord) -> float:
        """计算综合评分 (0-100)

        公式:
            score = normalize(annual_return) * 30
                  + normalize(sharpe) * 30
                  + normalize(max_drawdown) * 20  (越小越好)
                  + normalize(win_rate) * 10
                  + normalize(alpha) * 10
        """
        # 年化收益评分 (0-30): -20%~+40% → 0~30
        ar_score = max(0, min(30, (r.annual_return + 20) / 60 * 30))

        # 夏普评分 (0-30): 0~2 → 0~30
        sharpe_score = max(0, min(30, r.sharpe_ratio / 2 * 30))

        # 回撤评分 (0-20): -60%~0% → 20~0 (回撤越小分越高)
        dd_score = max(0, min(20, (60 - abs(r.max_drawdown)) / 60 * 20))

        # 胜率评分 (0-10): 0%~100% → 0~10
        wr_score = max(0, min(10, r.win_rate / 100 * 10))

        # Alpha评分 (0-10): -10%~+20% → 0~10
        alpha_score = max(0, min(10, (r.alpha + 10) / 30 * 10))

        return round(ar_score + sharpe_score + dd_score + wr_score + alpha_score, 1)

    def _update_ranks(self):
        """更新排名"""
        sorted_records = sorted(
            self.records.values(), key=lambda r: r.score, reverse=True
        )
        for i, r in enumerate(sorted_records):
            r.rank = i + 1

    def get_leaderboard(self, strategy_type: str = None,
                        market: str = None, limit: int = 20) -> List[StrategyRecord]:
        """获取排行榜"""
        records = list(self.records.values())
        if strategy_type:
            records = [r for r in records if r.strategy_type == strategy_type]
        if market:
            records = [r for r in records if r.market == market]
        records.sort(key=lambda r: r.score, reverse=True)
        return records[:limit]

    def get_record(self, strategy_id: str) -> Optional[StrategyRecord]:
        return self.records.get(strategy_id)

    def delete_record(self, strategy_id: str) -> bool:
        if strategy_id in self.records:
            del self.records[strategy_id]
            self._update_ranks()
            self._save()
            return True
        return False

    def get_summary(self) -> dict:
        """注册表摘要"""
        records = list(self.records.values())
        if not records:
            return {"total": 0}
        return {
            "total": len(records),
            "avg_score": round(sum(r.score for r in records) / len(records), 1),
            "best_score": max(r.score for r in records),
            "by_type": {t: len([r for r in records if r.strategy_type == t])
                        for t in set(r.strategy_type for r in records)},
            "by_market": {m: len([r for r in records if r.market == m])
                          for m in set(r.market for r in records)},
        }
