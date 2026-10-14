"use client";

import { useState, useEffect, useMemo } from "react";
import {
  ArrowLeft,
  Coins,
  Sparkles,
  RefreshCw,
  LayoutGrid,
  Columns,
  Eye,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ChevronRight,
  Maximize2,
  Download,
  Info,
} from "lucide-react";
import { translations, Language } from "@/lib/i18n";
import { ComicPanel } from "@/lib/types";
import { api } from "@/lib/api";

interface Props {
  panels: ComicPanel[];
  hasMore: boolean;
  lang: Language;
  onBackToEditor: () => void;
  onContinueComic: () => void;
  onAdaptToComic?: () => void;
  loadingMore: boolean;
  coinBalance?: number;
  onOpenCoinModal?: () => void;
}

function parseComicDialogue(rawText: string) {
  const clean = sanitizeComicCaption(rawText);
  if (!clean) return { speaker: null, text: "", isDialogue: false };

  // Match Speaker: "Speech" or Speaker: Speech
  const match = clean.match(/^([^:：]{2,25})[:：]\s*(.*)$/);
  if (match) {
    const speaker = match[1].trim();
    let text = match[2].trim();
    text = text.replace(/^["“](.*)["”]$/, "$1").trim();
    return { speaker, text, isDialogue: true };
  }

  // Check if text is wrapped in quotes
  const quoteMatch = clean.match(/^["“](.*)["”]$/);
  if (quoteMatch) {
    return { speaker: null, text: quoteMatch[1].trim(), isDialogue: true };
  }

  return { speaker: null, text: clean, isDialogue: false };
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

function splitIntoPages(panels: ComicPanel[], panelsPerPage = 4): ComicPanel[][] {
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
  onAdaptToComic,
  loadingMore,
  coinBalance = 100,
  onOpenCoinModal,
}: Props) {
  const t = translations[lang];
  const pages = splitIntoPages(panels, 4);
  const totalPanels = panels.length;

  const [viewMode, setViewMode] = useState<"page" | "panel">("page");
  const [selectedPanelIdx, setSelectedPanelIdx] = useState<number>(0);
  const [activeQueueIndex, setActiveQueueIndex] = useState(0);
  const [comfyStatus, setComfyStatus] = useState<{ available: boolean } | null>(null);
  const [loadedPanels, setLoadedPanels] = useState<Record<number, boolean>>({});
  const [errorPanels, setErrorPanels] = useState<Record<number, boolean>>({});
  const [retryKeys, setRetryKeys] = useState<Record<number, number>>({});

  useEffect(() => {
    let active = true;
    api.getComfyUIStatus()
      .then((res) => {
        if (active) setComfyStatus({ available: !!res?.available });
      })
      .catch(() => {
        if (active) setComfyStatus({ available: false });
      });
    return () => { active = false; };
  }, []);

  const handlePanelDone = (globalIndex: number) => {
    setLoadedPanels((prev) => ({ ...prev, [globalIndex]: true }));
    setErrorPanels((prev) => ({ ...prev, [globalIndex]: false }));
    setActiveQueueIndex((prev) => Math.max(prev, globalIndex + 1));
  };

  const handlePanelError = (globalIndex: number) => {
    const currentRetries = retryKeys[globalIndex] || 0;
    if (currentRetries < 3) {
      setTimeout(() => {
        setRetryKeys((prev) => ({ ...prev, [globalIndex]: currentRetries + 1 }));
      }, 4000);
    } else {
      setErrorPanels((prev) => ({ ...prev, [globalIndex]: true }));
      setActiveQueueIndex((prev) => Math.max(prev, globalIndex + 1));
    }
  };

  const retrySinglePanel = (globalIndex: number) => {
    setErrorPanels((prev) => ({ ...prev, [globalIndex]: false }));
    setLoadedPanels((prev) => ({ ...prev, [globalIndex]: false }));
    setRetryKeys((prev) => ({ ...prev, [globalIndex]: (prev[globalIndex] || 0) + 1 }));
  };

  const selectedPanel = panels[selectedPanelIdx] || panels[0];
  const parsedSelected = selectedPanel ? parseComicDialogue(selectedPanel.dialogue_text || "") : null;

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden bg-[#FAF7F2] text-neutral-900 font-sans transition-colors">
      
      {/* ========================================================= */}
      {/* MANGA STUDIO WORKSPACE HEADER */}
      {/* ========================================================= */}
      <header className="h-14 border-b border-neutral-300/80 bg-[#FAF7F2]/90 backdrop-blur-md px-3 sm:px-6 flex items-center justify-between gap-3 shrink-0 select-none">
        {/* Left: Breadcrumbs & Status */}
        <div className="flex min-w-0 items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={onBackToEditor}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-neutral-300/80 hover:bg-white text-xs font-mono font-bold uppercase tracking-wider text-neutral-900 transition-colors shadow-xs"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Story Lab</span>
          </button>

          <div className="flex items-center gap-1.5 text-xs font-mono text-neutral-500">
            <span>Dự án</span>
            <ChevronRight className="w-3 h-3 text-neutral-400" />
            <span className="font-bold text-neutral-950 uppercase tracking-wider">Manga Studio</span>
          </div>

          <div className="hidden sm:block h-4 w-px bg-neutral-300/80 mx-1" />

          {/* ComfyUI GPU Status Badge */}
          <div className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded border border-neutral-300/80 bg-white shadow-xs">
            {comfyStatus?.available ? (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-emerald-700 font-bold">GPU Sẵn Sàng</span>
              </>
            ) : (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-neutral-400" />
                <span className="text-neutral-500">ComfyUI Offline</span>
              </>
            )}
          </div>
        </div>

        {/* Right: View switcher & Actions */}
        <div className="flex items-center gap-2 font-mono text-xs">
          {/* Page vs Panel View Toggle */}
          <div className="hidden sm:flex rounded-lg border border-neutral-300/80 p-0.5 bg-neutral-200/50">
            <button
              type="button"
              onClick={() => setViewMode("page")}
              className={`px-2.5 py-1 rounded text-[11px] font-bold uppercase transition-colors flex items-center gap-1.5 ${
                viewMode === "page"
                  ? "bg-white text-neutral-950 shadow-xs"
                  : "text-neutral-600 hover:text-neutral-950"
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Trang Truyện</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("panel")}
              className={`px-2.5 py-1 rounded text-[11px] font-bold uppercase transition-colors flex items-center gap-1.5 ${
                viewMode === "panel"
                  ? "bg-white text-neutral-950 shadow-xs"
                  : "text-neutral-600 hover:text-neutral-950"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Chi Tiết Khung</span>
            </button>
          </div>

          {/* Continue Next Batch (4 Panels) */}
          <button
            type="button"
            onClick={onContinueComic}
            disabled={loadingMore}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-neutral-900 text-white hover:bg-neutral-800 transition-colors shadow-xs disabled:opacity-40"
          >
            {loadingMore ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            <span>{loadingMore ? "Đang tạo..." : "Vẽ 4 Khung Tiếp"}</span>
          </button>
        </div>
      </header>

      {/* ========================================================= */}
      {/* 3-COLUMN WORKSPACE BODY */}
      {/* ========================================================= */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        
        {/* ========================================================= */}
        {/* B. LEFT SIDEBAR — SCENE & PANEL NAVIGATOR */}
        {/* ========================================================= */}
        <aside className="w-64 border-r border-neutral-300/80 bg-[#FAF7F2] p-3.5 hidden md:flex flex-col justify-between shrink-0 overflow-y-auto select-none">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-neutral-300/70">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                Phân Cảnh Manga
              </span>
              <span className="text-[10px] font-mono text-neutral-400">
                [{panels.length} Khung]
              </span>
            </div>

            {/* List of Panels */}
            <div className="space-y-1.5">
              {panels.map((p, idx) => {
                const isLoaded = loadedPanels[idx];
                const isError = errorPanels[idx];
                const isRendering = activeQueueIndex === idx && !isLoaded && !isError;
                const isSelected = selectedPanelIdx === idx;

                const pId = p.id || p.panel_id;
                const rUrl = p.image_url || (pId ? `/api/comic/image/${pId}` : "");
                const fUrl = rUrl ? api.getComicImageUrl(rUrl) : "";

                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setSelectedPanelIdx(idx)}
                    className={`w-full text-left p-2 rounded-lg border transition-all flex items-center gap-2.5 ${
                      isSelected
                        ? "border-neutral-900 bg-white shadow-xs"
                        : "border-neutral-300/60 bg-white/60 hover:bg-white"
                    }`}
                  >
                    {/* Thumbnail preview */}
                    <div className="relative w-10 h-10 rounded bg-black overflow-hidden shrink-0 border border-neutral-700">
                      {fUrl && isLoaded ? (
                        <img src={fUrl} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-[9px] font-mono text-neutral-500 font-bold">
                          #{idx + 1}
                        </div>
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between text-[10px] font-mono">
                        <span className="font-bold text-neutral-900">Khung {idx + 1}</span>
                        {isLoaded ? (
                          <span className="text-emerald-600 font-bold">Xong</span>
                        ) : isRendering ? (
                          <span className="text-amber-600 font-bold animate-pulse">Đang vẽ</span>
                        ) : isError ? (
                          <span className="text-red-600 font-bold">Lỗi</span>
                        ) : (
                          <span className="text-neutral-500">Chờ</span>
                        )}
                      </div>
                      <p className="text-[11px] text-neutral-600 truncate mt-0.5">
                        {p.dialogue_text || p.image_prompt || "Không có thoại"}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bottom batch info */}
          <div className="pt-3 border-t border-neutral-300/70 text-[10px] font-mono text-neutral-500">
            Trang manga đen trắng · Định dạng 4 panel / trang.
          </div>
        </aside>

        {/* ========================================================= */}
        {/* C. CENTER — MANGA CANVAS */}
        {/* ========================================================= */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-8 flex justify-center bg-[#FAF7F2]">
          <div className="w-full max-w-4xl space-y-10">
            {pages.map((pagePanels, pageIndex) => (
              <article
                key={pageIndex}
                className="rounded-2xl border border-neutral-300/80 bg-white p-5 sm:p-10 shadow-md"
              >
                {/* Manga Page Header */}
                <div className="flex items-center justify-between pb-4 mb-6 border-b border-neutral-200 text-xs font-mono text-neutral-500">
                  <span className="uppercase tracking-widest font-bold">
                    [TRANG {pageIndex + 1}] · BẢN THẢO TRUYỆN TRANH ĐẠI VIỆT
                  </span>
                  <span>4 Khung / Trang</span>
                </div>

                {/* 2-Column Sequential Manga Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {pagePanels.map((panel, pIdx) => {
                    const globalIdx = pageIndex * 4 + pIdx;
                    const parsed = parseComicDialogue(panel.dialogue_text || "");
                    const dialogueText = parsed.text || sanitizeComicCaption(panel.dialogue_text || "");
                    const speakerName = parsed.speaker;
                    const isDialogue = parsed.isDialogue;

                    const pIdentifier = panel.id || panel.panel_id;
                    const rawUrl = panel.image_url || (pIdentifier ? `/api/comic/image/${pIdentifier}` : "");
                    const fullUrl = rawUrl ? api.getComicImageUrl(rawUrl) : "";
                    const retryKey = retryKeys[globalIdx] || 0;

                    const canLoad = activeQueueIndex >= globalIdx;
                    const isLoaded = loadedPanels[globalIdx];
                    const isError = errorPanels[globalIdx];
                    const shouldFetch = canLoad && !!fullUrl;
                    const imageUrl = shouldFetch
                      ? `${fullUrl}${fullUrl.includes("?") ? "&" : "?"}v=${retryKey}`
                      : "";

                    return (
                      <figure
                        key={pIdx}
                        onClick={() => setSelectedPanelIdx(globalIdx)}
                        className={`group relative rounded-xl border-2 transition-all p-3 cursor-pointer ${
                          selectedPanelIdx === globalIdx
                            ? "border-neutral-900 bg-[#FAF7F2] shadow-md"
                            : "border-neutral-200 hover:border-neutral-400 bg-white"
                        }`}
                      >
                        {/* Artwork container */}
                        <div className="relative aspect-[4/3] rounded-lg overflow-hidden bg-black border border-neutral-800">
                          {/* Rendering / Queue state */}
                          {!shouldFetch && !isLoaded && !isError && (
                            <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center bg-neutral-900/90 font-mono z-10">
                              <Clock className="w-5 h-5 text-neutral-500 mb-1.5 animate-pulse" />
                              <span className="text-[11px] font-bold text-neutral-400 uppercase">
                                [XẾP HÀNG GPU: KHUNG {globalIdx + 1}]
                              </span>
                            </div>
                          )}

                          {shouldFetch && imageUrl && !isLoaded && !isError && (
                            <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center bg-neutral-900/90 font-mono z-10">
                              <RefreshCw className="w-5 h-5 animate-spin text-white mb-1.5" />
                              <span className="text-[11px] font-bold text-white uppercase">
                                Đang vẽ ComfyUI...
                              </span>
                            </div>
                          )}

                          {shouldFetch && imageUrl && !isError ? (
                            <img
                              src={imageUrl}
                              alt={`Khung ${globalIdx + 1}`}
                              loading="eager"
                              onLoad={() => handlePanelDone(globalIdx)}
                              onError={() => handlePanelError(globalIdx)}
                              className={`w-full h-full object-cover transition-opacity duration-300 ${
                                isLoaded ? "opacity-100" : "opacity-0"
                              }`}
                            />
                          ) : null}

                          {isError && (
                            <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center bg-neutral-950 font-mono">
                              <AlertCircle className="w-5 h-5 text-red-500 mb-1.5" />
                              <span className="text-[11px] font-bold text-neutral-400">
                                Chưa tải được ảnh
                              </span>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  retrySinglePanel(globalIdx);
                                }}
                                className="mt-2 px-2.5 py-1 rounded text-[10px] font-bold uppercase bg-white text-black hover:bg-neutral-200"
                              >
                                Thử lại
                              </button>
                            </div>
                          )}

                          {/* Index Badge */}
                          <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/80 border border-white/20 text-[9px] font-mono font-bold text-white">
                            #{globalIdx + 1}
                          </span>
                        </div>

                        {/* Speech Balloon / Caption */}
                        {dialogueText && (
                          <div className="mt-3 p-2.5 rounded-lg bg-[#FAF7F2] border border-neutral-300/80 text-xs">
                            {speakerName ? (
                              <p className="font-sans leading-relaxed text-neutral-900">
                                <strong className="font-bold uppercase tracking-wider font-mono mr-1">
                                  {speakerName}:
                                </strong>
                                <span>{dialogueText}</span>
                              </p>
                            ) : isDialogue ? (
                              <p className="italic font-serif leading-relaxed text-neutral-900">
                                “{dialogueText}”
                              </p>
                            ) : (
                              <p className="font-sans leading-relaxed text-neutral-800">
                                {dialogueText}
                              </p>
                            )}
                          </div>
                        )}
                      </figure>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>
        </main>

        {/* ========================================================= */}
        {/* D. RIGHT SIDEBAR — SCENE INSPECTOR */}
        {/* ========================================================= */}
        <aside className="w-80 border-l border-neutral-300/80 bg-[#FAF7F2] p-4 hidden lg:flex flex-col justify-between shrink-0 overflow-y-auto select-none">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-neutral-300/70">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-neutral-500" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-900">
                  Thông Tin Cảnh (Khung {selectedPanelIdx + 1})
                </span>
              </div>
            </div>

            {selectedPanel ? (
              <div className="space-y-3.5 text-xs font-mono">
                {/* Dialogue */}
                <div className="p-3 rounded-lg bg-white border border-neutral-300/70 space-y-1">
                  <span className="text-[10px] text-neutral-500 uppercase font-bold block">
                    Lời Thoại / Caption
                  </span>
                  <p className="text-neutral-900 font-sans leading-relaxed">
                    {parsedSelected?.text || selectedPanel.dialogue_text || "Không có lời thoại."}
                  </p>
                  {parsedSelected?.speaker && (
                    <span className="text-[10px] text-neutral-400 block pt-1 border-t border-neutral-200">
                      Nhân vật: <strong>{parsedSelected.speaker}</strong>
                    </span>
                  )}
                </div>

                {/* ComfyUI Image Prompt */}
                <div className="p-3 rounded-lg bg-white border border-neutral-300/70 space-y-1">
                  <span className="text-[10px] text-neutral-500 uppercase font-bold block">
                    ComfyUI Prompt
                  </span>
                  <p className="text-[11px] text-neutral-700 leading-relaxed break-words font-mono">
                    {selectedPanel.image_prompt || "manga style, black and white ink, dynamic camera angle"}
                  </p>
                </div>

                {/* Layout Type */}
                <div className="p-3 rounded-lg bg-white border border-neutral-300/70 flex items-center justify-between">
                  <span className="text-[10px] text-neutral-500 uppercase font-bold">
                    Tỷ Lệ Khung
                  </span>
                  <span className="px-2 py-0.5 rounded bg-neutral-900 text-white font-bold text-[10px]">
                    {selectedPanel.layout_type?.toUpperCase() || "SQUARE"}
                  </span>
                </div>

                {/* Single Panel Action */}
                <button
                  type="button"
                  onClick={() => retrySinglePanel(selectedPanelIdx)}
                  className="w-full py-2 rounded-lg border border-neutral-300/80 hover:bg-white font-bold uppercase tracking-wider text-neutral-900 transition-colors flex items-center justify-center gap-1.5 shadow-xs"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Vẽ Lại Khung Này</span>
                </button>
              </div>
            ) : (
              <div className="p-4 text-center text-xs text-neutral-500">
                Hãy chọn một khung truyện để xem thông số chi tiết.
              </div>
            )}
          </div>

          <div className="p-2.5 rounded border border-neutral-300/70 bg-white text-[10px] font-mono text-neutral-600">
            Mỗi khung truyện được tối ưu hóa cho mô hình sinh tranh đen trắng ComfyUI.
          </div>
        </aside>

      </div>
    </div>
  );
}

export default ComicViewer;
