"use client";

import React, { useState, useEffect, useRef } from "react";
import { Language, translations } from "@/lib/i18n";
import { SocialPost, SocialComment } from "@/lib/types";
import { api } from "@/lib/api";
import { InteractiveTiltCard } from "@/components/cards/InteractiveTiltCard";
import { LikeButtonMorphicon } from "@/components/morphicons/LikeButtonMorphicon";
import { 
  BookOpen, 
  MessageSquare, 
  Eye, 
  Sparkles, 
  RefreshCw, 
  X, 
  Send, 
  Clock, 
  Palette, 
  ChevronRight,
  Bookmark,
  Share2,
  Compass
} from "lucide-react";

interface Props {
  lang: Language;
  currentUsername?: string;
  onReadInEditor?: (storyContent: string, title?: string) => void;
}

export function CommunityFeedView({ lang, currentUsername, onReadInEditor }: Props) {
  const t = translations[lang];
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGenre, setSelectedGenre] = useState<string>("Tất cả");
  const [activePost, setActivePost] = useState<SocialPost | null>(null);
  const [isReadingModalOpen, setIsReadingModalOpen] = useState(false);
  const [postDetailsLoading, setPostDetailsLoading] = useState(false);

  // Comment input in reader modal
  const [commentInput, setCommentInput] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  // Dwell time tracking in modal
  const dwellStartTimeRef = useRef<number | null>(null);

  const genres = [
    { id: "Tất cả", labelVi: "Tất cả", labelEn: "All" },
    { id: "Lịch sử", labelVi: "Lịch sử & Dã sử", labelEn: "History" },
    { id: "Tiên hiệp", labelVi: "Tiên hiệp & Kỳ ảo", labelEn: "Fantasy" },
    { id: "Khoa học viễn tưởng", labelVi: "Viễn tưởng & Cyberpunk", labelEn: "Sci-Fi" },
    { id: "Trinh thám", labelVi: "Trinh thám & Giật gân", labelEn: "Mystery" },
    { id: "Đô thị", labelVi: "Đô thị & Chữa lành", labelEn: "Urban" },
  ];

  const fetchFeed = async (genreFilter?: string) => {
    setLoading(true);
    try {
      const g = genreFilter === "Tất cả" ? undefined : genreFilter;
      const res = await api.getSocialFeed(g, 24, 0);
      if (res.success && res.data && Array.isArray(res.data.items)) {
        setPosts(res.data.items);
      } else {
        setPosts([]);
      }
    } catch (err) {
      console.error("Failed to load community feed:", err);
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeed(selectedGenre);
  }, [selectedGenre]);

  const handleOpenReader = async (post: SocialPost) => {
    setActivePost(post);
    setIsReadingModalOpen(true);
    setPostDetailsLoading(true);
    dwellStartTimeRef.current = Date.now();

    // Record view click interaction
    api.interactPost({
      post_id: post.id,
      interaction_type: "CLICK",
    }).catch(() => {});

    try {
      const res = await api.getPostDetails(post.id);
      if (res.success && res.data) {
        setActivePost(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch full post details:", err);
    } finally {
      setPostDetailsLoading(false);
    }
  };

  const handleCloseReader = () => {
    // Record dwell time if reader was open
    if (dwellStartTimeRef.current && activePost) {
      const dwellSeconds = Math.max(1, (Date.now() - dwellStartTimeRef.current) / 1000);
      api.interactPost({
        post_id: activePost.id,
        interaction_type: "DWELL_TIME",
        dwell_seconds: dwellSeconds,
      }).catch(() => {});
    }

    setIsReadingModalOpen(false);
    setActivePost(null);
    setCommentInput("");
  };

  const handleLikeToggle = async (postId: number, liked: boolean) => {
    try {
      await api.interactPost({
        post_id: postId,
        interaction_type: "LIKE",
      });

      // Optimistic update
      setPosts((prev) =>
        prev.map((p) =>
          p.id === postId
            ? { ...p, likes_count: liked ? p.likes_count + 1 : Math.max(0, p.likes_count - 1), liked_by_me: liked }
            : p
        )
      );

      if (activePost && activePost.id === postId) {
        setActivePost((prev) =>
          prev
            ? { ...prev, likes_count: liked ? prev.likes_count + 1 : Math.max(0, prev.likes_count - 1), liked_by_me: liked }
            : null
        );
      }
    } catch (err) {
      console.error("Error liking post:", err);
    }
  };

  const handleAddComment = async () => {
    if (!commentInput.trim() || !activePost || commentSubmitting) return;

    setCommentSubmitting(true);
    const commentText = commentInput.trim();
    try {
      const res = await api.interactPost({
        post_id: activePost.id,
        interaction_type: "COMMENT",
        comment_text: commentText,
      });

      if (res.success) {
        const newComment: SocialComment = {
          id: Date.now(),
          user_id: 0,
          username: currentUsername || "creator",
          full_name: currentUsername || "Tác giả",
          comment_text: commentText,
          created_at: new Date().toISOString(),
        };

        setActivePost((prev) =>
          prev
            ? {
                ...prev,
                comments_count: prev.comments_count + 1,
                comments: [newComment, ...(prev.comments || [])],
              }
            : null
        );

        setPosts((prev) =>
          prev.map((p) =>
            p.id === activePost.id ? { ...p, comments_count: p.comments_count + 1 } : p
          )
        );

        setCommentInput("");
      }
    } catch (err) {
      console.error("Error submitting comment:", err);
    } finally {
      setCommentSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50/60 dark:bg-slate-950/80 text-slate-900 dark:text-white">
      {/* Top Header & Filters */}
      <div className="border-b border-slate-200/80 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-6 py-4 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 max-w-7xl mx-auto">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                {lang === "vi" ? "Bảng Tin Tác Phẩm Cộng Đồng" : "Community Literary Feed"}
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-400 border border-emerald-300/60 dark:border-emerald-800/60">
                Live Feed
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {lang === "vi"
                ? "Khám phá các câu chuyện, tiểu thuyết và truyện tranh manga được xuất bản từ cộng đồng tác giả NarrAI"
                : "Explore stories, web novels, and manga comics published by NarrAI creators"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchFeed(selectedGenre)}
              disabled={loading}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
              title={lang === "vi" ? "Làm mới bảng tin" : "Refresh feed"}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Genre Filter Pills */}
        <div className="flex items-center gap-2 mt-3 overflow-x-auto pb-1 max-w-7xl mx-auto scrollbar-none">
          {genres.map((g) => {
            const isSelected = selectedGenre === g.id;
            return (
              <button
                key={g.id}
                onClick={() => setSelectedGenre(g.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  isSelected
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                {lang === "vi" ? g.labelVi : g.labelEn}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Feed Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {loading && posts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
              <p className="text-sm font-medium">
                {lang === "vi" ? "Đang tải các tác phẩm đề xuất..." : "Loading recommended stories..."}
              </p>
            </div>
          ) : posts.length === 0 ? (
            <div className="text-center py-20 bg-white/50 dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8">
              <BookOpen className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                {lang === "vi" ? "Chưa có bài đăng nào trong chuyên mục này" : "No stories published in this category yet"}
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
                {lang === "vi"
                  ? "Hãy là người đầu tiên sáng tác và bấm 'Lưu & Đăng bài' trong trình soạn thảo để chia sẻ tác phẩm với cộng đồng!"
                  : "Be the first to create and click 'Save & Publish' in the editor to share your story with the community!"}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {posts.map((post) => (
                <InteractiveTiltCard
                  key={post.id}
                  className="h-full rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col justify-between overflow-hidden group"
                >
                  <div className="p-5 flex flex-col flex-1">
                    {/* Cover or Header Badge */}
                    {post.cover_image_url ? (
                      <div className="relative w-full h-44 rounded-xl overflow-hidden mb-4 bg-slate-950">
                        <img
                          src={post.cover_image_url}
                          alt={post.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                          <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-black/70 backdrop-blur-md text-white border border-white/20">
                            {post.genre || "Tiểu thuyết"}
                          </span>
                          {post.is_cold_start_exploration && (
                            <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-amber-500 text-white shadow-sm">
                              Mới
                            </span>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between mb-3">
                        <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-800/60">
                          {post.genre || "Tiểu thuyết"}
                        </span>
                        {post.is_cold_start_exploration && (
                          <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-amber-500 text-white">
                            {lang === "vi" ? "Tác phẩm mới" : "New release"}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Title */}
                    <h3 
                      onClick={() => handleOpenReader(post)}
                      className="text-base font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-1 cursor-pointer mb-1.5"
                    >
                      {post.title}
                    </h3>

                    {/* Author */}
                    <div className="flex items-center gap-2 mb-3 text-xs text-slate-500 dark:text-slate-400">
                      <div className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-700 dark:text-slate-200">
                        {(post.author?.full_name || post.author?.username || "A")[0].toUpperCase()}
                      </div>
                      <span className="font-medium truncate">
                        {post.author?.full_name || post.author?.username || "Tác giả"}
                      </span>
                    </div>

                    {/* Snippet */}
                    <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-4 leading-relaxed font-serif flex-1 mb-4">
                      {post.content_snippet}
                    </p>

                    {/* Tags if any */}
                    {post.tags && post.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-4">
                        {post.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Card Action Footer */}
                  <div className="px-5 py-3.5 bg-slate-50/80 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <LikeButtonMorphicon
                        liked={post.liked_by_me}
                        count={post.likes_count}
                        onToggle={(liked) => handleLikeToggle(post.id, liked)}
                        size="sm"
                      />
                      <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>{post.comments_count}</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                        <Eye className="w-3.5 h-3.5" />
                        <span>{post.views_count}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleOpenReader(post)}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/60 flex items-center gap-1 transition-colors"
                    >
                      <span>{lang === "vi" ? "Đọc tiếp" : "Read"}</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </InteractiveTiltCard>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Reader Modal (Layer 3 Glassmorphism Overlay) */}
      {isReadingModalOpen && activePost && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden animate-scaleIn">
            
            {/* Modal Header */}
            <div className="h-16 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between shrink-0 bg-slate-50/70 dark:bg-slate-900/70">
              <div className="flex items-center gap-3 overflow-hidden">
                <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 shrink-0">
                  {activePost.genre || "Tác phẩm"}
                </span>
                <h2 className="text-base font-bold text-slate-900 dark:text-white truncate">
                  {activePost.title}
                </h2>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {onReadInEditor && (
                  <button
                    onClick={() => {
                      onReadInEditor(activePost.story_full_text || activePost.content_snippet, activePost.title);
                      handleCloseReader();
                    }}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    {lang === "vi" ? "Mở trong Editor" : "Open in Editor"}
                  </button>
                )}
                <button
                  onClick={handleCloseReader}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 sm:p-10 space-y-8">
              {/* Author & Stats Bar */}
              <div className="flex flex-wrap items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800 text-xs text-slate-500 gap-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-xs">
                    {(activePost.author?.full_name || activePost.author?.username || "A")[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white">
                      {activePost.author?.full_name || activePost.author?.username || "Tác giả"}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      @{activePost.author?.username || "creator"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <LikeButtonMorphicon
                    liked={activePost.liked_by_me}
                    count={activePost.likes_count}
                    onToggle={(liked) => handleLikeToggle(activePost.id, liked)}
                  />
                  <div className="flex items-center gap-1.5">
                    <Eye className="w-4 h-4 text-slate-400" />
                    <span>{activePost.views_count} lượt xem</span>
                  </div>
                </div>
              </div>

              {/* Linked Comic Panels (if present) */}
              {activePost.comic_panels && activePost.comic_panels.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Palette className="w-4 h-4 text-indigo-500" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                      {lang === "vi" ? "Chuyển thể Manga Comic" : "Manga Comic Adaptation"}
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {activePost.comic_panels.map((panel, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-slate-200 dark:border-slate-800 bg-black overflow-hidden shadow-md flex flex-col"
                      >
                        <div className="w-full aspect-square bg-slate-950 flex items-center justify-center overflow-hidden">
                          <img
                            src={panel.image_url}
                            alt={`Panel ${panel.panel_index}`}
                            className="w-full h-full object-cover filter grayscale contrast-110"
                          />
                        </div>
                        {panel.dialogue_text && (
                          <div className="p-3 bg-white dark:bg-slate-900 text-xs font-medium text-slate-800 dark:text-slate-200 leading-snug border-t border-slate-200 dark:border-slate-800">
                            {panel.dialogue_text}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Prose Novel Text */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-brand-600" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                    {lang === "vi" ? "Toàn văn tác phẩm" : "Full Story Prose"}
                  </h3>
                </div>

                <div className="bg-[#FAF8F5] dark:bg-slate-950/60 rounded-xl p-6 sm:p-8 border border-[#E8E4DC] dark:border-slate-800">
                  <div className="font-serif text-slate-900 dark:text-slate-100 text-base sm:text-lg leading-[1.85] tracking-wide whitespace-pre-wrap">
                    {activePost.story_full_text || activePost.content_snippet}
                  </div>
                </div>
              </div>

              {/* Reader Comments Section */}
              <div className="pt-6 border-t border-slate-200 dark:border-slate-800 space-y-5">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-indigo-500" />
                  <span>
                    {lang === "vi"
                      ? `Bình luận độc giả (${activePost.comments_count || 0})`
                      : `Reader Comments (${activePost.comments_count || 0})`}
                  </span>
                </h3>

                {/* Comment Input */}
                <div className="flex items-start gap-2.5">
                  <textarea
                    value={commentInput}
                    onChange={(e) => setCommentInput(e.target.value)}
                    placeholder={
                      lang === "vi"
                        ? "Chia sẻ cảm nghĩ của bạn về tác phẩm này..."
                        : "Leave your thoughts about this story..."
                    }
                    rows={2}
                    className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 text-xs text-slate-900 dark:text-white outline-none focus:border-indigo-500 transition-colors resize-none"
                  />
                  <button
                    onClick={handleAddComment}
                    disabled={!commentInput.trim() || commentSubmitting}
                    className="px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 shrink-0 shadow-sm"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{lang === "vi" ? "Gửi" : "Post"}</span>
                  </button>
                </div>

                {/* Comment List */}
                <div className="space-y-3">
                  {activePost.comments && activePost.comments.length > 0 ? (
                    activePost.comments.map((comm) => (
                      <div
                        key={comm.id}
                        className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs"
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-bold text-slate-900 dark:text-white">
                            {comm.full_name || comm.username}
                          </span>
                          {comm.created_at && (
                            <span className="text-[10px] text-slate-400">
                              {new Date(comm.created_at).toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US")}
                            </span>
                          )}
                        </div>
                        <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                          {comm.comment_text}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-400 italic">
                      {lang === "vi"
                        ? "Chưa có bình luận nào. Hãy là người đầu tiên để lại cảm nghĩ!"
                        : "No comments yet. Be the first to share your thoughts!"}
                    </p>
                  )}
                </div>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
