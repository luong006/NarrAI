"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { translations, Language } from "@/lib/i18n";
import { storage } from "@/lib/storage";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [lang, setLang] = useState<Language>("vi");

  useEffect(() => {
    console.error("NarrAI Client Exception:", error);
    const saved = storage.getLanguage() as Language;
    if (saved === "en" || saved === "vi") {
      setLang(saved);
    }
  }, [error]);

  const t = translations[lang] || translations.vi;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white p-6">
      <div className="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-xl text-center">
        <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-900 flex items-center justify-center text-red-600 dark:text-red-400">
          <AlertTriangle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white">
          {t.error_boundary_title}
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-6 leading-relaxed font-mono bg-slate-100 dark:bg-slate-800/80 p-3 rounded-lg text-left break-words max-h-36 overflow-y-auto">
          {error?.message || t.error_boundary_desc}
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => reset()}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl font-semibold text-sm bg-brand-700 hover:bg-brand-800 text-white shadow flex items-center justify-center gap-2 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            <span>{t.error_boundary_retry}</span>
          </button>
          <button
            onClick={() => (window.location.href = "/")}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl font-semibold text-sm bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center gap-2 transition-all"
          >
            <Home className="w-4 h-4" />
            <span>{t.error_boundary_home}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
