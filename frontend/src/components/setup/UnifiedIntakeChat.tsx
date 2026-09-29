"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import { Language, translations } from "@/lib/i18n";
import { ChatMessage, StoryLength } from "@/lib/types";
import { api } from "@/lib/api";
import { ModelSelectorMorphicon, ModelTier } from "@/components/morphicons/ModelSelectorMorphicon";
import {
  Sparkles,
  Send,
  ArrowRight,
  RefreshCw,
  ShieldCheck,
  Feather,
  RotateCcw,
  Zap,
  BookOpen,
  CheckCircle2,
} from "lucide-react";

/**
 * Robust lightweight Markdown renderer component for spacious chat bubbles.
 * Parses headings, bullet lists, numbered lists, blockquotes, bold, italic, and inline code.
 */
function FormattedMarkdown({ content, isUser }: { content: string; isUser: boolean }) {
  const blocks = useMemo(() => {
    if (!content) return [];
    return content.split(/\n\n+/);
  }, [content]);

  const renderInline = (text: string) => {
    // Regex for bold **text** or __text__, italic *text* or _text_, and code `text`
    const parts = text.split(/(\*\*[^\*]+\*\*|__[^_]+__|`[^`]+`|\*[^\*]+\*|_[^_]+_)/g);
    return parts.map((part, idx) => {
      if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
        return (
          <strong key={idx} className={isUser ? "font-bold text-white" : "font-bold text-slate-900 dark:text-white"}>
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={idx}
            className={`px-1.5 py-0.5 rounded text-xs font-mono ${
              isUser ? "bg-white/20 text-white" : "bg-slate-200/70 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400"
            }`}
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
        return (
          <em key={idx} className="italic">
            {part.slice(1, -1)}
          </em>
        );
      }
      return part;
    });
  };

  return (
    <div className="space-y-2.5 text-sm leading-relaxed">
      {blocks.map((block, bIdx) => {
        const lines = block.split(/\n/);

        // Check if block is blockquote
        if (lines.every((line) => line.trim().startsWith(">"))) {
          return (
            <blockquote
              key={bIdx}
              className={`border-l-2 pl-3 py-1 my-1.5 italic ${
                isUser
                  ? "border-white/50 text-white/90"
                  : "border-indigo-500/70 dark:border-indigo-400/70 text-slate-600 dark:text-slate-300 bg-indigo-50/30 dark:bg-indigo-950/20 rounded-r-md"
              }`}
            >
              {lines.map((l, lIdx) => (
                <div key={lIdx}>{renderInline(l.replace(/^>\s?/, ""))}</div>
              ))}
            </blockquote>
          );
        }

        // Check if block is unordered list
        if (lines.every((line) => /^\s*[-*•]\s+/.test(line))) {
          return (
            <ul key={bIdx} className="space-y-1 my-1 ml-4 list-disc">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="pl-1">
                  {renderInline(line.replace(/^\s*[-*•]\s+/, ""))}
                </li>
              ))}
            </ul>
          );
        }

        // Check if block is numbered list
        if (lines.every((line) => /^\s*\d+\.\s+/.test(line))) {
          return (
            <ol key={bIdx} className="space-y-1 my-1 ml-4 list-decimal">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="pl-1">
                  {renderInline(line.replace(/^\s*\d+\.\s+/, ""))}
                </li>
              ))}
            </ol>
          );
        }

        // Check headings
        if (lines.length === 1 && lines[0].startsWith("#")) {
          const match = lines[0].match(/^(#{1,3})\s+(.*)/);
          if (match) {
            const level = match[1].length;
            const headingText = match[2];
            if (level === 1) {
              return (
                <h1 key={bIdx} className="text-base font-bold text-slate-900 dark:text-white mt-1">
                  {renderInline(headingText)}
                </h1>
              );
            }
            if (level === 2) {
              return (
                <h2 key={bIdx} className="text-sm font-bold text-slate-900 dark:text-white mt-1">
                  {renderInline(headingText)}
                </h2>
              );
            }
            return (
              <h3 key={bIdx} className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1 uppercase tracking-wide">
                {renderInline(headingText)}
              </h3>
            );
          }
        }

        // Default Paragraph
        return (
          <p key={bIdx} className="whitespace-pre-wrap">
            {lines.map((line, lIdx) => (
              <React.Fragment key={lIdx}>
                {lIdx > 0 && <br />}
                {renderInline(line)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}

export interface IntakeTransitionOptions {
  refinedPrompt?: string;
  chatHistory: ChatMessage[];
  storyLength: StoryLength;
  modelTier: ModelTier;
}

interface Props {
  lang: Language;
  onStartWriting: (options: IntakeTransitionOptions) => Promise<void> | void;
  isGenerating?: boolean;
  initialChatHistory?: ChatMessage[];
  onClearHistory?: () => void;
}

export function UnifiedIntakeChat({
  lang,
  onStartWriting,
  isGenerating = false,
  initialChatHistory = [],
  onClearHistory,
}: Props) {
  const t = translations[lang] || translations.vi;
  const [messages, setMessages] = useState<ChatMessage[]>(initialChatHistory);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [modelTier, setModelTier] = useState<ModelTier>("versatile");
  const [storyLength, setStoryLength] = useState<StoryLength>("medium");
  const [hasReadySignal, setHasReadySignal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync initial chat history if provided
  useEffect(() => {
    if (initialChatHistory && initialChatHistory.length > 0 && messages.length === 0) {
      setMessages(initialChatHistory);
      const isReadyDetected = initialChatHistory.some(
        (m) => m.is_ready || (m.role === "assistant" && m.content.includes("[READY]"))
      );
      if (isReadyDetected) setHasReadySignal(true);
    }
  }, [initialChatHistory]);

  // Auto-scroll on new messages or loading state
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-focus input on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Readiness evaluation: either AI output [READY] / is_ready, or at least 1 assistant turn
  const assistantTurns = useMemo(
    () => messages.filter((m) => m.role === "assistant").length,
    [messages]
  );
  const isReady = hasReadySignal || assistantTurns >= 1;

  // Starter prompt suggestions covering Vietnamese History, Sci-Fi, Xianxia, Slice of Life
  const starterIdeas = useMemo(() => [
    {
      id: "history",
      title: t.starter_history_title || (lang === "vi" ? "📜 Lịch sử Việt Nam (Chính sử & Dã sử)" : "📜 Vietnamese History (Authentic & Fiction)"),
      badge: t.starter_history_badge || (lang === "vi" ? "Chính sử chuẩn mực • Dã sử phóng tác" : "Strict history • Fictional perspective"),
      prompt: t.starter_history_prompt || (lang === "vi"
        ? "Một nghĩa sĩ áo vải thời Hậu Lê mang gươm báu bảo vệ bến sông lịch sử, đứng trước ngã rẽ giữa đại cục quốc gia và nghĩa tình riêng biệt."
        : "A peasant warrior during the Later Le dynasty guarding a historic river port, torn between national destiny and personal affection."),
      iconColor: "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/30",
    },
    {
      id: "scifi",
      title: t.starter_scifi_title || (lang === "vi" ? "🚀 Cyberpunk Sài Gòn 2099" : "🚀 Cyberpunk Saigon 2099"),
      badge: t.starter_scifi_badge || (lang === "vi" ? "Hư cấu cá nhân tự do" : "Unconstrained creative sci-fi"),
      prompt: t.starter_scifi_prompt || (lang === "vi"
        ? "Một thám tử tư trong khu ổ chuột ngầm Sài Gòn năm 2099, chuyên điều tra các vụ đánh cắp ký ức và nhân dạng số bất hợp pháp."
        : "A private eye in the subterranean districts of Saigon 2099, investigating illegal synthetic memory theft and cybernetic identity fraud."),
      iconColor: "text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
    },
    {
      id: "xianxia",
      title: t.starter_xianxia_title || (lang === "vi" ? "⚔️ Tu Chân & Kỳ Ảo Đông Phương" : "⚔️ Eastern Cultivation Fantasy"),
      badge: t.starter_xianxia_badge || (lang === "vi" ? "Sáng tạo thế giới độc bản • Bảo hộ IP" : "Original worldbuilding • Protected IP"),
      prompt: t.starter_xianxia_prompt || (lang === "vi"
        ? "Thiếu niên vô danh sở hữu thần hồn dị biến, từng bước phá giải cổ trận nghìn năm chôn vùi dưới cấm địa phong ấn đan điền."
        : "An unassuming youth with an anomalous soul core unravels a thousand-year-old array hidden beneath a forbidden realm."),
      iconColor: "text-purple-600 dark:text-purple-400 bg-purple-500/10 border-purple-500/30",
    },
    {
      id: "life",
      title: t.starter_life_title || (lang === "vi" ? "🌿 Đời Sống & Chữa Lành Tâm Hồn" : "🌿 Urban Slice of Life & Healing"),
      badge: t.starter_life_badge || (lang === "vi" ? "Tâm lý sâu sắc • Show, don't tell" : "Introspective depth • Show, don't tell"),
      prompt: t.starter_life_prompt || (lang === "vi"
        ? "Hai tâm hồn cô đơn tình cờ gặp gỡ tại một quán cà phê sách mở thâu đêm ở phố cổ Hà Nội vào một đêm mưa lạnh, tìm thấy sự an ủi diệu kỳ."
        : "Two lonely souls meet by chance at an all-night book café in the Hanoi Old Quarter on a cold, rainy evening, discovering unexpected solace."),
      iconColor: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    },
  ], [lang, t]);

  const handleSend = async (customText?: string) => {
    const textToSend = (customText !== undefined ? customText : input).trim();
    if (!textToSend || loading || isFinalizing) return;

    const newHistory: ChatMessage[] = [...messages, { role: "user", content: textToSend }];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const res = await api.chatInterview(newHistory);
      if (res.status === "success" && res.message) {
        // Strip [READY] tag from assistant visible message prose
        const cleanMsg = res.message.replace(/\[READY\]/g, "").trim();
        const isReadyFlag = !!(res.is_ready || res.message.includes("[READY]"));
        if (isReadyFlag) {
          setHasReadySignal(true);
        }

        const updatedHistory: ChatMessage[] = [
          ...newHistory,
          { role: "assistant", content: cleanMsg, is_ready: isReadyFlag }
        ];
        setMessages(updatedHistory);
      } else {
        setMessages([
          ...newHistory,
          {
            role: "assistant",
            content: lang === "vi"
              ? "Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."
              : "Fascinating premise! Could you elaborate more on the protagonist, core conflict, or narrative setting?"
          }
        ]);
      }
    } catch (err: any) {
      console.error("Chat interview error:", err);
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content: lang === "vi"
            ? "Đang kết nối lại với trợ lý NarrAI. Bạn có thể tiếp tục chia sẻ hoặc bấm 'Bắt đầu viết truyện ngay' ở góc trên để khởi tạo bản thảo ngay lập tức!"
            : "Reconnecting to NarrAI Assistant. You can continue detailing or click 'Start writing story now' above to jump straight to drafting!"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const triggerFinalize = async () => {
    if (messages.length === 0 && !input.trim()) return;
    setIsFinalizing(true);

    try {
      let historyToUse = [...messages];
      if (input.trim()) {
        historyToUse.push({ role: "user", content: input.trim() });
        setMessages(historyToUse);
        setInput("");
      }

      // Step 1: Call api.refinePrompt (1-2s compression into Refined Narrative Bible)
      let refined = "";
      if (historyToUse.length > 0) {
        try {
          const res = await api.refinePrompt(historyToUse);
          if (res.status === "success" && res.refined_prompt) {
            refined = res.refined_prompt;
          }
        } catch (e) {
          console.error("Refine prompt API error:", e);
        }
      }

      // Fallback if refine returned empty
      if (!refined) {
        const userTexts = historyToUse.filter((m) => m.role === "user").map((m) => m.content);
        refined = userTexts.join("\n\n") || (lang === "vi" ? "Một câu chuyện kịch tính, lôi cuốn." : "A captivating, thrilling story.");
      }

      // Step 2: Trigger seamless transition to StoryEditor
      await onStartWriting({
        refinedPrompt: refined,
        chatHistory: historyToUse,
        storyLength,
        modelTier,
      });
    } catch (err) {
      console.error("Error finalizing intake prompt:", err);
      const fallbackPrompt = messages.map((m) => m.content).join("\n") || input.trim();
      await onStartWriting({
        refinedPrompt: fallbackPrompt || "Một câu chuyện kịch tính, lôi cuốn.",
        chatHistory: messages,
        storyLength,
        modelTier,
      });
    } finally {
      setIsFinalizing(false);
    }
  };

  const handleResetChat = () => {
    if (messages.length === 0) return;
    const confirmMsg = t.intake_clear_confirm || (lang === "vi"
      ? "Bạn có chắc muốn xóa lịch sử trò chuyện và bắt đầu lại ý tưởng mới?"
      : "Are you sure you want to clear chat history and start a new story concept?");
    if (window.confirm(confirmMsg)) {
      setMessages([]);
      setInput("");
      setHasReadySignal(false);
      onClearHistory?.();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-50/40 dark:bg-slate-950/40 backdrop-blur-[2px] text-slate-900 dark:text-slate-100 relative select-none">
      {/* Minimal Translucent Glass Header */}
      <header className="h-14 border-b border-slate-200/60 dark:border-slate-800/60 px-4 sm:px-6 flex items-center justify-between shrink-0 bg-white/60 dark:bg-slate-950/60 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-brand-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
                {t.intake_header_title || "NarrAI Co-creator"}
              </h2>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                {t.intake_header_badge || "Q&A Intake"}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden md:block">
              {t.intake_header_sub || (lang === "vi"
                ? "Đa thể loại • Lịch sử Dân tộc chuẩn mực • Hư cấu tự do • Bảo hộ IP"
                : "Multi-genre • Authentic History • Creative Liberty • IP Protection")}
            </p>
          </div>
        </div>

        {/* Action Header Controls */}
        <div className="flex items-center gap-2">
          {/* Reset Intake Chat Button */}
          {messages.length > 0 && (
            <button
              onClick={handleResetChat}
              disabled={loading || isFinalizing}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition-colors disabled:opacity-40"
              title={t.intake_clear_chat || (lang === "vi" ? "Làm mới trò chuyện" : "Reset intake chat")}
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Prominent Action Button: "Bắt đầu viết truyện ngay" / "Chốt cốt truyện" */}
          <button
            onClick={triggerFinalize}
            disabled={(messages.length === 0 && !input.trim()) || isFinalizing || isGenerating}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed ${
              isReady
                ? "bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/25 ring-2 ring-emerald-400/50 animate-pulse"
                : "bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white shadow-sm"
            }`}
            title={
              isReady
                ? (lang === "vi" ? "AI đã sẵn sàng! Chốt cốt truyện và chuyển thẳng sang chấp bút bản thảo" : "Ready! Finalize plot and start drafting manuscript")
                : (lang === "vi" ? "Bắt đầu viết truyện ngay với ý tưởng hiện tại" : "Start writing story now with current ideas")
            }
          >
            {isFinalizing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>{t.intake_refining || (lang === "vi" ? "Đang cô đọng..." : "Consolidating...")}</span>
              </>
            ) : isReady ? (
              <>
                <Zap className="w-3.5 h-3.5 text-amber-300" />
                <span>{t.intake_start_writing_now || (lang === "vi" ? "Bắt đầu viết truyện ngay" : "Start writing story now")}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>{t.intake_finalize_plot || (lang === "vi" ? "Chốt cốt truyện" : "Finalize plot")}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Conversation Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 pb-48">
        <div className="max-w-3xl mx-auto w-full flex flex-col min-h-full justify-between">

          {/* Empty State: Warm Hero & 4 Starter Prompt Pills */}
          {messages.length === 0 && (
            <div className="my-auto py-6 sm:py-10 text-center flex flex-col items-center animate-fadeIn">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-violet-600 text-white flex items-center justify-center shadow-lg shadow-brand-500/20 mb-4 sm:mb-5">
                <Feather className="w-7 h-7" />
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2">
                {t.intake_welcome_title || (lang === "vi" ? "Bạn đang ấp ủ câu chuyện gì hôm nay?" : "What story are you dreaming of today?")}
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-lg mb-8 leading-relaxed">
                {t.intake_welcome_subtitle || (lang === "vi"
                  ? "Trò chuyện tự do bằng bất kỳ ý tưởng nào. NarrAI am hiểu mọi thể loại văn học, tôn trọng sự thật lịch sử và đồng hành cùng bạn từ ý niệm đầu tiên đến tác phẩm hoàn chỉnh."
                  : "Chat freely with any premise. NarrAI understands all literary genres, honors historical truth, and walks with you from initial spark to complete masterpiece.")}
              </p>

              {/* Starter Prompt Suggestion Pills */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
                {starterIdeas.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleSend(item.prompt)}
                    className="p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/70 dark:bg-slate-900/60 hover:bg-white dark:hover:bg-slate-900 hover:border-indigo-400 dark:hover:border-indigo-500 backdrop-blur-sm transition-all text-left group shadow-sm hover:shadow-md active:scale-[0.99] flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                          {item.title}
                        </span>
                      </div>
                      <span className="inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full mb-2 border text-slate-600 dark:text-slate-300 bg-slate-100/80 dark:bg-slate-800/80 border-slate-200 dark:border-slate-700">
                        {item.badge}
                      </span>
                      <p className="text-[12px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {item.prompt}
                      </p>
                    </div>
                    <div className="mt-3 flex items-center gap-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>{lang === "vi" ? "Bắt đầu khám phá" : "Explore concept"}</span>
                      <ArrowRight className="w-3 h-3" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Active Message History with Spacious Bubbles & Markdown */}
          {messages.length > 0 && (
            <div className="space-y-6 pb-6">
              {messages.map((msg, index) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={index}
                    className={`flex items-start gap-3.5 ${isUser ? "flex-row-reverse" : "flex-row"} animate-fadeIn`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold shadow-sm ${
                        isUser
                          ? "bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900"
                          : "bg-gradient-to-tr from-brand-600 to-indigo-600 text-white"
                      }`}
                    >
                      {isUser ? "U" : <Sparkles className="w-4 h-4" />}
                    </div>

                    {/* Bubble Content */}
                    <div
                      className={`max-w-[88%] sm:max-w-[80%] px-4 py-3.5 rounded-2xl ${
                        isUser
                          ? "bg-brand-600 dark:bg-brand-700 text-white rounded-tr-sm shadow-md"
                          : "bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-slate-200/80 dark:border-slate-800/80 text-slate-800 dark:text-slate-100 rounded-tl-sm shadow-sm"
                      }`}
                    >
                      <FormattedMarkdown content={msg.content} isUser={isUser} />

                      {/* Ready Badge if assistant flagged readiness */}
                      {!isUser && msg.is_ready && (
                        <div className="mt-3 pt-2.5 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>{t.intake_ready_signal || (lang === "vi" ? "AI đã định hình đầy đủ cốt truyện!" : "AI has structured the narrative!")}</span>
                          </div>
                          <button
                            onClick={triggerFinalize}
                            className="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm flex items-center gap-1 active:scale-95 transition-all"
                          >
                            <span>{t.intake_start_writing_now || (lang === "vi" ? "Viết ngay" : "Write now")}</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Typing State */}
              {loading && (
                <div className="flex items-start gap-3.5 animate-fadeIn">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                    <Sparkles className="w-4 h-4 animate-pulse" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-slate-200/80 dark:border-slate-800/80 flex items-center gap-2 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.4s]" />
                    <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">
                      {lang === "vi" ? "NarrAI đang suy nghĩ..." : "NarrAI is formulating..."}
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

        </div>
      </div>

      {/* Floating Bottom Dock (Layer 1 Semantic DOM with Layer 2 Morphicon) */}
      <div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 bg-gradient-to-t from-slate-50/95 via-slate-50/80 to-transparent dark:from-slate-950/95 dark:via-slate-950/80 dark:to-transparent z-20 pointer-events-none">
        <div className="max-w-3xl mx-auto w-full pointer-events-auto">

          {/* Quick Guidance & Readiness Notification Banner if ready */}
          {isReady && messages.length > 0 && !isFinalizing && (
            <div className="mb-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 dark:bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-between text-xs text-emerald-700 dark:text-emerald-300 animate-fadeIn backdrop-blur-md">
              <div className="flex items-center gap-1.5 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
                <span>
                  {lang === "vi"
                    ? "Cốt truyện đã đủ độ chín! Bạn có thể bấm 'Bắt đầu viết truyện ngay' bất cứ lúc nào."
                    : "Plot premise is well formed! You can click 'Start writing story now' at any time."}
                </span>
              </div>
              <button
                onClick={triggerFinalize}
                className="font-bold underline hover:text-emerald-900 dark:hover:text-emerald-100 flex items-center gap-0.5 ml-2 shrink-0"
              >
                <span>{t.intake_jump_to_manuscript || (lang === "vi" ? "Chấp bút ngay ➔" : "Draft now ➔")}</span>
              </button>
            </div>
          )}

          {/* Glassmorphic Capsule */}
          <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800/90 rounded-2xl shadow-2xl p-2.5 sm:p-3 flex flex-col gap-2.5 transition-all">

            {/* Controls Bar: Model Tier Selector & Story Length Pill */}
            <div className="flex items-center justify-between gap-2 flex-wrap border-b border-slate-200/60 dark:border-slate-800/60 pb-2 px-1">
              {/* Integrated ModelSelectorMorphicon (Layer 2 SVG) */}
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 hidden md:inline">
                  {t.intake_model_tier_label || (lang === "vi" ? "Mô hình:" : "Model:")}
                </span>
                <ModelSelectorMorphicon
                  selectedTier={modelTier}
                  onSelectTier={setModelTier}
                  lang={lang}
                  className="scale-90 sm:scale-95 origin-left"
                />
              </div>

              {/* Story Length Pill Selector */}
              <div className="flex items-center gap-1 bg-slate-100/90 dark:bg-slate-800/90 p-1 rounded-xl border border-slate-200 dark:border-slate-700/80">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 px-1.5 hidden lg:inline">
                  {t.intake_length_label || (lang === "vi" ? "Độ dài:" : "Length:")}
                </span>
                {(["short", "medium", "long"] as StoryLength[]).map((len) => {
                  const isSelected = storyLength === len;
                  const labelMap = {
                    short: t.intake_len_short || (lang === "vi" ? "Ngắn" : "Short"),
                    medium: t.intake_len_medium || (lang === "vi" ? "Vừa" : "Medium"),
                    long: t.intake_len_long || (lang === "vi" ? "Tiểu thuyết" : "Novel"),
                  };
                  return (
                    <button
                      key={len}
                      type="button"
                      onClick={() => setStoryLength(len)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                        isSelected
                          ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm font-bold"
                          : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                      }`}
                    >
                      {labelMap[len]}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Input Row: Auto-expanding Textarea & Send Button */}
            <div className="flex items-end gap-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleTextareaInput}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={loading || isFinalizing}
                placeholder={
                  t.intake_input_placeholder || (lang === "vi"
                    ? "Nhập ý tưởng câu chuyện của bạn... (Enter để gửi, Shift+Enter xuống dòng)"
                    : "Type your story concept... (Enter to send, Shift+Enter for newline)")
                }
                className="flex-1 max-h-40 min-h-[44px] bg-transparent resize-none px-3 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 outline-none leading-relaxed"
              />

              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading || isFinalizing}
                className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white flex items-center justify-center shrink-0 transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-md active:scale-95"
                title={t.intake_send || (lang === "vi" ? "Gửi ý tưởng" : "Send idea")}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Bottom Guardrail Footer */}
          <div className="flex items-center justify-between mt-2 px-2 text-[11px] text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <span className="truncate">
                {t.intake_guardrail_notice || (lang === "vi"
                  ? "Tự do hư cấu cá nhân • Tôn trọng lịch sử Dân tộc • Bảo mật tác quyền"
                  : "Creative freedom • Historical authenticity • IP copyright protected")}
              </span>
            </div>

            {messages.length > 0 && (
              <button
                onClick={triggerFinalize}
                disabled={isFinalizing}
                className="font-bold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 shrink-0 ml-2"
              >
                <span>{t.intake_start_writing_now || (lang === "vi" ? "Bắt đầu viết" : "Start writing")}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default UnifiedIntakeChat;
