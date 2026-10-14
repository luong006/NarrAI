"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import {
  Sparkles,
  Share2,
  Image as ImageIcon,
  Download,
  Save,
  CheckCircle2,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  BookOpen,
  Maximize2,
  Minimize2,
  Bookmark,
  Users,
  Compass,
} from "lucide-react";
import { translations, Language } from "@/lib/i18n";

interface Props {
  content: string;
  onContentChange: (newContent: string) => void;
  lang: Language;
  onToggleCopilot?: () => void;
  onAdaptToComic: () => void;
  onDownload: () => void;
  onPublish?: () => void;
  onSelectText: (text: string, cursorPosition?: number) => void;
  onQuickAction: (action: 'rewrite' | 'expand' | 'shorten', targetText?: string) => void;
  onOpenCustomAI?: (text: string) => void;
  narrativeMode?: string;
  modeLabel?: string;
  isLoading?: boolean;
  isStreaming?: boolean;
}

function getCaretCharacterOffsetWithin(element: HTMLElement): { start: number; end: number } {
  let start = 0;
  let end = 0;
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0) {
    const range = sel.getRangeAt(0);
    if (element.contains(range.commonAncestorContainer)) {
      const preCaretRange = range.cloneRange();
      preCaretRange.selectNodeContents(element);
      preCaretRange.setEnd(range.startContainer, range.startOffset);
      start = preCaretRange.toString().length;
      end = start + range.toString().length;
    }
  }
  return { start, end };
}

function sanitizeProseSafetyNet(text: string): string {
  if (!text) return "";
  let clean = String(text).trim();

  const candidateKeys = [
    "updated_story_content",
    "story_content",
    "story",
    "content",
    "new_story_content",
    "revised_text",
    "text",
  ];

  for (let i = 0; i < 5; i++) {
    const prev = clean;
    clean = clean.replace(/^```(?:json|markdown)?\s*\n?/i, "").replace(/\n?```\s*$/i, "").trim();

    if (
      (clean.startsWith("{") && clean.endsWith("}")) ||
      clean.includes('"updated_story_content"') ||
      clean.includes('"action_params"')
    ) {
      try {
        const parsed = JSON.parse(clean);
        if (typeof parsed === "string") {
          clean = parsed.trim();
        } else if (typeof parsed === "object" && parsed !== null) {
          let found: string | null = null;
          for (const k of candidateKeys) {
            const v = (parsed as Record<string, unknown>)[k];
            if (v && typeof v === "string") {
              found = v;
            }
          }
          if (!found && parsed.action_params && typeof parsed.action_params === "object") {
            const sub = parsed.action_params as Record<string, unknown>;
            for (const k of candidateKeys) {
              const v = sub[k];
              if (v && typeof v === "string") {
                found = v;
                break;
              }
            }
          }
          if (found) {
            clean = found.trim();
          }
        }
      } catch {
        const match = clean.match(
          /"updated_story_content"\s*:\s*"([\s\S]*?)(?:",\s*"(?:summary_of_changes|message|action|instruction)"\s*:|"\s*\}[\}\]]?\s*$)/
        );
        if (match && match[1]) {
          clean = match[1].trim();
        }
      }
    }

    if (clean.includes("\\n") || clean.includes("\\r") || clean.includes('\\"') || clean.includes("\\\\")) {
      clean = clean
        .replace(/\\r\\n/g, "\n")
        .replace(/\\n/g, "\n")
        .replace(/\\r/g, "")
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, "\\");
    }

    if (clean === prev) break;
  }

  clean = clean.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  clean = clean.replace(/\n{3,}/g, "\n\n");
  clean = clean.replace(/<[^>]+>/g, "");
  clean = clean
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");

  clean = clean.replace(/^\s*\*\*(?:Hook|Rising Friction(?:\s*\/\s*Complication)?|Turning Point|Visceral Climax|Lingering Cliffhanger|Beat\s*\d+|Nhịp\s*\d+)\*\*\s*\n?/gim, "");
  clean = clean.replace(/\*\*(?:Hook|Rising Friction(?:\s*\/\s*Complication)?|Turning Point|Visceral Climax|Lingering Cliffhanger)\*\*\s*/gi, "");

  return clean.trim();
}

