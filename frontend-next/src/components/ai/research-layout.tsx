import AgentPool from "./agent-pool";
import ResearchChat from "./research-chat";
import CandidateStrategy from "./candidate-strategy";

export default function ResearchLayout() {
  return (
    <div className="h-full">
      <div className="grid grid-cols-12 gap-4 h-full">
        <div className="col-span-2">
          <AgentPool />
        </div>
        <div className="col-span-7">
          <ResearchChat />
        </div>
        <div className="col-span-3">
          <CandidateStrategy />
        </div>
      </div>
    </div>
  );
}
