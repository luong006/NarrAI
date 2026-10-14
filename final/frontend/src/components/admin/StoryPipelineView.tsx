"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { Language, translations } from "@/lib/i18n";
import {
  PipelineStoryItem,
  PipelineOverview,
  PipelineStoryDetail,
  PipelinePullRequest,
  PipelineLogEntry,
  PipelineValidationResult,
  PipelineStatus
} from "@/lib/types";

interface Props {
  lang: Language;
  onLoadStoryToEditor?: (content: string, title?: string, id?: number | null) => void;
  onAdaptStoryToComic?: (content: string, title?: string, id?: number | null) => void;
}

export function StoryPipelineView({ lang, onLoadStoryToEditor, onAdaptStoryToComic }: Props) {
  const { toast } = useToast();
  const t = translations[lang];

  // State
  const [loading, setLoading] = useState(true);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [isBatchRunning, setIsBatchRunning] = useState(false);

  // Main navigation: "library" (Story collection) vs "pipeline" (Admin pipeline tools)
  const [viewMode, setViewMode] = useState<"library" | "pipeline">("library");

  // Category Filter for Stories: "all" | "fairy" | "history"
  const [categoryFilter, setCategoryFilter] = useState<"all" | "fairy" | "history">("all");

  // Sub-tab for Pipeline admin: "queue" | "prs" | "logs"
  const [pipelineSubTab, setPipelineSubTab] = useState<"queue" | "prs" | "logs">("queue");

  // Data
  const [publishedStories, setPublishedStories] = useState<PipelineStoryDetail[]>([]);
  const [overview, setOverview] = useState<PipelineOverview | null>(null);
  const [pullRequests, setPullRequests] = useState<PipelinePullRequest[]>([]);
  const [recentLogs, setRecentLogs] = useState<PipelineLogEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [readStoryModal, setReadStoryModal] = useState<PipelineStoryDetail | null>(null);
  const [previewStory, setPreviewStory] = useState<PipelineStoryDetail | null>(null);
  const [validationModalData, setValidationModalData] = useState<{ title: string; result: PipelineValidationResult } | null>(null);

  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newTopic, setNewTopic] = useState("Truyện Cổ Tích & Lịch Sử Việt Nam");
  const [newCategory, setNewCategory] = useState("Truyện Cổ Tích");
  const [newGenre, setNewGenre] = useState("Cổ tích, Dân gian");
  const [newSourceLangs, setNewSourceLangs] = useState("vi, en");
  const [batchRawText, setBatchRawText] = useState("");

  // Helper to categorize stories
  const isFairyTale = useCallback((item: { category?: string; topic?: string; genre?: string[] }) => {
    const text = `${item.category || ""} ${item.topic || ""} ${(item.genre || []).join(" ")}`.toLowerCase();
    return text.includes("cổ tích") || text.includes("truyền thuyết") || text.includes("thần thoại") || text.includes("dân gian") || text.includes("phép màu");
  }, []);

  const isHistorical = useCallback((item: { category?: string; topic?: string; genre?: string[] }) => {
    const text = `${item.category || ""} ${item.topic || ""} ${(item.genre || []).join(" ")}`.toLowerCase();
    return text.includes("lịch sử") || text.includes("kháng chiến") || text.includes("bạch đằng") || text.includes("anh hùng") || text.includes("chiến trận") || text.includes("quân sự") || text.includes("vua") || text.includes("hoàng đế") || text.includes("tuyên ngôn");
  }, []);

  // Fetch Data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [pubRes, queueRes, prRes, jobsRes] = await Promise.allSettled([
        api.getPublishedStories(),
        api.getPipelineQueue(),
        api.getPipelinePullRequests(),
        api.getPipelineJobs()
      ]);

      if (pubRes.status === "fulfilled" && pubRes.value.data) {
        setPublishedStories(pubRes.value.data);
      }
      if (queueRes.status === "fulfilled" && queueRes.value.data) {
        setOverview(queueRes.value.data);
      }
      if (prRes.status === "fulfilled" && prRes.value.data) {
        setPullRequests(prRes.value.data);
      }
      if (jobsRes.status === "fulfilled" && jobsRes.value.recentLogs) {
        setRecentLogs(jobsRes.value.recentLogs);
      }
    } catch (err: any) {
      toast.error(err?.message || "Không thể tải dữ liệu câu chuyện");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Actions
  const handleAddStory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      toast.warning("Vui lòng nhập tên đề bài / câu chuyện");
      return;
    }

    try {
      const genres = newGenre.split(",").map((s) => s.trim()).filter(Boolean);
      const sourceLanguages = newSourceLangs.split(",").map((s) => s.trim()).filter(Boolean);

      const res = await api.addPipelinePrompt({
        title: newTitle.trim(),
        topic: newTopic.trim(),
        category: newCategory.trim(),
        genre: genres.length ? genres : ["Cổ tích"],
        sourceLanguages: sourceLanguages.length ? sourceLanguages : ["vi", "en"]
      });

      toast.success(`Đã thêm '${res.data.title}' vào hàng đợi!`);
      setShowAddModal(false);
      setNewTitle("");
      loadData();
    } catch (err: any) {
      toast.error(err?.message || "Lỗi khi thêm câu chuyện");
    }
  };

  const handleBatchAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!batchRawText.trim()) return;

    try {
      let items: any[] = [];
      if (batchRawText.trim().startsWith("[") || batchRawText.trim().startsWith("{")) {
        const parsed = JSON.parse(batchRawText);
        items = Array.isArray(parsed) ? parsed : [parsed];
      } else {
        items = batchRawText
          .split("\n")
          .map((line) => line.trim())
          .filter((line) => line.length > 1)
          .map((title) => ({
            title,
            topic: "Kho tàng câu chuyện Việt Nam",
            category: newCategory || "Truyện Cổ Tích",
            genre: ["Cổ tích"],
            sourceLanguages: ["vi", "en"]
          }));
      }

      if (items.length === 0) {
        toast.warning("Không có đề bài hợp lệ nào được tìm thấy.");
        return;
      }

      const res = await api.batchAddPipelinePrompts(items);
      toast.success(`Đã thêm thành công ${res.data.addedCount} đề bài vào hàng đợi!`);
      setShowBatchModal(false);
      setBatchRawText("");
      loadData();
    } catch (err: any) {
      toast.error(`Lỗi nhập hàng loạt: ${err?.message}`);
    }
  };

  const handleRunSingle = async (storyId: string) => {
    try {
      setExecutingId(storyId);
      toast.info(`Bắt đầu biên soạn và kiểm định: ${storyId}...`);
      const res = await api.runPipeline({ story_id: storyId });
      if (res.status === "success") {
        toast.success(`Đã biên soạn thành công truyện '${storyId}'!`);
      } else {
        toast.info("Đã gửi yêu cầu biên soạn.");
      }
      loadData();
    } catch (err: any) {
      toast.error(err?.message || "Lỗi khi chạy pipeline");
    } finally {
      setExecutingId(null);
    }
  };

  const handleRunBatch = async () => {
    try {
      setIsBatchRunning(true);
      toast.info("Đang tự động chạy hàng loạt các đề bài chờ xử lý...");
      await api.runPipeline({ limit: 3 });
      toast.success("Đã hoàn tất xử lý hàng loạt.");
      loadData();
    } catch (err: any) {
      toast.error(err?.message || "Lỗi khi chạy batch pipeline");
    } finally {
      setIsBatchRunning(false);
    }
  };

  const handleOpenPreview = async (storyId: string) => {
    try {
      const res = await api.getPipelineStoryPreview(storyId);
      if (res.data) {
        setPreviewStory(res.data);
      }
    } catch (err: any) {
      toast.error(err?.message || "Chưa có bản thảo xem trước");
    }
  };

  const handleValidateStory = async (storyId: string) => {
    try {
      const res = await api.revalidatePipelineStory(storyId);
      setValidationModalData({
        title: res.storyId,
        result: res.validation
      });
    } catch (err: any) {
      toast.error(err?.message || "Lỗi khi kiểm tra chất lượng");
    }
  };

  const handleMergePR = async (prNumber: number, storyId: string) => {
    try {
      toast.info(`Đang gửi yêu cầu merge PR #${prNumber}...`);
      const res = await api.mergePipelinePullRequest(prNumber, storyId);
      toast.success(res.message || `Đã merge PR #${prNumber} thành công!`);
      loadData();
    } catch (err: any) {
      toast.error(err?.message || "Không thể merge PR tự động");
    }
  };

  // Render Status Badge
  const renderStatusBadge = (status: PipelineStatus) => {
    switch (status) {
      case "pending":
        return (
          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-neutral-900 text-neutral-400 border border-neutral-800">
            CHỜ XỬ LÝ
          </span>
        );
      case "researching":
      case "writing":
      case "validating":
        return (
          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-white text-black font-bold border border-white animate-pulse">
            ĐANG BIÊN SOẠN
          </span>
        );
      case "pr_created":
        return (
          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-neutral-900 text-white border border-neutral-700">
            CHỜ DUYỆT PR
          </span>
        );
      case "merged":
        return (
          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-white text-black font-bold">
            ĐÃ XUẤT BẢN
          </span>
        );
      case "failed":
        return (
          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-neutral-950 text-neutral-500 border border-neutral-800 line-through">
            THẤT BẠI
          </span>
        );
      default:
        return null;
    }
  };

  // Filtered Stories in Library
  const filteredPublishedStories = useMemo(() => {
    return publishedStories.filter((s) => {
      const matchesSearch =
        s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.summary && s.summary.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (s.topic && s.topic.toLowerCase().includes(searchQuery.toLowerCase()));

      let matchesCategory = true;
      if (categoryFilter === "fairy") {
        matchesCategory = isFairyTale(s);
      } else if (categoryFilter === "history") {
        matchesCategory = isHistorical(s);
      }

      return matchesSearch && matchesCategory;
    });
  }, [publishedStories, searchQuery, categoryFilter, isFairyTale, isHistorical]);

  // Filtered Pipeline Queue
  const stories = overview?.stories || [];
  const filteredQueueStories = useMemo(() => {
    return stories.filter((s) => {
      const matchesSearch =
        s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.topic && s.topic.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesStatus = statusFilter === "all" || s.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [stories, searchQuery, statusFilter]);

  // Counts
  const fairyCount = useMemo(() => publishedStories.filter(isFairyTale).length, [publishedStories, isFairyTale]);
  const historyCount = useMemo(() => publishedStories.filter(isHistorical).length, [publishedStories, isHistorical]);

  return (
    <div className="flex-1 min-h-screen bg-[#FAF7F2] text-neutral-900 p-4 lg:p-8 select-none font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-neutral-300/80">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neutral-900 text-white flex items-center justify-center font-mono font-bold text-base shadow-xs">
                C
              </div>
              <div>
                <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-neutral-950 uppercase font-mono">
                  {lang === "vi" ? "KHO TÀNG CÂU CHUYỆN" : "VIETNAMESE STORY LIBRARY"}
                </h1>
                <p className="text-xs lg:text-sm text-neutral-600 mt-0.5">
                  {lang === "vi"
                    ? "Tuyển tập Truyện Cổ Tích & Truyện Lịch Sử Việt Nam — Sẵn sàng đọc, chỉnh sửa và chuyển thể truyện tranh"
                    : "Vietnamese Folk Tales & Historical Legends — Ready for reading, editing and manga adaptation"}
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* View Mode Toggle: Library vs Pipeline Tools */}
            <div className="flex rounded-lg bg-neutral-200/50 border border-neutral-300/80 p-1">
              <button
                onClick={() => setViewMode("library")}
                className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-wider transition-colors ${
                  viewMode === "library"
                    ? "bg-white text-neutral-950 font-bold shadow-xs"
                    : "text-neutral-600 hover:text-neutral-950"
                }`}
              >
                {lang === "vi" ? "Thư viện câu chuyện" : "Story Library"}
              </button>
              <button
                onClick={() => setViewMode("pipeline")}
                className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-wider transition-colors ${
                  viewMode === "pipeline"
                    ? "bg-white text-neutral-950 font-bold shadow-xs"
                    : "text-neutral-600 hover:text-neutral-950"
                }`}
              >
                {lang === "vi" ? "Trạm biên soạn & PR" : "Compilation Station"}
              </button>
            </div>

            <button
              onClick={() => setShowAddModal(true)}
              className="px-3.5 py-2 bg-neutral-900 text-white hover:bg-neutral-800 text-xs font-bold rounded-lg border border-neutral-900 transition-colors uppercase tracking-wider font-mono shadow-xs"
            >
              + {lang === "vi" ? "Thêm truyện mới" : "Add Story"}
            </button>
            <button
              onClick={loadData}
              className="px-3 py-2 rounded-lg bg-white text-neutral-700 hover:bg-neutral-100 hover:text-neutral-950 border border-neutral-300/80 text-xs font-mono transition-colors shadow-xs"
              title="Làm mới"
            >
              {loading ? "..." : "Làm mới"}
            </button>
          </div>
        </div>

        {/* ============================================================== */}
        {/* VIEW MODE 1: THƯ VIỆN CÂU CHUYỆN (PRIMARY STORY LIBRARY)       */}
        {/* ============================================================== */}
        {viewMode === "library" && (
          <div className="space-y-6">
            {/* 2 Primary Category Switchers & Search Bar */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 rounded-xl bg-white border border-neutral-300/80 shadow-xs">
              {/* Category Segmented Tabs */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setCategoryFilter("all")}
                  className={`px-4 py-2 rounded-lg text-xs font-mono uppercase tracking-wider transition-all ${
                    categoryFilter === "all"
                      ? "bg-neutral-900 text-white font-bold border border-neutral-900 shadow-xs"
                      : "bg-[#FAF7F2] text-neutral-700 hover:text-neutral-950 border border-neutral-300/70 hover:bg-white"
                  }`}
                >
                  {lang === "vi" ? "Tất cả câu chuyện" : "All Stories"} ({publishedStories.length})
                </button>

                <button
                  onClick={() => setCategoryFilter("fairy")}
                  className={`px-4 py-2 rounded-lg text-xs font-mono uppercase tracking-wider transition-all flex items-center gap-2 ${
                    categoryFilter === "fairy"
                      ? "bg-neutral-900 text-white font-bold border border-neutral-900 shadow-xs"
                      : "bg-[#FAF7F2] text-neutral-700 hover:text-neutral-950 border border-neutral-300/70 hover:bg-white"
                  }`}
                >
                  <span>{lang === "vi" ? "Truyện Cổ Tích" : "Fairy Tales"}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                    categoryFilter === "fairy" ? "bg-white text-neutral-900 font-bold" : "bg-neutral-200 text-neutral-800"
                  }`}>
                    {fairyCount}
                  </span>
                </button>

                <button
                  onClick={() => setCategoryFilter("history")}
                  className={`px-4 py-2 rounded-lg text-xs font-mono uppercase tracking-wider transition-all flex items-center gap-2 ${
                    categoryFilter === "history"
                      ? "bg-neutral-900 text-white font-bold border border-neutral-900 shadow-xs"
                      : "bg-[#FAF7F2] text-neutral-700 hover:text-neutral-950 border border-neutral-300/70 hover:bg-white"
                  }`}
                >
                  <span>{lang === "vi" ? "Truyện Lịch Sử" : "Historical Stories"}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                    categoryFilter === "history" ? "bg-white text-neutral-900 font-bold" : "bg-neutral-200 text-neutral-800"
                  }`}>
                    {historyCount}
                  </span>
                </button>
              </div>

              {/* Search Box */}
              <div className="w-full lg:w-72">
                <input
                  type="text"
                  placeholder={lang === "vi" ? "Tìm theo tên truyện, nhân vật..." : "Search stories, characters..."}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg bg-white border border-neutral-300/80 text-xs text-neutral-900 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 transition-colors font-mono shadow-xs"
                />
              </div>
            </div>

            {/* Stories Grid */}
            {loading && publishedStories.length === 0 ? (
              <div className="p-12 text-center text-neutral-500 font-mono text-xs">
                Đang tải kho câu chuyện...
              </div>
            ) : filteredPublishedStories.length === 0 ? (
              <div className="p-12 text-center border border-neutral-300/80 rounded-2xl bg-white shadow-xs space-y-3">
                <p className="text-neutral-500 text-xs font-mono">
                  Không tìm thấy câu chuyện nào phù hợp với bộ lọc hiện tại.
                </p>
                <button
                  onClick={() => { setCategoryFilter("all"); setSearchQuery(""); }}
                  className="px-4 py-2 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg text-xs font-mono uppercase border border-neutral-900 transition-colors shadow-xs"
                >
                  Đặt lại bộ lọc
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {filteredPublishedStories.map((story) => {
                  const isFairy = isFairyTale(story);
                  return (
                    <div
                      key={story.id}
                      className="rounded-2xl bg-white border border-neutral-300/80 hover:border-neutral-900 transition-all p-5 flex flex-col justify-between space-y-4 group shadow-xs hover:shadow-md text-neutral-900"
                    >
                      {/* Top Meta */}
                      <div className="space-y-2.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase border font-bold ${
                            isFairy
                              ? "bg-neutral-100 text-neutral-800 border-neutral-300/80"
                              : "bg-neutral-900 text-white border-neutral-900"
                          }`}>
                            {isFairy ? "TRUYỆN CỔ TÍCH" : "LỊCH SỬ VIỆT NAM"}
                          </span>

                          <span className="text-[10px] font-mono text-neutral-500">
                            {story.panels?.length ? `${story.panels.length} KHUNG TRANH AI` : "VĂN XUÔI"}
                          </span>
                        </div>

                        {/* Story Title */}
                        <h3 className="text-base font-bold text-neutral-950 group-hover:underline transition-colors line-clamp-2">
                          {story.title}
                        </h3>

                        {/* Topic / Setting */}
                        {story.topic && (
                          <p className="text-[11px] font-mono text-neutral-600 truncate">
                            {story.topic}
                          </p>
                        )}

                        {/* Summary */}
                        <p className="text-xs text-neutral-700 leading-relaxed line-clamp-3">
                          {story.summary || (story.content ? story.content.substring(0, 160) + "..." : "")}
                        </p>

                        {/* Character Pills */}
                        {story.characters && story.characters.length > 0 && (
                          <div className="pt-1 flex flex-wrap gap-1.5">
                            {story.characters.slice(0, 3).map((c, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded bg-[#FAF7F2] border border-neutral-300/60 text-[10px] font-mono text-neutral-700"
                              >
                                {c.name}
                              </span>
                            ))}
                            {story.characters.length > 3 && (
                              <span className="text-[10px] font-mono text-neutral-500 self-center">
                                +{story.characters.length - 3}
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="pt-3 border-t border-neutral-200 space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => setReadStoryModal(story)}
                            className="px-3 py-2 bg-neutral-100 hover:bg-neutral-200 text-neutral-900 rounded-lg text-xs font-mono uppercase tracking-wider border border-neutral-300/80 transition-colors text-center"
                          >
                            Đọc truyện
                          </button>

                          <button
                            onClick={() => {
                              if (onAdaptStoryToComic) {
                                onAdaptStoryToComic(story.content || story.summary, story.title);
                              } else {
                                toast.info("Đang mở trình chuyển thể truyện tranh...");
                              }
                            }}
                            className="px-3 py-2 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg text-xs font-mono font-bold uppercase tracking-wider transition-colors text-center shadow-xs"
                          >
                            Tạo tranh AI
                          </button>
                        </div>

                        {onLoadStoryToEditor && (
                          <button
                            onClick={() => onLoadStoryToEditor(story.content || story.summary, story.title)}
                            className="w-full py-1.5 text-[11px] font-mono text-neutral-500 hover:text-neutral-950 uppercase tracking-wider text-center transition-colors"
                          >
                            [Mở trong Bản thảo để biên tập]
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW MODE 2: TRẠM BIÊN SOẠN & PR (ADMIN PIPELINE DASHBOARD)    */}
        {/* ============================================================== */}
        {viewMode === "pipeline" && (
          <div className="space-y-6">
            {/* Controls Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-neutral-950 border border-neutral-800">
              <div className="text-xs text-neutral-400 font-mono">
                Pipeline tự động: Wikipedia Research → LLM Biên soạn → Kiểm định 5 lớp → GitHub PR
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setShowBatchModal(true)}
                  className="px-3.5 py-1.5 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg text-xs font-mono uppercase border border-neutral-700 transition-colors"
                >
                  Nhập hàng loạt
                </button>
                <button
                  onClick={handleRunBatch}
                  disabled={isBatchRunning || loading}
                  className="px-4 py-1.5 bg-white text-black hover:bg-neutral-200 disabled:opacity-50 text-xs font-bold rounded-lg uppercase font-mono transition-colors shadow"
                >
                  {isBatchRunning ? "Đang chạy..." : "Chạy tự động (Batch)"}
                </button>
              </div>
            </div>

            {/* Overview Metric Cards (Black & White Minimalist) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800">
                <span className="text-[10px] font-mono tracking-wider uppercase text-neutral-400">Tổng đề bài</span>
                <div className="text-2xl font-bold font-mono mt-1 text-white">
                  {overview?.totalStories ?? 0}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800">
                <span className="text-[10px] font-mono tracking-wider uppercase text-neutral-400">Chờ xử lý</span>
                <div className="text-2xl font-bold font-mono mt-1 text-white">
                  {overview?.pending ?? 0}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800">
                <span className="text-[10px] font-mono tracking-wider uppercase text-neutral-400">Đang viết</span>
                <div className="text-2xl font-bold font-mono mt-1 text-white">
                  {overview?.inProgress ?? 0}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800">
                <span className="text-[10px] font-mono tracking-wider uppercase text-neutral-400">Lỗi kiểm định</span>
                <div className="text-2xl font-bold font-mono mt-1 text-neutral-400">
                  {overview?.failed ?? 0}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800">
                <span className="text-[10px] font-mono tracking-wider uppercase text-neutral-400">Chờ duyệt PR</span>
                <div className="text-2xl font-bold font-mono mt-1 text-white">
                  {overview?.prCreated ?? 0}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800">
                <span className="text-[10px] font-mono tracking-wider uppercase text-neutral-400">Đã Merge</span>
                <div className="text-2xl font-bold font-mono mt-1 text-white">
                  {overview?.merged ?? 0}
                </div>
              </div>
            </div>

            {/* Sub-tab Navigation (Pure Typography, No Icons) */}
            <div className="flex items-center justify-between border-b border-neutral-800 pt-2">
              <div className="flex gap-6">
                <button
                  onClick={() => setPipelineSubTab("queue")}
                  className={`pb-3 text-xs lg:text-sm tracking-wide uppercase transition-all font-mono ${
                    pipelineSubTab === "queue"
                      ? "border-b-2 border-white text-white font-bold"
                      : "border-b-2 border-transparent text-neutral-500 hover:text-white"
                  }`}
                >
                  Hàng đợi đề bài ({stories.length})
                </button>
                <button
                  onClick={() => setPipelineSubTab("prs")}
                  className={`pb-3 text-xs lg:text-sm tracking-wide uppercase transition-all font-mono ${
                    pipelineSubTab === "prs"
                      ? "border-b-2 border-white text-white font-bold"
                      : "border-b-2 border-transparent text-neutral-500 hover:text-white"
                  }`}
                >
                  Pull Requests & Duyệt ({pullRequests.length})
                </button>
                <button
                  onClick={() => setPipelineSubTab("logs")}
                  className={`pb-3 text-xs lg:text-sm tracking-wide uppercase transition-all font-mono ${
                    pipelineSubTab === "logs"
                      ? "border-b-2 border-white text-white font-bold"
                      : "border-b-2 border-transparent text-neutral-500 hover:text-white"
                  }`}
                >
                  Nhật ký thực thi ({recentLogs.length})
                </button>
              </div>
            </div>

            {/* TAB: QUEUE TABLE */}
            {pipelineSubTab === "queue" && (
              <div className="space-y-4">
                {/* Search & Status Filter */}
                <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
                  <div className="w-full sm:w-80">
                    <input
                      type="text"
                      placeholder="Tìm kiếm đề bài theo tên, ID, chủ đề..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full px-3.5 py-2 rounded-lg bg-neutral-950 border border-neutral-800 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-white font-mono"
                    />
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    <span className="text-xs font-mono text-neutral-400">Trạng thái:</span>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="px-3 py-1.5 rounded-lg bg-neutral-950 border border-neutral-800 text-xs font-mono text-white focus:outline-none"
                    >
                      <option value="all">Tất cả ({stories.length})</option>
                      <option value="pending">Chờ xử lý</option>
                      <option value="pr_created">Chờ duyệt PR</option>
                      <option value="merged">Đã Merge</option>
                      <option value="failed">Thất bại</option>
                    </select>
                  </div>
                </div>

                {/* Table */}
                <div className="border border-neutral-800 rounded-xl overflow-hidden bg-neutral-950">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-neutral-800 bg-neutral-900/60 text-[11px] font-mono uppercase text-neutral-400">
                          <th className="py-3 px-4">Tên đề bài / Nhân vật</th>
                          <th className="py-3 px-4">Chủ đề & Thể loại</th>
                          <th className="py-3 px-4">Ngôn ngữ</th>
                          <th className="py-3 px-4">Trạng thái</th>
                          <th className="py-3 px-4">Thời gian</th>
                          <th className="py-3 px-4 text-right">Thao tác</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-900 text-xs">
                        {loading && stories.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="py-8 text-center text-neutral-500 font-mono">
                              Đang tải dữ liệu hàng đợi...
                            </td>
                          </tr>
                        ) : filteredQueueStories.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="py-8 text-center text-neutral-500 font-mono">
                              Không tìm thấy đề bài nào phù hợp.
                            </td>
                          </tr>
                        ) : (
                          filteredQueueStories.map((item) => (
                            <tr key={item.id} className="hover:bg-neutral-900/40 transition-colors">
                              <td className="py-3.5 px-4">
                                <div className="font-semibold text-white">{item.title}</div>
                                <div className="text-[10px] text-neutral-500 font-mono">ID: {item.id}</div>
                              </td>
                              <td className="py-3.5 px-4">
                                <div className="text-neutral-300">{item.topic || "Lịch sử Việt Nam"}</div>
                                <div className="text-[10px] text-neutral-500 font-mono">
                                  {item.category || "Truyền thuyết"}
                                </div>
                              </td>
                              <td className="py-3.5 px-4 font-mono text-[11px] text-neutral-400">
                                {item.sourceLanguages?.join(", ") || "vi, en"}
                              </td>
                              <td className="py-3.5 px-4">{renderStatusBadge(item.status)}</td>
                              <td className="py-3.5 px-4 font-mono text-[11px] text-neutral-500">
                                {item.updatedAt ? new Date(item.updatedAt).toLocaleTimeString() : "--"}
                              </td>
                              <td className="py-3.5 px-4 text-right">
                                <div className="flex items-center justify-end gap-1.5">
                                  <button
                                    onClick={() => handleRunSingle(item.id)}
                                    disabled={executingId === item.id}
                                    className="px-2.5 py-1 bg-white text-black hover:bg-neutral-200 disabled:opacity-50 text-[11px] font-bold rounded font-mono transition-colors"
                                  >
                                    {executingId === item.id ? "Đang chạy..." : "Chạy thử"}
                                  </button>

                                  <button
                                    onClick={() => handleOpenPreview(item.id)}
                                    className="px-2.5 py-1 bg-neutral-900 text-neutral-300 hover:text-white text-[11px] font-mono rounded border border-neutral-800 transition-colors"
                                  >
                                    Xem trước
                                  </button>

                                  <button
                                    onClick={() => handleValidateStory(item.id)}
                                    className="px-2.5 py-1 bg-neutral-900 text-neutral-300 hover:text-white text-[11px] font-mono rounded border border-neutral-800 transition-colors"
                                  >
                                    Kiểm định
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: PULL REQUESTS */}
            {pipelineSubTab === "prs" && (
              <div className="space-y-4">
                <div className="border border-neutral-800 rounded-xl overflow-hidden bg-neutral-950">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-neutral-800 bg-neutral-900/60 text-[11px] font-mono uppercase text-neutral-400">
                          <th className="py-3 px-4">Tác phẩm & Nhánh PR</th>
                          <th className="py-3 px-4">Chủ đề</th>
                          <th className="py-3 px-4">Trạng thái PR</th>
                          <th className="py-3 px-4">Đường dẫn GitHub</th>
                          <th className="py-3 px-4 text-right">Thao tác duyệt</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-900 text-xs">
                        {pullRequests.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="py-8 text-center text-neutral-500 font-mono">
                              Chưa có Pull Request nào trong hệ thống.
                            </td>
                          </tr>
                        ) : (
                          pullRequests.map((pr) => (
                            <tr key={pr.id} className="hover:bg-neutral-900/40 transition-colors">
                              <td className="py-3.5 px-4">
                                <div className="font-semibold text-white">{pr.title}</div>
                                <div className="text-[10px] text-neutral-500 font-mono">
                                  {pr.branchName || `ai-stories/${pr.id}`}
                                </div>
                              </td>
                              <td className="py-3.5 px-4 text-neutral-300">{pr.topic || pr.category || "Lịch sử"}</td>
                              <td className="py-3.5 px-4 font-mono">
                                {pr.isMerged ? (
                                  <span className="px-2 py-0.5 rounded text-[10px] bg-white text-black font-bold">
                                    MERGED
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 rounded text-[10px] bg-neutral-900 text-neutral-300 border border-neutral-700">
                                    OPEN (CHỜ DUYỆT)
                                  </span>
                                )}
                              </td>
                              <td className="py-3.5 px-4 font-mono text-[11px]">
                                {pr.prUrl ? (
                                  <a
                                    href={pr.prUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-white hover:underline truncate max-w-xs block font-bold"
                                  >
                                    PR #{pr.prNumber || pr.id} [Mở GitHub]
                                  </a>
                                ) : (
                                  <span className="text-neutral-600">--</span>
                                )}
                              </td>
                              <td className="py-3.5 px-4 text-right">
                                {!pr.isMerged && pr.prNumber ? (
                                  <button
                                    onClick={() => handleMergePR(pr.prNumber!, pr.id)}
                                    className="px-3 py-1 bg-white text-black hover:bg-neutral-200 font-bold rounded text-[11px] font-mono transition-colors"
                                  >
                                    Merge PR
                                  </button>
                                ) : (
                                  <span className="text-[11px] font-mono text-neutral-500">Đã hoàn tất</span>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: LOGS */}
            {pipelineSubTab === "logs" && (
              <div className="border border-neutral-800 rounded-xl bg-neutral-950 p-4 font-mono text-xs max-h-[500px] overflow-y-auto space-y-2">
                {recentLogs.length === 0 ? (
                  <div className="text-neutral-500 text-center py-6">Chưa có nhật ký hoạt động nào.</div>
                ) : (
                  recentLogs.map((log, idx) => (
                    <div key={idx} className="flex items-start gap-3 py-1 border-b border-neutral-900 text-neutral-300">
                      <span className="text-neutral-600 shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 uppercase ${
                        log.level === "error" ? "bg-neutral-900 text-neutral-400 border border-neutral-700" :
                        log.level === "success" ? "bg-white text-black font-bold" : "bg-neutral-900 text-neutral-400"
                      }`}>
                        {log.level}
                      </span>
                      <span className="text-neutral-400 shrink-0">[{log.storyId}]</span>
                      <span className="text-white flex-1">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ============================================================== */}
      {/* MODAL 1: ĐỌC TRUYỆN CHI TIẾT (FULL STORY READING MODAL)         */}
      {/* ============================================================== */}
      {readStoryModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FAF7F2] rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col border border-neutral-300/80 shadow-2xl overflow-hidden text-neutral-900 font-sans">
            {/* Header */}
            <div className="p-6 border-b border-neutral-300/80 flex items-center justify-between bg-[#FAF7F2]/90">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-white border border-neutral-300/80 text-neutral-800 font-bold shadow-xs">
                    {isFairyTale(readStoryModal) ? "TRUYỆN CỔ TÍCH" : "LỊCH SỬ VIỆT NAM"}
                  </span>
                  <span className="text-xs font-mono text-neutral-500">
                    {readStoryModal.topic}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-neutral-950 font-mono">{readStoryModal.title}</h2>
              </div>
              <button
                onClick={() => setReadStoryModal(null)}
                className="text-neutral-500 hover:text-neutral-950 font-bold text-base font-mono p-1"
              >
                ✕
              </button>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Summary */}
              {readStoryModal.summary && (
                <div className="p-4 rounded-xl bg-white border border-neutral-300/70 shadow-xs">
                  <h4 className="font-bold text-neutral-950 text-xs mb-1 uppercase tracking-wider font-mono">
                    Tóm tắt tác phẩm
                  </h4>
                  <p className="text-xs leading-relaxed text-neutral-700">{readStoryModal.summary}</p>
                </div>
              )}

              {/* Characters */}
              {readStoryModal.characters && readStoryModal.characters.length > 0 && (
                <div>
                  <h4 className="font-bold text-neutral-950 text-xs mb-2.5 uppercase tracking-wider font-mono">
                    Hệ thống nhân vật & Visual DNA
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {readStoryModal.characters.map((char, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-white border border-neutral-300/70 space-y-1 shadow-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-neutral-950 text-xs">{char.name}</span>
                          <span className="text-[10px] font-mono text-neutral-500 uppercase">{char.role || "Tuyến nhân vật"}</span>
                        </div>
                        {char.dna && (
                          <p className="text-[11px] text-neutral-600 leading-normal line-clamp-3 font-mono">
                            {char.dna}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Full Content */}
              <div>
                <h4 className="font-bold text-neutral-950 text-xs mb-3 uppercase tracking-wider font-mono">
                  Nội dung tác phẩm hoàn chỉnh
                </h4>
                <div className="prose max-w-none text-neutral-900 text-sm leading-relaxed whitespace-pre-line font-serif bg-white p-6 rounded-xl border border-neutral-300/70 shadow-xs">
                  {readStoryModal.content}
                </div>
              </div>

              {/* Comic Panels Outline */}
              {readStoryModal.panels && readStoryModal.panels.length > 0 && (
                <div>
                  <h4 className="font-bold text-neutral-950 text-xs mb-2.5 uppercase tracking-wider font-mono">
                    Kịch bản phân cảnh truyện tranh (4 Khung hình AI)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {readStoryModal.panels.map((p, idx) => (
                      <div key={idx} className="p-3.5 rounded-lg bg-white border border-neutral-300/70 space-y-1.5 shadow-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold bg-neutral-900 px-2 py-0.5 rounded text-white">
                            KHUNG {p.panel_index || idx + 1}
                          </span>
                          <span className="text-[10px] font-mono text-neutral-500 uppercase">{p.layout_type || "square"}</span>
                        </div>
                        <p className="text-xs text-neutral-900 font-medium">{p.dialogue_text}</p>
                        <p className="text-[10px] text-neutral-500 font-mono line-clamp-2">{p.image_prompt}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-neutral-300/80 bg-[#FAF7F2] flex flex-wrap items-center justify-between gap-3">
              <div className="text-[11px] font-mono text-neutral-500">
                Sẵn sàng chuyển thể truyện tranh ComfyUI
              </div>

              <div className="flex items-center gap-2">
                {onLoadStoryToEditor && (
                  <button
                    onClick={() => {
                      onLoadStoryToEditor(readStoryModal.content, readStoryModal.title);
                      setReadStoryModal(null);
                    }}
                    className="px-4 py-2 rounded-lg bg-white text-neutral-900 border border-neutral-300/80 text-xs font-mono uppercase tracking-wider hover:bg-neutral-100 transition-colors shadow-xs"
                  >
                    Mở trong Bản thảo
                  </button>
                )}

                {onAdaptStoryToComic && (
                  <button
                    onClick={() => {
                      onAdaptStoryToComic(readStoryModal.content, readStoryModal.title);
                      setReadStoryModal(null);
                    }}
                    className="px-4 py-2 rounded-lg bg-neutral-900 text-white font-bold text-xs font-mono uppercase tracking-wider hover:bg-neutral-800 transition-colors shadow-xs"
                  >
                    Chuyển thể truyện tranh ngay
                  </button>
                )}

                <button
                  onClick={() => setReadStoryModal(null)}
                  className="px-3 py-2 rounded-lg bg-white border border-neutral-300 text-neutral-700 text-xs font-mono hover:text-neutral-950 transition-colors shadow-xs"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 2: THÊM ĐỀ BÀI MỚI                                        */}
      {/* ============================================================== */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FAF7F2] rounded-2xl max-w-md w-full p-6 border border-neutral-300/80 shadow-2xl space-y-4 text-neutral-900">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-300/70">
              <h3 className="font-bold text-base uppercase tracking-wider font-mono text-neutral-950">Thêm câu chuyện mới</h3>
              <button onClick={() => setShowAddModal(false)} className="text-neutral-500 hover:text-neutral-950 font-bold text-sm">✕</button>
            </div>

            <form onSubmit={handleAddStory} className="space-y-3 text-xs">
              <div>
                <label className="block text-neutral-600 font-mono mb-1">Tên tác phẩm / Nhân vật (*)</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Thánh Gióng, Tấm Cám, Lê Lợi..."
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-neutral-300/80 text-neutral-900 focus:outline-none focus:border-neutral-900 font-mono shadow-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-mono mb-1">Phân loại thể loại</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-neutral-300/80 text-neutral-900 focus:outline-none font-mono shadow-xs"
                >
                  <option value="Truyện Cổ Tích">Truyện Cổ Tích & Truyền Thuyết Dân Gian</option>
                  <option value="Truyện Lịch Sử">Truyện Lịch Sử & Anh Hùng Dân Tộc</option>
                </select>
              </div>

              <div>
                <label className="block text-neutral-600 font-mono mb-1">Chủ đề câu chuyện</label>
                <input
                  type="text"
                  placeholder="Ví dụ: Đạo đức, Kháng chiến, Lòng dũng cảm..."
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-neutral-300/80 text-neutral-900 focus:outline-none font-mono shadow-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-mono mb-1">Thể loại / Từ khóa</label>
                <input
                  type="text"
                  placeholder="Cổ tích, Dân gian, Diệt ác..."
                  value={newGenre}
                  onChange={(e) => setNewGenre(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-neutral-300/80 text-neutral-900 focus:outline-none font-mono shadow-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-neutral-300/70">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg bg-white border border-neutral-300 text-neutral-700 font-mono hover:text-neutral-950 shadow-xs"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-neutral-900 text-white font-bold font-mono hover:bg-neutral-800 uppercase tracking-wider shadow-xs"
                >
                  Lưu vào hàng đợi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 3: NHẬP HÀNG LOẠT                                         */}
      {/* ============================================================== */}
      {showBatchModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FAF7F2] rounded-2xl max-w-lg w-full p-6 border border-neutral-300/80 shadow-2xl space-y-4 text-neutral-900">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-300/70">
              <h3 className="font-bold text-base uppercase tracking-wider font-mono text-neutral-950">Nhập hàng loạt đề bài</h3>
              <button onClick={() => setShowBatchModal(false)} className="text-neutral-500 hover:text-neutral-950 font-bold text-sm">✕</button>
            </div>

            <form onSubmit={handleBatchAdd} className="space-y-3 text-xs">
              <p className="text-neutral-600">
                Nhập danh sách tên truyện (mỗi dòng một câu chuyện), hoặc dán mảng JSON:
              </p>
              <textarea
                rows={6}
                value={batchRawText}
                onChange={(e) => setBatchRawText(e.target.value)}
                placeholder={"Thạch Sanh\nTấm Cám\nĂn Khế Trả Vàng\nTrần Hưng Đạo"}
                className="w-full p-3 rounded-lg bg-white border border-neutral-300/80 text-neutral-900 font-mono text-xs focus:outline-none focus:border-neutral-900 shadow-xs"
              />

              <div className="flex justify-end gap-2 pt-2 border-t border-neutral-300/70">
                <button
                  type="button"
                  onClick={() => setShowBatchModal(false)}
                  className="px-4 py-2 rounded-lg bg-white border border-neutral-300 text-neutral-700 font-mono hover:text-neutral-950 shadow-xs"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-neutral-900 text-white font-bold font-mono hover:bg-neutral-800 uppercase shadow-xs"
                >
                  Nhập danh sách
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 4: KIỂM ĐỊNH 5 LỚP                                       */}
      {/* ============================================================== */}
      {validationModalData && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FAF7F2] rounded-2xl max-w-lg w-full p-6 border border-neutral-300/80 shadow-2xl space-y-4 text-neutral-900 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-300/70">
              <h3 className="font-bold text-sm uppercase tracking-wider text-neutral-950">
                Kiểm định 5 lớp: {validationModalData.title}
              </h3>
              <button onClick={() => setValidationModalData(null)} className="text-neutral-500 hover:text-neutral-950 font-bold">✕</button>
            </div>

            <div className="space-y-3">
              <div className="p-3 rounded-lg flex items-center justify-between bg-white border border-neutral-300/70 shadow-xs">
                <span className="text-neutral-600">Kết quả tổng thể:</span>
                {validationModalData.result.passed ? (
                  <span className="text-emerald-700 font-bold uppercase bg-emerald-50 border border-emerald-300/80 px-2 py-0.5 rounded">ĐẠT CHUẨN</span>
                ) : (
                  <span className="text-red-700 font-bold uppercase bg-red-50 border border-red-300/80 px-2 py-0.5 rounded">CHƯA ĐẠT</span>
                )}
              </div>

              <div className="p-3 rounded-lg flex items-center justify-between bg-white border border-neutral-300/70 shadow-xs">
                <span className="text-neutral-600">Dung lượng thực tế:</span>
                <span className="text-neutral-950 font-bold">{validationModalData.result.wordCount} từ</span>
              </div>

              {validationModalData.result.errors.length > 0 && (
                <div className="p-3 rounded-lg bg-white border border-neutral-300/70 shadow-xs">
                  <span className="font-bold text-neutral-950 block mb-1">Lỗi cần khắc phục:</span>
                  <ul className="list-disc pl-4 space-y-1 text-neutral-600">
                    {validationModalData.result.errors.map((e, idx) => (
                      <li key={idx}>{e}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-neutral-300/70">
              <button
                onClick={() => setValidationModalData(null)}
                className="px-4 py-2 rounded-lg bg-neutral-900 text-white font-bold text-xs hover:bg-neutral-800 transition-colors shadow-xs"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 5: XEM TRƯỚC BẢN THẢO (PIPELINE PREVIEW)                  */}
      {/* ============================================================== */}
      {previewStory && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FAF7F2] rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col border border-neutral-300/80 shadow-2xl overflow-hidden text-neutral-900 font-mono text-xs">
            <div className="p-4 border-b border-neutral-300/80 flex items-center justify-between bg-white">
              <h3 className="font-bold text-sm uppercase tracking-wider text-neutral-950">{previewStory.title}</h3>
              <button onClick={() => setPreviewStory(null)} className="text-neutral-500 hover:text-neutral-950 font-bold">✕</button>
            </div>

            <div className="p-4 overflow-y-auto space-y-4">
              <div className="bg-white p-4 rounded-xl border border-neutral-300/70 font-serif whitespace-pre-line text-neutral-900 leading-relaxed text-sm shadow-xs">
                {previewStory.content}
              </div>
            </div>

            <div className="p-4 border-t border-neutral-300/80 bg-white flex justify-end">
              <button
                onClick={() => setPreviewStory(null)}
                className="px-4 py-2 rounded-lg bg-neutral-900 text-white font-bold hover:bg-neutral-800 shadow-xs"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
