"use client";

import { useEffect, useRef, useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { Sparkles, Download, Palette, Wand2, Maximize2, Minimize2, Check, X, FileText } from "lucide-react";

interface Props {
  content: string;
  onContentChange: (newContent: string) => void;
  lang: Language;
  onAdaptToComic: () => void;
  onDownload: () => void;
  onSelectText: (selectedText: string) => void;
  onQuickAction: (action: 'rewrite' | 'expand' | 'shorten') => void;
  onOpenCustomAI?: (selectedText: string) => void;
}

export function StoryEditor({
  content,
  onContentChange,
  lang,
  onAdaptToComic,
  onDownload,
  onSelectText,
  onQuickAction,
  onOpenCustomAI,
}: Props) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [floatingPos, setFloatingPos] = useState<{ x: number; y: number } | null>(null);
  const [selectedText, setSelectedText] = useState("");
  const isTypingRef = useRef(false);
  const t = translations[lang];

  // Sync content when streaming or loaded externally
  useEffect(() => {
    if (editorRef.current && !isTypingRef.current) {
      if (editorRef.current.innerText !== content) {
        editorRef.current.innerText = content;
      }
    }
  }, [content]);

  // Calculate word count
  const words = content.trim() ? content.trim().split(/\s+/).filter(w => w.length > 0).length : 0;

  // Handle text selection for floating toolbar
  const handleMouseUp = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      setFloatingPos(null);
      setSelectedText("");
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
      onSelectText(text);
    } else {
      setFloatingPos(null);
      setSelectedText("");
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
        </div>

        <div className="flex items-center gap-2">
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
          <div
            ref={editorRef}
            contentEditable
            suppressContentEditableWarning
            onMouseUp={handleMouseUp}
            onFocus={() => { isTypingRef.current = true; }}
            onBlur={() => { isTypingRef.current = false; }}
            onInput={(e) => {
              const newTxt = e.currentTarget.innerText;
              onContentChange(newTxt);
            }}
            className="outline-none font-serif text-slate-900 dark:text-slate-100 text-base sm:text-lg leading-[1.85] tracking-wide whitespace-pre-wrap min-h-[70vh]"
            data-placeholder={t.editor_placeholder}
          />
        </div>
      </div>

      {/* Floating Selection Toolbar */}
      {floatingPos && (
        <div
          style={{ left: `${floatingPos.x}px`, top: `${floatingPos.y}px` }}
          className="fixed z-40 flex items-center gap-1 p-1 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 animate-in fade-in zoom-in-95 duration-150"
        >
          <button
            onClick={() => {
              onQuickAction("rewrite");
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors"
          >
            <Wand2 className="w-3 h-3 text-indigo-400" />
            <span>{t.tool_rewrite}</span>
          </button>
          <button
            onClick={() => {
              onQuickAction("expand");
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors"
          >
            <Maximize2 className="w-3 h-3 text-emerald-400" />
            <span>{t.tool_expand}</span>
          </button>
          <button
            onClick={() => {
              onQuickAction("shorten");
              setFloatingPos(null);
            }}
            className="px-2.5 py-1 text-xs font-semibold hover:bg-slate-800 dark:hover:bg-slate-700 rounded flex items-center gap-1 transition-colors"
          >
            <Minimize2 className="w-3 h-3 text-amber-400" />
            <span>{t.tool_shorten}</span>
          </button>
          {onOpenCustomAI && (
            <button
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
