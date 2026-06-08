"use client";

import AIChat from "./ai-chat";
import CandidateStrategy from "./candidate-strategy";

export default function ResearchLayout() {
  return (
    <div className="h-full">
      <div className="grid grid-cols-12 gap-4 h-full">
        {/* AI 对话区 — 占主要位置 */}
        <div className="col-span-8">
          <AIChat />
        </div>
        {/* 右侧：策略排行 + 统计 */}
        <div className="col-span-4">
          <CandidateStrategy />
        </div>
      </div>
    </div>
  );
}
