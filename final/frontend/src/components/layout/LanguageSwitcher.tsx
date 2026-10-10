"use client";

import { Language } from "@/lib/i18n";

interface Props {
  currentLang: Language;
  onLanguageChange: (lang: Language) => void;
}

export function LanguageSwitcher({ currentLang, onLanguageChange }: Props) {
  return (
    <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-700 p-0.5 bg-slate-100 dark:bg-slate-800">
      <button
        onClick={() => onLanguageChange("vi")}
        className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
          currentLang === "vi"
            ? "bg-white dark:bg-slate-900 text-brand-700 dark:text-brand-300 shadow-sm"
            : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
        }`}
      >
        VIE
      </button>
      <button
        onClick={() => onLanguageChange("en")}
        className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
          currentLang === "en"
            ? "bg-white dark:bg-slate-900 text-brand-700 dark:text-brand-300 shadow-sm"
            : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
        }`}
      >
        ENG
      </button>
    </div>
  );
}
