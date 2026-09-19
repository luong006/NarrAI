"use client";

import { useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { Bot, Send, Check, X, Sparkles, Feather, BookmarkCheck } from "lucide-react";
import { ChatMessage } from "@/lib/types";

interface Props {
  lang: Language;
  selectedText: string;
  proposedText: string | null;
  copilotMessages: ChatMessage[];
  onAcceptEdit: () => void;
  onRejectEdit: () => void;
  onSubmitCustomInstruction: (instruction: string) => void;
  onSendCopilotMessage: (msg: string) => void;
  onContinueChapter: () => void;
  onEndStory: () => void;
  loading: boolean;
  streaming: boolean;
}

export function AICopilotPanel({
  lang,
  selectedText,
  proposedText,
  copilotMessages,
  onAcceptEdit,
  onRejectEdit,
  onSubmitCustomInstruction,
  onSendCopilotMessage,
  onContinueChapter,
  onEndStory,
  loading,
  streaming,
}: Props) {
  const [customInstruction, setCustomInstruction] = useState("");
  const [chatInput, setChatInput] = useState("");
  const t = translations[lang];

  const handleCustomSubmit = () => {
    if (!customInstruction.trim() || loading) return;
    onSubmitCustomInstruction(customInstruction.trim());
    setCustomInstruction("");
  };

  const handleChatSubmit = () => {
    if (!chatInput.trim() || loading || streaming) return;
    onSendCopilotMessage(chatInput.trim());
    setChatInput("");
  };

  return (
    <aside className="w-80 h-screen border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col shrink-0 p-4 select-none transition-colors">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-200 dark:border-slate-800 mb-3 shrink-0">
        <Bot className="w-5 h-5 text-brand-700 dark:text-brand-400" />
        <h3 className="font-bold text-sm text-slate-900 dark:text-white">
          {t.ai_copilot}
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {/* Selected Passage & Action Box */}
        {selectedText && (
          <div className="p-3.5 rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/50 dark:bg-indigo-950/30">
            <span className="text-[11px] font-bold uppercase tracking-wider text-brand-700 dark:text-brand-300 block mb-1">
              {t.selected_text}
            </span>
            <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-3 italic mb-3 font-serif bg-white/60 dark:bg-slate-900/60 p-2 rounded">
              "{selectedText}"
            </p>

            <div className="relative mb-2">
              <input
                type="text"
                value={customInstruction}
                onChange={(e) => setCustomInstruction(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCustomSubmit()}
                placeholder={t.ai_instruction_placeholder}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <button
              onClick={handleCustomSubmit}
              disabled={loading || !customInstruction.trim()}
              className="w-full py-2 rounded-lg text-xs font-bold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 shadow-sm transition-all disabled:opacity-50"
            >
              {t.ai_request_btn}
            </button>
          </div>
        )}

        {/* Proposed Text (Diff Preview) */}
        {proposedText && (
          <div className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/30">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 block mb-1">
              {t.ai_result}
            </span>
            <div className="text-xs text-slate-800 dark:text-slate-200 font-serif leading-relaxed mb-3 bg-white/70 dark:bg-slate-900/70 p-2.5 rounded border border-emerald-100 dark:border-emerald-900/40 whitespace-pre-wrap">
              {proposedText}
            </div>
            <div className="flex gap-2">
              <button
                onClick={onAcceptEdit}
                className="flex-1 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 flex items-center justify-center gap-1 shadow-sm transition-colors"
              >
                <Check className="w-3.5 h-3.5" />
                <span>{t.accept_btn}</span>
              </button>
              <button
                onClick={onRejectEdit}
                className="flex-1 py-1.5 rounded-lg text-xs font-bold text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center gap-1 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                <span>{t.reject_btn}</span>
              </button>
            </div>
          </div>
        )}

        {/* Default Welcome / Tip */}
        {!selectedText && !proposedText && copilotMessages.length === 0 && (
          <div className="p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-xs text-slate-600 dark:text-slate-400 space-y-2">
            <p>{t.ai_welcome_1}</p>
            <p className="text-slate-500">{t.ai_welcome_2}</p>
          </div>
        )}

        {/* Status indicator */}
        {(loading || streaming) && (
          <div className="p-2.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 border border-brand-200 dark:border-brand-900 flex items-center gap-2 text-xs text-brand-700 dark:text-brand-300">
            <div className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            <span>
              {streaming
                ? lang === "vi"
                  ? "AI đang chấp bút thời gian thực..."
                  : "AI is drafting live..."
                : t.ai_thinking}
            </span>
          </div>
        )}

        {/* Interactive Chat Box Messages */}
        <div className="space-y-2 pt-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            {t.copilot_chat_title}
          </span>
          {copilotMessages.map((msg, i) => (
            <div
              key={i}
              className={`p-2.5 rounded-xl text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-brand-700 text-white ml-6 rounded-tr-none"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 mr-4 rounded-tl-none border border-slate-200 dark:border-slate-700"
              }`}
            >
              {msg.content}
            </div>
          ))}
        </div>
      </div>

      {/* Chat Input Area */}
      <div className="pt-2 border-t border-slate-200 dark:border-slate-800 shrink-0 mb-3">
        <div className="relative">
          <textarea
            rows={2}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleChatSubmit();
              }
            }}
            placeholder={t.copilot_placeholder}
            className="w-full pl-3 pr-10 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500 resize-none shadow-sm"
          />
          <button
            onClick={handleChatSubmit}
            disabled={loading || streaming || !chatInput.trim()}
            className="absolute right-2 top-2 p-1.5 rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-40 transition-all"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Action Buttons: Continue chapter / End story */}
      <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-2 shrink-0">
        <button
          onClick={onContinueChapter}
          disabled={loading || streaming}
          className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 shadow flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
        >
          <Feather className="w-3.5 h-3.5" />
          <span>{t.continue_chapter_btn}</span>
        </button>

        <button
          onClick={onEndStory}
          disabled={loading || streaming}
          className="w-full py-2 rounded-xl text-xs font-semibold text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <BookmarkCheck className="w-3.5 h-3.5" />
          <span>{t.end_story_btn}</span>
        </button>
      </div>
    </aside>
  );
}
