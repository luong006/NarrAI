"use client";

import React from "react";
import { useToast, ToastItem } from "@/lib/toast";

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      aria-live="assertive"
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-2.5 pointer-events-none max-w-sm w-full px-4 sm:px-0 font-mono select-none"
    >
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

function ToastCard({ toast, onClose }: { toast: ToastItem; onClose: () => void }) {
  const tag = {
    success: "[THÀNH CÔNG]",
    error: "[LỖI]",
    warning: "[CHÚ Ý]",
    info: "[THÔNG BÁO]",
  }[toast.type];

  return (
    <div
      role="alert"
      className="pointer-events-auto flex items-start gap-2.5 p-3 rounded border border-neutral-300 dark:border-neutral-800 bg-white dark:bg-neutral-950 text-black dark:text-white shadow-xl transition-all"
    >
      <span className="font-bold text-xs uppercase shrink-0 pt-0.5">
        {tag}
      </span>
      <div className="flex-1 text-xs leading-relaxed break-words font-sans">
        {toast.message}
      </div>
      <button
        type="button"
        onClick={onClose}
        className="text-neutral-500 hover:text-black dark:hover:text-white font-bold text-xs shrink-0 px-1"
        aria-label="Close notification"
      >
        [x]
      </button>
    </div>
  );
}
