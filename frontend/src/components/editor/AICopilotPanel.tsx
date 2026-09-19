"use client";

import { useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { Bot, Send, Check, X, Sparkles, Feather, BookmarkCheck, RotateCcw, Wand2, Zap, Palette, Users } from "lucide-react";
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
  onUndo?: () => void;
  canUndo?: boolean;
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
  onUndo,
  canUndo,
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

  const handleQuickPrompt = (prompt: string) => {
    if (loading || streaming) return;
    onSendCopilotMessage(prompt);
  };

  const quickPrompts = lang === "vi" ? [
    { icon: Wand2, text: "Tạo phần mở đầu khác đi", label: "🪄 Mở đầu mới" },
    { icon: Zap, text: "Sửa lại đoạn kết kịch tính và bất ngờ hơn", label: "⚡ Kết kịch tính" },
    { icon: Palette, text: "Viết lại giọng văn u tối và hồi hộp hơn", label: "🎭 Đổi văn phong" },
    { icon: Users, text: "Bổ sung thêm diễn biến tâm lý và thoại cho nhân vật", label: "👥 Thêm tâm lý" },
  ] : [
    { icon: Wand2, text: "Write a completely different opening for this story", label: "🪄 New Intro" },
    { icon: Zap, text: "Make the ending much more dramatic and suspenseful", label: "⚡ Dramatic Outro" },
    { icon: Palette, text: "Rewrite in a darker, more gripping thriller tone", label: "🎭 Change Tone" },
    { icon: Users, text: "Add deeper internal thoughts and character dialogues", label: "👥 Deepen Characters" },
  ];

  return (
    <aside className="w-80 sm:w-96 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col h-full shrink-0 px-4 py-4 transition-colors">
      {/* Copilot Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800 flex items-center justify-center text-brand-700 dark:text-brand-300">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-slate-900 dark:text-white leading-tight">
              {t.ai_copilot}
            </h3>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {lang === "vi" ? "Trực tiếp sửa bản thảo" : "Live Manuscript Editor"}
            </span>
          </div>
        </div>

        {canUndo && onUndo && (
          <button
            onClick={onUndo}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-100 hover:bg-amber-200 dark:bg-amber-950/60 dark:hover:bg-amber-900/80 text-amber-800 dark:text-amber-300 transition-colors border border-amber-300 dark:border-amber-800 shadow-xs"
            title="Hoàn tác chỉnh sửa gần nhất"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Hoàn tác</span>
          </button>
        )}
      </div>

      {/* Main Copilot Content: Scrollable */}
      <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1">
        {/* If text is selected in the editor: Quick edit block */}
        {selectedText ? (
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                {t.selected_text}
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {selectedText.length} chars
              </span>
            </div>
            <p className="text-xs italic text-slate-600 dark:text-slate-300 line-clamp-2 border-l-2 border-brand-500 pl-2">
              "{selectedText}"
            </p>

            <div className="pt-2 space-y-2">
              <input
                type="text"
                value={customInstruction}
                onChange={(e) => setCustomInstruction(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCustomSubmit()}
                placeholder={t.ai_instruction_placeholder}
                className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <button
                onClick={handleCustomSubmit}
                disabled={loading || !customInstruction.trim()}
                className="w-full py-1.5 rounded-lg text-xs font-semibold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 disabled:opacity-50 flex items-center justify-center gap-1.5 transition-colors shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{t.ai_request_btn}</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 space-y-1.5">
            <p className="font-semibold text-slate-800 dark:text-slate-200">
              {t.ai_welcome_1}
            </p>
            <p className="text-[11px] leading-relaxed">
              {t.ai_welcome_2}
            </p>
          </div>
        )}

        {/* Proposed Text Diff/Preview */}
        {proposedText && (
          <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-2.5 animate-fadeIn">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300 block">
              {t.ai_result}
            </span>
            <p className="text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
              {proposedText}
            </p>
            <div className="flex gap-2 pt-1">
              <button
                onClick={onAcceptEdit}
                className="flex-1 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 flex items-center justify-center gap-1 shadow-xs transition-colors"
              >
                <Check className="w-3.5 h-3.5" />
                <span>{t.accept_btn}</span>
              </button>
              <button
                onClick={onRejectEdit}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center gap-1 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                <span>{t.reject_btn}</span>
              </button>
            </div>
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
        <div className="space-y-2 pt-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            {t.copilot_chat_title}
          </span>
          {copilotMessages.map((msg, i) => (
            <div
              key={i}
              className={`p-2.5 rounded-xl text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-brand-700 text-white ml-6 rounded-tr-none shadow-xs"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 mr-4 rounded-tl-none border border-slate-200 dark:border-slate-700 shadow-xs whitespace-pre-line"
              }`}
            >
              {msg.content}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Command Chips */}
      <div className="pt-2 border-t border-slate-200 dark:border-slate-800 shrink-0">
        <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 block mb-1">
          {lang === "vi" ? "Lệnh can thiệp nhanh bản thảo:" : "Direct manuscript commands:"}
        </span>
        <div className="flex flex-wrap gap-1 mb-2">
          {quickPrompts.map((qp, idx) => (
            <button
              key={idx}
              disabled={loading || streaming}
              onClick={() => handleQuickPrompt(qp.text)}
              className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 hover:bg-brand-50 hover:text-brand-700 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700 flex items-center gap-1 disabled:opacity-40"
            >
              <qp.icon className="w-2.5 h-2.5 text-brand-600" />
              <span>{qp.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Input Area */}
      <div className="shrink-0 mb-2">
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
            className="absolute right-2 top-2 p-1.5 rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-40 transition-all shadow-xs"
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
