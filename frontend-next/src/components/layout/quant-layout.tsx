import Sidebar from "./sidebar";
import Header from "./header";
import AIPanel from "./ai-panel";

export default function QuantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-slate-950">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
      <AIPanel />
    </div>
  );
}
