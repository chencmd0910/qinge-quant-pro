import StrategyTree from "./strategy-tree";
import MonacoEditor from "./monaco-editor";
import BacktestResult from "./backtest-result";

export default function StrategyLabLayout() {
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 grid grid-cols-12 gap-4">
        {/* Left: Strategy Tree */}
        <div className="col-span-3">
          <StrategyTree />
        </div>

        {/* Center: Monaco Editor */}
        <div className="col-span-6">
          <MonacoEditor />
        </div>

        {/* Right: Backtest Result */}
        <div className="col-span-3">
          <BacktestResult />
        </div>
      </div>
    </div>
  );
}
