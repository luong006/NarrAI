"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";
import { Language } from "@/lib/i18n";
import { StoryDetail, ComicPanel, ChatMessage, StoryLength, CreativityLevel, PacingLevel } from "@/lib/types";

import { LandingView } from "@/components/landing/LandingView";
import { Sidebar } from "@/components/layout/Sidebar";
import { AuthModal } from "@/components/modals/AuthModal";
import { HistoryModal } from "@/components/modals/HistoryModal";

import { Phase1Idea } from "@/components/setup/Phase1Idea";
import { Phase2Interview } from "@/components/setup/Phase2Interview";
import { Phase3Controls } from "@/components/setup/Phase3Controls";

import { StoryEditor } from "@/components/editor/StoryEditor";
import { AICopilotPanel } from "@/components/editor/AICopilotPanel";
import { ComicViewer } from "@/components/comic/ComicViewer";

/**
 * Recursively unwraps stringified JSON envelopes, extracts clean story prose,
 * strips markdown fences, and unconditionally converts escaped characters (\n, \", etc.).
 */
function unwrapStoryProseFrontend(content: string): string {
  if (!content) return "";
  let current = String(content).trim();

  const candidateKeys = [
    "updated_story_content",
    "story_content",
    "story",
    "content",
    "new_story_content",
    "revised_text",
    "text",
  ];

  for (let pass = 0; pass < 10; pass++) {
    const prev = current;

    // 1. Strip markdown code fences (```json ... ``` or ```markdown ... ``` or ``` ... ```)
    current = current.replace(/^```(?:json|markdown)?\s*\n?/i, "").replace(/\n?```\s*$/i, "").trim();

    // If enclosed in a code block embedded within text
    const fenceMatch = current.match(/```(?:json|markdown)?\s*\n?([\s\S]*?)\n?```/i);
    if (fenceMatch && fenceMatch[1]) {
      const inner = fenceMatch[1].trim();
      if (candidateKeys.some((k) => inner.includes(`"${k}"`)) || inner.includes('"action_params"')) {
        current = inner;
      }
    }

    // 2. Check if current looks like JSON
    const isJsonLike =
      (current.startsWith("{") && current.endsWith("}")) ||
      (current.startsWith('"{') && current.endsWith('}"')) ||
      candidateKeys.some((k) => current.includes(`"${k}"`)) ||
      current.includes('"action_params"');

    if (isJsonLike) {
      let extracted: string | null = null;
      try {
        const parsed = JSON.parse(current);
        if (typeof parsed === "string") {
          extracted = parsed;
        } else if (typeof parsed === "object" && parsed !== null) {
          // Check candidate keys at root
          for (const k of candidateKeys) {
            const val = (parsed as Record<string, unknown>)[k];
            if (val && (typeof val === "string" || typeof val === "object")) {
              extracted = typeof val === "string" ? val : JSON.stringify(val);
              break;
            }
          }
          // If not at root, check inside action_params
          if (!extracted && parsed.action_params && typeof parsed.action_params === "object") {
            const sub = parsed.action_params as Record<string, unknown>;
            for (const k of candidateKeys) {
              const val = sub[k];
              if (val && (typeof val === "string" || typeof val === "object")) {
                extracted = typeof val === "string" ? val : JSON.stringify(val);
                break;
              }
            }
          }
          // Fallback: check any key with string value > 30 characters
          if (!extracted) {
            for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
              if (
                typeof v === "string" &&
                v.length > 30 &&
                !["thought", "action", "message", "summary_of_changes"].includes(k)
              ) {
                extracted = v;
                break;
              }
            }
          }
        }
      } catch {
        // Robust regex fallback: handle dialogue quotes and truncated stream without premature cutoff
        const match = current.match(
          /"updated_story_content"\s*:\s*"([\s\S]*?)(?:",\s*"(?:summary_of_changes|message|action|instruction)"\s*:|"\s*\}[\}\]]?\s*|"?\s*$)/
        );
        if (match && match[1]) {
          extracted = match[1];
        } else {
          for (const k of candidateKeys) {
            const m = current.match(
              new RegExp(`"${k}"\\s*:\\s*"([\\s\\S]*?)(?:",\\s*"[a-zA-Z0-9_]+"\\s*:|\\"\\s*\\}[\\}\\]]?\\s*|"?\\s*$)`)
            );
            if (m && m[1]) {
              extracted = m[1];
              break;
            }
          }
        }
      }

      if (extracted !== null) {
        current = extracted.trim();
      }
    }

    // 3. Unconditionally unescape escaped sequences
    if (current.includes("\\n") || current.includes("\\r") || current.includes('\\"') || current.includes("\\\\")) {
      current = current
        .replace(/\\r\\n/g, "\n")
        .replace(/\\n/g, "\n")
        .replace(/\\r/g, "")
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, "\\");
    }

    if (current === prev) {
      break;
    }
  }

  // Normalize newlines
  current = current.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  current = current.replace(/\n{3,}/g, "\n\n");

  return current.trim();
}

