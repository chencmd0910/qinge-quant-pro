"""每日自动策略研究 - Cron 调用脚本"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.research_engine.lab import AIResearchLab
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "data", "research")
lab = AIResearchLab(DATA_DIR)

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始每日策略研究 (count=100)...")
result = lab.run_full_pipeline(count=100)

# 保存到 latest
output_file = os.path.join(DATA_DIR, "latest_research_run.json")
with open(output_file, "w", encoding="utf-8") as f:
    # all_results 太大，单独保存
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)

# 追加历史
history_file = os.path.join(DATA_DIR, "research_runs.json")
history = []
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
history_entry = {k: v for k, v in result.items() if k != "all_results"}
history_entry["run_id"] = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
history.append(history_entry)
if len(history) > 50:
    history = history[-50:]
with open(history_file, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2, default=str)

# 汇报摘要
print("\n" + "=" * 50)
print("📊 每日策略研究完成")
print(f"   生成策略: {result['generated']}")
print(f"   通过验证: {result['validated']}")
print(f"   过滤掉:   {result['filtered']}")
print(f"   失败:     {result.get('failed', 0)}")
print(f"\n🏆 Top 3:")
for r in result["top10"][:3]:
    print(f"   #{r['rank']} {r['name']}")
    print(f"       年化:{r['annual_return']:+.2f}% | 回撤:{r['max_drawdown']:+.2f}% | 夏普:{r['sharpe']:.3f} | 评分:{r['validation_score']:.1f}")
print("=" * 50)
