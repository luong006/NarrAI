"use client";

import { useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { ComicPanel } from "@/lib/types";
import { api } from "@/lib/api";
import { ArrowLeft, RefreshCw, BookOpen, Layers } from "lucide-react";

interface Props {
  panels: ComicPanel[];
  hasMore: boolean;
  lang: Language;
  onBackToEditor: () => void;
  onContinueComic: () => void;
  loadingMore: boolean;
}

export function ComicViewer({
  panels,
  hasMore,
  lang,
  onBackToEditor,
  onContinueComic,
  loadingMore,
}: Props) {
  const t = translations[lang];

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-200 dark:bg-slate-950 transition-colors">
      {/* Header */}
      <div className="h-14 border-b border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToEditor}
            className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={t.back_to_editor}
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-brand-700 dark:text-brand-400" />
            <h2 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
              {t.comic_view_title}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasMore && (
            <button
              onClick={onContinueComic}
              disabled={loadingMore}
              className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-700 shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingMore ? "animate-spin" : ""}`} />
              <span>{t.btn_continue_comic}</span>
            </button>
          )}

          <button
            onClick={onBackToEditor}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {t.back_to_editor}
          </button>
        </div>
      </div>

      {/* Manga Page Grid Canvas */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-8">
        <div className="comic-grid">
          {panels.map((panel, idx) => (
            <div
              key={panel.panel_id || idx}
              className={`comic-panel panel-${panel.layout_type || "square"}`}
            >
              {/* Image loading */}
              <img
                src={api.getComicImageUrl(panel.image_url)}
                alt={panel.image_prompt || "Manga Comic Panel"}
                loading="lazy"
                onError={(e) => {
                  // Subtle fallback retry
                  const target = e.currentTarget;
                  if (!target.dataset.retried) {
                    target.dataset.retried = "true";
                    setTimeout(() => {
                      target.src = `${api.getComicImageUrl(panel.image_url)}?retry=${Date.now()}`;
                    }, 1500);
                  }
                }}
              />

              {/* Overlaid Speech Bubble - Strictly zero scrollbars */}
              {panel.dialogue_text && panel.dialogue_text.trim() && (
                <div className="speech-bubble">
                  {panel.dialogue_text.trim()}
                </div>
              )}
            </div>
          ))}
        </div>

        {loadingMore && (
          <div className="py-8 text-center text-sm font-semibold text-slate-600 dark:text-slate-400 animate-pulse">
            {t.loading_comic}
          </div>
        )}
      </div>
    </div>
  );
}
