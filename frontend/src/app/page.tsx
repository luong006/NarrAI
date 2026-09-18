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

    const token = storage.getToken();
    if (token) {
      api.me()
        .then((res) => {
          if (res.status === "success" && res.username) {
            setUser({ username: res.username });
            setView("workspace");
          }
        })
        .catch(() => {
          storage.removeToken();
        });
    }
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
  };

  // Phase 1 -> Phase 2
  const handlePhase1Continue = async (prompt: string, genres: string[], themes: string[]) => {
    setInitialPrompt(prompt);
    setLoading(true);
    try {
      const fullContext = `Thể loại: ${genres.join(", ")}; Chủ đề: ${themes.join(", ")}; Ý tưởng: ${prompt}`;
      const res = await api.chatInterview(fullContext, []);
      if (res.status === "success") {
        setChatHistory([
          { role: "assistant", content: res.reply || res.questions?.join("\n\n") || "Hãy chia sẻ thêm về nhân vật chính của bạn." }
        ]);
        setSetupPhase(2);
      }
    } catch (e: any) {
      alert("Lỗi phỏng vấn AI: " + e.message);
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
      const res = await api.chatInterview(initialPrompt, updatedHistory, msg);
      if (res.status === "success") {
        setChatHistory([...updatedHistory, { role: "assistant", content: res.reply }]);
      }
    } catch (e: any) {
      alert("Lỗi: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // Phase 2 Skip / Finalize
  const handleSkipInterview = async () => {
    setLoading(true);
    try {
      const res = await api.refinePrompt(initialPrompt, chatHistory);
      if (res.status === "success") {
        setRefinedPrompt(res.refined_prompt || initialPrompt);
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

    await api.streamStory(
      "generate-story-stream",
      {
        refined_prompt: refinedPrompt || initialPrompt,
        story_length: length,
        creativity: creativity,
        pacing: pacing,
      },
      (chunk) => {
        setStoryContent((prev) => prev + chunk);
      },
      (full) => {
        setStreaming(false);
        setLoading(false);
        // Refresh session to get storyId
        api.getStories().then((res) => {
          if (res.status === "success" && res.stories && res.stories.length > 0) {
            setStoryId(res.stories[0].id);
          }
        });
      },
      (err) => {
        setStreaming(false);
        setLoading(false);
        alert("Lỗi chấp bút: " + err.message);
      }
    );
  };

  // Quick Action on Selected Text
  const handleQuickAction = async (action: "rewrite" | "expand" | "shorten") => {
    if (!selectedText) return;
    const instructions = {
      rewrite: "Hãy viết lại đoạn này cho hay, trau chuốt và giàu cảm xúc hơn.",
      expand: "Hãy mở rộng đoạn này, bổ sung miêu tả chi tiết bối cảnh và tâm trạng.",
      shorten: "Hãy tóm lược đoạn này cho ngắn gọn, nhịp độ nhanh hơn.",
    };
    setLoading(true);
    try {
      const res = await api.editText(storyContent, selectedText, instructions[action]);
      if (res.status === "success") {
        setProposedText(res.new_text);
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
      const res = await api.editText(storyContent, selectedText, instruction);
      if (res.status === "success") {
        setProposedText(res.new_text);
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

  // Continue Chapter (Streaming)
  const handleContinueChapter = async () => {
    if (streaming || loading) return;
    setStreaming(true);
    setLoading(true);

    await api.streamStory(
      "generate-chapter",
      {
        story_id: storyId,
        session_id: sessionId,
        story_text: storyContent,
      },
      (chunk) => {
        setStoryContent((prev) => prev + chunk);
      },
      () => {
        setStreaming(false);
        setLoading(false);
      },
      (err) => {
        setStreaming(false);
        setLoading(false);
        alert("Lỗi viết tiếp: " + err.message);
      }
    );
  };

  // End Story (Streaming)
  const handleEndStory = async () => {
    if (streaming || loading) return;
    setStreaming(true);
    setLoading(true);

    await api.streamStory(
      "end-story",
      {
        story_id: storyId,
        session_id: sessionId,
        story_text: storyContent,
      },
      (chunk) => {
        setStoryContent((prev) => prev + chunk);
      },
      () => {
        setStreaming(false);
        setLoading(false);
        alert(lang === "vi" ? "Truyện đã kết thúc trọn vẹn!" : "Story concluded!");
      },
      (err) => {
        setStreaming(false);
        setLoading(false);
        alert("Lỗi kết thúc: " + err.message);
      }
    );
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
    setSessionId(story.session_id);
    setStoryContent(story.story_content);
    setActiveTab("editor");
    setComicPanels([]);
    setComicId(null);
  };

  // Adapt to Comic
  const handleAdaptToComic = async () => {
    if (!storyContent || storyContent.length < 50) {
      alert(lang === "vi" ? "Bản thảo cần ít nhất 50 từ để chuyển thể truyện tranh." : "Manuscript needs at least 50 words to adapt.");
      return;
    }

    setComicLoading(true);
    setActiveTab("comic");

    try {
      const res = await api.generateComic(storyId || 1, storyContent);
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
        }}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === "setup" && (
          <div className="flex-1 overflow-y-auto">
            {setupPhase === 1 && (
              <Phase1Idea lang={lang} onContinue={handlePhase1Continue} />
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
          <>
            <StoryEditor
              content={storyContent}
              onContentChange={setStoryContent}
              lang={lang}
              onAdaptToComic={handleAdaptToComic}
              onDownload={handleDownload}
              onSelectText={setSelectedText}
              onQuickAction={handleQuickAction}
            />
            <AICopilotPanel
              lang={lang}
              selectedText={selectedText}
              proposedText={proposedText}
              onAcceptEdit={handleAcceptEdit}
              onRejectEdit={handleRejectEdit}
              onSubmitCustomInstruction={handleSubmitCustomInstruction}
              onContinueChapter={handleContinueChapter}
              onEndStory={handleEndStory}
              loading={loading}
              streaming={streaming}
            />
          </>
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
