"use client";

import Sidebar from "./sidebar";
import Header from "./header";
import { ToastContainer } from "@/lib/toast";

export default function ClientShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: "var(--bg-primary)" }}>
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
        <ToastContainer />
      </div>
    </div>
  );
}
