"use client";

import { useEffect, useRef, useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { Sparkles, Download, Palette, Wand2, Maximize2, Minimize2, Check, X, FileText, Share2, Shield, BookOpen } from "lucide-react";

interface Props {
  content: string;
  onContentChange: (newContent: string) => void;
  lang: Language;
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
    // Strip markdown code fences
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
              break;
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
  return clean.trim();
}

export function StoryEditor({
  content,
  onContentChange,
  lang,
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
  const t = translations[lang];

  // Feature 23: Loading Skeleton state during Intake-to-Editor transition
  const isSkeletonVisible = Boolean(
    (isLoading || isStreaming) && (!content || content.trim().length === 0)
  );

  // Determine narrative mode (passed or auto-detected from content)
  const resolvedMode = (() => {
    if (narrativeMode) return narrativeMode.toUpperCase();
    const lower = (content || "").toLowerCase();
    const canonHeroes = ["trần hưng đạo", "bạch đằng", "quang trung", "lê lợi", "lý thường kiệt", "hai bà trưng", "ngô quyền", "đinh bộ lĩnh", "võ nguyên giáp", "điện biên phủ", "thánh gióng", "hùng vương", "an dương vương", "bà triệu", "như nguyệt", "ngọc hồi"];
    if (canonHeroes.some(h => lower.includes(h))) return "CHINH_SU";
    const daSuTerms = ["thời nhà trần", "thời nhà lê", "thời nguyễn", "thời lý", "kinh thành thăng long", "cấm vệ quân", "nghĩa quân"];
    if (daSuTerms.some(term => lower.includes(term))) return "DA_SU";
    return "HU_CAU_TU_DO";
  })();

  const resolvedLabel = (() => {
    if (modeLabel) return modeLabel;
    if (resolvedMode === "CHINH_SU") return "Chính sử";
    if (resolvedMode === "DA_SU") return "Dã sử";
    return "Hư cấu tự do";
  })();

  // Sync content when streaming or loaded externally
  useEffect(() => {
    if (editorRef.current && !isTypingRef.current) {
      let displayContent = content;
      if (
        typeof displayContent === "string" &&
        (displayContent.trim().startsWith("{") ||
          displayContent.includes('"updated_story_content"') ||
          displayContent.includes("\\n"))
      ) {
        displayContent = sanitizeProseSafetyNet(displayContent);
      }
      if (editorRef.current.innerText !== displayContent) {
        editorRef.current.innerText = displayContent;
      }
    }
  }, [content, isSkeletonVisible]);

  // Calculate word count
  const words = content.trim() ? content.trim().split(/\s+/).filter(w => w.length > 0).length : 0;

  // Handle text selection for floating toolbar and DOM caret position calculation
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
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-100 dark:bg-slate-950 transition-colors">
      {/* Editor Top Bar */}
      <div className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-brand-700 dark:text-brand-400" />
          <h2 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white truncate">
            {t.editor_title}
          </h2>
          <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            {words} {t.words}
          </span>
          {/* Narrative Mode Auto-detected Badge */}
          <div
            className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-semibold transition-all shadow-xs ${
              resolvedMode === "CHINH_SU"
                ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30"
                : resolvedMode === "DA_SU"
                ? "bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30"
                : "bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-500/30"
            }`}
            title={`Chế độ sáng tác: ${resolvedLabel}`}
          >
            {resolvedMode === "CHINH_SU" && <Shield className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />}
            {resolvedMode === "DA_SU" && <BookOpen className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />}
            {resolvedMode === "HU_CAU_TU_DO" && <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 shrink-0" />}
            <span>{resolvedLabel}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onPublish && (
            <button
              onClick={onPublish}
              className="px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 shadow-sm flex items-center gap-1.5 transition-all"
              title={lang === "vi" ? "Lưu bản thảo và xuất bản lên Bảng tin cộng đồng" : "Save and publish to community feed"}
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>{t.btn_publish}</span>
            </button>
          )}

          <button
            onClick={onAdaptToComic}
            className="px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-700 shadow-sm flex items-center gap-1.5 transition-all"
          >
            <Palette className="w-3.5 h-3.5" />
            <span>{t.comic_btn}</span>
          </button>

          <button
            onClick={onDownload}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t.download_btn}</span>
          </button>
        </div>
      </div>

      {/* Manuscript Reading Paper Canvas */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-8 flex justify-center">
        <div className="relative w-full max-w-3xl min-h-[85vh] bg-[#FAF8F5] dark:bg-[#111827] rounded-xl shadow-md border border-[#E8E4DC] dark:border-slate-800 p-8 sm:p-14 transition-colors">
          {isSkeletonVisible ? (
            <div
              className="space-y-6 animate-pulse select-none"
              data-testid="manuscript-loading-skeleton"
            >
              {/* Dong Son Bronze Header */}
              <div className="flex items-center justify-between pb-6 border-b border-amber-500/20 dark:border-amber-500/10">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/15 dark:bg-amber-400/10 border border-amber-500/30 flex items-center justify-center text-amber-700 dark:text-amber-400 shadow-sm">
                    <Sparkles className="w-5 h-5 animate-spin text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-amber-950 dark:text-amber-300 font-serif tracking-wide">
                      {lang === "vi" ? "Đang khởi tạo bản thảo văn học..." : "Composing literary manuscript..."}
                    </h3>
                    <p className="text-[11px] text-amber-800/80 dark:text-amber-400/70">
                      {lang === "vi"
                        ? "AI đang kiến tạo dàn ý, thiết lập phân cảnh và chấp bút những dòng đầu tiên..."
                        : "AI is structuring narrative beats and drafting opening lines..."}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 dark:bg-amber-400/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                  <span>Dong Son AI</span>
                </div>
              </div>

              {/* Animated pulse placeholder title bar */}
              <div className="h-9 w-2/3 rounded-lg bg-gradient-to-r from-amber-400/20 via-amber-300/40 to-amber-400/20 dark:from-amber-600/20 dark:via-amber-500/35 dark:to-amber-600/20 shadow-sm mb-8" />

              {/* Multi-line shimmering paragraph blocks with varying widths (90%, 80%, 95%, 70%) */}
              <div className="space-y-3.5">
                <div className="h-4 w-[90%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[80%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[95%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[70%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
              </div>

              {/* Decorative separator */}
              <div className="py-2 flex items-center justify-center opacity-60">
                <div className="w-20 h-0.5 bg-gradient-to-r from-transparent via-amber-500/40 to-transparent" />
              </div>

              {/* Shimmer paragraph 2 */}
              <div className="space-y-3.5">
                <div className="h-4 w-[92%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[85%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[90%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[75%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
              </div>

              {/* Shimmer paragraph 3 */}
              <div className="space-y-3.5 pt-2">
                <div className="h-4 w-[88%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[95%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
                <div className="h-4 w-[65%] rounded bg-gradient-to-r from-amber-500/15 via-amber-400/30 to-amber-500/15 dark:from-amber-700/20 dark:via-amber-600/35 dark:to-amber-700/20" />
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
              className="outline-none font-serif text-slate-900 dark:text-slate-100 text-base sm:text-lg leading-[1.85] tracking-wide whitespace-pre-wrap min-h-[70vh]"
              data-placeholder={t.editor_placeholder}
            />
          )}
        </div>
      </div>

      {/* Floating Selection Toolbar */}
      {floatingPos && (
        <div
          style={{ left: `${floatingPos.x}px`, top: `${floatingPos.y}px` }}
          className="fixed z-40 flex items-center gap-1 p-1 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 animate-in fade-in zoom-in-95 duration-150"
        >
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              onQuickAction("rewrite", selectedText);
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors"
          >
            <Wand2 className="w-3 h-3 text-indigo-400" />
            <span>{t.tool_rewrite}</span>
          </button>
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              onQuickAction("expand", selectedText);
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors"
          >
            <Maximize2 className="w-3 h-3 text-emerald-400" />
            <span>{t.tool_expand}</span>
          </button>
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              onQuickAction("shorten", selectedText);
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors"
          >
            <Minimize2 className="w-3 h-3 text-amber-400" />
            <span>{t.tool_shorten}</span>
          </button>
          {onOpenCustomAI && (
            <button
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onOpenCustomAI(selectedText);
                setFloatingPos(null);
              }}
              className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors text-indigo-300"
            >
              <Sparkles className="w-3 h-3 text-brand-400" />
              <span>{t.tool_ai}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
