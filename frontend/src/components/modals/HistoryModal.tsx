"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StoryDetail } from "@/lib/types";
import { translations, Language } from "@/lib/i18n";
import { X, BookOpen, Clock, FileText } from "lucide-react";

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
      setError(e.message || "Lỗi tải lịch sử truyện.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl max-h-[85vh] bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col">
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-600 dark:text-brand-400" />
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              {t.story_history}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {loading && (
            <div className="py-12 text-center text-slate-500 dark:text-slate-400">
              {t.loading}
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          {!loading && !error && stories.length === 0 && (
            <div className="py-16 text-center text-slate-400">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-40" />
              <p>{lang === 'vi' ? "Bạn chưa có bản thảo nào được lưu." : "No saved manuscripts found."}</p>
            </div>
          )}

          {!loading &&
            stories.map((story) => (
              <div
                key={story.id}
                onClick={() => {
                  onSelectStory(story);
                  onClose();
                }}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 hover:bg-indigo-50/50 dark:bg-slate-800/60 dark:hover:bg-slate-800 cursor-pointer transition-all hover:border-brand-300 dark:hover:border-brand-700"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <h3 className="font-semibold text-slate-900 dark:text-white text-sm line-clamp-1">
                    {story.refined_prompt || (lang === 'vi' ? "Bản thảo không tên" : "Untitled Manuscript")}
                  </h3>
                  <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                    {story.word_count || 0} {t.words}
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
                  {story.story_content?.replace(/<[^>]*>/g, '') || ""}
                </p>
                <div className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                  <Clock className="w-3 h-3" />
                  <span>{story.created_at}</span>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
