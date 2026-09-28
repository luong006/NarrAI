"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

export interface ToastContextValue {
  toasts: ToastItem[];
  addToast: (type: ToastType, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
  toast: {
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
  };
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string, duration: number = 4000) => {
      if (!message) return;
      const id = Math.random().toString(36).substring(2, 9) + Date.now().toString(36);
      setToasts((prev) => [...prev, { id, type, message, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const toast = {
    success: useCallback(
      (message: string, duration?: number) => addToast("success", message, duration),
      [addToast]
    ),
    error: useCallback(
      (message: string, duration?: number) => addToast("error", message, duration),
      [addToast]
    ),
    warning: useCallback(
      (message: string, duration?: number) => addToast("warning", message, duration),
      [addToast]
    ),
    info: useCallback(
      (message: string, duration?: number) => addToast("info", message, duration),
      [addToast]
    ),
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, toast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      toasts: [],
      addToast: () => {},
      removeToast: () => {},
      toast: {
        success: (msg: string) => console.log("[Toast success]", msg),
        error: (msg: string) => console.error("[Toast error]", msg),
        warning: (msg: string) => console.warn("[Toast warning]", msg),
        info: (msg: string) => console.info("[Toast info]", msg),
      },
    };
  }
  return context;
}
