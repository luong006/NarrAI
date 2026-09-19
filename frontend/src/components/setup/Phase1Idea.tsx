"use client";

import { useEffect, useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { api } from "@/lib/api";
import { TrendingTopic, GenreCategory } from "@/lib/types";
import { Sparkles, Search, Flame, BookOpen } from "lucide-react";

// Full 28 bilingual genres grouped into 5 literary categories from legacy frontend
const GENRE_CATEGORIES: GenreCategory[] = [
  {
    name_vi: "Tình cảm",
    name_en: "Romance",
    items: [
      { vi: "Ngôn tình", en: "Romance" },
      { vi: "Đam mỹ", en: "Boys' Love (BL)" },
      { vi: "Bách hợp", en: "Girls' Love (GL)" },
      { vi: "Thanh xuân", en: "School Life" },
      { vi: "Cưới trước yêu sau", en: "Arranged Marriage" },
    ],
  },
  {
    name_vi: "Kỳ ảo & Viễn tưởng",
    name_en: "Fantasy & Sci-Fi",
    items: [
      { vi: "Tiên hiệp", en: "Xianxia" },
      { vi: "Kiếm hiệp", en: "Wuxia" },
      { vi: "Huyền huyễn", en: "Xuanhuan" },
      { vi: "Kỳ ảo", en: "Fantasy" },
      { vi: "Khoa học viễn tưởng", en: "Sci-Fi" },
      { vi: "Xuyên không", en: "Isekai" },
      { vi: "Trọng sinh", en: "Rebirth" },
      { vi: "Hệ thống", en: "System" },
      { vi: "Mạt thế", en: "Post-Apocalyptic" },
    ],
  },
  {
    name_vi: "Hành động & Phiêu lưu",
    name_en: "Action & Adventure",
    items: [
      { vi: "Hành động", en: "Action" },
      { vi: "Phiêu lưu", en: "Adventure" },
      { vi: "Võng du", en: "LitRPG" },
    ],
  },
  {
    name_vi: "Bí ẩn & Giật gân",
    name_en: "Mystery & Thriller",
    items: [
      { vi: "Trinh thám", en: "Mystery" },
      { vi: "Kinh dị", en: "Horror" },
      { vi: "Giật gân", en: "Thriller" },
      { vi: "Linh dị", en: "Supernatural" },
    ],
  },
  {
    name_vi: "Đời sống & Lịch sử",
    name_en: "Slice of Life & Historical",
    items: [
      { vi: "Đô thị", en: "Urban" },
      { vi: "Điền văn", en: "Slice of Life" },
      { vi: "Hài hước", en: "Comedy" },
      { vi: "Bi kịch", en: "Tragedy" },
      { vi: "Lịch sử", en: "Historical" },
      { vi: "Cung đấu", en: "Palace Scheme" },
    ],
  },
];

const FALLBACK_THEMES: TrendingTopic[] = [
  {
    id: "trend_chua_lanh",
    title: "Chữa lành & Bỏ phố về quê",
    genre: "Slice of Life, Lãng mạn",
    tags: ["chữa lành", "thanh bình", "Đà Lạt"],
    description: "Rời bỏ áp lực đô thị, tìm về vùng quê thanh bình chữa lành tâm hồn.",
    prompt_snippet: "Viết một câu chuyện nhẹ nhàng mang phong cách chữa lành tại một vùng quê yên bình, bối cảnh thiên nhiên trong lành và tình cảm chớm nở.",
  },
  {
    id: "trend_trung_sinh",
    title: "Trùng sinh báo thù & Nữ cường",
    genre: "Drama, Đấu trí",
    tags: ["trùng sinh", "nữ cường", "báo thù"],
    description: "Nhân vật chính sống lại sau kiếp bi thảm, dùng ký ức kiếp trước lật ngược ván cờ.",
    prompt_snippet: "Viết một câu chuyện kịch tính về nhân vật trùng sinh quay lại quá khứ, thông minh, quyết đoán, từng bước vạch trần kẻ phản bội.",
  },
  {
    id: "trend_cuoi_truoc",
    title: "Cưới trước yêu sau / Hợp đồng",
    genre: "Ngôn tình, Hiện đại",
    tags: ["hợp đồng", "oan gia", "ngọt ngào"],
    description: "Hợp đồng hôn nhân vì lợi ích, từ oan gia dần trở thành tri kỷ chân chính.",
    prompt_snippet: "Viết một truyện tình cảm hiện đại motif cưới trước yêu sau, ban đầu là hợp đồng 1 năm, dần dà lửa gần rơm bén lửa.",
  },
  {
    id: "trend_linh_di",
    title: "Linh dị dân gian Việt Nam",
    genre: "Kinh dị, Giật gân",
    tags: ["tâm linh", "dân gian", "bí ẩn"],
    description: "Khai thác tín ngưỡng dân gian, truyền thuyết làng quê và luật nhân quả.",
    prompt_snippet: "Viết một truyện ngắn kinh dị mang màu sắc tâm linh dân gian Việt Nam, bối cảnh làng quê cổ kính, không khí âm u hồi hộp.",
  },
  {
    id: "trend_he_thong",
    title: "Xuyên thư & Hệ thống 'Vô tri'",
    genre: "Hài hước, Xuyên không",
    tags: ["hài hước", "xuyên thư", "vô tri"],
    description: "Xuyên vào tiểu thuyết làm nhân vật phản diện nhưng do vô tri nên tạo ra hàng loạt tình huống tấu hài.",
    prompt_snippet: "Viết một câu chuyện hài hước về nhân vật xuyên vào tiểu thuyết, bị ép làm vai ác nhưng tính cách lười biếng vô tri tạo nên trò cười.",
  },
];

interface Props {
  lang: Language;
  onContinue: (combinedPrompt: string, genres: string[], themes: string[]) => void;
  loading: boolean;
}

export function Phase1Idea({ lang, onContinue, loading }: Props) {
  const [prompt, setPrompt] = useState("");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [genreFilter, setGenreFilter] = useState("");
  const [trendingTopics, setTrendingTopics] = useState<TrendingTopic[]>(FALLBACK_THEMES);

  const t = translations[lang];

  useEffect(() => {
    api.getTrendingTopics().then((res) => {
      if (res.status === "success" && res.topics && res.topics.length > 0) {
        setTrendingTopics(res.topics);
      }
    });
  }, []);

  const toggleGenre = (genreVi: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genreVi) ? prev.filter((item) => item !== genreVi) : [...prev, genreVi]
    );
  };

  const toggleTheme = (theme: TrendingTopic) => {
    const isSelected = selectedThemes.includes(theme.title);
    if (isSelected) {
      setSelectedThemes((prev) => prev.filter((item) => item !== theme.title));
    } else {
      setSelectedThemes((prev) => [...prev, theme.title]);
      // If prompt is empty, suggest snippet
      if (!prompt.trim() && theme.prompt_snippet) {
        setPrompt(theme.prompt_snippet);
      }
    }
  };

  const handleNext = () => {
    let combined = prompt.trim();
    if (selectedGenres.length > 0) {
      combined = `[Thể loại: ${selectedGenres.join(", ")}] ${combined}`;
    }
    if (selectedThemes.length > 0) {
      combined = `[Chủ đề: ${selectedThemes.join(", ")}] ${combined}`;
    }

    if (!combined.trim()) {
      alert(
        lang === "vi"
          ? "Vui lòng nhập ý tưởng khởi đầu hoặc chọn ít nhất 1 thể loại/chủ đề!"
          : "Please enter your story concept or select at least one genre/theme!"
      );
      return;
    }

    onContinue(combined, selectedGenres, selectedThemes);
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      {/* Header */}
      <div className="mb-6">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-900 mb-3">
          <Sparkles className="w-3 h-3" />
          <span>{t.istartup_badge}</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          {t.step1_title}
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {lang === "vi"
            ? "Lựa chọn từ 28 thể loại truyện chuẩn, hòa trộn chủ đề thịnh hành và phác thảo sơ lược ý tưởng của bạn."
            : "Select from 28 literature genres, blend trending tropes, and outline your core spark."}
        </p>
      </div>

      {/* 28 Genres Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-brand-600" />
            <span>{t.genres_label}</span>
            {selectedGenres.length > 0 && (
              <span className="text-[11px] font-mono text-brand-600 dark:text-brand-400">
                ({selectedGenres.length} đã chọn)
              </span>
            )}
          </label>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={genreFilter}
            onChange={(e) => setGenreFilter(e.target.value)}
            placeholder={t.search_genre}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
          />
        </div>

        {/* Categories container */}
        <div className="space-y-3 max-h-56 overflow-y-auto p-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60">
          {GENRE_CATEGORIES.map((cat) => {
            const filteredItems = cat.items.filter(
              (item) =>
                item.vi.toLowerCase().includes(genreFilter.toLowerCase()) ||
                item.en.toLowerCase().includes(genreFilter.toLowerCase())
            );

            if (filteredItems.length === 0) return null;

            return (
              <div key={cat.name_vi} className="space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                  {lang === "vi" ? cat.name_vi : cat.name_en}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {filteredItems.map((item) => {
                    const isSelected = selectedGenres.includes(item.vi);
                    const label = lang === "vi" ? item.vi : `${item.en} (${item.vi})`;
                    return (
                      <button
                        key={item.vi}
                        onClick={() => toggleGenre(item.vi)}
                        className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                          isSelected
                            ? "bg-brand-700 text-white shadow-sm ring-2 ring-brand-400"
                            : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:bg-slate-50"
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Trending Themes */}
      <div className="mb-6">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2">
          <Flame className="w-3.5 h-3.5 text-amber-500" />
          <span>{t.themes_label}</span>
          {selectedThemes.length > 0 && (
            <span className="text-[11px] font-mono text-amber-600 dark:text-amber-400">
              ({selectedThemes.length} đã chọn)
            </span>
          )}
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {trendingTopics.map((theme) => {
            const isSelected = selectedThemes.includes(theme.title);
            return (
              <div
                key={theme.id || theme.title}
                onClick={() => toggleTheme(theme)}
                className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                  isSelected
                    ? "bg-amber-500/10 border-amber-500 text-slate-900 dark:text-white shadow-sm"
                    : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-amber-400"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-amber-700 dark:text-amber-400">
                    🔥 {theme.title}
                  </span>
                  <span className="text-[10px] text-slate-400">{theme.genre}</span>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                  {theme.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Prompt Textarea */}
      <div className="mb-6">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
          {lang === "vi" ? "Ý tưởng cốt truyện của bạn:" : "Your story premise:"}
        </label>
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={t.prompt_placeholder}
          className="w-full p-4 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm leading-relaxed"
        />
      </div>

      {/* Continue Button */}
      <button
        onClick={handleNext}
        disabled={loading}
        className="w-full py-3.5 rounded-xl font-bold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {loading ? (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>{t.loading}</span>
          </div>
        ) : (
          <span>{t.continue_btn}</span>
        )}
      </button>
    </div>
  );
}