export default function WorkspacePage() {
  // Global State
  const [user, setUser] = useState<{ username: string } | null>(null);
  const [lang, setLang] = useState<Language>("vi");
  const [view, setView] = useState<"landing" | "workspace">("landing");
  const [activeTab, setActiveTab] = useState<"setup" | "editor" | "comic">("setup");
  const [setupPhase, setSetupPhase] = useState<1 | 2 | 3>(1);

  // Modals
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Setup Flow State
  const [initialPrompt, setInitialPrompt] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [refinedPrompt, setRefinedPrompt] = useState("");

  // Editor State
  const [storyId, setStoryId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [storyContent, setStoryContent] = useState("");
  const [selectedText, setSelectedText] = useState("");
  const [proposedText, setProposedText] = useState<string | null>(null);
  const [copilotMessages, setCopilotMessages] = useState<ChatMessage[]>([]);
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const [manuscriptNotice, setManuscriptNotice] = useState<string | null>(null);

  // Comic State
  const [comicId, setComicId] = useState<number | null>(null);
  const [comicPanels, setComicPanels] = useState<ComicPanel[]>([]);
  const [comicHasMore, setComicHasMore] = useState(false);

  // Loading States
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [comicLoading, setComicLoading] = useState(false);

  // Initialize Auth & Language
  useEffect(() => {
    const savedLang = storage.getLanguage();
    setLang(savedLang);

    const initAuth = async () => {
      const token = storage.getToken();
      if (!token) return;

      try {
        const res = await api.getMe();
        if (res.status === "success" && res.username) {
          setUser({ username: res.username });
          setView("workspace");
        } else {
          storage.removeToken();
        }
      } catch (err) {
        console.error("Auth check error:", err);
      }
    };

    initAuth();
  }, []);

  const handleLanguageChange = (newLang: Language) => {
    setLang(newLang);
    storage.setLanguage(newLang);
  };

  const handleLogout = () => {
    storage.removeToken();
    setUser(null);
    setView("landing");
    setActiveTab("setup");
    setSetupPhase(1);
    setStoryContent("");
    setCopilotMessages([]);
  };

  // Phase 1 -> Phase 2 (Immediately switch screen & send user prompt to AI)
  const handlePhase1Continue = async (combinedPrompt: string, genres: string[], themes: string[]) => {
    setInitialPrompt(combinedPrompt);
    const initialUserMsg: ChatMessage = { role: "user", content: combinedPrompt };
    setChatHistory([initialUserMsg]);
    setSetupPhase(2);
    setLoading(true);

    try {
      const res = await api.chatInterview([initialUserMsg]);
      if (res.status === "success" && res.message) {
        setChatHistory([
          initialUserMsg,
          { role: "assistant", content: res.message }
        ]);
        if (res.is_ready) {
          handleSkipInterview();
        }
      } else {
        setChatHistory([
          initialUserMsg,
          {
            role: "assistant",
            content: lang === "vi"
              ? "Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính và bối cảnh câu chuyện nhé."
              : "Fascinating concept! Could you tell me more about the main protagonist and setting?"
          }
        ]);
      }
    } catch (e: any) {
      console.error(e);
      setChatHistory([
        initialUserMsg,
        {
          role: "assistant",
          content: lang === "vi"
            ? "Đang kết nối lại với AI. Bạn có thể gõ câu trả lời bên dưới hoặc bấm 'Bỏ qua hỏi đáp' để tiếp tục."
            : "Reconnecting to AI. You can reply below or skip to proceed."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Phase 2 Chat
  const handleSendMessage = async (msg: string) => {
    const updatedHistory: ChatMessage[] = [...chatHistory, { role: "user", content: msg }];
    setChatHistory(updatedHistory);
    setLoading(true);
    try {
      const res = await api.chatInterview(updatedHistory);
      if (res.status === "success" && res.message) {
        setChatHistory([...updatedHistory, { role: "assistant", content: res.message }]);
        if (res.is_ready) {
          handleSkipInterview();
        }
      } else {
        alert("Lỗi từ AI: " + (res.message || "Vui lòng thử lại"));
      }
    } catch (e: any) {
      alert("Lỗi kết nối: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // Phase 2 Skip / Finalize
  const handleSkipInterview = async () => {
    setLoading(true);
    try {
      const res = await api.refinePrompt(chatHistory);
      if (res.status === "success" && res.refined_prompt) {
        setRefinedPrompt(res.refined_prompt);
        setSetupPhase(3);
      } else {
        setRefinedPrompt(initialPrompt);
        setSetupPhase(3);
      }
    } catch (e: any) {
      setRefinedPrompt(initialPrompt);
      setSetupPhase(3);
    } finally {
      setLoading(false);
    }
  };

  // Phase 3 -> Start Writing
  const handleStartWriting = async (length: StoryLength, creativity: CreativityLevel, pacing: PacingLevel) => {
    setLoading(true);
    setStreaming(true);
    setActiveTab("editor");
    setStoryContent("");
    setStoryId(null);
    setSessionId(null);

    let extraPrompt = "";
    if (creativity === 1) extraPrompt += " Hãy giữ cốt truyện cực kỳ logic, thực tế.";
    else if (creativity === 3) extraPrompt += " Hãy bùng nổ sáng tạo, thêm những tình tiết bất ngờ (plot twist) điên rồ.";

    if (pacing === 1) extraPrompt += " Nhịp độ truyện chậm rãi, miêu tả nội tâm và bối cảnh thật chi tiết.";
    else if (pacing === 3) extraPrompt += " Nhịp độ truyện nhanh, dồn dập, tập trung vào hành động và hội thoại kịch tính.";

    const finalPrompt = (refinedPrompt || initialPrompt) + (extraPrompt ? "\n" + extraPrompt : "");
    const endpoint = length === "long" ? "init-story" : "generate-story";

    await api.streamStory(
      endpoint,
      {
        refined_prompt: finalPrompt,
        story_length: length,
      },
      (chunk, cleanAccumulated) => {
        setStoryContent(cleanAccumulated);
      },
      (result) => {
        setStreaming(false);
        setLoading(false);
        setStoryContent(result.cleanText);
        if (result.sessionId) setSessionId(result.sessionId);
        if (result.storyId) setStoryId(result.storyId);
        if (result.error) {
          alert("Thông báo hệ thống: " + result.error);
        } else {
          setCopilotMessages([
            {
              role: "assistant",
              content: length === "long"
                ? "Chương 1 đã hoàn tất! Bạn có thể ra lệnh cho Copilot bên dưới, ấn 'Viết tiếp chương mới' hoặc 'Chuyển thể Truyện tranh'."
                : "Bản thảo đã hoàn tất! Bạn có thể bôi đen văn bản để sửa nhanh, ra lệnh cho Copilot hoặc chuyển thể sang truyện tranh."
            }
          ]);
        }
      },
      (err) => {
        setStreaming(false);
        setLoading(false);
        alert("Lỗi chấp bút: " + err.message);
      }
    );
  };

  // Quick Action on Selected Text (Rewrite, Expand, Shorten)
  const handleQuickAction = async (action: "rewrite" | "expand" | "shorten", targetText?: string) => {
    const textToEdit = targetText || selectedText;
    if (!textToEdit || !textToEdit.trim()) return;
    const instructions = {
      rewrite: lang === "vi" ? "Hãy viết lại đoạn này cho hay và văn vẻ hơn." : "Rewrite this beautifully.",
      expand: lang === "vi" ? "Hãy mở rộng đoạn này, miêu tả chi tiết bối cảnh và cảm xúc." : "Expand this with more descriptive details.",
      shorten: lang === "vi" ? "Hãy tóm lược đoạn này cho súc tích, nhịp độ nhanh hơn." : "Shorten this for faster pacing.",
    };
    setLoading(true);
    try {
      const res = await api.editText(textToEdit, instructions[action]);
      if (res.status === "success" && res.revised_text) {
        const revised = res.revised_text.trim();
        // Push previous state to undo stack
        setUndoStack((prev) => [...prev, storyContent]);
        // Directly update editor content so user sees immediate results
        setStoryContent((prev) => prev.replace(textToEdit, revised));
        setProposedText(revised);

        const actionLabels = {
          rewrite: lang === "vi" ? "viết lại" : "rewritten",
          expand: lang === "vi" ? "mở rộng" : "expanded",
          shorten: lang === "vi" ? "rút gọn" : "shortened",
        };
        const noticeMsg = lang === "vi"
          ? `✨ Đã ${actionLabels[action]} đoạn văn thành công! Bạn có thể nhấn "Hoàn tác" ở góc trên nếu muốn quay lại.`
          : `✨ Successfully ${actionLabels[action]} selected text! Click "Undo" above to revert.`;
        setManuscriptNotice(noticeMsg);
        setTimeout(() => setManuscriptNotice(null), 8000);
      } else {
        alert("Không thể sửa: " + (res.message || "Lỗi xử lý"));
      }
    } catch (e: any) {
      alert("Lỗi sửa văn bản: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitCustomInstruction = async (instruction: string) => {
    if (!selectedText) return;
    setLoading(true);
    try {
      const res = await api.editText(selectedText, instruction);
      if (res.status === "success" && res.revised_text) {
        setProposedText(res.revised_text);
      } else {
        alert("Không thể sửa: " + (res.message || "Lỗi xử lý"));
      }
    } catch (e: any) {
      alert("Lỗi: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptEdit = () => {
    if (!proposedText || !selectedText) return;
    setStoryContent((prev) => prev.replace(selectedText, proposedText));
    setProposedText(null);
    setSelectedText("");
  };

  const handleRejectEdit = () => {
    setProposedText(null);
    setSelectedText("");
  };

  const handleUndoEdit = () => {
    if (undoStack.length === 0) return;
    const previous = undoStack[undoStack.length - 1];
    setUndoStack((prev) => prev.slice(0, -1));
    setStoryContent(previous);
    setManuscriptNotice(lang === "vi" ? "Đã hoàn tác thay đổi gần nhất của bản thảo!" : "Reverted the latest manuscript change!");
    setTimeout(() => setManuscriptNotice(null), 4000);
  };

  // Interactive Copilot Live Chat & Direct Story Modification
  const handleSendCopilotMessage = async (msg: string) => {
    const userMsg: ChatMessage = { role: "user", content: msg };
    setCopilotMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const storyContext = storyContent.slice(0, 15000);
      const res = await api.sendCopilotEvent(
        sessionId,
        storyId,
        "USER_CHAT",
        JSON.stringify({
          user_message: msg,
          current_story: storyContext,
        })
      );

      if (res.status === "success" && res.data) {
        const action = res.data.action;
        const params = res.data.action_params || {};

        if (action === "edit_story_direct") {
          let newContent = params.updated_story_content || (res.data as any).updated_story_content;
          if (newContent) {
            newContent = unwrapStoryProseFrontend(newContent);
            if (!newContent.startsWith("{") && !newContent.includes('"updated_story_content"')) {
              setUndoStack((prev) => [...prev, storyContent]);
              setStoryContent(newContent);
              const notice = params.summary_of_changes || (lang === "vi" ? "Bản thảo đã được AI Co-pilot cập nhật trực tiếp!" : "Manuscript directly updated by AI Co-pilot!");
              setManuscriptNotice(notice);
              setTimeout(() => setManuscriptNotice(null), 8000);
            }
          }
          const responseMsg = (params.message || (lang === "vi" ? "Tôi đã cập nhật trực tiếp vào bản thảo của bạn theo yêu cầu!" : "I directly updated your manuscript as requested!")) +
            (params.summary_of_changes ? `\n\n📝 Chi tiết thay đổi: ${params.summary_of_changes}` : "");
          setCopilotMessages((prev) => [
            ...prev,
            { role: "assistant", content: responseMsg }
          ]);
        } else if (action === "reply_user") {
          setCopilotMessages((prev) => [
            ...prev,
            { role: "assistant", content: params.message || "Đã xử lý." }
          ]);
        } else if (action === "command_writer") {
          if (params.message) {
            const pMsg = String(params.message);
            setCopilotMessages((prev) => [
              ...prev,
              { role: "assistant", content: pMsg }
            ]);
          }
          await handleContinueChapterWithInstruction(params.instruction || "");
        } else if (action === "reject_and_rewrite") {
          setCopilotMessages((prev) => [
            ...prev,
            { role: "assistant", content: "Đang yêu cầu viết lại: " + (params.critique || "") }
          ]);
          await handleContinueChapterWithInstruction(params.fix_instruction || params.instruction || params.critique || "");
        } else {
          setCopilotMessages((prev) => [
            ...prev,
            { role: "assistant", content: "Đã xử lý tác vụ: " + action }
          ]);
        }
      } else {
        // Fallback to /api/chat
        const chatRes = await api.chatCopilot(storyContext, msg, storyId || undefined);
        if (chatRes.chat_reply) {
          const replyText = String(chatRes.chat_reply);
          setCopilotMessages((prev) => [...prev, { role: "assistant", content: replyText }]);
        }
        if (chatRes.new_story_content) {
          const cleanNew = unwrapStoryProseFrontend(chatRes.new_story_content);
          setStoryContent((prev) => prev ? prev + "\n\n" + cleanNew : cleanNew);
        }
      }
    } catch (err: any) {
      setCopilotMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Lỗi kết nối Copilot: " + (err.message || "Không xác định") }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Continue Chapter (Streaming)
  const handleContinueChapterWithInstruction = async (userInstruction: string = "") => {
    if (streaming || loading) return;
    setStreaming(true);
    setLoading(true);

    if (sessionId) {
      let accumulatedChapter = "";
      await api.streamStory(
        "generate-chapter",
        {
          session_id: sessionId,
          user_instruction: userInstruction,
        },
        (chunk, cleanAccumulated) => {
          accumulatedChapter = cleanAccumulated;
        },
        (result) => {
          setStreaming(false);
          setLoading(false);
          if (result.error) {
            alert("Lỗi viết chương: " + result.error);
          } else {
            setStoryContent((prev) => prev + "\n\n" + result.cleanText);
            setCopilotMessages((prev) => [
              ...prev,
              { role: "assistant", content: "Đã viết xong chương mới! Bạn có thể tiếp tục ra lệnh hoặc kết thúc truyện." }
            ]);
          }
        },
        (err) => {
          setStreaming(false);
          setLoading(false);
          alert("Lỗi viết tiếp: " + err.message);
        }
      );
    } else {
      try {
        const res = await api.chatCopilot(
          storyContent,
          userInstruction || "Hãy viết tiếp chương tiếp theo. Tối thiểu 2000 từ. Kết thúc bằng tình tiết kịch tính.",
          storyId || undefined
        );
        setStreaming(false);
        setLoading(false);
        if (res.chat_reply) {
          setCopilotMessages((prev) => [...prev, { role: "assistant", content: res.chat_reply }]);
        }
        if (res.new_story_content) {
          const cleanNew = unwrapStoryProseFrontend(res.new_story_content);
          setStoryContent((prev) => prev ? prev + "\n\n" + cleanNew : cleanNew);
        }
      } catch (err: any) {
        setStreaming(false);
        setLoading(false);
        alert("Lỗi: " + err.message);
      }
    }
  };

  const handleContinueChapter = async () => {
    await handleContinueChapterWithInstruction("");
  };

  // End Story (Streaming)
  const handleEndStory = async () => {
    if (streaming || loading) return;
    if (!confirm(lang === "vi" ? "Bạn có chắc muốn kết thúc câu chuyện? AI sẽ chấp bút đoạn kết trọn vẹn." : "Are you sure you want to conclude the story?")) return;

    setStreaming(true);
    setLoading(true);

    if (sessionId) {
      await api.streamStory(
        "end-story",
        { session_id: sessionId },
        (chunk, cleanAccumulated) => {},
        (result) => {
          setStreaming(false);
          setLoading(false);
          if (result.error) {
            alert("Lỗi kết thúc: " + result.error);
          } else {
            setStoryContent((prev) => prev + "\n\n" + result.cleanText);
            setCopilotMessages((prev) => [
              ...prev,
              { role: "assistant", content: "Câu chuyện đã kết thúc trọn vẹn! Bạn có thể tải xuống bản thảo hoặc chuyển thể sang truyện tranh." }
            ]);
          }
        },
        (err) => {
          setStreaming(false);
          setLoading(false);
          alert("Lỗi kết thúc: " + err.message);
        }
      );
    } else {
      try {
        const res = await api.chatCopilot(
          storyContent,
          "Hãy viết ĐOẠN KẾT THÚC. Gói gọn tất cả tuyến truyện, giải quyết xung đột chính và mang lại dư ba sâu lắng.",
          storyId || undefined
        );
        setStreaming(false);
        setLoading(false);
        if (res.chat_reply) {
          setCopilotMessages((prev) => [...prev, { role: "assistant", content: res.chat_reply }]);
        }
        if (res.new_story_content) {
          const cleanNew = unwrapStoryProseFrontend(res.new_story_content);
          setStoryContent((prev) => prev ? prev + "\n\n" + cleanNew : cleanNew);
        }
      } catch (err: any) {
        setStreaming(false);
        setLoading(false);
        alert("Lỗi: " + err.message);
      }
    }
  };

  // Download Story
  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([storyContent], { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = `NarrAI_${Date.now()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  // Load Saved Story from History
  const handleSelectStory = (story: StoryDetail) => {
    setStoryId(story.id);
    setSessionId(story.session_id || null);
    setStoryContent(unwrapStoryProseFrontend(story.story_content || ""));
    setRefinedPrompt(story.refined_prompt || "");
    setActiveTab("editor");
    setComicPanels([]);
    setComicId(null);
    setCopilotMessages([
      {
        role: "assistant",
        content: `Đã tải bản thảo "${story.title || 'Đang viết'}". Bạn có thể tiếp tục chỉnh sửa, ra lệnh cho Copilot hoặc chuyển thể sang truyện tranh.`
      }
    ]);
  };

  // Adapt to Comic
  const handleAdaptToComic = async () => {
    if (!storyContent || storyContent.length < 10) {
      alert(lang === "vi" ? "Bản thảo cần có nội dung chữ để chuyển thể truyện tranh." : "Manuscript needs content to adapt.");
      return;
    }

    if (!storyId) {
      alert(lang === "vi" ? "Chưa có mã bản thảo trên máy chủ. Hãy chờ AI tạo xong bản thảo hoặc lưu truyện trước khi chuyển thể." : "Story ID not ready.");
      return;
    }

    setComicLoading(true);
    setActiveTab("comic");

    try {
      const res = await api.generateComic(storyId, storyContent.substring(0, 30000));
      if (res.status === "success" && res.panels) {
        setComicId(res.comic_id || null);
        setComicPanels(res.panels);
        setComicHasMore(!!res.has_more);
      } else {
        alert("Lỗi chuyển thể truyện tranh: " + (res.message || "Lỗi hệ thống"));
        setActiveTab("editor");
      }
    } catch (e: any) {
      alert("Lỗi: " + e.message);
      setActiveTab("editor");
    } finally {
      setComicLoading(false);
    }
  };

  // Continue Comic
  const handleContinueComic = async () => {
    if (!comicId) return;
    setComicLoading(true);
    try {
      const res = await api.continueComic(comicId, storyContent);
      if (res.no_more_text) {
        alert(lang === "vi" ? "Chưa có thêm nội dung chữ mới để vẽ tiếp tranh!" : "No new text written yet to continue comic serialization!");
        setComicHasMore(false);
      } else if (res.status === "success" && res.panels) {
        setComicPanels((prev) => [...prev, ...(res.panels || [])]);
        setComicHasMore(!!res.has_more);
      }
    } catch (e: any) {
      alert("Lỗi: " + e.message);
    } finally {
      setComicLoading(false);
    }
  };

  // If on landing view
  if (view === "landing") {
    return (
      <>
        <LandingView
          lang={lang}
          onLanguageChange={handleLanguageChange}
          onOpenAuth={() => setIsAuthOpen(true)}
        />
        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onSuccess={(u) => {
            setUser({ username: u });
            setView("workspace");
          }}
          lang={lang}
        />
      </>
    );
  }

  // If on workspace view
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white">
      {/* Left Sidebar */}
      <Sidebar
        username={user?.username || ""}
        lang={lang}
        onLanguageChange={handleLanguageChange}
        onNewStory={() => {
          setActiveTab("setup");
          setSetupPhase(1);
          setStoryContent("");
          setComicPanels([]);
          setCopilotMessages([]);
        }}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === "setup" && (
          <div className="flex-1 overflow-y-auto">
            {setupPhase === 1 && (
              <Phase1Idea
                lang={lang}
                onContinue={handlePhase1Continue}
                loading={loading}
              />
            )}
            {setupPhase === 2 && (
              <Phase2Interview
                lang={lang}
                history={chatHistory}
                onSendMessage={handleSendMessage}
                onSkip={handleSkipInterview}
                loading={loading}
              />
            )}
            {setupPhase === 3 && (
              <Phase3Controls
                lang={lang}
                onStartWriting={handleStartWriting}
                loading={loading}
              />
            )}
          </div>
        )}

        {activeTab === "editor" && (
          <div className="flex-1 flex flex-col h-full overflow-hidden">
            {manuscriptNotice && (
              <div className="bg-emerald-600 dark:bg-emerald-700 text-white px-4 py-2 flex items-center justify-between shadow text-xs font-medium shrink-0 animate-fadeIn">
                <div className="flex items-center gap-2">
                  <span className="text-sm">✨</span>
                  <span>{manuscriptNotice}</span>
                </div>
                {undoStack.length > 0 && (
                  <button
                    onClick={handleUndoEdit}
                    className="ml-4 font-bold bg-white/20 hover:bg-white/35 px-2.5 py-0.5 rounded transition-colors text-white"
                  >
                    {lang === "vi" ? "Hoàn tác (Undo)" : "Undo"}
                  </button>
                )}
              </div>
            )}
            <div className="flex-1 flex overflow-hidden">
              <StoryEditor
                content={storyContent}
                onContentChange={setStoryContent}
                lang={lang}
                onAdaptToComic={handleAdaptToComic}
                onDownload={handleDownload}
                onSelectText={setSelectedText}
                onQuickAction={handleQuickAction}
                onOpenCustomAI={(txt) => setSelectedText(txt)}
              />
              <AICopilotPanel
                lang={lang}
                selectedText={selectedText}
                proposedText={proposedText}
                copilotMessages={copilotMessages}
                onAcceptEdit={handleAcceptEdit}
                onRejectEdit={handleRejectEdit}
                onSubmitCustomInstruction={handleSubmitCustomInstruction}
                onSendCopilotMessage={handleSendCopilotMessage}
                onContinueChapter={handleContinueChapter}
                onEndStory={handleEndStory}
                loading={loading}
                streaming={streaming}
                onUndo={handleUndoEdit}
                canUndo={undoStack.length > 0}
              />
            </div>
          </div>
        )}

        {activeTab === "comic" && (
          <ComicViewer
            panels={comicPanels}
            hasMore={comicHasMore}
            lang={lang}
            onBackToEditor={() => setActiveTab("editor")}
            onContinueComic={handleContinueComic}
            loadingMore={comicLoading}
          />
        )}
      </main>

      {/* Modals */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(u) => setUser({ username: u })}
        lang={lang}
      />

      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectStory={handleSelectStory}
        lang={lang}
      />
    </div>
  );
}
