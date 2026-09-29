"use client";

import { translations, Language } from "@/lib/i18n";
import { ThemeToggle } from "./ThemeToggle";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { PlusCircle, BookOpen, LogOut, User, MessageSquare, Compass, FileText, Palette } from "lucide-react";
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
  activeTab?: "setup" | "editor" | "comic" | "posts";
  onTabChange?: (tab: "setup" | "editor" | "comic" | "posts") => void;
  hasActiveStory?: boolean;
  hasActiveComic?: boolean;
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
  activeTab = "setup",
  onTabChange,
  hasActiveStory = false,
  hasActiveComic = false,
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
          {/* Sáng tác mới */}
          <button
            onClick={() => {
              onNewStory();
              onTabChange?.("setup");
            }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === "setup"
                ? "bg-brand-50 dark:bg-brand-950/70 text-brand-700 dark:text-brand-300 font-bold"
                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <PlusCircle className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <span>{t.tab_create || t.new_story}</span>
          </button>

          {/* Bản thảo (Editor) */}
          {hasActiveStory && (
            <button
              onClick={() => onTabChange?.("editor")}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === "editor"
                  ? "bg-indigo-50 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 font-bold"
                  : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <span>{t.tab_editor}</span>
            </button>
          )}

          {/* Truyện tranh (Comic) */}
          {hasActiveComic && (
            <button
              onClick={() => onTabChange?.("comic")}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === "comic"
                  ? "bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-bold"
                  : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <Palette className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>{t.tab_comic}</span>
            </button>
          )}

          {/* Bảng tin Bài đăng (Community Feed) */}
          <button
            onClick={() => onTabChange?.("posts")}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === "posts"
                ? "bg-violet-50 dark:bg-violet-950/70 text-violet-700 dark:text-violet-300 font-bold"
                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Compass className="w-4 h-4 text-violet-600 dark:text-violet-400" />
            <span>{t.tab_posts || (lang === "vi" ? "Bài đăng" : "Community Feed")}</span>
          </button>

          {/* Lịch sử */}
          <button
            onClick={onOpenHistory}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span>{t.story_history}</span>
          </button>

          {/* Open Messenger Trigger Button */}
          <button
            onClick={onOpenMessenger}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group"
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
