"use client";

import { translations, Language } from "@/lib/i18n";
import { ThemeToggle } from "./ThemeToggle";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { PlusCircle, BookOpen, LogOut, User, Sparkles } from "lucide-react";

interface Props {
  username: string;
  lang: Language;
  onLanguageChange: (lang: Language) => void;
  onNewStory: () => void;
  onOpenHistory: () => void;
  onLogout: () => void;
}

export function Sidebar({ username, lang, onLanguageChange, onNewStory, onOpenHistory, onLogout }: Props) {
  const t = translations[lang];

  return (
    <aside className="w-64 h-screen border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between p-4 select-none shrink-0 transition-colors">
      <div>
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-2 py-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-brand-700 flex items-center justify-center text-white font-bold text-base shadow">
            N
          </div>
          <div>
            <h1 className="font-bold text-base tracking-tight text-slate-900 dark:text-white">NarrAI</h1>
            <p className="text-[11px] text-slate-500 font-mono">Workspace v2.0</p>
          </div>
        </div>

        {/* User Card */}
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 mb-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-950 flex items-center justify-center text-brand-700 dark:text-brand-300 shrink-0">
                <User className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                {username || t.not_logged_in}
              </span>
            </div>
            <button
              onClick={onLogout}
              className="text-slate-400 hover:text-red-600 dark:hover:text-red-400 p-1"
              title={t.logout}
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Menu Navigation */}
        <div className="space-y-1">
          <button
            onClick={onNewStory}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <PlusCircle className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <span>{t.new_story}</span>
          </button>

          <button
            onClick={onOpenHistory}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span>{t.story_history}</span>
          </button>
        </div>
      </div>

      {/* Footer controls */}
      <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between px-1">
        <LanguageSwitcher currentLang={lang} onLanguageChange={onLanguageChange} />
        <ThemeToggle />
      </div>
    </aside>
  );
}
