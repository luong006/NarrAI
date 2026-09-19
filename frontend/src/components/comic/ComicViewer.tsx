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

function ComicPanelCard({ panel, t }: { panel: ComicPanel; t: any }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  const handleManualRetry = () => {
    setError(false);
    setLoaded(false);
    setRetryKey((k) => k + 1);
  };

  return (
    <div className={`comic-panel panel-${panel.layout_type || "square"} relative group`}>
      {/* Panel Sequence Badge */}
      <div className="absolute top-2 left-2 z-10 bg-black/75 text-white text-[10px] font-mono px-2 py-0.5 rounded shadow border border-white/20">
        #{panel.panel_index}
      </div>

      {!loaded && !error && (
        <div className="comic-panel-skeleton flex flex-col items-center justify-center p-4">
          <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mb-2" />
          <span className="text-xs text-slate-500 dark:text-slate-400 text-center font-medium">{t.loading_comic}</span>
        </div>
      )}
      {error && (
        <div className="comic-panel-skeleton text-center p-4 flex flex-col items-center justify-center">
          <span className="text-red-500 text-xs font-semibold mb-2">Chưa tải được khung tranh #{panel.panel_index}</span>
          <button
            onClick={handleManualRetry}
            className="px-3 py-1 bg-brand-700 hover:bg-brand-800 text-white rounded text-xs font-medium transition-colors shadow flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Thử lại</span>
          </button>
        </div>
      )}
      <img
        src={`${api.getComicImageUrl(panel.image_url)}${retryKey > 0 ? `?retry=${retryKey}` : ''}`}
        alt={panel.image_prompt || "Manga Comic Panel"}
        onLoad={() => {
          setLoaded(true);
          setError(false);
        }}
        onError={() => {
          if (retryKey < 4) {
            setTimeout(() => setRetryKey((k) => k + 1), 2000);
          } else {
            setError(true);
          }
        }}
        className={loaded ? "loaded" : "opacity-0"}
      />
      {panel.dialogue_text && panel.dialogue_text.trim() && (
        <div className="speech-bubble">
          {panel.dialogue_text.trim()}
        </div>
      )}
    </div>
  );
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
            <ComicPanelCard key={panel.panel_id || idx} panel={panel} t={t} />
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
