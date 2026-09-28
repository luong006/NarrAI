"use client";

import { useEffect, useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { api } from "@/lib/api";
import { TrendingTopic, GenreCategory } from "@/lib/types";
import { Sparkles, Search, Flame, BookOpen } from "lucide-react";
import { useToast } from "@/lib/toast";

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

interface LocalizedTopic extends TrendingTopic {
  title_en?: string;
  genre_en?: string;
  description_en?: string;
  prompt_snippet_en?: string;
}

const THEME_EN_MAP: Record<string, { title_en: string; genre_en: string; description_en: string; prompt_snippet_en: string }> = {
  trend_chua_lanh: {
    title_en: "Healing & Rural Escape",
    genre_en: "Slice of Life, Romance",
    description_en: "Leaving urban pressure behind to heal the soul in a tranquil countryside, intertwined with gentle romance.",
    prompt_snippet_en: "Write a heartwarming slice-of-life story set in a tranquil countryside retreat like Da Lat or the Northwest. Focus on natural scenery, rustic meals, and an unfolding gentle romance.",
  },
  trend_trung_sinh: {
    title_en: "Rebirth Revenge & Powerful Female Lead",
    genre_en: "Drama, Intellectual Battle",
    description_en: "The protagonist is reborn after a tragic fate, using memories of the past to turn the tables and punish traitors.",
    prompt_snippet_en: "Write a dramatic revenge thriller where a sharp, decisive female protagonist is reborn 5 years before tragedy strikes. She uses prior knowledge to lay traps and dismantle her enemies.",
  },
  trend_trung_sinh_nu_cuong: {
    title_en: "Rebirth Revenge & Powerful Female Lead",
    genre_en: "Drama, Intellectual Battle",
    description_en: "The protagonist is reborn after a tragic fate, using memories of the past to turn the tables and punish traitors.",
    prompt_snippet_en: "Write a dramatic revenge thriller where a sharp, decisive female protagonist is reborn 5 years before tragedy strikes. She uses prior knowledge to lay traps and dismantle her enemies.",
  },
  trend_cuoi_truoc: {
    title_en: "Contract Marriage to True Love",
    genre_en: "Romance, Contemporary",
    description_en: "A classic contract marriage for mutual benefit where daily life turns two reluctant partners into devoted soulmates.",
    prompt_snippet_en: "Write a witty modern romance with a contract marriage trope. Two leads sign a 1-year marriage of convenience. Starting as rivals, shared daily moments spark genuine love.",
  },
  trend_cuoi_truoc_yeu_sau: {
    title_en: "Contract Marriage to True Love",
    genre_en: "Romance, Contemporary",
    description_en: "A classic contract marriage for mutual benefit where daily life turns two reluctant partners into devoted soulmates.",
    prompt_snippet_en: "Write a witty modern romance with a contract marriage trope. Two leads sign a 1-year marriage of convenience. Starting as rivals, shared daily moments spark genuine love.",
  },
  trend_linh_di: {
    title_en: "Vietnamese Folklore Supernatural",
    genre_en: "Horror, Thriller",
    description_en: "Exploring folk beliefs, rural folklore, ancient rituals, karmic retribution, and eerie village mysteries.",
    prompt_snippet_en: "Write a chilling supernatural suspense mystery rooted in Vietnamese village folklore. Atmospheric setting with midnight knocks, shadows, and karmic justice.",
  },
  trend_linh_di_dan_gian: {
    title_en: "Vietnamese Folklore Supernatural",
    genre_en: "Horror, Thriller",
    description_en: "Exploring folk beliefs, rural folklore, ancient rituals, karmic retribution, and eerie village mysteries.",
    prompt_snippet_en: "Write a chilling supernatural suspense mystery rooted in Vietnamese village folklore. Atmospheric setting with midnight knocks, shadows, and karmic justice.",
  },
  trend_he_thong: {
    title_en: "Transmigration & Whimsical System",
    genre_en: "Comedy, Isekai",
    description_en: "Transmigrating into a novel as a villain, but innocent laziness and comedic blunders charm everyone instead.",
    prompt_snippet_en: "Write a hilarious transmigration comedy where an unwilling villain is forced by a system to do bad deeds, but sheer clumsiness and humor turn every evil plan into a comedy show.",
  },
  trend_he_thong_vo_tri: {
    title_en: "Transmigration & Whimsical System",
    genre_en: "Comedy, Isekai",
    description_en: "Transmigrating into a novel as a villain, but innocent laziness and comedic blunders charm everyone instead.",
    prompt_snippet_en: "Write a hilarious transmigration comedy where an unwilling villain is forced by a system to do bad deeds, but sheer clumsiness and humor turn every evil plan into a comedy show.",
  },
  trend_thanh_xuan_vuon_truong: {
    title_en: "School Youth & First Love",
    genre_en: "Youth, Romance",
    description_en: "Nostalgic high school memories, pure first romantic feelings, summer rain, and graduation bittersweet moments.",
    prompt_snippet_en: "Write a nostalgic youth romance about high school memories in Vietnam: window seat, white ao dai, cicadas, and an unconfessed first love.",
  },
  trend_cong_so_gen_z: {
    title_en: "Office Drama & Gen Z Worklife",
    genre_en: "Realism, Comedy",
    description_en: "A witty satirical take on office life, tight deadlines, and hilarious exchanges between a Gen Z employee and a strict boss.",
    prompt_snippet_en: "Write a humorous modern office story about a Gen Z worker juggling deadlines, office politics, and banter with an exacting yet protective boss.",
  },
};

const FALLBACK_THEMES: LocalizedTopic[] = [
  {
    id: "trend_chua_lanh",
    title: "Chữa lành & Bỏ phố về quê",
    title_en: "Healing & Rural Escape",
    genre: "Slice of Life, Lãng mạn",
    genre_en: "Slice of Life, Romance",
    tags: ["chữa lành", "thanh bình", "Đà Lạt"],
    description: "Rời bỏ áp lực đô thị, tìm về vùng quê thanh bình chữa lành tâm hồn.",
    description_en: "Leaving urban pressure behind to heal the soul in a tranquil countryside, intertwined with gentle romance.",
    prompt_snippet: "Viết một câu chuyện nhẹ nhàng mang phong cách chữa lành tại một vùng quê yên bình, bối cảnh thiên nhiên trong lành và tình cảm chớm nở.",
    prompt_snippet_en: "Write a heartwarming slice-of-life story set in a tranquil countryside retreat like Da Lat or the Northwest. Focus on natural scenery, rustic meals, and an unfolding gentle romance.",
  },
  {
    id: "trend_trung_sinh_nu_cuong",
    title: "Trùng sinh báo thù & Nữ cường",
    title_en: "Rebirth Revenge & Powerful Female Lead",
    genre: "Drama, Đấu trí",
    genre_en: "Drama, Intellectual Battle",
    tags: ["trùng sinh", "nữ cường", "báo thù"],
    description: "Nhân vật chính sống lại sau kiếp bi thảm, dùng ký ức kiếp trước lật ngược ván cờ.",
    description_en: "The protagonist is reborn after a tragic fate, using memories of the past to turn the tables and punish traitors.",
    prompt_snippet: "Viết một câu chuyện kịch tính về nhân vật trùng sinh quay lại quá khứ, thông minh, quyết đoán, từng bước vạch trần kẻ phản bội.",
    prompt_snippet_en: "Write a dramatic revenge thriller where a sharp, decisive female protagonist is reborn 5 years before tragedy strikes. She uses prior knowledge to lay traps and dismantle her enemies.",
  },
  {
    id: "trend_cuoi_truoc_yeu_sau",
    title: "Cưới trước yêu sau / Hợp đồng",
    title_en: "Contract Marriage to True Love",
    genre: "Ngôn tình, Hiện đại",
    genre_en: "Romance, Contemporary",
    tags: ["hợp đồng", "oan gia", "ngọt ngào"],
    description: "Hợp đồng hôn nhân vì lợi ích, từ oan gia dần trở thành tri kỷ chân chính.",
    description_en: "A classic contract marriage for mutual benefit where daily life turns two reluctant partners into devoted soulmates.",
    prompt_snippet: "Viết một truyện tình cảm hiện đại motif cưới trước yêu sau, ban đầu là hợp đồng 1 năm, dần dà lửa gần rơm bén lửa.",
    prompt_snippet_en: "Write a witty modern romance with a contract marriage trope. Two leads sign a 1-year marriage of convenience. Starting as rivals, shared daily moments spark genuine love.",
  },
  {
    id: "trend_linh_di_dan_gian",
    title: "Linh dị dân gian Việt Nam",
    title_en: "Vietnamese Folklore Supernatural",
    genre: "Kinh dị, Giật gân",
    genre_en: "Horror, Thriller",
    tags: ["tâm linh", "dân gian", "bí ẩn"],
    description: "Khai thác tín ngưỡng dân gian, truyền thuyết làng quê và luật nhân quả.",
    description_en: "Exploring folk beliefs, rural folklore, ancient rituals, karmic retribution, and eerie village mysteries.",
    prompt_snippet: "Viết một truyện ngắn kinh dị mang màu sắc tâm linh dân gian Việt Nam, bối cảnh làng quê cổ kính, không khí âm u hồi hộp.",
    prompt_snippet_en: "Write a chilling supernatural suspense mystery rooted in Vietnamese village folklore. Atmospheric setting with midnight knocks, shadows, and karmic justice.",
  },
  {
    id: "trend_he_thong_vo_tri",
    title: "Xuyên thư & Hệ thống 'Vô tri'",
    title_en: "Transmigration & Whimsical System",
    genre: "Hài hước, Xuyên không",
    genre_en: "Comedy, Isekai",
    tags: ["hài hước", "xuyên thư", "vô tri"],
    description: "Xuyên vào tiểu thuyết làm nhân vật phản diện nhưng do vô tri nên tạo ra hàng loạt tình huống tấu hài.",
    description_en: "Transmigrating into a novel as a villain, but innocent laziness and comedic blunders charm everyone instead.",
    prompt_snippet: "Viết một câu chuyện hài hước về nhân vật xuyên vào tiểu thuyết, bị ép làm vai ác nhưng tính cách lười biếng vô tri tạo nên trò cười.",
    prompt_snippet_en: "Write a hilarious transmigration comedy where an unwilling villain is forced by a system to do bad deeds, but sheer clumsiness and humor turn every evil plan into a comedy show.",
  },
  {
    id: "trend_thanh_xuan_vuon_truong",
    title: "Thanh xuân vườn trường & Tình đầu",
    title_en: "School Youth & First Love",
    genre: "Thanh xuân, Lãng mạn",
    genre_en: "Youth, Romance",
    tags: ["thanh xuân", "cấp 3", "tình đầu"],
    description: "Cảm giác hoài niệm về những năm tháng học trò cấp 3, những rung động đầu đời trong veo.",
    description_en: "Nostalgic high school memories, pure first romantic feelings, summer rain, and graduation bittersweet moments.",
    prompt_snippet: "Viết một truyện ngắn về chủ đề thanh xuân vườn trường bối cảnh cấp 3 với áo dài, tiếng ve kêu và lời tỏ tình dang dở.",
    prompt_snippet_en: "Write a nostalgic youth romance about high school memories in Vietnam: window seat, white ao dai, cicadas, and an unconfessed first love.",
  },
  {
    id: "trend_cong_so_gen_z",
    title: "Drama công sở & Gen Z đi làm",
    title_en: "Office Drama & Gen Z Worklife",
    genre: "Hiện thực, Hài hước",
    genre_en: "Realism, Comedy",
    tags: ["công sở", "Gen Z", "deadline"],
    description: "Góc nhìn hài hước, châm biếm về đời sống văn phòng và những tình huống dở khóc dở cười giữa sếp và nhân viên.",
    description_en: "A witty satirical take on office life, tight deadlines, and hilarious exchanges between a Gen Z employee and a strict boss.",
    prompt_snippet: "Viết một mẩu chuyện đời sống công sở hiện đại với góc nhìn hài hước về nhân viên Gen Z vật lộn với deadline.",
    prompt_snippet_en: "Write a humorous modern office story about a Gen Z worker juggling deadlines, office politics, and banter with an exacting yet protective boss.",
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
  const [trendingTopics, setTrendingTopics] = useState<LocalizedTopic[]>(FALLBACK_THEMES);

  const t = translations[lang];
  const { toast } = useToast();

  useEffect(() => {
    api.getTrendingTopics().then((res) => {
      if (res.status === "success" && res.topics && res.topics.length > 0) {
        setTrendingTopics(
          res.topics.map((t: LocalizedTopic) => {
            const en = THEME_EN_MAP[t.id] || FALLBACK_THEMES.find((f) => f.id === t.id || t.id.startsWith(f.id) || f.id.startsWith(t.id));
            return {
              ...t,
              title_en: t.title_en || en?.title_en,
              genre_en: t.genre_en || en?.genre_en,
              description_en: t.description_en || en?.description_en,
              prompt_snippet_en: t.prompt_snippet_en || en?.prompt_snippet_en,
            };
          })
        );
      }
    });
  }, []);

  const toggleGenre = (genreVi: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genreVi) ? prev.filter((item) => item !== genreVi) : [...prev, genreVi]
    );
  };

  const toggleTheme = (theme: LocalizedTopic) => {
    const title = lang === "vi" ? theme.title : theme.title_en || theme.title;
    const isSelected = selectedThemes.includes(title);
    if (isSelected) {
      setSelectedThemes((prev) => prev.filter((item) => item !== title));
    } else {
      setSelectedThemes((prev) => [...prev, title]);
      // If prompt is empty, suggest snippet
      const snippet = lang === "vi" ? theme.prompt_snippet : theme.prompt_snippet_en || theme.prompt_snippet;
      if (!prompt.trim() && snippet) {
        setPrompt(snippet);
      }
    }
  };

  const handleNext = () => {
    let combined = prompt.trim();
    const genrePrefix = t.tag_genre_prefix || (lang === "vi" ? "Thể loại: " : "Genre: ");
    const themePrefix = t.tag_theme_prefix || (lang === "vi" ? "Chủ đề: " : "Theme: ");

    if (selectedGenres.length > 0) {
      combined = `[${genrePrefix}${selectedGenres.join(", ")}] ${combined}`;
    }
    if (selectedThemes.length > 0) {
      combined = `[${themePrefix}${selectedThemes.join(", ")}] ${combined}`;
    }

    if (!combined.trim()) {
      toast.error(t.idea_validation_error);
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
          {t.step1_sub}
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
                ({selectedGenres.length} {t.selected_count})
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
              ({selectedThemes.length} {t.selected_count})
            </span>
          )}
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {trendingTopics.map((theme) => {
            const title = lang === "vi" ? theme.title : theme.title_en || theme.title;
            const genre = lang === "vi" ? theme.genre : theme.genre_en || theme.genre;
            const description = lang === "vi" ? theme.description : theme.description_en || theme.description;
            const isSelected = selectedThemes.includes(title);

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
                    🔥 {title}
                  </span>
                  <span className="text-[10px] text-slate-400">{genre}</span>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                  {description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Prompt Textarea */}
      <div className="mb-6">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
          {t.your_premise}
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
