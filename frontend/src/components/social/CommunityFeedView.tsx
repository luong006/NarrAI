"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
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
  ChevronLeft,
  Search,
  Maximize2,
  Bookmark,
  Share2,
  Compass,
  UserPlus,
  UserCheck,
  CornerDownRight
} from "lucide-react";
import { tfjsRecommender } from "@/services/tfjsRecommender";


interface Props {
  lang: Language;
  currentUsername?: string;
  onReadInEditor?: (storyContent: string, title?: string) => void;
}

function sanitizeDisplayProse(text: string | null | undefined): string {
  if (!text) return "";
  let clean = String(text);
  // Strip all HTML tags completely (<b>, </b>, <i>, <p>, <br>, etc.)
  clean = clean.replace(/<[^>]+>/g, "");
  // Unescape common HTML entities
  clean = clean
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");
  // Strip raw English dramatic beat meta-tags
  clean = clean.replace(/^\s*\*\*(?:Hook|Rising Friction(?:\s*\/\s*Complication)?|Turning Point|Visceral Climax|Lingering Cliffhanger|Beat\s*\d+|Nhịp\s*\d+)\*\*\s*\n?/gim, "");
  clean = clean.replace(/\*\*(?:Hook|Rising Friction(?:\s*\/\s*Complication)?|Turning Point|Visceral Climax|Lingering Cliffhanger)\*\*\s*/gi, "");
  return clean.trim();
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

  // Threaded comments: replying to a specific comment
  const [replyingToComment, setReplyingToComment] = useState<{ id: number; author: string } | null>(null);

  // Author Follow/Unfollow state
  const [followingAuthorIds, setFollowingAuthorIds] = useState<Set<number>>(new Set());
  const [followLoadingIds, setFollowLoadingIds] = useState<Set<number>>(new Set());

  // Dwell time tracking in modal
  const dwellStartTimeRef = useRef<number | null>(null);

  // Feature 25: Search box on Posts tab
  const [searchQuery, setSearchQuery] = useState("");

  // Feature 24: Fullscreen Comic Reader sequential carousel & swipe
  const [isComicReaderOpen, setIsComicReaderOpen] = useState(false);
  const [comicPanelIndex, setComicPanelIndex] = useState(0);
  const [comicReaderPost, setComicReaderPost] = useState<SocialPost | null>(null);
  const touchStartXRef = useRef<number | null>(null);
  const touchStartYRef = useRef<number | null>(null);

  // Keyboard navigation for Fullscreen Comic Reader (ArrowLeft, ArrowRight, Escape)
  useEffect(() => {
    if (!isComicReaderOpen) return;

    const currentPost = comicReaderPost || activePost;
    const panels = currentPost?.comic_panels || [];
    const total = panels.length;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setComicPanelIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        setComicPanelIndex((prev) => (total > 0 ? Math.min(total - 1, prev + 1) : 0));
      } else if (e.key === "Escape") {
        e.preventDefault();
        setIsComicReaderOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isComicReaderOpen, comicReaderPost, activePost]);

  // Touch gesture swipe handlers for Fullscreen Comic Reader
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartXRef.current = e.touches[0].clientX;
    touchStartYRef.current = e.touches[0].clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartXRef.current === null || touchStartYRef.current === null) return;
    const deltaX = e.changedTouches[0].clientX - touchStartXRef.current;
    const deltaY = e.changedTouches[0].clientY - touchStartYRef.current;
    touchStartXRef.current = null;
    touchStartYRef.current = null;

    const currentPost = comicReaderPost || activePost;
    const panels = currentPost?.comic_panels || [];
    const total = panels.length;

    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 40) {
      if (deltaX > 0) {
        // Swiped right -> go to previous panel
        setComicPanelIndex((prev) => Math.max(0, prev - 1));
      } else {
        // Swiped left -> go to next panel
        setComicPanelIndex((prev) => (total > 0 ? Math.min(total - 1, prev + 1) : 0));
      }
    }
  };

  // Feature 25: Dynamic post filtering matching title or author (author_name / user_id)
  const filteredPosts = posts.filter((post) => {
    // Genre filter (client-side for instant response alongside API fetch)
    if (selectedGenre && selectedGenre !== "Tất cả") {
      const postGenre = (post.genre || "").toLowerCase();
      const filterGenre = selectedGenre.toLowerCase();
      if (!postGenre.includes(filterGenre) && !filterGenre.includes(postGenre)) {
        return false;
      }
    }
    // Text search
    if (!searchQuery.trim()) return true;
    const q = searchQuery.trim().toLowerCase();
    const title = (post.title || "").toLowerCase();
    const authorName = (post.author?.full_name || (post as any).author_name || "").toLowerCase();
    const authorUsername = (post.author?.username || "").toLowerCase();
    const snippet = (post.content_snippet || "").toLowerCase();
    const tagsRaw = (post as any).tags;
    const tags = tagsRaw ? (typeof tagsRaw === "string" ? tagsRaw : JSON.stringify(tagsRaw)).toLowerCase() : "";
    return (
      title.includes(q) ||
      authorName.includes(q) ||
      authorUsername.includes(q) ||
      snippet.includes(q) ||
      tags.includes(q)
    );
  });

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

  useEffect(() => {
    tfjsRecommender.syncVectorsFromBackend().catch((error) => {
      console.error("[TFJSRecommender] Vector sync failed:", error);
    });
  }, []);


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

  const handleFollowToggle = async (authorId?: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!authorId || followLoadingIds.has(authorId)) return;

    setFollowLoadingIds((prev) => new Set(prev).add(authorId));
    const isCurrentlyFollowing = followingAuthorIds.has(authorId);

    try {
      if (isCurrentlyFollowing) {
        await api.unfollowAuthor(authorId);
        setFollowingAuthorIds((prev) => {
          const next = new Set(prev);
          next.delete(authorId);
          return next;
        });
      } else {
        await api.followAuthor(authorId);
        setFollowingAuthorIds((prev) => new Set(prev).add(authorId));
      }
    } catch (err) {
      console.error("Error toggling author follow:", err);
    } finally {
      setFollowLoadingIds((prev) => {
        const next = new Set(prev);
        next.delete(authorId);
        return next;
      });
    }
  };

  const handleAddComment = async () => {
    if (!commentInput.trim() || !activePost || commentSubmitting) return;

    setCommentSubmitting(true);
    const commentText = commentInput.trim();
    const parentId = replyingToComment ? replyingToComment.id : undefined;

    try {
      const res = await api.interactPost({
        post_id: activePost.id,
        interaction_type: "COMMENT",
        comment_text: commentText,
        parent_comment_id: parentId,
      });

      if (res.success) {
        const newComment: SocialComment = {
          id: Date.now(),
          user_id: 0,
          username: currentUsername || "creator",
          full_name: currentUsername || "Tác giả",
          comment_text: commentText,
          created_at: new Date().toISOString(),
          parent_comment_id: parentId || null,
        };

        setActivePost((prev) =>
          prev
            ? {
                ...prev,
                comments_count: prev.comments_count + 1,
                comments: [...(prev.comments || []), newComment],
              }
            : null
        );

        setPosts((prev) =>
          prev.map((p) =>
            p.id === activePost.id ? { ...p, comments_count: p.comments_count + 1 } : p
          )
        );

        setCommentInput("");
        setReplyingToComment(null);
      }
    } catch (err) {
      console.error("Error submitting comment:", err);
    } finally {
      setCommentSubmitting(false);
    }
  };

  const organizedComments = useMemo(() => {
    const allComments = activePost?.comments || [];
    const rootComments: SocialComment[] = [];
    const replyMap: Record<number, SocialComment[]> = {};

    for (const c of allComments) {
      if (c.parent_comment_id) {
        if (!replyMap[c.parent_comment_id]) {
          replyMap[c.parent_comment_id] = [];
        }
        replyMap[c.parent_comment_id].push(c);
      } else {
        rootComments.push(c);
      }
    }

    return { rootComments, replyMap };
  }, [activePost?.comments]);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#F0F2F5] dark:bg-slate-950 text-slate-900 dark:text-white">

      {/* Facebook-style top bar: search + genre chips */}
      <div className="shrink-0 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-2.5 shadow-sm">
        {/* Row 1: search */}
        <div className="flex items-center gap-2 max-w-2xl mx-auto">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={lang === "vi" ? "Tìm kiếm tác phẩm, tác giả..." : "Search stories, authors..."}
              className="w-full pl-9 pr-8 py-2 text-sm rounded-full border border-slate-200 dark:border-slate-700 bg-[#F0F2F5] dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <button
            onClick={() => fetchFeed(selectedGenre)}
            disabled={loading}
            className="p-2 rounded-full bg-[#F0F2F5] dark:bg-slate-800 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors shrink-0"
            title={lang === "vi" ? "Làm mới" : "Refresh"}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Row 2: genre chips */}
        <div className="flex gap-1.5 overflow-x-auto pt-2 pb-0.5 scrollbar-none max-w-2xl mx-auto">
          {genres.map((g) => {
            const isActive = selectedGenre === g.id;
            return (
              <button
                key={g.id}
                onClick={() => { setSelectedGenre(g.id); fetchFeed(g.id); }}
                className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all shrink-0 ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-[#F0F2F5] dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                {lang === "vi" ? g.labelVi : g.labelEn}
              </button>
            );
          })}
          {(searchQuery || selectedGenre !== "Tất cả") && (
            <button
              onClick={() => { setSearchQuery(""); setSelectedGenre("Tất cả"); fetchFeed("Tất cả"); }}
              className="px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap shrink-0 bg-red-50 dark:bg-red-950/40 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/50 flex items-center gap-1"
            >
              <X className="w-3 h-3" />
              {lang === "vi" ? "Xóa lọc" : "Clear"}
            </button>
          )}
        </div>
      </div>

      {/* Main Feed — scroll area */}
      <div className="flex-1 overflow-y-auto py-4 px-3">
        <div className="max-w-[680px] mx-auto">
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
          ) : filteredPosts.length === 0 ? (
            <div className="text-center py-20 bg-white/50 dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8">
              <Search className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                {lang === "vi"
                  ? `Không tìm thấy tác phẩm nào khớp với "${searchQuery}"`
                  : `No stories found matching "${searchQuery}"`}
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
                {lang === "vi"
                  ? "Hãy thử tìm kiếm với từ khóa khác hoặc bấm nút xóa để hiển thị toàn bộ tác phẩm."
                  : "Try searching with different keywords or clear the search box to view all stories."}
              </p>
              <button
                onClick={() => setSearchQuery("")}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-sm"
              >
                {lang === "vi" ? "Xóa tìm kiếm" : "Clear search"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredPosts.map((post) => (
                <div
                  key={post.id}
                  className="rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
                >
                  {/* Facebook-style Feed Post */}

                  {/* Post Header: avatar + author + follow */}
                  <div className="flex items-center justify-between px-4 pt-4 pb-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shrink-0">
                        {(post.author?.full_name || post.author?.username || "A")[0].toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-bold text-slate-900 dark:text-white truncate">
                          {post.author?.full_name || post.author?.username || "Tác giả"}
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                          <span>{post.genre || "Tiểu thuyết"}</span>
                          {post.is_fanfiction && <span className="px-1.5 py-0 rounded bg-purple-100 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 font-semibold">Fanfic</span>}
                          {post.is_cold_start_exploration && <span className="px-1.5 py-0 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 font-semibold">{lang === "vi" ? "Mới" : "New"}</span>}
                        </div>
                      </div>
                    </div>
                    {/* Follow button — chỉ hiện khi không phải bản thân */}
                    {(post.author?.id || post.user_id) &&
                     (post.author?.username !== currentUsername) && (
                      <button
                        onClick={(e) => handleFollowToggle(post.author?.id || post.user_id, e)}
                        disabled={followLoadingIds.has(post.author?.id || post.user_id || 0)}
                        className={`px-2.5 py-1 rounded-xl text-[11px] font-bold flex items-center gap-1 transition-all shrink-0 ${
                          followingAuthorIds.has(post.author?.id || post.user_id || 0)
                            ? "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800"
                            : "text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-indigo-600 hover:text-white border border-slate-200 dark:border-slate-700"
                        }`}
                      >
                        {followingAuthorIds.has(post.author?.id || post.user_id || 0) ? (
                          <><UserCheck className="w-3 h-3" /><span>{lang === "vi" ? "Đang theo dõi" : "Following"}</span></>
                        ) : (
                          <><UserPlus className="w-3 h-3" /><span>{lang === "vi" ? "Theo dõi" : "Follow"}</span></>
                        )}
                      </button>
                    )}
                  </div>

                  {/* Cover image (nếu có) */}
                  {post.cover_image_url && (
                    <div className="w-full h-52 overflow-hidden bg-slate-950 cursor-pointer" onClick={() => handleOpenReader(post)}>
                      <img
                        src={post.cover_image_url}
                        alt={post.title}
                        className="w-full h-full object-cover hover:scale-105 transition-transform duration-500"
                      />
                    </div>
                  )}

                  {/* Title + Snippet */}
                  <div className="px-4 pt-3 pb-2">
                    <h3
                      onClick={() => handleOpenReader(post)}
                      className="text-base font-bold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors cursor-pointer mb-1.5 leading-snug"
                    >
                      {post.title}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-serif line-clamp-3">
                      {sanitizeDisplayProse(post.content_snippet)}
                    </p>
                  </div>

                  {/* Tags */}
                  {post.tags && post.tags.length > 0 && (
                    <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                      {post.tags.slice(0, 4).map((tag: string, idx: number) => (
                        <span key={idx} className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Comic preview strip (nếu có) */}
                  {post.comic_panels && post.comic_panels.length > 0 && (
                    <div
                      className="px-4 pb-3 cursor-pointer"
                      onClick={() => { setComicReaderPost(post); setComicPanelIndex(0); setIsComicReaderOpen(true); }}
                    >
                      <div className="flex gap-1.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700">
                        {post.comic_panels.slice(0, 3).map((panel, idx) => (
                          <div key={idx} className="flex-1 aspect-square bg-slate-950 overflow-hidden">
                            <img src={panel.image_url} alt={`panel ${idx+1}`} className="w-full h-full object-cover filter grayscale" />
                          </div>
                        ))}
                        <div className="flex-none w-12 bg-indigo-600 flex items-center justify-center">
                          <span className="text-white text-[10px] font-bold text-center leading-tight px-1">
                            {post.comic_panels.length}<br/>panels
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Action bar: like, comment, views, read */}
                  <div className="px-4 py-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <LikeButtonMorphicon
                        liked={post.liked_by_me}
                        count={post.likes_count}
                        onToggle={(liked) => handleLikeToggle(post.id, liked)}
                        size="sm"
                      />
                      <button
                        onClick={() => handleOpenReader(post)}
                        className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>{post.comments_count}</span>
                      </button>
                      <div className="flex items-center gap-1 text-xs text-slate-400">
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
                </div>
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
              <div className="flex items-center gap-2 sm:gap-3 overflow-hidden">
                <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 shrink-0">
                  {activePost.genre || "Tác phẩm"}
                </span>
                {activePost.is_fanfiction && (
                  <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-purple-600 text-white shrink-0">
                    Fanfiction
                  </span>
                )}
                <h2 className="text-base font-bold text-slate-900 dark:text-white truncate">
                  {activePost.title}
                </h2>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {onReadInEditor && (
                  <button
                    onClick={() => {
                      onReadInEditor(sanitizeDisplayProse(activePost.story_full_text || activePost.content_snippet), activePost.title);
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
              {/* Fanfiction Copyright Disclaimer Banner */}
              {activePost.is_fanfiction && (
                <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-purple-900 dark:text-purple-200 text-xs sm:text-sm leading-relaxed flex items-start gap-3 shadow-sm">
                  <span className="text-base select-none shrink-0">⚠️</span>
                  <div>
                    <span className="font-bold block mb-0.5">Tác phẩm Phái sinh / Fanfiction:</span>
                    <span>
                      {activePost.disclaimer || "Tác phẩm fan fiction sáng tạo dựa trên các thương hiệu nhãn hiệu có sẵn — không liên quan đến tác phẩm gốc và không nhằm mục đích thương mại."}
                    </span>
                  </div>
                </div>
              )}
              {/* Author & Stats Bar */}
              <div className="flex flex-wrap items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800 text-xs text-slate-500 gap-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-xs">
                    {(activePost.author?.full_name || activePost.author?.username || "A")[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>{activePost.author?.full_name || activePost.author?.username || "Tác giả"}</span>
                      {(activePost.author?.id || activePost.user_id) && (
                        <button
                          onClick={(e) => handleFollowToggle(activePost.author?.id || activePost.user_id, e)}
                          disabled={followLoadingIds.has(activePost.author?.id || activePost.user_id || 0)}
                          className={`px-2 py-0.5 rounded-md text-[10px] font-bold flex items-center gap-1 transition-all ${
                            followingAuthorIds.has(activePost.author?.id || activePost.user_id || 0)
                              ? "bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800"
                              : "bg-indigo-600 text-white hover:bg-indigo-700"
                          }`}
                        >
                          {followingAuthorIds.has(activePost.author?.id || activePost.user_id || 0) ? (
                            <>
                              <UserCheck className="w-2.5 h-2.5" />
                              <span>{lang === "vi" ? "Đang theo dõi" : "Following"}</span>
                            </>
                          ) : (
                            <>
                              <UserPlus className="w-2.5 h-2.5" />
                              <span>{lang === "vi" ? "Theo dõi" : "Follow"}</span>
                            </>
                          )}
                        </button>
                      )}
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
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <Palette className="w-4 h-4 text-indigo-500" />
                      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                        {lang === "vi" ? "Chuyển thể Manga Comic" : "Manga Comic Adaptation"}
                      </h3>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 font-mono font-semibold">
                        {activePost.comic_panels.length} {lang === "vi" ? "khung" : "panels"}
                      </span>
                    </div>

                    <button
                      onClick={() => {
                        setComicReaderPost(activePost);
                        setComicPanelIndex(0);
                        setIsComicReaderOpen(true);
                      }}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 shadow-sm flex items-center gap-1.5 transition-all"
                      title={lang === "vi" ? "Đọc truyện tranh toàn màn hình" : "Open Fullscreen Comic Reader"}
                    >
                      <Maximize2 className="w-3.5 h-3.5" />
                      <span>{lang === "vi" ? "Đọc toàn màn hình" : "Fullscreen Reader"}</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {activePost.comic_panels.map((panel, idx) => (
                      <div
                        key={idx}
                        onClick={() => {
                          setComicReaderPost(activePost);
                          setComicPanelIndex(idx);
                          setIsComicReaderOpen(true);
                        }}
                        className="rounded-xl border border-slate-200 dark:border-slate-800 bg-black overflow-hidden shadow-md flex flex-col cursor-pointer group/panel hover:border-indigo-500/60 hover:shadow-xl transition-all"
                        title={lang === "vi" ? `Xem toàn màn hình trang ${idx + 1}` : `View panel ${idx + 1} fullscreen`}
                      >
                        <div className="relative w-full aspect-square bg-slate-950 flex items-center justify-center overflow-hidden">
                          <img
                            src={panel.image_url}
                            alt={`Panel ${panel.panel_index}`}
                            className="w-full h-full object-cover filter grayscale contrast-110 group-hover/panel:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/panel:opacity-100 flex items-center justify-center transition-opacity">
                            <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-white/95 text-slate-900 shadow-md flex items-center gap-1">
                              <Maximize2 className="w-3 h-3" />
                              <span>{lang === "vi" ? "Phóng to" : "Enlarge"}</span>
                            </span>
                          </div>
                        </div>
                        {panel.dialogue_text && (
                          <div className="p-3 bg-white dark:bg-slate-900 text-xs font-medium text-slate-800 dark:text-slate-200 leading-snug border-t border-slate-200 dark:border-slate-800 line-clamp-2">
                            {sanitizeDisplayProse(panel.dialogue_text)}
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
                    {sanitizeDisplayProse(activePost.story_full_text || activePost.content_snippet)}
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

                {/* Replying Banner if user clicked reply */}
                {replyingToComment && (
                  <div className="flex items-center justify-between px-3 py-1.5 bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800/60 rounded-xl text-xs text-indigo-700 dark:text-indigo-300">
                    <div className="flex items-center gap-1.5">
                      <CornerDownRight className="w-3.5 h-3.5" />
                      <span>
                        {lang === "vi"
                          ? `Đang trả lời @${replyingToComment.author}`
                          : `Replying to @${replyingToComment.author}`}
                      </span>
                    </div>
                    <button
                      onClick={() => setReplyingToComment(null)}
                      className="p-1 rounded-md hover:bg-indigo-100 dark:hover:bg-indigo-900 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      title={lang === "vi" ? "Hủy trả lời" : "Cancel reply"}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}

                {/* Comment Input */}
                <div className="flex items-start gap-2.5">
                  <textarea
                    value={commentInput}
                    onChange={(e) => setCommentInput(e.target.value)}
                    placeholder={
                      replyingToComment
                        ? (lang === "vi"
                            ? `Nhập câu trả lời cho @${replyingToComment.author}...`
                            : `Write a reply to @${replyingToComment.author}...`)
                        : (lang === "vi"
                            ? "Chia sẻ cảm nghĩ của bạn về tác phẩm này..."
                            : "Leave your thoughts about this story...")
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

                {/* Comment List with Threaded Hierarchical Replies */}
                <div className="space-y-3">
                  {organizedComments.rootComments.length > 0 ? (
                    organizedComments.rootComments.map((comm) => (
                      <div key={comm.id} className="space-y-2">
                        {/* Root Comment Card */}
                        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs shadow-xs">
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
                          <p className="text-slate-700 dark:text-slate-300 leading-relaxed mb-2">
                            {comm.comment_text}
                          </p>
                          <div className="flex items-center gap-2 pt-1.5 border-t border-slate-200/50 dark:border-slate-700/50">
                            <button
                              onClick={() => setReplyingToComment({ id: comm.id, author: comm.full_name || comm.username })}
                              className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                            >
                              <CornerDownRight className="w-3 h-3" />
                              <span>{lang === "vi" ? "Trả lời" : "Reply"}</span>
                            </button>
                          </div>
                        </div>

                        {/* Nested Replies */}
                        {organizedComments.replyMap[comm.id]?.map((reply) => (
                          <div
                            key={reply.id}
                            className="border-l-2 border-indigo-400/40 dark:border-indigo-500/40 pl-3 sm:pl-4 ml-4 sm:ml-6"
                          >
                            <div className="p-3 rounded-xl bg-indigo-50/40 dark:bg-slate-800/80 border border-indigo-100/60 dark:border-slate-700/60 text-xs">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-bold text-slate-900 dark:text-white">
                                  {reply.full_name || reply.username}
                                </span>
                                {reply.created_at && (
                                  <span className="text-[10px] text-slate-400">
                                    {new Date(reply.created_at).toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US")}
                                  </span>
                                )}
                              </div>
                              <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                                {reply.comment_text}
                              </p>
                            </div>
                          </div>
                        ))}
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

      {/* Feature 24: Fullscreen Comic Reader Sequential Carousel Modal */}
      {isComicReaderOpen && (
        (() => {
          const currentPost = comicReaderPost || activePost;
          const panels = currentPost?.comic_panels || [];
          const total = panels.length;
          const currentPanel = panels[comicPanelIndex] || panels[0];

          if (!currentPanel || total === 0) return null;

          return (
            <div
              className="fixed inset-0 z-[70] bg-black/95 backdrop-blur-md flex flex-col justify-between select-none animate-fadeIn"
              role="dialog"
              aria-modal="true"
              aria-label="Fullscreen Comic Reader"
            >
              {/* Top Navigation Bar */}
              <div className="h-16 px-6 flex items-center justify-between border-b border-white/10 bg-black/60 shrink-0">
                <div className="flex items-center gap-3 overflow-hidden">
                  <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-600 text-white shrink-0">
                    Manga Comic
                  </span>
                  <h2 className="text-sm sm:text-base font-bold text-white truncate max-w-md">
                    {currentPost?.title || "Chuyển thể Manga"}
                  </h2>
                </div>

                {/* Page Indicator */}
                <div className="flex items-center gap-2">
                  <div className="px-3.5 py-1 rounded-full bg-white/10 border border-white/20 text-white text-xs font-mono font-semibold">
                    {lang === "vi"
                      ? `Trang ${comicPanelIndex + 1} / ${total}`
                      : `Page ${comicPanelIndex + 1} of ${total}`}
                  </div>
                </div>

                {/* Close Button with Esc Hint */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsComicReaderOpen(false)}
                    className="p-2 rounded-xl text-white/70 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-1.5"
                    title={lang === "vi" ? "Đóng trình xem truyện (Esc)" : "Close reader (Esc)"}
                  >
                    <span className="hidden sm:inline text-xs text-white/50 font-mono">Esc</span>
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Main Carousel View */}
              <div
                className="flex-1 relative flex items-center justify-between px-3 sm:px-8 py-4 overflow-hidden touch-pan-y"
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
              >
                {/* Previous Button */}
                <button
                  onClick={() => setComicPanelIndex((prev) => Math.max(0, prev - 1))}
                  disabled={comicPanelIndex === 0}
                  className="z-10 w-11 h-11 sm:w-14 sm:h-14 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-20 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all backdrop-blur-sm border border-white/15 shadow-xl shrink-0"
                  title={lang === "vi" ? "Trang trước (←)" : "Previous page (←)"}
                >
                  <ChevronLeft className="w-6 h-6 sm:w-7 sm:h-7" />
                </button>

                {/* Single Panel Card with Transition */}
                <div className="flex-1 flex flex-col items-center justify-center max-h-full px-2 sm:px-6">
                  <div
                    key={comicPanelIndex}
                    className="relative flex flex-col items-center justify-center max-w-3xl w-full animate-scaleIn transition-all duration-300"
                  >
                    <div className="max-h-[64vh] sm:max-h-[70vh] flex items-center justify-center overflow-hidden rounded-2xl bg-black border border-white/15 shadow-2xl">
                      <img
                        src={currentPanel.image_url}
                        alt={`Panel ${currentPanel.panel_index || comicPanelIndex + 1}`}
                        className="max-h-[64vh] sm:max-h-[70vh] w-auto max-w-full object-contain filter grayscale contrast-110 select-none pointer-events-none"
                      />
                    </div>

                    {/* Dialogue / Subtitle Caption Bar */}
                    {currentPanel.dialogue_text && (
                      <div className="mt-3.5 max-w-2xl px-5 py-2.5 rounded-xl bg-black/80 backdrop-blur-md border border-white/15 text-center shadow-lg">
                        <p className="text-xs sm:text-sm font-medium text-white/95 leading-relaxed font-serif">
                          {sanitizeDisplayProse(currentPanel.dialogue_text)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Next Button */}
                <button
                  onClick={() => setComicPanelIndex((prev) => Math.min(total - 1, prev + 1))}
                  disabled={comicPanelIndex === total - 1}
                  className="z-10 w-11 h-11 sm:w-14 sm:h-14 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-20 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all backdrop-blur-sm border border-white/15 shadow-xl shrink-0"
                  title={lang === "vi" ? "Trang sau (→)" : "Next page (→)"}
                >
                  <ChevronRight className="w-6 h-6 sm:w-7 sm:h-7" />
                </button>
              </div>

              {/* Bottom Thumbnail Strip & Navigation Hint */}
              <div className="border-t border-white/10 bg-black/60 shrink-0 py-3 px-6 flex flex-col items-center gap-2">
                {/* Thumbnails */}
                <div className="flex items-center justify-center gap-2 overflow-x-auto max-w-full pb-1 scrollbar-none">
                  {panels.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => setComicPanelIndex(idx)}
                      className={`h-11 w-11 sm:h-14 sm:w-14 rounded-lg overflow-hidden border-2 transition-all shrink-0 ${
                        idx === comicPanelIndex
                          ? "border-indigo-500 scale-105 shadow-md shadow-indigo-500/40 opacity-100"
                          : "border-white/20 opacity-40 hover:opacity-80"
                      }`}
                      title={lang === "vi" ? `Trang ${idx + 1}` : `Page ${idx + 1}`}
                    >
                      <img
                        src={p.image_url}
                        alt={`Trang ${idx + 1}`}
                        className="w-full h-full object-cover filter grayscale"
                      />
                    </button>
                  ))}
                </div>

                {/* Keyboard & Gesture Hints */}
                <div className="text-[11px] text-white/50 text-center flex flex-wrap items-center justify-center gap-3 sm:gap-6">
                  <span>
                    {lang === "vi" ? "Dùng phím" : "Use keys"}{" "}
                    <kbd className="px-1.5 py-0.5 rounded bg-white/10 border border-white/20 text-white/80">←</kbd>{" "}
                    <kbd className="px-1.5 py-0.5 rounded bg-white/10 border border-white/20 text-white/80">→</kbd>{" "}
                    {lang === "vi" ? "để lật trang" : "to navigate"}
                  </span>
                  <span>{lang === "vi" ? "Vuốt màn hình cảm ứng để chuyển ảnh" : "Swipe on touch screen"}</span>
                  <span>
                    {lang === "vi" ? "Bấm" : "Press"}{" "}
                    <kbd className="px-1.5 py-0.5 rounded bg-white/10 border border-white/20 text-white/80">Esc</kbd>{" "}
                    {lang === "vi" ? "để thoát" : "to exit"}
                  </span>
                </div>
              </div>
            </div>
          );
        })()
      )}
    </div>
  );
}