export function StoryEditor({
  content,
  onContentChange,
  lang,
  onToggleCopilot,
  onAdaptToComic,
  onDownload,
  onPublish,
  onSelectText,
  onQuickAction,
  onOpenCustomAI,
  narrativeMode,
  modeLabel,
  isLoading,
  isStreaming,
}: Props) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [floatingPos, setFloatingPos] = useState<{ x: number; y: number } | null>(null);
  const [selectedText, setSelectedText] = useState("");
  const isTypingRef = useRef(false);
  const [isOutlineOpen, setIsOutlineOpen] = useState(true);
  const [isFocusMode, setIsFocusMode] = useState(false);
  const [storyTitle, setStoryTitle] = useState(lang === "vi" ? "Bản Thảo Đại Việt" : "Untitled Manuscript");
  const [savedStatus, setSavedStatus] = useState<"saved" | "saving">("saved");
  const t = translations[lang];

  const isSkeletonVisible = Boolean(
    (isLoading || isStreaming) && (!content || content.trim().length === 0)
  );

  const cleanContent = useMemo(() => sanitizeProseSafetyNet(content), [content]);

  useEffect(() => {
    if (editorRef.current && !isTypingRef.current) {
      if (editorRef.current.innerText !== cleanContent) {
        editorRef.current.innerText = cleanContent;
      }
    }
    setSavedStatus("saving");
    const saveTimer = setTimeout(() => {
      setSavedStatus("saved");
    }, 800);
    return () => clearTimeout(saveTimer);
  }, [cleanContent]);

  // Extract chapters or headings
  const chapters = useMemo(() => {
    if (!cleanContent) return [{ id: 1, title: lang === "vi" ? "Chương 1: Khởi đầu" : "Chapter 1: The Beginning" }];
    const lines = cleanContent.split("\n");
    const found: Array<{ id: number; title: string }> = [];
    let count = 1;
    for (const line of lines) {
      const trimmed = line.trim();
      if (/^(chương|hồi|tiết|chapter|part)\s+\d+/i.test(trimmed)) {
        found.push({ id: count++, title: trimmed.slice(0, 40) });
      }
    }
    if (found.length === 0) {
      return [{ id: 1, title: lang === "vi" ? "Chương 1: Mở màn" : "Chapter 1: Opening Scene" }];
    }
    return found;
  }, [cleanContent, lang]);

  const words = useMemo(() => {
    return cleanContent ? cleanContent.split(/\s+/).filter(Boolean).length : 0;
  }, [cleanContent]);

  const readTimeMinutes = Math.max(1, Math.ceil(words / 220));

  const resolvedLabel = useMemo(() => {
    if (modeLabel) return modeLabel;
    if (narrativeMode === "authentic_history") {
      return lang === "vi" ? "Chính sử" : "Authentic History";
    }
    return lang === "vi" ? "Dã sử" : "Historical Fiction";
  }, [modeLabel, narrativeMode, lang]);

  const handleSelectionChange = () => {
    const selection = window.getSelection();
    if (!selection || !editorRef.current) {
      setFloatingPos(null);
      setSelectedText("");
      onSelectText("");
      return;
    }

    const { start } = getCaretCharacterOffsetWithin(editorRef.current);

    if (selection.isCollapsed) {
      setFloatingPos(null);
      setSelectedText("");
      onSelectText("", start);
      return;
    }

    const text = selection.toString().trim();
    if (text.length > 3) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      setFloatingPos({
        x: Math.max(10, rect.left + rect.width / 2 - 140),
        y: Math.max(10, rect.top - 48 + window.scrollY),
      });
      setSelectedText(text);
      onSelectText(text, start);
    } else {
      setFloatingPos(null);
      setSelectedText("");
      onSelectText("", start);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden bg-[#FAF7F2] text-neutral-900 transition-colors font-sans">
      
      {/* ========================================================= */}
      {/* WORKSPACE HEADER (STORY LAB) */}
      {/* ========================================================= */}
      <div className="h-14 border-b border-neutral-300/80 bg-[#FAF7F2]/90 backdrop-blur-md px-3 sm:px-6 flex items-center justify-between gap-3 shrink-0 select-none">
        {/* Left: Breadcrumb & Title */}
        <div className="flex min-w-0 items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={() => setIsOutlineOpen(!isOutlineOpen)}
            className="hidden lg:flex p-1.5 rounded hover:bg-neutral-200/70 text-neutral-600 hover:text-neutral-950 transition-colors"
            title={isOutlineOpen ? "Thu gọn thanh điều hướng" : "Mở thanh điều hướng"}
          >
            {isOutlineOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
          </button>

          {/* Breadcrumbs */}
          <div className="flex items-center gap-1.5 text-xs font-mono text-neutral-500 shrink-0">
            <span>NarrAI</span>
            <ChevronRight className="w-3 h-3 text-neutral-400" />
            <span className="text-neutral-950 font-bold uppercase tracking-wider">Story Lab</span>
          </div>

          <div className="hidden sm:block h-4 w-px bg-neutral-300 mx-1" />

          {/* Editable Story Title */}
          <input
            type="text"
            value={storyTitle}
            onChange={(e) => setStoryTitle(e.target.value)}
            className="hidden sm:block bg-transparent text-xs font-mono font-bold text-neutral-950 border-b border-transparent hover:border-neutral-400 focus:border-neutral-950 outline-none px-1 py-0.5 max-w-[180px] lg:max-w-xs truncate"
            title="Đổi tiêu đề tác phẩm"
          />

          {/* Auto-save Status Badge */}
          <div className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded border border-neutral-300/80 bg-white text-neutral-700 shadow-xs">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>{savedStatus === "saved" ? (lang === "vi" ? "Đã lưu" : "Saved") : (lang === "vi" ? "Đang lưu..." : "Saving...")}</span>
          </div>

          {/* Narrative Mode Badge */}
          <div
            className="hidden md:inline-flex items-center text-[11px] px-2 py-0.5 rounded border border-neutral-300/80 bg-white text-neutral-900 font-mono font-bold shadow-xs"
            title={`Chế độ sáng tác: ${resolvedLabel}`}
          >
            <span>[{resolvedLabel}]</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 font-mono text-xs">
          {/* Focus Mode Toggle */}
          <button
            type="button"
            onClick={() => setIsFocusMode(!isFocusMode)}
            className="hidden md:flex items-center gap-1 px-2 py-1 rounded border border-neutral-300 hover:bg-neutral-200/70 text-neutral-700 hover:text-neutral-950 transition-colors"
            title={isFocusMode ? "Thoát chế độ tập trung" : "Chế độ tập trung viết"}
          >
            {isFocusMode ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>

          {/* Toggle Assistant on Mobile */}
          {onToggleCopilot && (
            <button
              type="button"
              onClick={onToggleCopilot}
              className="lg:hidden flex items-center gap-1 px-2.5 py-1.5 rounded text-xs font-bold uppercase tracking-wider text-neutral-900 border border-neutral-300 hover:bg-neutral-200/70 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "AI Co-pilot" : "Copilot"}</span>
            </button>
          )}

          {/* Publish to Feed */}
          {onPublish && (
            <button
              type="button"
              onClick={onPublish}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold uppercase tracking-wider text-neutral-900 border border-neutral-300 hover:bg-neutral-200/70 transition-colors"
              title={lang === "vi" ? "Lưu bản thảo và xuất bản lên Bảng tin cộng đồng" : "Save and publish to community feed"}
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>{t.btn_publish}</span>
            </button>
          )}

          {/* Adapt to Comic */}
          <button
            type="button"
            onClick={onAdaptToComic}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-neutral-950 text-white hover:bg-neutral-800 transition-colors shadow-sm"
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>{t.comic_btn}</span>
          </button>

          {/* Export / Download */}
          <button
            type="button"
            onClick={onDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-neutral-300 hover:bg-neutral-200/70 text-neutral-900 transition-colors"
            title="Tải về bản thảo dạng TXT"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t.download_btn}</span>
          </button>
        </div>
      </div>

      {/* ========================================================= */}
      {/* BODY AREA (LEFT OUTLINE + CENTER EDITOR) */}
      {/* ========================================================= */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        
        {/* B. Left Outline & Chapter Sidebar (Collapsible) */}
        {isOutlineOpen && !isFocusMode && (
          <aside className="w-60 border-r border-neutral-300/80 bg-[#FAF7F2] p-3.5 flex flex-col justify-between shrink-0 overflow-y-auto hidden lg:flex select-none">
            <div className="space-y-4">
              {/* Story Overview Card */}
              <div className="p-3 rounded-lg border border-neutral-300/80 bg-white shadow-xs">
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-neutral-500 mb-2">
                  <span>Tổng quan truyện</span>
                  <BookOpen className="w-3.5 h-3.5" />
                </div>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-1.5 rounded bg-neutral-100/90 border border-neutral-200">
                    <span className="text-xs font-bold text-neutral-950 font-mono">{words}</span>
                    <span className="text-[9px] block text-neutral-500 uppercase">{t.words}</span>
                  </div>
                  <div className="p-1.5 rounded bg-neutral-100/90 border border-neutral-200">
                    <span className="text-xs font-bold text-neutral-950 font-mono">~{readTimeMinutes}m</span>
                    <span className="text-[9px] block text-neutral-500 uppercase">Đọc</span>
                  </div>
                </div>
              </div>

              {/* Chapters Navigator */}
              <div>
                <div className="flex items-center justify-between px-1 mb-2">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                    Danh Sách Chương
                  </span>
                  <span className="text-[10px] font-mono text-neutral-400">[{chapters.length}]</span>
                </div>
                <div className="space-y-1">
                  {chapters.map((ch) => (
                    <button
                      key={ch.id}
                      type="button"
                      className="w-full text-left px-2.5 py-2 rounded-lg text-xs font-mono font-medium transition-colors flex items-center justify-between bg-neutral-950 text-white font-bold shadow-xs"
                    >
                      <span className="truncate">{ch.title}</span>
                      <span className="text-[10px] opacity-75">●</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Character & Lore Shortcuts in Chapter */}
              <div className="pt-2 border-t border-neutral-200">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500 block mb-2 px-1">
                  Nhân Vật & Điển Tích
                </span>
                <div className="space-y-1.5 text-xs font-mono">
                  <div className="p-2 rounded-lg bg-white border border-neutral-200 shadow-xs flex items-center gap-2">
                    <Users className="w-3.5 h-3.5 text-neutral-500" />
                    <span className="truncate text-[11px] text-neutral-800">Trần Khắc Liêm (Hiệp sĩ)</span>
                  </div>
                  <div className="p-2 rounded-lg bg-white border border-neutral-200 shadow-xs flex items-center gap-2">
                    <Compass className="w-3.5 h-3.5 text-neutral-500" />
                    <span className="truncate text-[11px] text-neutral-800">Bến đò Vạn Kiếp (Bối cảnh)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Quick Advice */}
            <div className="p-2.5 rounded-lg border border-neutral-300/80 bg-white text-[10px] font-mono text-neutral-600 shadow-xs">
              💡 Bôi đen đoạn văn để gọi nhanh các lệnh viết lại của AI Co-pilot.
            </div>
          </aside>
        )}

        {/* C. Center Editor Manuscript Reading Canvas */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-6 lg:p-8 flex justify-center bg-[#FAF7F2]">
          <div className="relative w-full max-w-3xl min-h-[85vh] bg-white rounded-xl shadow-md border border-neutral-300/80 p-6 sm:p-12 lg:p-14 transition-colors">
            
            {/* Manuscript Header Bar inside paper */}
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-neutral-200 text-xs font-mono text-neutral-500">
              <span className="uppercase tracking-widest font-bold">
                {lang === "vi" ? "BẢN THẢO VĂN HỌC" : "LITERARY MANUSCRIPT"}
              </span>
              <div className="flex items-center gap-3">
                <span>{words} {t.words}</span>
                <span>·</span>
                <span>{cleanContent.length} ký tự</span>
              </div>
            </div>

            {isSkeletonVisible ? (
              <div
                className="space-y-6 animate-pulse select-none"
                data-testid="manuscript-loading-skeleton"
              >
                <div className="flex items-center justify-between pb-4 border-b border-neutral-200">
                  <div className="flex items-center gap-3">
                    <div className="px-2.5 py-1 rounded bg-neutral-100 border border-neutral-300 text-xs font-mono font-bold text-neutral-950">
                      [ĐANG SOẠN]
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-neutral-950 font-serif tracking-wide">
                        {lang === "vi" ? "Đang khởi tạo bản thảo văn học..." : "Composing literary manuscript..."}
                      </h3>
                      <p className="text-[11px] text-neutral-600">
                        {lang === "vi"
                          ? "AI đang kiến tạo dàn ý, thiết lập phân cảnh và chấp bút những dòng đầu tiên..."
                          : "AI is structuring narrative beats and drafting opening lines..."}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 px-3 py-1 rounded border border-neutral-300 bg-neutral-100 text-neutral-950 text-xs font-mono">
                    <span>[NARR AI]</span>
                  </div>
                </div>

                <div className="h-9 w-2/3 rounded bg-neutral-200 shadow-sm mb-8" />

                <div className="space-y-3.5">
                  <div className="h-4 w-[90%] rounded bg-neutral-200" />
                  <div className="h-4 w-[80%] rounded bg-neutral-200" />
                  <div className="h-4 w-[95%] rounded bg-neutral-200" />
                  <div className="h-4 w-[70%] rounded bg-neutral-200" />
                </div>

                <div className="py-2 flex items-center justify-center opacity-60">
                  <div className="w-20 h-0.5 bg-neutral-300" />
                </div>

                <div className="space-y-3.5">
                  <div className="h-4 w-[92%] rounded bg-neutral-200" />
                  <div className="h-4 w-[85%] rounded bg-neutral-200" />
                  <div className="h-4 w-[90%] rounded bg-neutral-200" />
                  <div className="h-4 w-[75%] rounded bg-neutral-200" />
                </div>
              </div>
            ) : (
              <div
                ref={editorRef}
                contentEditable
                suppressContentEditableWarning
                onMouseUp={handleSelectionChange}
                onKeyUp={handleSelectionChange}
                onFocus={() => { isTypingRef.current = true; }}
                onBlur={() => { isTypingRef.current = false; }}
                onInput={(e) => {
                  const newTxt = e.currentTarget.innerText;
                  onContentChange(newTxt);
                }}
                className="outline-none font-serif text-neutral-950 text-base sm:text-lg leading-[1.85] tracking-wide whitespace-pre-wrap min-h-[70vh] selection:bg-neutral-200"
                data-placeholder={t.editor_placeholder}
              />
            )}
          </div>
        </div>

      </div>

      {/* Floating Selection Toolbar */}
      {floatingPos && (
        <div
          style={{ left: `${floatingPos.x}px`, top: `${floatingPos.y}px` }}
          className="fixed z-40 flex items-center gap-1.5 p-1.5 bg-neutral-900 dark:bg-[#171717] text-white rounded-lg border border-neutral-700 dark:border-white/20 shadow-2xl animate-in fade-in zoom-in-95 duration-150 font-mono text-xs backdrop-blur-md"
        >
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              onQuickAction("rewrite", selectedText);
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 hover:bg-neutral-800 dark:hover:bg-neutral-800 rounded transition-colors"
          >
            [Viết lại]
          </button>
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              onQuickAction("expand", selectedText);
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 hover:bg-neutral-800 dark:hover:bg-neutral-800 rounded transition-colors"
          >
            [Mở rộng]
          </button>
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              onQuickAction("shorten", selectedText);
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 hover:bg-neutral-800 dark:hover:bg-neutral-800 rounded transition-colors"
          >
            [Rút gọn]
          </button>
          {onOpenCustomAI && (
            <button
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onOpenCustomAI(selectedText);
                setFloatingPos(null);
              }}
              className="px-2.5 py-1 bg-white text-black hover:bg-neutral-200 rounded font-bold transition-colors"
            >
              [AI Co-pilot]
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default StoryEditor;
