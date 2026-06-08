"use client";

import { useState, useCallback } from "react";
import { X, CheckCircle2, AlertTriangle, Info } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

let _add: ((type: ToastType, message: string) => void) | null = null;

export function toast(type: ToastType, message: string) {
  _add?.(type, message);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  let idCounter = 0;

  _add = useCallback((type: ToastType, message: string) => {
    const id = ++idCounter;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const icons: Record<ToastType, any> = {
    success: CheckCircle2,
    error: AlertTriangle,
    info: Info,
  };
  const colors: Record<ToastType, string> = {
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    error: "border-red-500/30 bg-red-500/10 text-red-400",
    info: "border-blue-500/30 bg-blue-500/10 text-blue-400",
  };

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => {
        const Icon = icons[t.type];
        return (
          <div
            key={t.id}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-xs ${colors[t.type]} min-w-[200px] shadow-lg`}
          >
            <Icon size={14} />
            <span>{t.message}</span>
            <button onClick={() => setToasts((p) => p.filter((x) => x.id !== t.id))} className="ml-auto">
              <X size={12} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
