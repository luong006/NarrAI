"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { Language, translations } from "@/lib/i18n";
import { SocialPost, SocialComment } from "@/lib/types";
import { api } from "@/lib/api";
import { InteractiveTiltCard } from "@/components/cards/InteractiveTiltCard";
import { LikeButtonMorphicon } from "@/components/morphicons/LikeButtonMorphicon";
import { useToast } from "@/lib/toast";
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
  const { toast } = useToast();
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [feedType, setFeedType] = useState<"recommended" | "following">("recommended");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [isGenreMenuOpen, setIsGenreMenuOpen] = useState(false);
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
  const readerScrollSignalsRef = useRef({ postId: 0, fiftyPercent: false, complete: false });

  // Feature 25: Search box on Posts tab
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");

  // Feature 24: Fullscreen Comic Reader sequential carousel & swipe
  const [isComicReaderOpen, setIsComicReaderOpen] = useState(false);
  const [comicPanelIndex, setComicPanelIndex] = useState(0);
  const [comicReaderPost, setComicReaderPost] = useState<SocialPost | null>(null);
  const touchStartXRef = useRef<number | null>(null);
  const touchStartYRef = useRef<number | null>(null);
  const openedSharedPostRef = useRef<string | null>(null);
  const feedScrollRef = useRef<HTMLDivElement | null>(null);
  const loadMoreSentinelRef = useRef<HTMLDivElement | null>(null);
  const loadingMoreRef = useRef(false);
  const feedRequestIdRef = useRef(0);

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

  const filteredPosts = posts;
  const genreGroups = [
    {
      labelVi: "Bối cảnh & thời đại",
      labelEn: "Setting & era",
      options: [
        { id: "Lịch sử", vi: "Lịch sử", en: "Historical" },
        { id: "Dã sử", vi: "Dã sử", en: "Historical fiction" },
        { id: "Học đường", vi: "Học đường", en: "School life" },
        { id: "Đô thị", vi: "Đô thị", en: "Urban" },
        { id: "Cyberpunk", vi: "Cyberpunk", en: "Cyberpunk" },
      ],
    },
    {
      labelVi: "Thể loại",
      labelEn: "Genres",
      options: [
        { id: "Tiên hiệp", vi: "Tiên hiệp", en: "Xianxia" },
        { id: "Kỳ ảo", vi: "Kỳ ảo", en: "Fantasy" },
        { id: "Kiếm hiệp", vi: "Kiếm hiệp", en: "Wuxia" },
        { id: "Khoa học viễn tưởng", vi: "Khoa học viễn tưởng", en: "Science fiction" },
        { id: "Trinh thám", vi: "Trinh thám", en: "Mystery" },
        { id: "Kinh dị", vi: "Kinh dị", en: "Horror" },
        { id: "Tình cảm", vi: "Tình cảm", en: "Romance" },
        { id: "Phiêu lưu", vi: "Phiêu lưu", en: "Adventure" },
      ],
    },
    {
      labelVi: "Chủ đề",
      labelEn: "Themes",
      options: [
        { id: "Chữa lành", vi: "Chữa lành", en: "Healing" },
        { id: "Gia đình", vi: "Gia đình", en: "Family" },
        { id: "Chiến tranh", vi: "Chiến tranh", en: "War" },
        { id: "Hài hước", vi: "Hài hước", en: "Comedy" },
      ],
    },
  ];

  const fetchFeed = async (
    type = feedType,
    append = false
  ) => {
    const requestId = append
      ? feedRequestIdRef.current
      : ++feedRequestIdRef.current;
    if (append) {
      if (loadingMoreRef.current) return;
      loadingMoreRef.current = true;
      setLoadingMore(true);
    } else {
      loadingMoreRef.current = false;
      setLoadingMore(false);
      setLoading(true);
    }
    try {
      const offset = append ? posts.length : 0;
      const res = await api.getSocialFeed({
        genres: selectedGenres,
        q: debouncedSearchQuery,
        limit: 24,
        offset,
        feed_type: type,
      });
      if (requestId !== feedRequestIdRef.current) return;
      if (res.success && res.data && Array.isArray(res.data.items)) {
        setPosts((prev) => {
          if (!append) return res.data.items;
          const seen = new Set(prev.map((post) => post.id));
          return [...prev, ...res.data.items.filter((post) => !seen.has(post.id))];
        });
        setHasMore(res.data.has_more);
      } else {
        if (!append) setPosts([]);
        setHasMore(false);
        toast.error(res.message || (lang === "vi" ? "Không thể tải bảng tin." : "Unable to load the feed."));
      }
    } catch (err) {
      if (requestId !== feedRequestIdRef.current) return;
      console.error("Failed to load community feed:", err);
      if (!append) setPosts([]);
      setHasMore(false);
      toast.error(lang === "vi" ? "Không thể tải bảng tin cộng đồng." : "Unable to load the community feed.");
    } finally {
      if (append && requestId === feedRequestIdRef.current) {
        loadingMoreRef.current = false;
        setLoadingMore(false);
      }
      else if (!append && requestId === feedRequestIdRef.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearchQuery(searchQuery.trim()), 350);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    fetchFeed(feedType);
  }, [selectedGenres, debouncedSearchQuery, feedType]);

  useEffect(() => {
    const sentinel = loadMoreSentinelRef.current;
    const root = feedScrollRef.current;
    if (!sentinel || !root || !hasMore || loading || loadingMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting) && !loadingMore) {
          void fetchFeed(feedType, true);
        }
      },
      { root, rootMargin: "500px 0px" }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [feedType, hasMore, loading, loadingMore, posts.length]);

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
    readerScrollSignalsRef.current = {
      postId: post.id,
      fiftyPercent: false,
      complete: false,
    };

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

  const handleReaderScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, clientHeight, scrollHeight } = event.currentTarget;
    const progress = scrollHeight > 0 ? (scrollTop + clientHeight) / scrollHeight : 0;
    const signals = readerScrollSignalsRef.current;
    if (!activePost || signals.postId !== activePost.id) return;

    const milestones: Array<{ threshold: number; type: "SCROLL_50" | "SCROLL_100"; key: "fiftyPercent" | "complete" }> = [
      { threshold: 0.5, type: "SCROLL_50", key: "fiftyPercent" },
      { threshold: 0.98, type: "SCROLL_100", key: "complete" },
    ];
    for (const milestone of milestones) {
      if (progress >= milestone.threshold && !signals[milestone.key]) {
        signals[milestone.key] = true;
        void api.interactPost({
          post_id: activePost.id,
          interaction_type: milestone.type,
          scroll_depth: milestone.type === "SCROLL_100" ? 100 : 50,
        }).then((result) => {
          if (!result.success) console.error(`Failed to record ${milestone.type} interaction:`, result.message);
        }).catch((error) => {
          console.error(`Failed to record ${milestone.type} interaction:`, error);
        });
      }
    }
  };

  useEffect(() => {
    const sharedPostId = new URLSearchParams(window.location.search).get("post");
    if (!sharedPostId || !/^\d+$/.test(sharedPostId) || loading) return;
    if (openedSharedPostRef.current === sharedPostId) return;
    openedSharedPostRef.current = sharedPostId;

    const post = posts.find((item) => item.id === Number(sharedPostId));
    if (post) {
      void handleOpenReader(post);
      return;
    }

    void api.getPostDetails(Number(sharedPostId)).then((res) => {
      if (res.success && res.data) {
        setActivePost(res.data);
        setIsReadingModalOpen(true);
        dwellStartTimeRef.current = Date.now();
      } else {
        toast.error(lang === "vi" ? "Không tìm thấy bài viết được chia sẻ." : "The shared post could not be found.");
      }
    }).catch((error) => {
      console.error("Failed to open shared post:", error);
      toast.error(lang === "vi" ? "Không thể mở bài viết được chia sẻ." : "Unable to open the shared post.");
    });
  }, [loading, posts]);

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
    const url = new URL(window.location.href);
    if (url.searchParams.has("post")) {
      url.searchParams.delete("post");
      url.searchParams.delete("tab");
      window.history.replaceState({}, "", url);
      openedSharedPostRef.current = null;
    }
  };

  const handleLikeToggle = async (postId: number, liked: boolean) => {
    try {
      const res = await api.interactPost({
        post_id: postId,
        interaction_type: "LIKE",
      });
      if (!res.success) {
        toast.error(res.message || (lang === "vi" ? "Không thể cập nhật lượt thích." : "Unable to update the like."));
        return;
      }

      setPosts((prev) =>
        prev.map((p) =>
          p.id === postId
            ? { ...p, likes_count: res.metadata?.post_likes ?? (liked ? p.likes_count + 1 : Math.max(0, p.likes_count - 1)), liked_by_me: liked }
            : p
        )
      );

      if (activePost && activePost.id === postId) {
        setActivePost((prev) =>
          prev
            ? { ...prev, likes_count: res.metadata?.post_likes ?? (liked ? prev.likes_count + 1 : Math.max(0, prev.likes_count - 1)), liked_by_me: liked }
            : null
        );
      }
    } catch (err) {
      console.error("Error liking post:", err);
      toast.error(lang === "vi" ? "Không thể cập nhật lượt thích." : "Unable to update the like.");
    }
  };

  const handleSharePost = async (post: SocialPost) => {
    const url = new URL("/", window.location.origin);
    url.searchParams.set("tab", "posts");
    url.searchParams.set("post", String(post.id));

    let shared = false;
    if (navigator.share) {
      try {
        await navigator.share({ title: post.title, text: post.content_snippet, url: url.toString() });
        shared = true;
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
      }
    }

    if (!shared) {
      try {
        await navigator.clipboard.writeText(url.toString());
        shared = true;
        toast.success(lang === "vi" ? "Đã sao chép liên kết bài viết." : "Post link copied.");
      } catch (error) {
        console.error("Failed to copy shared post link:", error);
        toast.error(lang === "vi" ? "Không thể chia sẻ hoặc sao chép liên kết." : "Unable to share or copy the link.");
        return;
      }
    }

    const result = await api.interactPost({
      post_id: post.id,
      interaction_type: "SHARE",
    });
    if (!result.success) {
      toast.error(result.message || (lang === "vi" ? "Đã chia sẻ nhưng không ghi nhận được lượt chia sẻ." : "Shared, but the share could not be recorded."));
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
          id: res.interaction_id || Date.now(),
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
      } else {
        toast.error(res.message || (lang === "vi" ? "Không thể gửi bình luận." : "Unable to post the comment."));
      }
    } catch (err) {
      console.error("Error submitting comment:", err);
      toast.error(lang === "vi" ? "Không thể gửi bình luận." : "Unable to post the comment.");
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
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#f2eee7] dark:bg-[#211d19] text-[#342722] dark:text-[#eee6d9]">

      {/* Facebook-style top bar: search + genre chips */}
      <div className="shrink-0 bg-[#faf7f0] dark:bg-[#28231f] border-b border-[#ded5c9] dark:border-[#50453c] px-4 py-2.5">
        {/* Row 1: search */}
        <div className="flex items-center gap-2 max-w-2xl mx-auto">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={lang === "vi" ? "Tìm theo tag, thể loại hoặc nội dung..." : "Search tags, genres, or story content..."}
              className="w-full pl-9 pr-8 py-2 text-sm rounded-lg border border-[#ded5c9] dark:border-[#50453c] bg-[#f2eee7] dark:bg-[#332c26] text-[#342722] dark:text-[#eee6d9] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#9f684a]/30 transition-all"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <button
            onClick={() => fetchFeed(feedType)}
            disabled={loading}
            className="p-2 rounded-lg bg-[#f2eee7] dark:bg-[#332c26] text-slate-500 hover:bg-[#e9dfd0] dark:hover:bg-[#45352c] transition-colors shrink-0"
            title={lang === "vi" ? "Làm mới" : "Refresh"}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        <div className="flex gap-2 max-w-2xl mx-auto pt-2">
          {([
            { id: "recommended", vi: "Khám phá", en: "For you" },
            { id: "following", vi: "Đang theo dõi", en: "Following" },
          ] as const).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFeedType(tab.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors ${
                feedType === tab.id
                  ? "bg-[#714033] text-[#fffaf0] shadow-sm"
                  : "bg-[#f2eee7] dark:bg-[#332c26] text-slate-600 dark:text-slate-400 hover:bg-[#e9dfd0] dark:hover:bg-[#45352c]"
              }`}
            >
              {lang === "vi" ? tab.vi : tab.en}
            </button>
          ))}
        </div>

        <div className="relative max-w-2xl mx-auto pt-2">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setIsGenreMenuOpen((open) => !open)}
              aria-expanded={isGenreMenuOpen}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#f2eee7] dark:bg-[#332c26] text-slate-700 dark:text-slate-200 hover:bg-[#e9dfd0] dark:hover:bg-[#45352c] flex items-center gap-2"
            >
              {lang === "vi" ? "Thể loại & tag" : "Genres & tags"}
              {selectedGenres.length > 0 && (
                <span className="rounded-full bg-[#714033] text-white px-1.5 min-w-5 text-center">
                  {selectedGenres.length}
                </span>
              )}
              <ChevronRight className={`w-3.5 h-3.5 transition-transform ${isGenreMenuOpen ? "rotate-90" : ""}`} />
            </button>
            {selectedGenres.map((genre) => (
              <button
                key={genre}
                onClick={() => setSelectedGenres((prev) => prev.filter((item) => item !== genre))}
                className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#eee4d7] dark:bg-[#45352c] text-[#704331] dark:text-[#dfb79b] flex items-center gap-1"
              >
                {genre}<X className="w-3 h-3" />
              </button>
            ))}
            {(searchQuery || selectedGenres.length > 0) && (
              <button
                onClick={() => { setSearchQuery(""); setSelectedGenres([]); }}
                className="px-2.5 py-1 rounded-full text-[11px] font-semibold text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
              >
                {lang === "vi" ? "Xóa bộ lọc" : "Clear filters"}
              </button>
            )}
          </div>
          {isGenreMenuOpen && (
            <div className="absolute left-0 top-full z-30 mt-2 w-full max-w-xl max-h-[65vh] overflow-y-auto rounded-xl border border-[#ded5c9] dark:border-[#50453c] bg-[#fbf8f1] dark:bg-[#302a25] p-4 shadow-lg">
              {genreGroups.map((group) => (
                <fieldset key={group.labelEn} className="mb-4 last:mb-0">
                  <legend className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    {lang === "vi" ? group.labelVi : group.labelEn}
                  </legend>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {group.options.map((option) => {
                      const checked = selectedGenres.includes(option.id);
                      return (
                        <label
                          key={option.id}
                          className={`flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs cursor-pointer transition-colors ${
                            checked
                              ? "bg-[#eee4d7] dark:bg-[#45352c] text-[#704331] dark:text-[#dfb79b]"
                              : "bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => setSelectedGenres((prev) => (
                              checked
                                ? prev.filter((item) => item !== option.id)
                                : [...prev, option.id]
                            ))}
                            className="accent-[#805342]"
                          />
                          {lang === "vi" ? option.vi : option.en}
                        </label>
                      );
                    })}
                  </div>
                </fieldset>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Feed — scroll area */}
      <div ref={feedScrollRef} className="flex-1 overflow-y-auto py-4 px-3">
        <div className="max-w-[680px] mx-auto">
          {loading && posts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-[#9f684a] mb-3" />
              <p className="text-sm font-medium">
                {lang === "vi" ? "Đang tải các tác phẩm đề xuất..." : "Loading recommended stories..."}
              </p>
            </div>
          ) : posts.length === 0 ? (
            <div className="text-center py-20 bg-white/50 dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8">
              <BookOpen className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                {feedType === "following"
                  ? (lang === "vi" ? "Bảng tin theo dõi đang trống" : "Your following feed is empty")
                  : (lang === "vi" ? "Chưa có bài đăng nào trong chuyên mục này" : "No stories published in this category yet")}
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
                {feedType === "following"
                  ? (lang === "vi"
                      ? "Theo dõi các tác giả bạn yêu thích để xem tác phẩm mới của họ tại đây."
                      : "Follow authors you enjoy to see their new stories here.")
                  : (lang === "vi"
                      ? "Hãy là người đầu tiên sáng tác và bấm 'Lưu & Đăng bài' trong trình soạn thảo để chia sẻ tác phẩm với cộng đồng!"
                      : "Be the first to create and click 'Save & Publish' in the editor to share your story with the community!")}
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
                className="px-4 py-2 rounded-lg text-xs font-semibold text-[#fffaf0] bg-[#714033] hover:bg-[#573229] transition-colors shadow-sm"
              >
                {lang === "vi" ? "Xóa tìm kiếm" : "Clear search"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredPosts.map((post) => (
                <div
                  key={post.id}
                  className="rounded-xl bg-[#fbf8f1] dark:bg-[#302a25] border border-[#e2d8cb] dark:border-[#50453c] shadow-sm hover:shadow-md transition-shadow overflow-hidden"
                >
                  {/* Facebook-style Feed Post */}

                  {/* Post Header: avatar + author + follow */}
                  <div className="flex items-center justify-between px-4 pt-4 pb-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-9 h-9 rounded-full bg-[#714033] text-[#fffaf0] flex items-center justify-center font-semibold text-sm shrink-0">
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
                            ? "text-[#704331] dark:text-[#dfb79b] bg-[#eee4d7] dark:bg-[#45352c] border border-[#ddc9b5] dark:border-[#665044]"
                            : "text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-[#714033] hover:text-white border border-slate-200 dark:border-slate-700"
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
                      className="text-base font-bold text-slate-900 dark:text-white hover:text-[#805342] dark:hover:text-[#dfb79b] transition-colors cursor-pointer mb-1.5 leading-snug"
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
                        <button
                          key={idx}
                          onClick={() => setSearchQuery(tag)}
                          className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-[#f1ece3] dark:bg-[#332c26] text-slate-500 dark:text-slate-400 hover:bg-[#eee4d7] dark:hover:bg-[#45352c] hover:text-[#704331] dark:hover:text-[#dfb79b]"
                        >
                          #{tag}
                        </button>
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
                        <div className="flex-none w-12 bg-[#714033] flex items-center justify-center">
                          <span className="text-white text-[10px] font-bold text-center leading-tight px-1">
                            {post.comic_panels.length}<br/>panels
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Action bar: like, comment, share, views, read */}
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
                        className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 hover:text-[#805342] dark:hover:text-[#dfb79b] transition-colors"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>{post.comments_count}</span>
                      </button>
                      <button
                        onClick={() => void handleSharePost(post)}
                        className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 hover:text-[#805342] dark:hover:text-[#dfb79b] transition-colors"
                        aria-label={lang === "vi" ? "Chia sẻ bài viết" : "Share post"}
                      >
                        <Share2 className="w-3.5 h-3.5" />
                        <span>{lang === "vi" ? "Chia sẻ" : "Share"}</span>
                      </button>
                      <div className="flex items-center gap-1 text-xs text-slate-400">
                        <Eye className="w-3.5 h-3.5" />
                        <span>{post.views_count}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleOpenReader(post)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[#704331] dark:text-[#dfb79b] hover:bg-[#eee4d7] dark:hover:bg-[#45352c] flex items-center gap-1 transition-colors"
                    >
                      <span>{lang === "vi" ? "Đọc tiếp" : "Read"}</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
              {hasMore && (
                <div ref={loadMoreSentinelRef} className="flex justify-center py-6 text-xs text-slate-400">
                  {loadingMore && (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      {lang === "vi" ? "Đang tải thêm tác phẩm..." : "Loading more stories..."}
                    </span>
                  )}
                </div>
              )}
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
                <span className="px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-[#eee4d7] dark:bg-[#45352c] text-[#704331] dark:text-[#dfb79b] border border-[#ddc9b5] dark:border-[#665044] shrink-0">
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
            <div onScroll={handleReaderScroll} className="flex-1 overflow-y-auto p-6 sm:p-10 space-y-8">
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
                              ? "bg-[#eee4d7] dark:bg-[#45352c] text-[#704331] dark:text-[#dfb79b] border border-[#ddc9b5] dark:border-[#665044]"
                              : "bg-[#714033] text-[#fffaf0] hover:bg-[#573229]"
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
                  <button
                    onClick={() => void handleSharePost(activePost)}
                    className="px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-[#eee4d7] dark:hover:bg-[#45352c] hover:text-[#704331] dark:hover:text-[#dfb79b] transition-colors flex items-center gap-1.5 text-xs font-semibold"
                  >
                    <Share2 className="w-4 h-4" />
                    <span>{lang === "vi" ? "Chia sẻ" : "Share"}</span>
                  </button>
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
                      <Palette className="w-4 h-4 text-[#805342]" />
                      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                        {lang === "vi" ? "Chuyển thể Manga Comic" : "Manga Comic Adaptation"}
                      </h3>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-[#eee4d7] dark:bg-[#45352c] text-[#704331] dark:text-[#dfb79b] font-mono font-semibold">
                        {activePost.comic_panels.length} {lang === "vi" ? "khung" : "panels"}
                      </span>
                    </div>

                    <button
                      onClick={() => {
                        setComicReaderPost(activePost);
                        setComicPanelIndex(0);
                        setIsComicReaderOpen(true);
                      }}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-[#fffaf0] bg-[#714033] hover:bg-[#573229] shadow-sm flex items-center gap-1.5 transition-colors"
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
                        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-black overflow-hidden shadow-sm flex flex-col cursor-pointer group/panel hover:border-[#9f684a] transition-colors"
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
                  <MessageSquare className="w-4 h-4 text-[#805342]" />
                  <span>
                    {lang === "vi"
                      ? `Bình luận độc giả (${activePost.comments_count || 0})`
                      : `Reader Comments (${activePost.comments_count || 0})`}
                  </span>
                </h3>

                {/* Replying Banner if user clicked reply */}
                {replyingToComment && (
                  <div className="flex items-center justify-between px-3 py-1.5 bg-[#f1ece3] dark:bg-[#332c26] border border-[#e2d8cb] dark:border-[#50453c] rounded-lg text-xs text-[#704331] dark:text-[#dfb79b]">
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
                      className="p-1 rounded-md hover:bg-[#eee4d7] dark:hover:bg-[#45352c] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
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
                    className="flex-1 rounded-lg border border-[#ded5c9] dark:border-[#50453c] bg-[#fbf8f1] dark:bg-[#302a25] p-3 text-xs text-slate-900 dark:text-white outline-none focus:border-[#9f684a] transition-colors resize-none"
                  />
                  <button
                    onClick={handleAddComment}
                    disabled={!commentInput.trim() || commentSubmitting}
                    className="px-4 py-3 rounded-lg bg-[#714033] hover:bg-[#573229] text-[#fffaf0] text-xs font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 shrink-0 shadow-sm"
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
                              className="text-[11px] font-semibold text-[#805342] dark:text-[#dfb79b] hover:underline flex items-center gap-1"
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
                            className="border-l-2 border-[#b78969]/50 dark:border-[#8e6650]/60 pl-3 sm:pl-4 ml-4 sm:ml-6"
                          >
                            <div className="p-3 rounded-lg bg-[#f7f2ec] dark:bg-[#332c26] border border-[#e2d8cb] dark:border-[#50453c] text-xs">
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
                  <span className="px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-[#714033] text-[#fffaf0] shrink-0">
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
                          ? "border-[#9f684a] scale-105 shadow-md shadow-[#9f684a]/25 opacity-100"
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
