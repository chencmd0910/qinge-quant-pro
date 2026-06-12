"""
Research API — 把 research_engine 接入 API 层

端到端自动策略研究:
    POST /api/research/run        → 触发完整流水线（生成→回测→验证→锦标赛）
    GET  /api/research/status     → 最新研究运行状态
    GET  /api/research/top10      → 锦标赛排行榜
    GET  /api/research/history    → 历史运行记录
    POST /api/research/promote    → 手动晋升策略到注册表
"""
import json
import os
import threading
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

router = APIRouter(prefix="/api/research", tags=["Research"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "research")
os.makedirs(DATA_DIR, exist_ok=True)

# 当前运行状态
_run_state = {
    "status": "idle",       # idle | running | completed | failed
    "started_at": None,
    "finished_at": None,
    "progress": 0,          # 0-100
    "step": "",             # 当前步骤描述
    "result": None,         # 最新运行结果
    "error": None,
}


def _save_state():
    with open(os.path.join(DATA_DIR, "run_state.json"), "w", encoding="utf-8") as f:
        s = {k: v for k, v in _run_state.items()}
        s["result"] = None  # 不持久化大结果
        json.dump(s, f, ensure_ascii=False, indent=2, default=str)


def _run_pipeline_background(count: int, generation: int):
    """后台运行研究流水线"""
    global _run_state
    try:
        _run_state["status"] = "running"
        _run_state["started_at"] = datetime.now().isoformat()
        _run_state["progress"] = 5
        _run_state["step"] = "初始化策略生成器..."
        _save_state()

        from app.research_engine.generator import StrategyGenerator, GeneratedStrategy
        from app.research_engine.lab import AIResearchLab

        lab = AIResearchLab(DATA_DIR)
        _run_state["progress"] = 10
        _run_state["step"] = f"生成 {count} 个策略变体..."
        _save_state()

        # 1. 生成
        strategies = lab.generator.generate_diverse(count)
        _run_state["progress"] = 30
        _run_state["step"] = f"已生成 {len(strategies)} 个策略，开始回测..."
        _save_state()

        # 2. 批量回测
        results = []
        total = len(strategies)
        for i, strategy in enumerate(strategies):
            if (i + 1) % max(total // 10, 1) == 0:
                pct = 30 + int((i + 1) / total * 40)
                _run_state["progress"] = min(pct, 70)
                _run_state["step"] = f"回测中... {i+1}/{total}"
                _save_state()

            try:
                metrics = lab._simulate_backtest(strategy)
                # 计算验证分
                is_valid, reasons = lab._validate_strategy(metrics)
                val_score = lab._calculate_validation_score(metrics) if is_valid else 0
                results.append({
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.name,
                    "strategy_type": "auto_generated",
                    "factors": [{"name": f[0], "weight": round(f[1], 4)} for f in strategy.factors],
                    "top_n": strategy.top_n,
                    "rebalance_freq": strategy.rebalance_freq,
                    "factor_categories": strategy.factor_categories,
                    "generation": strategy.generation,
                    "status": "VALIDATED" if is_valid else "FILTERED",
                    "validation_score": round(val_score, 1),
                    "filter_reasons": reasons if not is_valid else [],
                                    **{k: v for k, v in metrics.items() if k !=  status},
                })
            except Exception as e:
                results.append({
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.name,
                    "status": "FAILED",
                    "error": str(e),
                })

        # 3. 排名
        validated = [r for r in results if r.get("status") == "VALIDATED"]
        validated.sort(key=lambda r: r.get("validation_score", 0), reverse=True)
        top10 = validated[:10]

        _run_state["progress"] = 85
        _run_state["step"] = f"验证完成: {len(validated)} 通过 / {len(results)} 总计，正在排名..."
        _save_state()

        # 4. 保存结果
        output = {
            "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated": len(strategies),
            "backtested": len([r for r in results if r["status"] not in ("FAILED",)]),
            "validated_count": len(validated),
            "filtered": len([r for r in results if r.get("status") == "FILTERED"]),
            "failed": len([r for r in results if r.get("status") == "FAILED"]),
            "top10": [
                {
                    "rank": i + 1,
                    "strategy_id": r["strategy_id"],
                    "name": r["strategy_name"],
                    "annual_return": r.get("annual_return", 0),
                    "max_drawdown": r.get("max_drawdown", 0),
                    "sharpe": r.get("sharpe", 0),
                    "alpha": r.get("alpha", 0),
                    "validation_score": r.get("validation_score", 0),
                    "factors": [f["name"] for f in r.get("factors", [])],
                    "factor_count": len(r.get("factors", [])),
                    "top_n": r.get("top_n", 0),
                    "rebalance_freq": r.get("rebalance_freq", ""),
                }
                for i, r in enumerate(top10)
            ],
            "all_results": results,
            "summary": {
                "avg_annual": round(sum(r.get("annual_return", 0) for r in validated) / max(len(validated), 1), 2),
                "avg_sharpe": round(sum(r.get("sharpe", 0) for r in validated) / max(len(validated), 1), 3),
                "best_sharpe": max((r.get("sharpe", 0) for r in validated), default=0),
                "best_annual": max((r.get("annual_return", 0) for r in validated), default=0),
                "categories_covered": sorted(set(c for r in validated for c in r.get("factor_categories", []))),
            },
            "generation": generation,
            "created_at": datetime.now().isoformat(),
        }

        # 持久化
        output_file = os.path.join(DATA_DIR, "latest_research_run.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)

        # 追加历史
        history_file = os.path.join(DATA_DIR, "research_runs.json")
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

        history_entry = {k: v for k, v in output.items() if k != "all_results"}
        history.append(history_entry)
        if len(history) > 50:
            history = history[-50:]

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2, default=str)

        _run_state["status"] = "completed"
        _run_state["finished_at"] = datetime.now().isoformat()
        _run_state["progress"] = 100
        _run_state["step"] = f"完成! {len(validated)} 个策略通过验证，Top1: {top10[0]['strategy_name'] if top10 else 'N/A'}"
        _run_state["result"] = {k: v for k, v in output.items() if k != "all_results"}
        _save_state()

    except Exception as e:
        _run_state["status"] = "failed"
        _run_state["error"] = str(e)
        _run_state["finished_at"] = datetime.now().isoformat()
        _run_state["step"] = f"失败: {str(e)}"
        _save_state()
        import traceback
        traceback.print_exc()


@router.post("/run")
def run_research(payload: dict, background_tasks: BackgroundTasks):
    """触发一次完整研究流水线

    Body:
        count: 生成策略数量 (默认 100, 最大 500)
        generation: 代数 (默认 0)
    """
    global _run_state
    if _run_state["status"] == "running":
        return {
            "ok": False,
            "message": "已有研究任务在运行中",
            "current_step": _run_state["step"],
            "progress": _run_state["progress"],
        }

    count = min(payload.get("count", 100), 500)
    generation = payload.get("generation", 0)

    _run_state["status"] = "starting"
    _run_state["progress"] = 0
    _run_state["step"] = "准备启动..."
    _run_state["error"] = None
    _run_state["result"] = None
    _save_state()

    background_tasks.add_task(_run_pipeline_background, count, generation)

    return {
        "ok": True,
        "message": f"研究流水线已启动: 生成 {count} 个策略, 代数 {generation}",
        "estimated_seconds": count * 35,  # 真K线回测 ~30-40s/策略
    }


@router.get("/status")
def research_status():
    """查询研究流水线运行状态"""
    return {
        "status": _run_state["status"],
        "progress": _run_state["progress"],
        "step": _run_state["step"],
        "started_at": _run_state["started_at"],
        "finished_at": _run_state["finished_at"],
        "error": _run_state.get("error"),
        "result": _run_state.get("result"),
    }


@router.get("/top10")
def research_top10():
    """获取最新锦标赛 Top10"""
    output_file = os.path.join(DATA_DIR, "latest_research_run.json")
    if not os.path.exists(output_file):
        return {"ok": False, "message": "暂无研究结果，请先 POST /api/research/run", "top10": []}

    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "ok": True,
        "run_id": data.get("run_id", ""),
        "created_at": data.get("created_at", ""),
        "top10": data.get("top10", []),
        "summary": data.get("summary", {}),
    }


@router.get("/history")
def research_history(limit: int = 20):
    """获取历史运行记录"""
    history_file = os.path.join(DATA_DIR, "research_runs.json")
    if not os.path.exists(history_file):
        return {"ok": True, "history": []}

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    return {
        "ok": True,
        "total_runs": len(history),
        "history": history[-limit:],
    }


@router.post("/promote")
def promote_strategy(payload: dict):
    """将研究策略晋升到策略注册表

    Body:
        strategy_id: 要晋升的策略 ID
    """
    strategy_id = payload.get("strategy_id", "")
    if not strategy_id:
        raise HTTPException(400, "缺少 strategy_id")

    output_file = os.path.join(DATA_DIR, "latest_research_run.json")
    if not os.path.exists(output_file):
        raise HTTPException(404, "暂无研究结果")

    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 查找策略
    target = None
    for r in data.get("all_results", []):
        if r.get("strategy_id") == strategy_id:
            target = r
            break

    if not target:
        raise HTTPException(404, f"未找到策略 {strategy_id}")

    # 更新注册表
    registry_path = os.path.join(os.path.dirname(DATA_DIR), "strategy_registry.json")
    registry = []
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

    new_entry = {
        "strategy_id": target["strategy_id"],
        "name": target["strategy_name"],
        "type": "auto_generated",
        "status": "active",
        "annual_return": target.get("annual_return", 0),
        "sharpe_ratio": target.get("sharpe", 0),
        "max_drawdown": target.get("max_drawdown", 0),
        "total_return": target.get("total_return", 0),
        "alpha": target.get("alpha", 0),
        "factors": target.get("factors", []),
        "top_n": target.get("top_n", 0),
        "rebalance_freq": target.get("rebalance_freq", ""),
        "promoted_at": datetime.now().isoformat(),
        "source": "research_pipeline",
    }
    registry.append(new_entry)

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2, default=str)

    return {
        "ok": True,
        "message": f"策略 {target['strategy_name']} ({strategy_id}) 已晋升到注册表",
        "entry": new_entry,
    }
