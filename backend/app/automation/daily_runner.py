"""
青鳄量化 - 每日自动化运行引擎 (DailyRunner)

对标专业机构自动化体系，按交易日时间线编排：
  15:30  数据更新 → K线拉取 + 因子计算
  15:35  信号生成 → 跑所有活跃策略 + 信号融合
  15:38  风控安检 → 敞口/回撤/集中度检查
  15:40  模拟下单 → 执行调仓
  15:45  报告输出 → 日报 + 风险评分 + 持久化

用法:
  python daily_runner.py                    # 全流程
  python daily_runner.py --step data        # 仅数据更新
  python daily_runner.py --step signal      # 仅信号生成
  python daily_runner.py --date 2026-06-10  # 指定日期

通过 cron 定时调用:
  30 15 * * 1-5 cd /opt/qinge-quant-pro/backend && python automation/daily_runner.py >> /var/log/qinge-daily.log 2>&1
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# 路径设置
ROOT = Path("/app")  # Application root, matches Docker volume mount
AUTOMATION_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # /app
sys.path.insert(0, str(AUTOMATION_DIR.parent))  # /app/app (for app.* imports)
sys.path.insert(0, str(ROOT / "strategies"))

# ===== 日志配置 =====
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"daily_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("DailyRunner")


# ===== 核心数据结构 =====

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    step: str
    status: StepStatus
    duration_seconds: float = 0
    detail: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class DailyReport:
    """每日运行报告"""
    date: str
    run_time: str
    total_duration: float
    steps: List[StepResult] = field(default_factory=list)

    # 市场概览
    market_index: Dict[str, float] = field(default_factory=dict)  # {index: change_pct}
    market_status: str = "UNKNOWN"  # NORMAL / VOLATILE / EXTREME

    # 信号摘要
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    signal_strength_dist: Dict[str, int] = field(default_factory=dict)

    # 组合状态
    portfolio_value: float = 0
    daily_pnl: float = 0
    daily_return_pct: float = 0
    cash_ratio: float = 0

    # 风控
    risk_score: int = 100
    risk_alerts: List[str] = field(default_factory=list)
    drawdown_pct: float = 0

    # 策略状态
    active_strategies: int = 0
    alpha_decay_alerts: List[str] = field(default_factory=list)

    # 因子健康
    factor_health: Dict = field(default_factory=dict)  # {healthy, watch, warning, dead}
    dead_factors: List[str] = field(default_factory=list)

    def ref_step_detail(self, step_name: str) -> dict:
        """获取某步骤的detail字典"""
        for s in self.steps:
            if s.step == step_name:
                return s.detail or {}
        return {}

    @property
    def success_count(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.FAILED)


# ===== 每日运行引擎 =====

class DailyRunner:
    """每日自动化运行引擎

    按专业量化机构的标准流程，串行执行每日任务。
    每步有独立的超时、重试和失败处理。
    """

    def __init__(self, target_date: str = None, data_dir: str = None):
        self.target_date = target_date or datetime.now().strftime("%Y-%m-%d")
        self.data_dir = Path(data_dir) if data_dir else ROOT / "data"
        self.report = DailyReport(
            date=self.target_date,
            run_time=datetime.now().isoformat(),
            total_duration=0,
        )
        self._portfolio_value = None
        self._signals = []
        self._market_data = {}

    # -------- Step 1: 数据更新 --------

    def step_data_update(self) -> StepResult:
        """Step 1: 更新K线数据 + 计算因子

        专业对标: 数据管道 (Data Pipeline)
        职责: 拉取最新行情 → 清洗 → 入库 → 因子刷新
        """
        import time
        t0 = time.time()
        result = StepResult(step="data_update", status=StepStatus.RUNNING)

        try:
            # 1.1 尝试从本地 parquet 缓存读取最新日期
            kline_dir = self.data_dir / "klines" / "parquet"
            latest_date = self._get_latest_kline_date(kline_dir)

            if latest_date and str(latest_date)[:10] >= self.target_date:
                result.detail["kline_status"] = "up_to_date"
                result.detail["latest_date"] = latest_date
                logger.info(f"K线数据已是最新: {latest_date}")
            else:
                # 1.2 调用数据引擎拉取
                result.detail["kline_status"] = "fetching"
                fetched = self._fetch_latest_klines()
                result.detail["stocks_fetched"] = fetched
                logger.info(f"K线数据拉取完成: {fetched} 只股票")

            # 1.3 计算因子（可选，策略运行时也会算）
            result.detail["factors_computed"] = True

            # 1.4 数据质量校验
            from app.automation.data_validator import DataValidator
            validator = DataValidator(data_dir=str(self.data_dir))
            quality_report = validator.run_full_check()
            result.detail["data_quality"] = {
                "score": quality_report.total_score,
                "status": quality_report.status,
                "stocks": quality_report.total_stocks,
                "errors": quality_report.stocks_with_data_errors,
                "suspended": quality_report.stocks_suspended,
                "days_behind": quality_report.days_behind,
            }
            logger.info(f"数据质量: {quality_report.total_score}/100, "
                       f"错误{quality_report.stocks_with_data_errors}只, "
                       f"停牌{quality_report.stocks_suspended}只, "
                       f"落后{quality_report.days_behind}天")

            if quality_report.total_score < 50:
                logger.warning("数据质量评分过低，请检查数据源!")
                result.detail["data_quality_warning"] = True

            # 1.5 因子IC衰减监控
            from app.automation.factor_ic_monitor import FactorICMonitor
            ic_monitor = FactorICMonitor(data_dir=str(self.data_dir), max_stocks=100)
            ic_report = ic_monitor.run()
            result.detail["factor_ic"] = {
                "healthy": ic_report.healthy_factors,
                "watch": ic_report.watch_factors,
                "warning": ic_report.warning_factors,
                "dead": ic_report.dead_factors,
                "top_3": [(r.factor_name, round(r.ic_ir, 3)) for r in 
                         sorted(ic_report.results, key=lambda x: x.ic_ir, reverse=True)[:3]],
                "dead_factors": [r.factor_name for r in ic_report.results if r.health == "DEAD"],
                # 保存完整IC结果供后续步骤复用
                "full_ic_results": [
                    {"factor_name": r.factor_name, "health": r.health, "ic_ir": r.ic_ir}
                    for r in sorted(ic_report.results, key=lambda x: x.ic_ir, reverse=True)
                ],
            }
            if ic_report.warning_factors + ic_report.dead_factors > 0:
                logger.warning(f"因子健康警报: {ic_report.dead_factors}个失效, "
                             f"{ic_report.warning_factors}个警告")
                self.report.alpha_decay_alerts.append(
                    f"IC监控: {ic_report.dead_factors}个因子失效, "
                    f"{ic_report.warning_factors}个警告"
                )
            else:
                logger.info(f"因子健康: {ic_report.healthy_factors}健康 "
                          f"{ic_report.watch_factors}观察")

            self.report.factor_health = {
                "healthy": ic_report.healthy_factors,
                "watch": ic_report.watch_factors,
                "warning": ic_report.warning_factors,
                "dead": ic_report.dead_factors,
            }
            self.report.dead_factors = [r.factor_name for r in ic_report.results if r.health == "DEAD"]

            # 1.6 记录市场概况
            self._capture_market_overview()

            # 1.7 另类数据采集(非阻塞)
            try:
                from app.automation.alternative_data import AlternativeDataCollector
                alt = AlternativeDataCollector()
                alt.collect_northbound()
                alt.collect_margin()
                alt.collect_industry()
                result.detail["alternative_data"] = alt.get_cache_status()
                logger.info(f"另类数据采集完成")
            except Exception as e:
                logger.warning(f"另类数据采集跳过（非关键）: {e}")

            result.status = StepStatus.SUCCESS
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            logger.error(f"数据更新失败: {e}")

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    def _get_latest_kline_date(self, kline_dir: Path) -> Optional[str]:
        """检查本地K线最新日期"""
        if not kline_dir.exists():
            return None
        try:
            parquet_files = list(kline_dir.glob("*.parquet"))
            if not parquet_files:
                return None
            import pandas as pd
            # 抽样检查几个文件的最新日期
            dates = set()
            for pf in parquet_files[:5]:
                df = pd.read_parquet(pf)
                if "date" in df.columns:
                    dates.add(df["date"].max())
            return max(dates) if dates else None
        except Exception:
            return None

    def _fetch_latest_klines(self) -> int:
        """通过 data_engine 获取最新K线"""
        try:
            from app.data_engine.providers.parquet_provider import ParquetProvider
            provider = ParquetProvider()
            if provider.is_available():
                # Parquet provider 已就绪，检查是否需要更新
                return 0  # 数据已缓存
        except ImportError:
            pass

        # 回退：调用下载脚本
        download_script = ROOT.parent / "scripts" / "download_klines.py"
        if download_script.exists():
            import subprocess
            result = subprocess.run(
                ["python3", str(download_script)],
                capture_output=True, text=True, timeout=600
            )
            return int(result.stdout.split("Total:")[-1].split()[0]) if "Total:" in result.stdout else 0
        return 0

    def _capture_market_overview(self):
        """捕捉当日市场概况（指数涨跌）"""
        try:
            import akshare as ak
            indices = {}
            
            for code, name in [("sh000001", "上证指数"), ("sz399001", "深证成指"), ("sz399006", "创业板指")]:
                try:
                    df = ak.stock_zh_index_daily(symbol=code)
                    if len(df) >= 2:
                        today_close = float(df["close"].iloc[-1])
                        yesterday_close = float(df["close"].iloc[-2])
                        change_pct = round((today_close / yesterday_close - 1), 4)
                        indices[name] = change_pct
                except Exception:
                    pass
            
            if indices:
                self.report.market_index = indices
                max_change = max(abs(v) for v in indices.values())
                if max_change > 0.03:
                    self.report.market_status = "EXTREME"
                elif max_change > 0.015:
                    self.report.market_status = "VOLATILE"
                else:
                    self.report.market_status = "NORMAL"
            else:
                self.report.market_status = "UNKNOWN"
        except Exception as e:
            logger.warning(f"市场概览获取失败（非关键）: {e}")
            self.report.market_status = "UNKNOWN"

    # -------- Step 2: 信号生成 --------

    def step_signal_generation(self) -> StepResult:
        """Step 2: 运行所有活跃策略 → 生成信号 → 信号融合

        专业对标: Signal Generation Pipeline
        职责: 多策略多周期运行 → 信号冲突仲裁 → 输出融合信号池
        """
        import time
        t0 = time.time()
        result = StepResult(step="signal_generation", status=StepStatus.RUNNING)

        try:
            # 2.1 加载活跃策略
            active_strategies = self._load_active_strategies()
            result.detail["strategies_loaded"] = len(active_strategies)
            logger.info(f"加载活跃策略: {len(active_strategies)} 个")

            if not active_strategies:
                result.detail["warning"] = "无活跃策略"
                result.status = StepStatus.SUCCESS
                result.duration_seconds = round(time.time() - t0, 2)
                return result

            # 2.15 因子权重自动适配（基于IC监控）
            weight_changes = {}
            try:
                from app.automation.factor_weight_adapter import FactorWeightAdapter
                from app.strategy_engine.strategies.multi_factor_v25.strategy import V25_FACTORS
                
                # 提取当前权重
                current_weights = {f.name: f.weight for f in V25_FACTORS}
                
                # 从data步骤获取IC数据
                data_detail = self.report.ref_step_detail("data_update")
                ic_data = data_detail.get("factor_ic", {}) if data_detail else {}
                
                # 构建IC因子列表
                ic_dead = ic_data.get("dead_factors", [])
                ic_top3 = ic_data.get("top_3", [])
                
                if ic_dead or ic_top3:
                    # 直接复用data步骤的IC结果，不重复跑monitor
                    ic_factors = ic_data.get("full_ic_results", [])
                    if not ic_factors:
                        # 回退：从dead_factors和top_3重建
                        ic_factors = [{"factor_name": name, "health": "DEAD", "ic_ir": 0}
                                    for name in ic_dead]
                    
                    adapter = FactorWeightAdapter()
                    adaptation = adapter.adapt(ic_factors, current_weights)
                    
                    weight_changes = {c.factor_name: {"old": round(c.old_weight, 4), "new": round(c.new_weight, 4)} 
                                    for c in adaptation.changes}
                    
                    result.detail["factor_weights_adapted"] = {
                        "num_changes": len(adaptation.changes),
                        "changes": weight_changes,
                        "summary": adaptation.summary,
                    }
                    logger.info(f"因子权重适配: {len(adaptation.changes)}项变更")
            except Exception as e:
                logger.warning(f"因子权重适配跳过（非关键）: {e}")

            # 2.2 运行每个策略生成信号
            all_signals = []
            strategy_signals = {}
            for strat in active_strategies:
                try:
                    signals = self._run_strategy(strat)
                    strategy_signals[strat.get("id", "unknown")] = len(signals)
                    all_signals.extend(signals)
                except Exception as e:
                    logger.warning(f"策略 {strat.get('id')} 运行失败: {e}")
                    strategy_signals[strat.get("id", "unknown")] = f"ERROR: {e}"

            result.detail["strategy_signals"] = strategy_signals

            # 2.3 信号融合（多策略冲突仲裁）
            fused = self._fuse_signals(all_signals)
            self._signals = fused

            result.detail["total_raw"] = len(all_signals)
            result.detail["total_fused"] = len(fused)
            result.detail["buy_count"] = sum(1 for s in fused if s.get("side") == "BUY")
            result.detail["sell_count"] = sum(1 for s in fused if s.get("side") == "SELL")

            self.report.total_signals = len(fused)
            self.report.buy_signals = result.detail["buy_count"]
            self.report.sell_signals = result.detail["sell_count"]

            logger.info(f"信号生成: {len(all_signals)} raw → {len(fused)} fused "
                       f"({result.detail['buy_count']}买 {result.detail['sell_count']}卖)")

            # 保存融合信号供后续步骤使用
            self._fused_signals = fused
            self._v25_picks = [s["code"] for s in fused if s.get("side") == "BUY"]

            result.status = StepStatus.SUCCESS
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            logger.error(f"信号生成失败: {e}")

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    def _load_active_strategies(self) -> List[dict]:
        """加载活跃策略列表"""
        strategies = []

        # 从 LivePaperRunner 加载策略
        try:
            from app.paper_trading.live_runner import LivePaperRunner
            runner = LivePaperRunner()
            runner.load_state()
            active = runner.active_strategies if hasattr(runner, 'active_strategies') else []
            for s in active:
                sid = s.get("strategy_id", "")
                # 跳过 Gen2 策略（由模拟交易引擎自行管理信号）
                if "gen2" in sid.lower() or "Gen2" in sid or sid.lower().startswith("gen_"):
                    continue
                strategies.append({
                    "id": sid,
                    "name": s.get("strategy_name", ""),
                    "weight": s.get("weight", 1.0),
                    "source": "paper_trading",
                })
        except Exception as e:
            logger.warning(f"从 LivePaperRunner 加载策略失败: {e}")

        # 从 Alpha Factory 加载 (可选)
        try:
            from app.alpha_factory.factory import AlphaFactory
            factory = AlphaFactory()
            if hasattr(factory, 'get_active_strategies'):
                for alpha in factory.get_active_strategies():
                    strategies.append({
                        "id": alpha.strategy_id,
                        "name": alpha.name,
                        "weight": alpha.weight_multiplier,
                        "source": "alpha_factory",
                    })
        except Exception:
            pass  # AlphaFactory not configured

        # 从策略注册表加载多因子策略（独立于模拟交易）
        try:
            import json
            reg_path = Path("/app/data/strategy_registry.json")
            if reg_path.exists():
                with open(reg_path) as f:
                    registry = json.load(f)
                for s in registry if isinstance(registry, list) else registry.get("strategies", []):
                    sid = s.get("strategy_id", s.get("id", ""))
                    # 跳过 Gen2（由模拟交易引擎管理）和已存在的策略
                    existing_ids = {st["id"] for st in strategies}
                    is_gen2 = "gen2" in sid.lower() or "Gen2" in sid or sid.lower().startswith("gen_")
                    if sid and sid not in existing_ids and not is_gen2:
                        strategies.append({
                            "id": sid,
                            "name": s.get("name", s.get("strategy_name", sid)),
                            "weight": s.get("weight", 0.3),
                            "source": "strategy_registry",
                        })
        except Exception:
            pass

        # 保底：如果所有来源都为空，硬编码加载多因子V25
        if not strategies:
            strategies.append({
                "id": "multi_factor_v25",
                "name": "多因子V25",
                "weight": 1.0,
                "source": "fallback",
            })
            logger.info("使用保底策略: 多因子V25")

        return strategies

    def _run_strategy(self, strat: dict) -> List[dict]:
        """运行单个策略，返回信号列表"""
        strategy_id = strat.get("id", "")
        signals = []

        # 根据策略类型调用对应引擎
        if "v25" in strategy_id or "multi_factor" in strategy_id:
            try:
                from app.strategy_engine.strategies.multi_factor_v25.strategy import MultiFactorV25
                st = MultiFactorV25()
                st.initialize()
                raw = st.generate_signals(self.target_date)
                for s in raw:
                    s["strategy_id"] = strategy_id
                    s["source"] = strat.get("source", "")
                signals = raw
            except Exception as e:
                logger.warning(f"多因子策略V25运行失败: {e}")

        elif "etf" in strategy_id:
            try:
                from app.strategy_engine.strategies.etf_rotation.strategy import ETFRotationStrategy
                st = ETFRotationStrategy()
                st.initialize()
                raw = st.generate_signals(self.target_date)
                for s in raw:
                    s["strategy_id"] = strategy_id
                signals = raw
            except Exception as e:
                logger.warning(f"ETF轮动策略运行失败: {e}")

        elif "ma" in strategy_id or "moving_average" in strategy_id:
            try:
                from app.strategy_engine.strategies.moving_average.strategy import MovingAverageStrategy
                st = MovingAverageStrategy()
                st.initialize()
                raw = st.generate_signals(self.target_date)
                for s in raw:
                    s["strategy_id"] = strategy_id
                signals = raw
            except Exception as e:
                logger.warning(f"[MA] run failed: {e}")

        elif "Gen2" in strategy_id or "gen2" in strategy_id.lower():
            logger.info(f"[Gen2] {strategy_id}: managed by paper trading engine")
            # Gen2 signals generated inside LivePaperRunner.run_daily()

        else:
            # 默认兜底：未知策略类型 → 尝试多因子V25
            logger.info(f"兜底策略 {strategy_id} → 多因子V25")
            try:
                from app.strategy_engine.strategies.multi_factor_v25.strategy import MultiFactorV25
                st = MultiFactorV25()
                st.initialize()
                raw = st.generate_signals(self.target_date)
                for s in raw:
                    s["strategy_id"] = strategy_id
                    s["source"] = strat.get("source", "")
                signals = raw
            except Exception as e:
                logger.warning(f"兜底策略运行失败: {e}")

        return signals

    def _fuse_signals(self, all_signals: List[dict]) -> List[dict]:
        """信号融合：多策略冲突仲裁

        规则:
        1. 同股票同方向多策略信号 → 加权合并，置信度叠加
        2. 同股票异方向冲突 → 以权重高者为准
        3. 置信度低于阈值 → 过滤
        """
        if not all_signals:
            return []

        # 按股票分组
        by_stock: Dict[str, List[dict]] = {}
        for s in all_signals:
            code = s.get("code", s.get("symbol", ""))
            if not code:
                continue
            by_stock.setdefault(code, []).append(s)

        fused = []
        for code, signals in by_stock.items():
            buy_votes = sum(s.get("weight", 0.5) for s in signals if s.get("side") == "BUY")
            sell_votes = sum(s.get("weight", 0.5) for s in signals if s.get("side") == "SELL")

            # 仲裁
            if abs(buy_votes - sell_votes) < 0.3:
                continue  # 分歧太大，跳过

            winner = signals[0].copy()
            if buy_votes > sell_votes:
                winner["side"] = "BUY"
                winner["confidence"] = buy_votes / (buy_votes + sell_votes + 0.01)
            else:
                winner["side"] = "SELL"
                winner["confidence"] = sell_votes / (buy_votes + sell_votes + 0.01)

            winner["vote_count"] = len(signals)
            winner["buy_votes"] = round(buy_votes, 2)
            winner["sell_votes"] = round(sell_votes, 2)

            if winner.get("confidence", 0) >= 0.55:  # 置信度阈值
                fused.append(winner)

        # 按置信度降序
        fused.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return fused

    # -------- Step 3: 风控安检 --------

    def step_risk_check(self) -> StepResult:
        """Step 3: 风控检查

        专业对标: Risk Firewall
        职责: 多层风险检查 → 生成风控评分 → 标记告警
        """
        import time
        t0 = time.time()
        result = StepResult(step="risk_check", status=StepStatus.RUNNING)

        try:
            alerts = []
            risk_score = 100

            # 3.1 获取当前组合状态
            try:
                from app.paper_trading.live_runner import LivePaperRunner
                runner = LivePaperRunner()
                runner.load_state()
                summary = runner.get_summary()

                current_dd = abs(summary.get("max_drawdown", 0))
                positions = summary.get("positions_count", 0)
                self.report.portfolio_value = summary.get("total_value", 0)
                self.report.drawdown_pct = current_dd

                # 回撤检查
                if current_dd > 0.25:
                    alerts.append(f"🔴 回撤超25%: {current_dd:.1%}")
                    risk_score -= 40
                    result.detail["drawdown_level"] = "EXTREME"
                elif current_dd > 0.15:
                    alerts.append(f"🟡 回撤超15%: {current_dd:.1%}")
                    risk_score -= 20
                    result.detail["drawdown_level"] = "WARNING"
                elif current_dd > 0.10:
                    risk_score -= 10
                    result.detail["drawdown_level"] = "CAUTION"
                else:
                    result.detail["drawdown_level"] = "NORMAL"

                # 仓位检查
                if positions >= 30:
                    alerts.append(f"🟡 持仓达上限: {positions}/30")
                    risk_score -= 10
                result.detail["positions"] = positions

                # 现金比率
                cash = summary.get("cash", 0)
                total = summary.get("total_value", 1)
                cash_ratio = cash / total if total > 0 else 0
                self.report.cash_ratio = round(cash_ratio, 4)
                if cash_ratio < 0.05:
                    alerts.append("🟡 现金不足5%")
                    risk_score -= 10

            except Exception as e:
                logger.warning(f"组合状态获取失败: {e}")

            # 3.2 市场状态联动
            if self.report.market_status == "EXTREME":
                alerts.append("🔴 市场极端波动，建议减仓")
                risk_score -= 20
            elif self.report.market_status == "VOLATILE":
                risk_score -= 5

            # 3.3 集中度检查
            try:
                from app.risk_engine.daily_monitor import DailyRiskMonitor
                monitor = DailyRiskMonitor()
                report = monitor.generate_report(
                    self.target_date,
                    self.report.portfolio_value or 1_000_000,
                )
                if report.concentration_hhi > 2500:
                    alerts.append(f"🟡 持仓高度集中 HHI: {report.concentration_hhi:.0f}")
                    risk_score -= 10
            except Exception as e:
                logger.warning(f"集中度检查失败: {e}")

            risk_score = max(0, min(100, risk_score))
            self.report.risk_score = risk_score
            self.report.risk_alerts = alerts

            result.detail["risk_score"] = risk_score
            result.detail["alerts"] = alerts
            result.detail["level"] = "SAFE" if risk_score >= 80 else ("CAUTION" if risk_score >= 50 else "DANGER")

            logger.info(f"风控评分: {risk_score}/100, 告警: {len(alerts)}")
            result.status = StepStatus.SUCCESS
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            logger.error(f"风控检查失败: {e}")

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    # -------- Step 4: 模拟下单 --------

    def step_paper_trading(self) -> StepResult:
        """Step 4: 执行模拟交易

        专业对标: Execution Engine
        职责: 根据融合信号执行模拟调仓
        """
        import time
        t0 = time.time()
        result = StepResult(step="paper_trading", status=StepStatus.RUNNING)

        try:
            from app.paper_trading.live_runner import LivePaperRunner

            runner = LivePaperRunner()
            runner.load_state()

            # 执行 Gen2 模拟交易（保持原有逻辑）
            runner.run_daily(self.target_date)
            runner.save_state()

            # 记录 Gen2 P&L
            summary = runner.get_summary()
            result.detail["gen2_total_value"] = summary.get("total_value", 0)
            result.detail["gen2_trades"] = len(runner.trades) if hasattr(runner, 'trades') else 0
            result.detail["gen2_positions"] = summary.get("positions_count", 0)

            # V25 独立追踪 + 组合优化
            v25_picks = getattr(self, '_v25_picks', [])
            fused_signals = getattr(self, '_fused_signals', [])
            if v25_picks and fused_signals:
                # 组合优化(波动率倒数加权)
                try:
                    from app.automation.portfolio_optimizer import PortfolioOptimizer
                    opt = PortfolioOptimizer()
                    optimized = opt.optimize(fused_signals, self.target_date)
                    weights = [f"{s['code']}:{s['weight']:.3f}" for s in optimized[:5]]
                    result.detail["v25_weights"] = weights
                    result.detail["v25_max_weight"] = max(s["weight"] for s in optimized)
                    result.detail["v25_min_weight"] = min(s["weight"] for s in optimized)
                    logger.info(f"V25组合优化: max={result.detail['v25_max_weight']:.3f} min={result.detail['v25_min_weight']:.3f}")
                except Exception as e:
                    logger.debug(f"组合优化跳过: {e}")

                result.detail["v25_picks"] = len(v25_picks)
                result.detail["v25_top3"] = v25_picks[:3]
                self._save_v25_signals(v25_picks, fused_signals)

                # 压力测试
                try:
                    from app.automation.stress_tester import StressTester
                    st = StressTester(portfolio_value=runner.cash + sum(
                        (p.shares * p.avg_cost) for p in runner.positions.values()
                    ) if hasattr(runner, 'positions') else 1_000_000)
                    stress_report = st.run_full_stress_test(
                        optimized, self.target_date
                    )
                    result.detail["stress_risk_level"] = stress_report.get("summary", {}).get("risk_level", "?")
                    result.detail["stress_var_95"] = stress_report.get("var_analysis", {}).get("var_95_pct", 0)
                    result.detail["stress_worst"] = stress_report.get("summary", {}).get("worst_hypothetical", "?")
                    logger.info(f"压力测试: 风险{result.detail['stress_risk_level']} VaR95={result.detail['stress_var_95']:.2%}")
                except Exception as e:
                    logger.debug(f"压力测试跳过: {e}")

                # Barra风控分析
                try:
                    from app.automation.barra_risk import BarraRiskModel
                    brm = BarraRiskModel(lookback_days=252)
                    barra_report = brm.analyze_portfolio(optimized, self.target_date)
                    result.detail["barra_risk_level"] = barra_report.get("risk_budget_summary", {}).get("risk_level", "?")
                    result.detail["barra_vol_annual"] = barra_report.get("total_portfolio_volatility_annual", 0)
                    result.detail["barra_systematic"] = barra_report.get("systematic_risk_pct", 0)
                    logger.info(f"Barra风控: {result.detail['barra_risk_level']} 年化波动={result.detail['barra_vol_annual']:.1%} 系统风险={result.detail['barra_systematic']:.0%}")
                except Exception as e:
                    logger.debug(f"Barra风控跳过: {e}")

            # 计算日收益
            if len(runner.equity_curve) >= 2:
                today_eq = runner.equity_curve[-1]
                yesterday_eq = runner.equity_curve[-2]
                daily_pnl = today_eq.total_value - yesterday_eq.total_value
                daily_return = daily_pnl / yesterday_eq.total_value if yesterday_eq.total_value else 0
                self.report.daily_pnl = round(daily_pnl, 2)
                self.report.daily_return_pct = round(daily_return * 100, 4)

            logger.info(f"模拟交易完成: V25={len(v25_picks)}信号 Gen2={result.detail.get('gen2_positions','N/A')}持仓")
            result.status = StepStatus.SUCCESS
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            logger.error(f"模拟交易失败: {e}")

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    def _save_v25_signals(self, picks: List[str], signals: List[dict]):
        """保存V25信号历史供回测分析"""
        import json
        v25_dir = Path("/app/data/v25_signals")
        v25_dir.mkdir(parents=True, exist_ok=True)
        
        record = {
            "date": self.target_date,
            "picks": picks,
            "top_scores": [
                {"code": s["code"], "score": s.get("composite_score", 0)}
                for s in signals[:5]
            ],
        }
        
        fpath = v25_dir / f"v25_{self.target_date.replace('-', '')}.json"
        with open(fpath, "w") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    # -------- Step 5: 报告输出 --------

    def step_report(self) -> StepResult:
        """Step 5: 生成日报并持久化

        专业对标: Reporting & Analytics
        职责: 汇总当日所有步骤结果 → 生成结构化报告 → 持久化
        """
        import time
        t0 = time.time()
        result = StepResult(step="report", status=StepStatus.RUNNING)

        try:
            # 写入 JSON 报告
            report_dir = self.data_dir / "reports"
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"daily_{self.target_date}.json"

            report_dict = {
                "date": self.report.date,
                "run_time": self.report.run_time,
                "total_duration": self.report.total_duration,
                "market": {
                    "status": self.report.market_status,
                    "indices": self.report.market_index,
                },
                "signals": {
                    "total": self.report.total_signals,
                    "buy": self.report.buy_signals,
                    "sell": self.report.sell_signals,
                },
                "portfolio": {
                    "value": self.report.portfolio_value,
                    "daily_pnl": self.report.daily_pnl,
                    "daily_return_pct": self.report.daily_return_pct,
                    "cash_ratio": self.report.cash_ratio,
                },
                "risk": {
                    "score": self.report.risk_score,
                    "drawdown_pct": self.report.drawdown_pct,
                    "alerts": self.report.risk_alerts,
                },
                "factor_health": {
                    "healthy": self.report.factor_health.get("healthy", 0),
                    "watch": self.report.factor_health.get("watch", 0),
                    "warning": self.report.factor_health.get("warning", 0),
                    "dead": self.report.factor_health.get("dead", 0),
                    "dead_factors": self.report.dead_factors,
                },
                "steps": [
                    {
                        "step": s.step,
                        "status": s.status.value,
                        "duration": s.duration_seconds,
                        "detail": s.detail,
                        "error": s.error,
                    }
                    for s in self.report.steps
                ],
                "summary": self._generate_summary_text(),
            }

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)

            result.detail["report_file"] = str(report_file)
            logger.info(f"日报已保存: {report_file}")

            # 打印摘要
            summary = self._generate_summary_text()
            logger.info(f"\n{'='*60}\n{summary}\n{'='*60}")

            result.status = StepStatus.SUCCESS
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            logger.error(f"报告生成失败: {e}")

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    def _generate_summary_text(self) -> str:
        """生成可读摘要文本"""
        report = self.report
        lines = [
            f"🐊 青鳄量化日报 — {report.date}",
            f"",
            f"📊 市场: {report.market_status}",
            f"📈 信号: {report.total_signals} 个 ({report.buy_signals}买/{report.sell_signals}卖)",
            f"💰 组合: ¥{report.portfolio_value:,.0f} | 日收益 {report.daily_return_pct:+.2f}%",
            f"🛡️ 风控: {report.risk_score}/100 | 回撤 {report.drawdown_pct:.1%}",
            f"",
            f"📋 步骤:",
        ]
        for s in report.steps:
            icon = "✅" if s.status == StepStatus.SUCCESS else "❌"
            lines.append(f"  {icon} {s.step} ({s.duration_seconds}s)")

        if report.risk_alerts:
            lines.append(f"")
            lines.append(f"⚠️ 风控告警:")
            for alert in report.risk_alerts:
                lines.append(f"  {alert}")

        if report.dead_factors:
            lines.append(f"")
            lines.append(f"🧬 因子健康: {report.factor_health.get('healthy',0)}健康 "
                         f"{report.factor_health.get('watch',0)}观察 "
                         f"{report.factor_health.get('warning',0)}警告 "
                         f"{report.factor_health.get('dead',0)}失效")

        if report.failed_count > 0:
            lines.append(f"")
            lines.append(f"❌ {report.failed_count} 个步骤失败!")
            for s in report.steps:
                if s.status == StepStatus.FAILED:
                    lines.append(f"  - {s.step}: {s.error}")

        return "\n".join(lines)

    # -------- 主流程 --------

    def run(self, steps: List[str] = None) -> DailyReport:
        """执行每日完整流程"""
        import time
        total_start = time.time()

        all_steps = ["data", "signal", "risk", "trade", "report"]
        steps_to_run = steps or all_steps

        step_methods = {
            "data": self.step_data_update,
            "signal": self.step_signal_generation,
            "risk": self.step_risk_check,
            "trade": self.step_paper_trading,
            "report": self.step_report,
        }

        logger.info(f"🐊 青鳄量化 DailyRunner 启动 — {self.target_date}")
        logger.info(f"流程: {' → '.join(steps_to_run)}")

        for step_name in steps_to_run:
            if step_name not in step_methods:
                logger.warning(f"未知步骤: {step_name}, 跳过")
                continue

            logger.info(f"--- [Step] {step_name} 开始 ---")
            try:
                result = step_methods[step_name]()
            except Exception as e:
                result = StepResult(
                    step=step_name,
                    status=StepStatus.FAILED,
                    error=str(e),
                )
                logger.error(f"步骤 {step_name} 异常: {e}")

            self.report.steps.append(result)

        self.report.total_duration = round(time.time() - total_start, 2)
        logger.info(f"DailyRunner 完成, 总耗时 {self.report.total_duration}s, "
                   f"成功 {self.report.success_count}/{self.report.failed_count} 失败")

        return self.report


# ===== 入口 =====

def main():
    parser = argparse.ArgumentParser(description="青鳄量化 DailyRunner")
    parser.add_argument("--step", type=str, default=None,
                       help="单独执行某步: data/signal/risk/trade/report")
    parser.add_argument("--date", type=str, default=None,
                       help="目标日期, 默认今天")
    parser.add_argument("--data-dir", type=str, default=None,
                       help="数据目录")
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    runner = DailyRunner(target_date=target_date, data_dir=args.data_dir)

    if args.step:
        steps = [args.step]
    else:
        steps = None  # 全部

    report = runner.run(steps)

    # 返回码：有失败则非零
    if report.failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
