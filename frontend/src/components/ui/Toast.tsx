"use client";

import React from "react";
import { useToast, ToastItem } from "@/lib/toast";
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from "lucide-react";

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      aria-live="assertive"
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-2.5 pointer-events-none max-w-sm w-full px-4 sm:px-0"
    >
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

function ToastCard({ toast, onClose }: { toast: ToastItem; onClose: () => void }) {
  const config = {
    success: {
      bg: "bg-emerald-50 dark:bg-emerald-950/80 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-100",
      icon: <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />,
    },
    error: {
      bg: "bg-rose-50 dark:bg-rose-950/80 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-100",
      icon: <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />,
    },
    warning: {
      bg: "bg-amber-50 dark:bg-amber-950/80 border-amber-300 dark:border-amber-800 text-amber-900 dark:text-amber-100",
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />,
    },
    info: {
      bg: "bg-sky-50 dark:bg-sky-950/80 border-sky-300 dark:border-sky-800 text-sky-900 dark:text-sky-100",
      icon: <Info className="w-5 h-5 text-sky-600 dark:text-sky-400 shrink-0" />,
    },
  }[toast.type];

  return (
    <div
      role="alert"
      className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border shadow-lg backdrop-blur-sm transition-all duration-200 animate-in fade-in slide-in-from-top-2 ${config.bg}`}
    >
      <div className="mt-0.5">{config.icon}</div>
      <div className="flex-1 text-sm font-medium leading-snug break-words">{toast.message}</div>
      <button
        onClick={onClose}
        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors shrink-0 p-0.5"
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
