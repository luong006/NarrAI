"use client";

import { useEffect, useState } from "react";
import { ClientPortal } from "@/components/portals/ClientPortal";
import { api } from "@/lib/api";
import { StoryDetail } from "@/lib/types";
import { translations, Language } from "@/lib/i18n";
import { useToast } from "@/lib/toast";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectStory: (story: StoryDetail) => void;
  lang: Language;
}

export function HistoryModal({ isOpen, onClose, onSelectStory, lang }: Props) {
  const [stories, setStories] = useState<StoryDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const t = translations[lang];
  const { toast } = useToast();

  useEffect(() => {
    if (isOpen) {
      fetchStories();
    }
  }, [isOpen]);

  const fetchStories = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.getStories();
      if (res.status === 'success' && res.stories) {
        setStories(res.stories);
      } else {
        setStories([]);
      }
    } catch (e: any) {
      setError(e.message || (lang === 'vi' ? "Lỗi tải lịch sử truyện." : "Failed to load story history."));
    } finally {
      setLoading(false);
    }
  };

  const handleStoryClick = async (id: number) => {
    setLoading(true);
    try {
      const res = await api.getStoryDetail(id);
      if (res.status === 'success' && res.story) {
        onSelectStory(res.story);
        onClose();
      } else {
        toast.error(t.unknown_error || (lang === 'vi' ? "Không thể tải chi tiết truyện." : "Failed to load story details."));
      }
    } catch (e: any) {
      toast.error(e.message || t.network_error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <ClientPortal zIndex={60}>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 select-none font-sans">
        <div className="relative w-full max-w-2xl max-h-[85vh] bg-[#FAF7F2] rounded-xl p-6 shadow-2xl border border-neutral-300/80 flex flex-col text-neutral-900">
          <div className="flex items-center justify-between pb-4 border-b border-neutral-300/70 mb-4">
            <div className="flex items-center gap-2.5">
              <span className="px-2 py-0.5 rounded border border-neutral-300/80 bg-white font-mono text-xs font-bold uppercase shadow-xs">
                [LỊCH SỬ]
              </span>
              <h2 className="text-base font-bold font-mono uppercase tracking-wider text-neutral-950">
                {t.story_history}
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="px-2 py-0.5 text-xs font-mono font-bold uppercase rounded border border-neutral-300/80 bg-white text-neutral-700 hover:text-neutral-950 hover:bg-neutral-100 transition-colors shadow-xs"
            >
              [ĐÓNG]
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1 font-mono">
            {loading && (
              <div className="py-12 text-center text-xs text-neutral-500">
                {t.loading}
              </div>
            )}

            {error && (
              <div className="p-3 rounded border border-red-300 bg-red-50 text-red-700 text-xs">
                [LỖI]: {error}
              </div>
            )}

            {!loading && !error && stories.length === 0 && (
              <div className="py-16 text-center text-neutral-500 text-xs">
                <div className="mb-2 font-bold">[TRỐNG]</div>
                <p>{lang === 'vi' ? "Bạn chưa có bản thảo nào được lưu." : "No saved manuscripts found."}</p>
              </div>
            )}

            {!loading &&
              stories.map((story) => (
                <div
                  key={story.id}
                  onClick={() => handleStoryClick(story.id)}
                  className="p-4 rounded border border-neutral-300/70 bg-white hover:bg-neutral-100/70 cursor-pointer transition-colors shadow-xs"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <h3 className="font-bold text-sm text-neutral-950 line-clamp-1">
                      {story.title || story.refined_prompt || (lang === 'vi' ? "Bản thảo không tên" : "Untitled Manuscript")}
                    </h3>
                    <span className="text-xs text-neutral-500 font-mono">
                      {story.word_count || 0} {t.words}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-600 line-clamp-2 mb-2 font-sans">
                    {(story.snippet || story.story_content || "").replace(/<[^>]*>/g, "").replace(/&nbsp;/gi, " ").trim()}
                  </p>
                  <div className="text-[11px] text-neutral-500 font-mono">
                    <span>{story.created_at}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </ClientPortal>
  );
}
