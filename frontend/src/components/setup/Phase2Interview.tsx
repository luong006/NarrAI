"use client";

import { useState, useRef, useEffect } from "react";
import { translations, Language } from "@/lib/i18n";
import { ChatMessage } from "@/lib/types";
import { Send, FastForward, Bot, User } from "lucide-react";

interface Props {
  lang: Language;
  history: ChatMessage[];
  onSendMessage: (msg: string) => void;
  onSkip: () => void;
  loading: boolean;
}

export function Phase2Interview({ lang, history, onSendMessage, onSkip, loading }: Props) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const t = translations[lang];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-6 flex flex-col h-[calc(100vh-80px)]">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
          {t.step2_title}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {lang === 'vi' ? "Trả lời các câu hỏi để AI định hình cốt truyện hoặc bấm bỏ qua để chốt dàn ý ngay." : "Answer AI questions to flesh out your narrative, or skip to finalize immediately."}
        </p>
      </div>

      {/* Chat History Box */}
      <div className="flex-1 overflow-y-auto space-y-3 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 mb-4">
        {history.map((msg, index) => (
          <div
            key={index}
            className={`flex items-start gap-2.5 ${
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs shrink-0 ${
                msg.role === "user"
                  ? "bg-brand-700 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-brand-700 text-white rounded-tr-none"
                  : "bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 rounded-tl-none shadow-sm"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 pl-9">
            <div className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            <span>{t.ai_thinking}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="space-y-3">
        <div className="relative">
          <textarea
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={t.chat_placeholder}
            className="w-full pl-4 pr-12 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm resize-none"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="absolute right-3 top-3 p-2 rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-40 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <button
          onClick={onSkip}
          className="w-full py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold transition-all flex items-center justify-center gap-1.5"
        >
          <FastForward className="w-3.5 h-3.5" />
          <span>{t.skip_chat_btn}</span>
        </button>
      </div>
    </div>
  );
}
