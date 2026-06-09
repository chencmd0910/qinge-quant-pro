"""AI Lab API — 面向AI的全能力接口

统一入口：策略创建、回测、保存、对比、优化，一条命令搞定。
所有端点均返回结构化JSON，适合AI直接调用。
"""
import json
import os
import sys
from datetime import datetime
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/ai", tags=["AI Lab"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")
RESULTS_DIR = os.path.join(DATA_DIR, "backtest_results")
REGISTRY_FILE = os.path.join(DATA_DIR, "strategy_registry.json")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_registry(data):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _save_result(strategy_id: str, result: dict):
    """保存回测结果到文件"""
    path = os.path.join(RESULTS_DIR, f"{strategy_id}.json")
    result["saved_at"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)


def _load_result(strategy_id: str) -> dict | None:
    path = os.path.join(RESULTS_DIR, f"{strategy_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ═══════════════════════════════════════════════════════════
# 1. 一站式：创建策略 + 回测 + 保存
# ═══════════════════════════════════════════════════════════

@router.post("/create-and-backtest")
def create_and_backtest(payload: dict):
    """创建策略并立即回测，一条命令搞定。

    请求体:
    {
        "strategy_name": "我的多因子策略",
        "strategy_type": "multi_factor",    // multi_factor | etf_rotation | industry_rotation | dividend
        "description": "基于v25因子的改进策略",
        
        // 回测参数（全部可选，有默认值）
        "start": "2024-06-01",
        "end": "2026-06-09",
        "cash": 1000000,
        "top_n": 20,
        "rebalance": "monthly",             // monthly | biweekly | weekly
        "stop_loss": -0.08,
        "commission": 0.0003,
        "slippage": 0.0002,
        "ranking_factor": "v25_multi",
        
        // 自定义股票池（可选，不传默认沪深前300只）
        "codes": ["000001", "600519", ...],
        
        // 自定义因子权重（可选，不传默认v25权重）
        "factor_weights": {
            "mom_5d": 0.30,
            "mom_10d": 0.15,
            ...
        }
    }

    返回：策略详情 + 回测结果
    """
    from backtest_engine.real_backtest import RealBacktest
    from data_engine.kline_parquet import get_kline_engine

    # ── 1. 创建策略 ──
    strategy_id = payload.get("strategy_id") or f"ai_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    strategy_name = payload.get("strategy_name", f"AI策略_{datetime.now().strftime('%m%d_%H%M')}")
    strategy_type = payload.get("strategy_type", "multi_factor")

    registry = _load_registry()
    strategy = {
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "strategy_type": strategy_type,
        "version": payload.get("version", "1.0"),
        "description": payload.get("description", ""),
        "status": "RESEARCH",
        "lifecycle": {"status": "RESEARCH", "live_days": 0, "decay_status": "NONE"},
        "backtest_params": {
            "start": payload.get("start", "2024-06-01"),
            "end": payload.get("end", "2026-06-09"),
            "cash": payload.get("cash", 1_000_000),
            "top_n": payload.get("top_n", 20),
            "rebalance": payload.get("rebalance", "monthly"),
            "stop_loss": payload.get("stop_loss", -0.08),
            "commission": payload.get("commission", 0.0003),
            "slippage": payload.get("slippage", 0.0002),
            "ranking_factor": payload.get("ranking_factor", "v25_multi"),
        },
        "factor_weights": payload.get("factor_weights"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # 去重：如果已有同名策略，用新版本号
    existing = [s for s in registry if s.get("strategy_id") == strategy_id]
    for ex in existing:
        registry.remove(ex)
    registry.append(strategy)
    _save_registry(registry)

    # ── 2. 运行回测 ──
    try:
        codes = payload.get("codes")
        if not codes:
            engine = get_kline_engine()
            codes = engine.get_available_stocks()[:300]

        bt = RealBacktest(
            codes=codes,
            start=payload.get("start", "2024-06-01"),
            end=payload.get("end", "2026-06-09"),
            cash=payload.get("cash", 1_000_000),
            top_n=payload.get("top_n", 20),
            rebalance=payload.get("rebalance", "monthly"),
            commission=payload.get("commission", 0.0003),
            slippage=payload.get("slippage", 0.0002),
            stop_loss=payload.get("stop_loss", -0.08),
            ranking_factor=payload.get("ranking_factor", "v25_multi"),
        )
        result = bt.run()

        if result.get("error"):
            strategy["status"] = "ERROR"
            strategy["error"] = result["error"]
            _save_registry(registry)
            return {"strategy": strategy, "backtest": None, "error": result["error"]}

        # ── 3. 保存回测结果 ──
        m = result["metrics"]
        strategy["metrics"] = {
            "total_return": m.get("total_return", 0),
            "annual_return": m.get("annual_return", 0),
            "sharpe_ratio": m.get("sharpe_ratio", 0),
            "max_drawdown": m.get("max_drawdown", 0),
            "win_rate": m.get("win_rate", 0),
            "alpha": round(m.get("annual_return", 0) - 3.0, 1),
            "trade_count": len(result.get("trades", [])),
            "calmar_ratio": m.get("calmar_ratio", 0),
        }
        strategy["status"] = "BACKTESTED"
        strategy["equity_curve"] = result.get("equity_curve", [])
        strategy["trades_sample"] = result.get("trades", [])[:20]  # 只保留前20笔用于预览
        strategy["updated_at"] = datetime.now().isoformat()
        _save_registry(registry)

        # 保存完整回测文件
        result["strategy_id"] = strategy_id
        result["strategy_name"] = strategy_name
        _save_result(strategy_id, result)

        return {
            "success": True,
            "strategy": strategy,
            "backtest_summary": {
                "total_return": m["total_return"],
                "annual_return": m["annual_return"],
                "sharpe_ratio": m["sharpe_ratio"],
                "max_drawdown": m["max_drawdown"],
                "win_rate": m["win_rate"],
                "trade_count": len(result.get("trades", [])),
                "equity_curve_points": len(result.get("equity_curve", [])),
            },
            "message": f"策略 [{strategy_name}] 创建并回测完成！"
                       f" 累计收益: {m['total_return']}%"
                       f" 年化: {m['annual_return']}%"
                       f" 夏普: {m['sharpe_ratio']:.2f}"
                       f" 最大回撤: {m['max_drawdown']}%",
        }

    except Exception as e:
        strategy["status"] = "ERROR"
        strategy["error"] = str(e)
        _save_registry(registry)
        return {"strategy": strategy, "backtest": None, "error": str(e)}


# ═══════════════════════════════════════════════════════════
# 2. 批量回测：跑多组参数对比
# ═══════════════════════════════════════════════════════════

@router.post("/batch-backtest")
def batch_backtest(payload: dict):
    """批量回测多组参数，用于AI自动寻优。

    请求体:
    {
        "variations": [
            {"strategy_name": "动量×10", "top_n": 10},
            {"strategy_name": "动量×20", "top_n": 20},
            {"strategy_name": "动量×30", "top_n": 30},
        ],
        // 共享基础参数
        "start": "2024-06-01",
        "end": "2026-06-09",
        "cash": 1000000,
        "rebalance": "monthly",
    }
    """
    from backtest_engine.real_backtest import RealBacktest
    from data_engine.kline_parquet import get_kline_engine

    base = {
        "start": payload.get("start", "2024-06-01"),
        "end": payload.get("end", "2026-06-09"),
        "cash": payload.get("cash", 1_000_000),
        "rebalance": payload.get("rebalance", "monthly"),
        "stop_loss": payload.get("stop_loss", -0.08),
        "commission": payload.get("commission", 0.0003),
        "slippage": payload.get("slippage", 0.0002),
        "ranking_factor": payload.get("ranking_factor", "v25_multi"),
    }

    engine = get_kline_engine()
    codes = payload.get("codes") or engine.get_available_stocks()[:300]

    results = []
    variations = payload.get("variations", [{"strategy_name": "默认配置", "top_n": 20}])

    for i, var in enumerate(variations):
        params = {**base, **var}
        try:
            bt = RealBacktest(codes=codes, **{
                k: v for k, v in params.items()
                if k in ["start", "end", "cash", "top_n", "rebalance", "commission", "slippage", "stop_loss", "ranking_factor"]
            })
            r = bt.run()
            if r.get("error"):
                results.append({"name": var.get("strategy_name", f"var_{i}"), "error": r["error"]})
            else:
                m = r["metrics"]
                results.append({
                    "name": var.get("strategy_name", f"var_{i}"),
                    "params": {k: v for k, v in params.items() if k not in ["codes"] and k in var},
                    "total_return": m["total_return"],
                    "annual_return": m["annual_return"],
                    "sharpe_ratio": m["sharpe_ratio"],
                    "max_drawdown": m["max_drawdown"],
                    "win_rate": m["win_rate"],
                    "trades": len(r.get("trades", [])),
                })
        except Exception as e:
            results.append({"name": var.get("strategy_name", f"var_{i}"), "error": str(e)})

    # 按夏普排序
    valid = [r for r in results if "error" not in r]
    valid.sort(key=lambda x: x.get("sharpe_ratio", -99), reverse=True)

    # 自动保存所有策略到基因库
    saved = []
    registry = _load_registry()
    gen_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for r in results:
        sid = f"gen_{datetime.now().strftime('%Y%m%d%H%M')}_{len(saved):03d}"
        s = {
            "strategy_id": sid,
            "strategy_name": r.get("name", sid),
            "strategy_type": payload.get("strategy_type", "multi_factor"),
            "generation_id": gen_id,
            "rank": len(saved) + 1,
            "lifecycle": {"status": "ARCHIVED", "live_days": 0, "decay_status": "NONE"},
            "metrics": {
                "total_return": r.get("total_return", 0),
                "annual_return": r.get("annual_return", 0),
                "sharpe_ratio": r.get("sharpe_ratio", 0),
                "max_drawdown": r.get("max_drawdown", 0),
                "win_rate": r.get("win_rate", 0),
                "trade_count": r.get("trades", 0),
            },
            "backtest_params": r.get("params", {}),
            "created_at": datetime.now().isoformat(),
        }
        if "error" in r:
            s["lifecycle"]["status"] = "FAILED"
            s["error"] = r["error"]
        registry.append(s)
        saved.append(s)
        
        # 保存完整回测文件（如果有数据）
        if "error" not in r:
            _save_result(sid, {
                "strategy_id": sid,
                "strategy_name": r["name"],
                "generation_id": gen_id,
                "metrics": s["metrics"],
                "params": s["backtest_params"],
            })
    
    _save_registry(registry)
    
    # 自动提拔前5名
    top_n = payload.get("promote_top", 5)
    promoted = []
    for i, s in enumerate(saved):
        if i < top_n and s["lifecycle"]["status"] != "FAILED":
            # 更新registry中的状态
            for reg in registry:
                if reg.get("strategy_id") == s["strategy_id"]:
                    reg["lifecycle"]["status"] = "ACTIVE"
                    break
            s["lifecycle"]["status"] = "ACTIVE"
            promoted.append(s["strategy_id"])
    
    _save_registry(registry)

    return {
        "generation_id": gen_id,
        "total": len(results),
        "succeeded": len(valid),
        "failed": len(results) - len(valid),
        "promoted_top": top_n,
        "promoted_ids": promoted,
        "ranked": valid,
        "errors": [r for r in results if "error" in r],
        "best": valid[0] if valid else None,
        "all_saved": True,
        "gene_pool_size": len(registry),
    }


# ═══════════════════════════════════════════════════════════
# 3. 查看所有策略（含回测结果）
# ═══════════════════════════════════════════════════════════

@router.get("/strategies")
def list_all_strategies():
    """列出所有已创建的策略及其回测状态"""
    registry = _load_registry()
    summaries = []
    for s in registry:
        m = s.get("metrics", {})
        summaries.append({
            "strategy_id": s.get("strategy_id"),
            "strategy_name": s.get("strategy_name"),
            "strategy_type": s.get("strategy_type"),
            "status": s.get("status"),
            "total_return": m.get("total_return", 0),
            "annual_return": m.get("annual_return", 0),
            "sharpe_ratio": m.get("sharpe_ratio", 0),
            "max_drawdown": m.get("max_drawdown", 0),
            "trade_count": m.get("trade_count", 0),
            "created_at": s.get("created_at"),
        })
    return sorted(summaries, key=lambda x: x.get("created_at", ""), reverse=True)


# ═══════════════════════════════════════════════════════════
# 4. 回测结果详情
# ═══════════════════════════════════════════════════════════

@router.get("/backtest-result/{strategy_id}")
def get_backtest_detail(strategy_id: str):
    """获取某个策略的完整回测结果（含权益曲线和交易明细）"""
    result = _load_result(strategy_id)
    if not result:
        raise HTTPException(404, f"策略 {strategy_id} 的回测结果不存在，请先运行回测")
    return result


# ═══════════════════════════════════════════════════════════
# 5. 策略对比
# ═══════════════════════════════════════════════════════════

@router.post("/compare")
def compare_strategies(payload: dict):
    """对比多个策略的回测结果

    {"strategy_ids": ["ai_strategy_xxx", "ai_strategy_yyy"]}
    """
    ids = payload.get("strategy_ids", [])
    results = {}
    for sid in ids:
        result = _load_result(sid)
        if result:
            m = result.get("metrics", {})
            results[sid] = {
                "strategy_name": result.get("strategy_name", sid),
                "total_return": m.get("total_return"),
                "annual_return": m.get("annual_return"),
                "sharpe_ratio": m.get("sharpe_ratio"),
                "max_drawdown": m.get("max_drawdown"),
                "win_rate": m.get("win_rate"),
                "trade_count": len(result.get("trades", [])),
            }
    return {"compared": results}


# ═══════════════════════════════════════════════════════════
# 6. 策略基因库 — 演变/存留/学习
# ═══════════════════════════════════════════════════════════

@router.get("/genealogy")
def get_genealogy():
    """获取策略家族树 — 所有已生成策略的完整DNA，供AI进化学习
    
    返回每代所有策略的参数+回测指标，AI可分析：
    - 哪些参数组合表现好/差
    - 进化方向建议
    - 参数与夏普/收益/回撤的相关性
    """
    registry = _load_registry()
    
    by_gen = {}
    for s in registry:
        gen = s.get("generation_id", "legacy")
        by_gen.setdefault(gen, [])
        m = s.get("metrics", {})
        by_gen[gen].append({
            "strategy_id": s.get("strategy_id"),
            "strategy_name": s.get("strategy_name"),
            "status": s.get("lifecycle", {}).get("status", s.get("status", "UNKNOWN")),
            "rank": s.get("rank"),
            "params": s.get("backtest_params", {}),
            "total_return": m.get("total_return", 0),
            "annual_return": m.get("annual_return", 0),
            "sharpe_ratio": m.get("sharpe_ratio", 0),
            "max_drawdown": m.get("max_drawdown", 0),
            "win_rate": m.get("win_rate", 0),
            "trade_count": m.get("trade_count", 0),
        })
    
    active_count = sum(1 for s in registry if s.get("lifecycle", {}).get("status") == "ACTIVE")
    archived_count = sum(1 for s in registry if s.get("lifecycle", {}).get("status") == "ARCHIVED")
    failed_count = sum(1 for s in registry if s.get("lifecycle", {}).get("status") == "FAILED")
    
    # 参数洞察：好策略（夏普>0.3）的通用参数
    good = [s for s in registry if s.get("metrics", {}).get("sharpe_ratio", 0) > 0.3]
    param_insights = {}
    for s in good:
        for k, v in s.get("backtest_params", {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                param_insights.setdefault(k, []).append(v)
    for k in param_insights:
        vals = param_insights[k]
        if len(vals) >= 3:
            param_insights[k] = {"avg": round(sum(vals)/len(vals), 4), "min": min(vals), "max": max(vals)}
        else:
            param_insights[k] = None
    param_insights = {k: v for k, v in param_insights.items() if v}
    
    return {
        "generations_count": len(by_gen),
        "total_strategies": len(registry),
        "active": active_count,
        "archived": archived_count,
        "failed": failed_count,
        "param_insights": param_insights,
        "by_generation": by_gen,
    }


@router.get("/genealogy/summary")
def get_genealogy_summary():
    """基因库速览 — 每代TOP3 + 史上最佳"""
    registry = _load_registry()
    by_gen = {}
    for s in registry:
        gen = s.get("generation_id", "legacy")
        by_gen.setdefault(gen, []).append(s)
    
    summary = {"total": len(registry), "active_count": 0, "all_time_best": None, "generations": []}
    for s in registry:
        if s.get("lifecycle", {}).get("status") == "ACTIVE":
            summary["active_count"] += 1
    
    all_best_sharpe = -99
    for gen_id, strategies in by_gen.items():
        ranked = sorted(strategies, key=lambda x: x.get("metrics", {}).get("sharpe_ratio", -99), reverse=True)
        top3 = ranked[:3]
        gen_summary = {
            "generation_id": gen_id,
            "count": len(strategies),
            "active": sum(1 for s in strategies if s.get("lifecycle", {}).get("status") == "ACTIVE"),
            "avg_sharpe": round(sum(s.get("metrics", {}).get("sharpe_ratio", 0) for s in strategies) / max(len(strategies), 1), 3),
            "top3": [{
                "id": s["strategy_id"], "name": s["strategy_name"],
                "sharpe": s.get("metrics", {}).get("sharpe_ratio", 0),
                "total_return": s.get("metrics", {}).get("total_return", 0),
                "max_drawdown": s.get("metrics", {}).get("max_drawdown", 0),
                "params": s.get("backtest_params", {}),
            } for s in top3],
        }
        summary["generations"].append(gen_summary)
        if top3 and top3[0].get("metrics", {}).get("sharpe_ratio", -99) > all_best_sharpe:
            all_best_sharpe = top3[0]["metrics"]["sharpe_ratio"]
            summary["all_time_best"] = {
                "strategy_id": top3[0]["strategy_id"], "name": top3[0]["strategy_name"],
                "sharpe": all_best_sharpe, "total_return": top3[0]["metrics"]["total_return"],
                "params": top3[0].get("backtest_params", {}),
            }
    return summary


@router.post("/promote")
def promote_strategies(payload: dict):
    """批量提拔/淘汰策略
    {
        "promote": ["id1", "id2"],    // ACTIVE
        "retire": ["id3"],            // RETIRED
        "archive": ["id4"]            // ARCHIVED
    }"""
    registry = _load_registry()
    results = {"promoted": [], "retired": [], "archived": []}
    for sid in payload.get("promote", []):
        for s in registry:
            if s.get("strategy_id") == sid:
                s.setdefault("lifecycle", {})["status"] = "ACTIVE"
                s["lifecycle"]["live_days"] = s["lifecycle"].get("live_days", 0) + 1
                s["updated_at"] = datetime.now().isoformat()
                results["promoted"].append(sid)
    for sid in payload.get("retire", []):
        for s in registry:
            if s.get("strategy_id") == sid:
                s.setdefault("lifecycle", {})["status"] = "RETIRED"
                s["lifecycle"]["decay_status"] = "RETIRED_BY_USER"
                s["updated_at"] = datetime.now().isoformat()
                results["retired"].append(sid)
    for sid in payload.get("archive", []):
        for s in registry:
            if s.get("strategy_id") == sid:
                s.setdefault("lifecycle", {})["status"] = "ARCHIVED"
                s["updated_at"] = datetime.now().isoformat()
                results["archived"].append(sid)
    _save_registry(registry)
    return results


@router.post("/evolve")
def evolve_next_generation(payload: dict):
    """基于历史基因库进化下一代策略（自动读取历史+变异+回测+全保存）
    {
        "count": 50,
        "promote_top": 5,
        "base": {"start": "2024-06-01", "end": "2026-06-09", "rebalance": "monthly"},
        "explore_params": {"top_n": [10,20,30,40], "stop_loss": [-5,-8,-10,-12]},
        "inherit_from_best": true
    }"""
    from backtest_engine.real_backtest import RealBacktest
    from data_engine.kline_parquet import get_kline_engine
    import random

    count = payload.get("count", 30)
    promote_top = payload.get("promote_top", 5)
    base = payload.get("base", {})
    explore = payload.get("explore_params", {
        "top_n": [10, 20, 30, 40, 50],
        "stop_loss": [-5, -8, -10, -12, -15],
        "rebalance": ["monthly", "biweekly"],
    })
    inherit = payload.get("inherit_from_best", True)

    engine = get_kline_engine()
    codes = payload.get("codes") or engine.get_available_stocks()[:300]

    # 读取历史基因库
    genealogy = get_genealogy()
    best_params_hint = genealogy.get("param_insights", {})

    # 史上最佳策略
    best_ever = None
    for gen in genealogy.get("by_generation", {}).values():
        for s in gen:
            if best_ever is None or s.get("sharpe_ratio", -99) > best_ever.get("sharpe_ratio", -99):
                best_ever = s

    gen_num = len(genealogy.get("by_generation", {})) + 1
    variations = []

    for i in range(count):
        var = {"strategy_name": f"Gen{gen_num}_Strategy_{i+1:03d}"}
        for param_key, options in explore.items():
            if isinstance(options, list) and options:
                if inherit and param_key in best_params_hint:
                    hint = best_params_hint[param_key]
                    if isinstance(hint, dict) and "avg" in hint:
                        noise = hint["avg"] * random.uniform(-0.3, 0.3)
                        var[param_key] = hint["avg"] + noise if isinstance(hint["avg"], float) else int(hint["avg"] + noise)
                    else:
                        var[param_key] = random.choice(options)
                else:
                    var[param_key] = random.choice(options)
        variations.append(var)

    # 最佳策略变异体
    if best_ever and inherit:
        bp = best_ever.get("params", {})
        for i in range(min(count // 10, 5)):
            var = {"strategy_name": f"Gen{gen_num}_BestMutant_{i+1}"}
            for k, v in bp.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    var[k] = int(v * random.uniform(0.85, 1.15)) if isinstance(v, int) else v * random.uniform(0.85, 1.15)
                else:
                    var[k] = v
            variations.append(var)

    result = batch_backtest({**payload, "variations": variations, "promote_top": promote_top})
    result["evolved_from_generations"] = len(genealogy.get("by_generation", {}))
    result["best_ever_inherited"] = best_ever["strategy_name"] if best_ever else None
    return result


# ═══════════════════════════════════════════════════════════
# 7. 系统能力清单（供AI了解可用操作）
# ═══════════════════════════════════════════════════════════

@router.get("/capabilities")
def get_capabilities():
    """AI Lab 完整能力清单"""
    return {
        "version": "2.0",
        "gene_pool_enabled": True,
        "data": {
            "stocks": "4965只A股（Parquet K线，2024-06 至 2026-06）",
            "engine": "v25 多因子（7因子：mom_5d/10d, ma_dev_20d, consistency, money_flow, vol_20d, boll_pos）",
        },
        "endpoints": [
            {"method": "POST", "path": "/api/ai/create-and-backtest", "desc": "创建策略+回测+保存"},
            {"method": "POST", "path": "/api/ai/batch-backtest", "desc": "批量回测+全保存+自动提优"},
            {"method": "POST", "path": "/api/ai/evolve", "desc": "基于历史基因库进化下一代"},
            {"method": "GET", "path": "/api/ai/genealogy", "desc": "策略家族树（全部DNA）"},
            {"method": "GET", "path": "/api/ai/genealogy/summary", "desc": "基因库速览（每代TOP3）"},
            {"method": "POST", "path": "/api/ai/promote", "desc": "批量提拔/淘汰/归档策略"},
            {"method": "GET", "path": "/api/ai/strategies", "desc": "列出所有策略"},
            {"method": "GET", "path": "/api/ai/backtest-result/{id}", "desc": "完整回测结果"},
            {"method": "POST", "path": "/api/ai/compare", "desc": "多策略横向对比"},
        ],
    }
