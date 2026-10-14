"use client";

import { Language } from "@/lib/i18n";

interface Props {
  currentLang: Language;
  onLanguageChange: (lang: Language) => void;
}

export function LanguageSwitcher({ currentLang, onLanguageChange }: Props) {
  return (
    <div className="flex items-center rounded border border-neutral-300 dark:border-neutral-700 p-0.5 bg-neutral-100 dark:bg-neutral-900">
      <button
        type="button"
        onClick={() => onLanguageChange("vi")}
        className={`px-2.5 py-1 text-xs font-mono font-bold rounded transition-colors ${
          currentLang === "vi"
            ? "bg-white dark:bg-black text-black dark:text-white shadow-sm border border-neutral-200 dark:border-neutral-800"
            : "text-neutral-500 hover:text-black dark:hover:text-white"
        }`}
      >
        VIE
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange("en")}
        className={`px-2.5 py-1 text-xs font-mono font-bold rounded transition-colors ${
          currentLang === "en"
            ? "bg-white dark:bg-black text-black dark:text-white shadow-sm border border-neutral-200 dark:border-neutral-800"
            : "text-neutral-500 hover:text-black dark:hover:text-white"
        }`}
      >
        ENG
      </button>
    </div>
  );
}
