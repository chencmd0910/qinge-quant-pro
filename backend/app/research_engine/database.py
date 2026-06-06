"""Research Database - 研究结果数据库

存储所有策略研究结果。
未来100→1000→10000个策略时，最大的资产是历史研究数据。

表: research_runs
    id, created_at, strategy_id, strategy_name, strategy_type,
    status, annual_return, max_drawdown, sharpe, alpha,
    validation_score, walk_forward_score, factor_count, factors
"""
from typing import List, Optional, Dict
from datetime import datetime
import json, os


class ResearchDatabase:
    """研究结果数据库

    使用JSON文件存储（生产环境可换PostgreSQL）。
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'research'
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self._db_file = os.path.join(self.data_dir, 'research_runs.json')
        self.runs: List[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self._db_file):
            with open(self._db_file, 'r', encoding='utf-8') as f:
                self.runs = json.load(f)

    def _save(self):
        with open(self._db_file, 'w', encoding='utf-8') as f:
            json.dump(self.runs, f, ensure_ascii=False, indent=2)

    def insert(self, run: dict) -> dict:
        """插入一条研究记录"""
        run.setdefault("id", len(self.runs) + 1)
        run.setdefault("created_at", datetime.now().isoformat())
        self.runs.append(run)
        self._save()
        return run

    def insert_batch(self, runs: List[dict]) -> int:
        """批量插入"""
        for run in runs:
            run.setdefault("id", len(self.runs) + 1)
            run.setdefault("created_at", datetime.now().isoformat())
        self.runs.extend(runs)
        self._save()
        return len(runs)

    def get_all(self) -> List[dict]:
        return self.runs

    def get_by_status(self, status: str) -> List[dict]:
        return [r for r in self.runs if r.get("status") == status]

    def get_top(self, metric: str = "sharpe", limit: int = 10) -> List[dict]:
        """获取排行榜"""
        valid = [r for r in self.runs if r.get("status") not in ("FAILED", "FILTERED")]
        return sorted(valid, key=lambda r: r.get(metric, 0), reverse=True)[:limit]

    def get_summary(self) -> dict:
        """研究数据库摘要"""
        if not self.runs:
            return {"total": 0}
        return {
            "total": len(self.runs),
            "by_status": {s: len([r for r in self.runs if r.get("status") == s])
                          for s in set(r.get("status", "unknown") for r in self.runs)},
            "avg_sharpe": round(sum(r.get("sharpe", 0) for r in self.runs) / len(self.runs), 3),
            "avg_alpha": round(sum(r.get("alpha", 0) for r in self.runs) / len(self.runs), 3),
            "best_sharpe": max(r.get("sharpe", 0) for r in self.runs),
            "best_alpha": max(r.get("alpha", 0) for r in self.runs),
        }

    def count(self) -> int:
        return len(self.runs)
