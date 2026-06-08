"""AI 对话端点 — 直接调用 LLM API，带布布人设和量化系统上下文
自然语言 → DeepSeek API (同 Gateway 模型) → 量化上下文 + 布布人设
"""
import json
import os
import re
from fastapi import APIRouter
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/ai", tags=["AI Chat"])

# LLM 配置（用 Gateway 同样的模型）
LLM_URL = os.getenv("AI_CHAT_URL", "https://api.deepseek.com/v1/chat/completions")
LLM_KEY = os.getenv("AI_CHAT_KEY", "sk-1020b96a41d743b2a008b3614d5fa564")
LLM_MODEL = os.getenv("AI_CHAT_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """你是布布🐊，青鳄量化系统的全能AI助手。你现在在量化前端 AI Lab 的对话框里和老大聊天。

## 你的角色
- 称呼用户为「老大」
- 回答简洁直接、不废话，用中文
- 保持布布的人设：高效、可靠、有点幽默感
- 你面前有个完整的量化系统，所有数据都是真实的

## 后端 API（localhost:8000）
老大打开的系统有以下真实数据接口：
- /api/dashboard/summary — 仪表盘总览（总资产、日盈亏、夏普、回撤、胜率、Top策略）
- /api/backtest/result — ETF轮动回测结果（2年+59%，夏普0.82）
- /api/portfolio/positions — 实时持仓
- /api/portfolio/allocation — 策略分配（按夏普加权）
- /api/portfolio/correlation — 相关性矩阵
- /api/paper-trading/summary — 模拟交易总览
- /api/paper-trading/positions — 模拟持仓
- /api/paper-trading/trades — 交易记录
- /api/paper-trading/equity — 权益曲线
- /api/strategy-lab/results — 策略回测结果
- /api/risk/categories — 风险分类
- /api/risk/heatmap — 相关性热力图
- /api/risk/timeline — 风险事件时间线
- /api/risk/auto-actions — 自动风控操作
- /api/alpha-factory/strategies — Alpha工厂策略池
- **/api/research/run** — 策略自动生成流水线（生成→回测→验证→排名）
- **/api/research/top10** — 最新锦标赛 Top10
- **/api/research/status** — 流水线运行状态

## 特殊能力：策略自动生成
老大可以对你说以下指令，你会自动触发：
- 「生成100个策略」→ POST /api/research/run {"count": 100}
- 「跑一轮研究」→ POST /api/research/run {"count": 100}
- 「看排行榜」→ GET /api/research/top10
- 「研究进度」→ GET /api/research/status
- 「更多策略/200个」→ POST /api/research/run {"count": 200}

触发后回复："收到老大！研究流水线已启动，预计 XX 秒完成。可以随时问我进度 🐊"

## 数据能力
- 所有数据和图表都已接入真实后端，不是假数据
- 行情/实时数据暂不可用（需 tushare/QMT）- 如实告知老大
- 回测数据来自 Multi-Factor V25 策略（月度调仓、ETF轮动、20只持仓）
- 系统有 5 个策略在策略注册表中
- 策略生成器基于 17 因子池（动量/资金/量价/波动/基本面）随机组合

## 回答规则
- 量化相关问题：基于真实数据回答，告诉老大数据在哪
- 闲聊/打招呼：像朋友一样自然回复
- 不要输出 JSON、不要格式化代码块、就像正常微信聊天
- 每次回答控制在 2-5 句话，不要太长
- 如果被问到数据，可以提到具体接口路径"""


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/chat")
async def ai_chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        return {"reply": "老大，有什么想聊的？量化、策略、数据…都可以问我 🐊", "tool": None}

    # ─── 意图识别：策略自动生成 ───
    research_intent = _detect_research_intent(msg)
    if research_intent:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.post(
                    "http://localhost:8000/api/research/run",
                    json=research_intent.get("payload", {"count": 100}),
                )
                run_data = r.json()
                if run_data.get("ok"):
                    return {
                        "reply": (
                            f"收到老大！🧬 研究流水线已启动\n\n"
                            f"📊 生成 {research_intent.get('payload', {}).get('count', 100)} 个策略\n"
                            f"⏱ 预计 {run_data.get('estimated_seconds', 5):.0f} 秒完成\n\n"
                            f"随时问我「研究进度」或「看排行榜」🐊"
                        ),
                        "tool": "research_pipeline",
                    }
                else:
                    return {"reply": f"⚠️ {run_data.get('message', '启动失败')}", "tool": "research_pipeline"}
            except Exception as e:
                return {"reply": f"研究流水线启动失败: {str(e)[:100]}", "tool": "research_pipeline"}

    # ─── 意图识别：查询研究状态 ───
    if _is_status_query(msg):
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get("http://localhost:8000/api/research/status")
                status_data = r.json()
                if status_data.get("status") == "completed":
                    top_info = ""
                    if status_data.get("result", {}).get("top10"):
                        top1 = status_data["result"]["top10"][0]
                        top_info = f"\n🏆 Top1: {top1['name']} (年化{top1['annual_return']:+.1f}%, 夏普{top1['sharpe']:.2f})"
                    return {
                        "reply": f"✅ 研究已完成！{status_data['result']['validated_count']} 个策略通过验证{top_info}\n\n说「看排行榜」查看 Top10 🐊",
                        "tool": "research_status",
                    }
                elif status_data.get("status") == "running":
                    return {
                        "reply": f"🔄 正在运行中… {status_data.get('progress', 0)}%\n{status_data.get('step', '')}",
                        "tool": "research_status",
                    }
                elif status_data.get("status") == "failed":
                    return {
                        "reply": f"❌ 上次运行失败: {status_data.get('error', '未知错误')[:200]}",
                        "tool": "research_status",
                    }
                else:
                    return {
                        "reply": "还没有运行过研究流水线。说「生成100个策略」开始第一轮 🧬",
                        "tool": "research_status",
                    }
            except Exception:
                pass  # 回退到 LLM

    # ─── 意图识别：查看排行榜 ───
    if _is_leaderboard_query(msg):
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get("http://localhost:8000/api/research/top10")
                top10_data = r.json()
                if top10_data.get("ok") and top10_data.get("top10"):
                    lines = ["🏆 策略锦标赛 Top10:\n"]
                    for i, s in enumerate(top10_data["top10"][:10]):
                        lines.append(
                            f"{i+1}. {s['name']} | "
                            f"年化{s['annual_return']:+.1f}% | "
                            f"夏普{s['sharpe']:.2f} | "
                            f"回撤{s['max_drawdown']:.1f}% | "
                            f"评分{s['validation_score']:.0f}"
                        )
                    return {"reply": "\n".join(lines), "tool": "research_top10"}
                else:
                    return {"reply": "还没有排行榜数据。说「生成100个策略」开始第一轮 🧬", "tool": "research_top10"}
            except Exception:
                pass

    # ─── 回退到 LLM ───

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for h in req.history[-20:]:
        role = h.get("role", "user")
        if role == "agent":
            role = "assistant"
        content = h.get("content", "")
        if content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": msg})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_KEY}",
    }

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                LLM_URL,
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.7,
                },
                headers=headers,
            )
            data = resp.json()

            if "error" in data:
                err_msg = data["error"].get("message", str(data["error"]))
                return {"reply": f"API 错误: {err_msg}", "tool": None}

            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not reply:
                return {"reply": "模型返回为空", "tool": None}

            return {"reply": reply, "tool": LLM_MODEL}

    except httpx.ConnectError:
        return {
            "reply": (
                "老大，LLM 连接不上 🔌\n\n"
                "不过我还是能回答你的：\n"
                "📊 仪表盘 → /api/dashboard/summary\n"
                "💼 持仓 → /api/portfolio/positions\n"
                "⚡ 回测 → /api/backtest/result\n"
                "🧪 策略 → /api/strategy-lab/results\n\n"
                "选一个问我 👆"
            ),
            "tool": None,
        }
    except Exception as e:
        return {"reply": f"连接异常: {str(e)[:200]}", "tool": None}


# ─── 意图检测 ───

def _detect_research_intent(msg: str) -> dict | None:
    """检测是否为策略生成请求，返回 {action, payload}"""
    msg_lower = msg.lower().replace(" ", "")

    patterns = [
        # (正则, 默认count)
        (r"生成(\d+)个策略", None),           # 生成100个策略
        (r"生成(\d+)个", None),
        (r"跑(\d+)个策略", None),
        (r"自动生成(\d+)个", None),
        (r"批量生成(\d+)个", None),
        (r"生成策略", 100),                   # 生成策略（默认100）
        (r"跑一轮研究", 100),
        (r"跑研究", 100),
        (r"开始研究", 100),
        (r"自动跑", 100),
        (r"startresearch", 100),
        (r"自动生成策略", 100),
        (r"再来一轮", 100),
        (r"多生成.*策略", 200),
        (r"多来.*策略", 200),
    ]

    for pattern, default_count in patterns:
        m = re.search(pattern, msg_lower)
        if m:
            count = int(m.group(1)) if m.lastindex and m.group(1) else default_count
            count = max(10, min(count, 500))
            return {"action": "run", "payload": {"count": count}}

    # 模糊匹配
    if any(kw in msg_lower for kw in ["生成新策略", "批量生成", "自动生成", "跑研究流水线"]):
        return {"action": "run", "payload": {"count": 100}}

    return None


def _is_status_query(msg: str) -> bool:
    """检测是否为研究状态查询"""
    kw = ["研究进度", "进度", "跑完了吗", "完成了没", "怎么样了", "status",
           "生成完了", "跑完了", "好了没", "完成了没有", "好了吗"]
    msg_lower = msg.lower().replace(" ", "")
    return any(k in msg_lower for k in kw)


def _is_leaderboard_query(msg: str) -> bool:
    """检测是否为排行榜查询"""
    kw = ["排行榜", "排名", "top", "前十", "top10", "前10", "锦标赛",
           "最好", "最强", "哪.*好", "看结果", "结果"]
    msg_lower = msg.lower().replace(" ", "")
    return any(k in msg_lower for k in kw)
