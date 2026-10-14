"use client";

import { useEffect, useState } from "react";
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
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black text-black dark:text-white p-6 font-mono select-none">
      <div className="max-w-md w-full bg-white dark:bg-neutral-950 border border-neutral-300 dark:border-neutral-800 rounded-xl p-8 shadow-xl text-center">
        <div className="inline-block mb-4 px-3 py-1 rounded border border-neutral-400 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-900 text-xs font-bold tracking-widest uppercase">
          [LỖI HỆ THỐNG]
        </div>
        <h2 className="text-lg font-bold mb-2 text-black dark:text-white uppercase tracking-wider">
          {t.error_boundary_title}
        </h2>
        <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-6 leading-relaxed font-mono bg-neutral-100 dark:bg-neutral-900 p-3 rounded border border-neutral-200 dark:border-neutral-800 text-left break-words max-h-36 overflow-y-auto">
          {error?.message || t.error_boundary_desc}
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => reset()}
            className="w-full sm:w-auto px-5 py-2.5 rounded font-bold text-xs uppercase tracking-wider bg-black text-white hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 shadow transition-colors"
          >
            [Thử lại]
          </button>
          <button
            type="button"
            onClick={() => (window.location.href = "/")}
            className="w-full sm:w-auto px-5 py-2.5 rounded font-bold text-xs uppercase tracking-wider border border-neutral-300 dark:border-neutral-700 bg-white text-black hover:bg-neutral-100 dark:bg-black dark:text-white dark:hover:bg-neutral-900 transition-colors"
          >
            [Về trang chủ]
          </button>
        </div>
      </div>
    </div>
  );
}
