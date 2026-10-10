"use client";

import { useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { ComicPanel } from "@/lib/types";
import { api } from "@/lib/api";
import { ArrowLeft, RefreshCw, Layers } from "lucide-react";

interface Props {
  panels: ComicPanel[];
  hasMore: boolean;
  lang: Language;
  onBackToEditor: () => void;
  onContinueComic: () => void;
  onAdaptToComic?: () => void;
  loadingMore: boolean;
}

function ComicPanelFrame({ panel, t, lang, slot, eager }: {
  panel: ComicPanel;
  t: (typeof translations)[Language];
  lang: Language;
  slot: number;
  eager: boolean;
}) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const imageUrl = api.getComicImageUrl(panel.image_url);
  const imageFailed = error || !imageUrl;

  return (
    <figure className="manga-panel" data-slot={slot}>
      <div className={`manga-artwork${imageFailed ? " has-error" : ""}`}>
        {imageUrl && (
          <img
            key={retryKey}
            src={`${imageUrl}${imageUrl.includes("?") ? "&" : "?"}retry=${retryKey}`}
            alt={panel.image_prompt || (lang === "vi" ? "Khung truyện manga" : "Manga panel")}
            loading={eager ? "eager" : "lazy"}
            decoding="async"
            onLoad={() => {
              setLoaded(true);
              setError(false);
            }}
            onError={() => {
              setLoaded(false);
              setError(true);
            }}
            className={loaded ? "is-loaded" : "is-loading"}
          />
        )}
      </div>

      {(imageFailed || !loaded || panel.dialogue_text?.trim()) && (
        <figcaption className="manga-caption" aria-live={imageFailed ? "polite" : undefined}>
          {panel.dialogue_text?.trim() && (
            <p>{sanitizeComicCaption(panel.dialogue_text)}</p>
          )}
          {imageFailed ? (
            <div className="manga-image-error">
              <span>{t.panel_load_error || (lang === "vi" ? "Chưa tạo được ảnh. Hãy thử lại để yêu cầu ảnh mới." : "Image generation failed. Retry to request a fresh image.")}</span>
              {imageUrl && (
                <button
                  type="button"
                  onClick={() => {
                    setError(false);
                    setRetryKey((key) => key + 1);
                  }}
                  className="manga-image-retry"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>{t.retry_btn || (lang === "vi" ? "Thử lại" : "Retry")}</span>
                </button>
              )}
            </div>
          ) : !loaded ? (
            <span className="manga-image-status">{t.loading_comic}</span>
          ) : null}
        </figcaption>
      )}
    </figure>
  );
}

function sanitizeComicCaption(value: string): string {
  return value
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}#{1,6}\s*/gm, "")
    .replace(/^\s{0,3}>\s?/gm, "")
    .replace(/^\s*(?:[-+*]|\d+[.)])\s+/gm, "")
    .replace(/(\*\*|__|~~|`{1,3})([\s\S]*?)\1/g, "$2")
    .replace(/(^|\s)[*_]([^*_\n]+)[*_](?=$|\s|[.,!?])/g, "$1$2")
    .replace(/\s+/g, " ")
    .trim();
}

function splitIntoPages(panels: ComicPanel[], panelsPerPage = 6): ComicPanel[][] {
  const pages: ComicPanel[][] = [];
  for (let index = 0; index < panels.length; index += panelsPerPage) {
    pages.push(panels.slice(index, index + panelsPerPage));
  }
  return pages;
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
  const pages = splitIntoPages(panels);

  return (
    <div className="flex h-screen flex-1 flex-col overflow-hidden bg-[#d7d7d7] dark:bg-slate-950">
      <header className="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-300 bg-white px-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBackToEditor}
            className="rounded-lg p-1.5 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            title={t.back_to_editor}
            aria-label={t.back_to_editor}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-brand-700 dark:text-brand-400" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white sm:text-base">
              {t.comic_view_title}
            </h2>
          </div>
        </div>

        {hasMore && (
          <button
            type="button"
            onClick={onContinueComic}
            disabled={loadingMore}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-700 px-4 py-1.5 text-xs font-bold text-white shadow-sm transition-all hover:bg-emerald-800 disabled:opacity-50 dark:bg-emerald-600 dark:hover:bg-emerald-700"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loadingMore ? "animate-spin" : ""}`} />
            <span>{t.btn_continue_comic}</span>
          </button>
        )}
      </header>

      <main className="flex-1 overflow-y-auto px-3 py-5 sm:px-8 sm:py-8">
        <div className="manga-pages">
          {pages.map((page, pageIndex) => (
            <section className="manga-page" key={`page-${pageIndex + 1}`} aria-label={`Page ${pageIndex + 1}`}>
              {page.map((panel, panelIndex) => (
                <ComicPanelFrame
                  key={panel.panel_id || `${pageIndex}-${panelIndex}`}
                  panel={panel}
                  t={t}
                  lang={lang}
                  slot={panelIndex + 1}
                  eager={pageIndex === 0}
                />
              ))}
            </section>
          ))}
        </div>

        {loadingMore && (
          <p className="py-8 text-center text-sm font-semibold text-slate-600 dark:text-slate-400" role="status">
            {t.loading_comic}
          </p>
        )}
      </main>
    </div>
  );
}
