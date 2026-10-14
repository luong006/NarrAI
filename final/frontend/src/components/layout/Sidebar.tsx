"use client";

import Image from "next/image";
import {
  PenTool,
  FileText,
  Image as ImageIcon,
  Globe,
  BookOpen,
  History,
  MessageSquare,
  Coins,
  LogOut,
} from "lucide-react";
import { translations, Language } from "@/lib/i18n";
import { LanguageSwitcher } from "./LanguageSwitcher";

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
  activeTab?: "setup" | "editor" | "comic" | "lore" | "motion" | "posts" | "pipeline";
  onTabChange?: (tab: "setup" | "editor" | "comic" | "lore" | "motion" | "posts" | "pipeline") => void;
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
    <aside className="hidden lg:flex w-64 h-screen border-r border-neutral-300/80 bg-[#FAF7F2] text-neutral-900 flex-col justify-between p-4 select-none shrink-0 transition-colors z-10 font-sans">
      <div>
        {/* Logo (Official Brand Logo) */}
        <div className="px-2 py-3 mb-4 border-b border-neutral-200">
          <div className="flex items-center gap-2.5">
            <Image
              src="/assets/logo.png"
              alt="NARR AI Logo"
              width={30}
              height={30}
              className="w-7 h-7 object-contain rounded bg-neutral-900"
              priority
            />
            <h1 className="font-bold text-base tracking-widest uppercase text-neutral-950 font-mono">NarrAI</h1>
          </div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-neutral-500 mt-1.5 font-mono">
            {lang === "vi" ? "Không gian sáng tác" : "Writing workspace"}
          </p>
        </div>

        {/* User Card */}
        <div className="p-3 rounded-lg bg-white border border-neutral-200/90 mb-4 shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-bold text-neutral-950 truncate font-mono">
                {displayName || t.not_logged_in}
              </span>
              {fullName && username && (
                <span className="text-[10px] text-neutral-500 truncate font-mono">
                  @{username}
                </span>
              )}
            </div>
            {username && (
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-1 text-[10px] font-mono text-neutral-600 hover:text-neutral-950 uppercase px-1.5 py-0.5 rounded border border-neutral-300 hover:border-neutral-900 transition-colors cursor-pointer"
                title={t.logout}
              >
                <LogOut className="w-3 h-3" />
                <span>Thoát</span>
              </button>
            )}
          </div>

          {/* Coin Badge */}
          <div className="mt-3 pt-2.5 border-t border-neutral-200 flex items-center justify-between">
            <button
              type="button"
              onClick={onOpenCoinTopup}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded bg-neutral-100 hover:bg-neutral-200/80 border border-neutral-200 text-[11px] font-mono transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-1.5 text-neutral-600 uppercase tracking-wider">
                <Coins className="w-3.5 h-3.5" />
                <span>Số dư xu</span>
              </div>
              <span className="font-bold text-neutral-950 font-mono">{coinBalance} XU</span>
            </button>
          </div>
        </div>

        {/* Menu Navigation */}
        <div className="space-y-1.5">
          {/* Sáng tác mới */}
          <button
            type="button"
            onClick={() => {
              onNewStory();
              onTabChange?.("setup");
            }}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase transition-colors cursor-pointer ${
              activeTab === "setup"
                ? "bg-neutral-950 text-white font-bold shadow-sm"
                : "text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <PenTool className="w-4 h-4" />
              <span>{t.tab_create || t.new_story}</span>
            </div>
            {activeTab === "setup" && <span className="text-[10px] font-mono">[•]</span>}
          </button>

          {/* Bản thảo (Editor) */}
          {hasActiveStory && (
            <button
              type="button"
              onClick={() => onTabChange?.("editor")}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase transition-colors cursor-pointer ${
                activeTab === "editor"
                  ? "bg-neutral-950 text-white font-bold shadow-sm"
                  : "text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4" />
                <span>{t.tab_editor}</span>
              </div>
              {activeTab === "editor" && <span className="text-[10px] font-mono">[•]</span>}
            </button>
          )}

          {/* Truyện tranh (Comic) */}
          {hasActiveComic && (
            <button
              type="button"
              onClick={() => onTabChange?.("comic")}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase transition-colors cursor-pointer ${
                activeTab === "comic"
                  ? "bg-neutral-950 text-white font-bold shadow-sm"
                  : "text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <ImageIcon className="w-4 h-4" />
                <span>{t.tab_comic}</span>
              </div>
              {activeTab === "comic" && <span className="text-[10px] font-mono">[•]</span>}
            </button>
          )}

          {/* Mạng xã hội / Cộng đồng tác giả */}
          <button
            type="button"
            onClick={() => onTabChange?.("posts")}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase transition-colors cursor-pointer ${
              activeTab === "posts"
                ? "bg-neutral-950 text-white font-bold shadow-sm"
                : "text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Globe className="w-4 h-4" />
              <span>{lang === "vi" ? "Mạng xã hội" : "Community"}</span>
            </div>
            {activeTab === "posts" && <span className="text-[10px] font-mono">[•]</span>}
          </button>

          {/* Câu chuyện */}
          <button
            type="button"
            onClick={() => onTabChange?.("pipeline")}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase transition-colors cursor-pointer ${
              activeTab === "pipeline"
                ? "bg-neutral-950 text-white font-bold shadow-sm"
                : "text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <BookOpen className="w-4 h-4" />
              <span>{lang === "vi" ? "Câu chuyện" : "Stories"}</span>
            </div>
            {activeTab === "pipeline" && <span className="text-[10px] font-mono">[•]</span>}
          </button>

          {/* Lịch sử */}
          <button
            type="button"
            onClick={onOpenHistory}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <History className="w-4 h-4" />
              <span>{t.story_history}</span>
            </div>
          </button>

          {/* Open Messenger */}
          <button
            type="button"
            onClick={onOpenMessenger}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs tracking-wider uppercase text-neutral-700 hover:text-neutral-950 hover:bg-neutral-200/60 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <MessageSquare className="w-4 h-4" />
              <span>{lang === "vi" ? "Hộp thư Messenger" : "Messenger"}</span>
            </div>
            {unreadCount > 0 ? (
              <span className="px-1.5 py-0.2 text-[10px] font-mono font-bold bg-neutral-950 text-white rounded">
                {unreadCount}
              </span>
            ) : (
              <span className="text-[10px] font-mono text-neutral-500">[ON]</span>
            )}
          </button>
        </div>
      </div>

      {/* Footer controls */}
      <div className="pt-4 border-t border-neutral-200 flex items-center justify-between px-1">
        <LanguageSwitcher currentLang={lang} onLanguageChange={onLanguageChange} />
        <button
          type="button"
          onClick={() => {
            window.dispatchEvent(new CustomEvent("narrai:replay-intro"));
          }}
          className="text-[11px] font-mono font-bold text-neutral-600 hover:text-neutral-950 px-2.5 py-1.5 rounded hover:bg-neutral-200/60 transition-colors flex items-center gap-1 cursor-pointer"
          title={lang === "vi" ? "Xem lại Intro Trống Đồng Đông Sơn" : "Play Dong Son Drum Intro"}
        >
          <span>↻</span>
          <span>Intro Trống Đồng</span>
        </button>
      </div>
    </aside>
  );
}
