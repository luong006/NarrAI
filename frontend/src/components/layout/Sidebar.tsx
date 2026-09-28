"use client";

import { translations, Language } from "@/lib/i18n";
import { ThemeToggle } from "./ThemeToggle";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { PlusCircle, BookOpen, LogOut, User, MessageSquare } from "lucide-react";
import { CoinBadgeMorphicon } from "@/components/morphicons/CoinBadgeMorphicon";

interface Props {
  username: string;
  fullName?: string;
  lang: Language;
  onLanguageChange: (lang: Language) => void;
  onNewStory: () => void;
  onOpenHistory: () => void;
  onLogout: () => void;
  coinBalance?: number;
  onOpenCoinTopup?: () => void;
  onOpenMessenger?: () => void;
  unreadCount?: number;
}

export function Sidebar({
  username,
  fullName,
  lang,
  onLanguageChange,
  onNewStory,
  onOpenHistory,
  onLogout,
  coinBalance = 100,
  onOpenCoinTopup,
  onOpenMessenger,
  unreadCount = 0,
}: Props) {
  const t = translations[lang];
  const displayName = fullName || username;

  return (
    <aside className="w-64 h-screen border-r border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md flex flex-col justify-between p-4 select-none shrink-0 transition-colors z-10">
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
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-950 flex items-center justify-center text-brand-700 dark:text-brand-300 shrink-0">
                <User className="w-4 h-4" />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                  {displayName || t.not_logged_in}
                </span>
                {fullName && username && (
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                    @{username}
                  </span>
                )}
              </div>
            </div>
            {username && (
              <button
                onClick={onLogout}
                className="text-slate-400 hover:text-red-600 dark:hover:text-red-400 p-1 transition-colors"
                title={t.logout}
                aria-label={t.logout}
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Coin Badge Micro-Interaction (Layer 2) */}
          <div className="mt-3 pt-2.5 border-t border-slate-200/70 dark:border-slate-700/60 flex items-center justify-between">
            <CoinBadgeMorphicon
              balance={coinBalance}
              onClick={onOpenCoinTopup}
              lang={lang}
              size="sm"
              className="w-full justify-between"
            />
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

          {/* Open Messenger Trigger Button */}
          <button
            onClick={onOpenMessenger}
            className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group"
            title={lang === "vi" ? "Mở hộp thư Open Messenger" : "Open Messenger"}
          >
            <div className="flex items-center gap-2.5">
              <MessageSquare className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <span>{lang === "vi" ? "Open Messenger" : "Messenger"}</span>
            </div>
            {unreadCount > 0 ? (
              <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold text-white bg-rose-500 rounded-full animate-pulse shadow-sm">
                {unreadCount}
              </span>
            ) : (
              <span
                className="w-2 h-2 rounded-full bg-emerald-500 group-hover:scale-125 transition-transform"
                title={lang === "vi" ? "Đang trực tuyến" : "Online"}
              />
            )}
          </button>
        </div>
      </div>

      {/* Footer controls */}
      <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between px-1">
        <LanguageSwitcher currentLang={lang} onLanguageChange={onLanguageChange} />
        <ThemeToggle lang={lang} />
      </div>
    </aside>
  );
}
