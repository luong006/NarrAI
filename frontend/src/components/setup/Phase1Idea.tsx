"use client";

import { useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { Sparkles, Search } from "lucide-react";

const PRESET_GENRES = [
  "Tiên hiệp", "Kiếm hiệp", "Khoa học viễn tưởng", "Trinh thám", 
  "Kinh dị", "Tâm lý xã hội", "Kỳ ảo (Fantasy)", "Học đường", 
  "Xuyên không", "Hài hước", "Hậu tận thế", "Drama"
];

const PRESET_THEMES = [
  "Trí tuệ nhân tạo thức tỉnh", "Hành trình báo thù", "Xuyên qua dị giới", 
  "Sát thủ về hưu", "Bí ẩn căn phòng khóa kín", "Tận thế băng giá",
  "Khám phá di tích cổ xưa", "Đấu trí thương trường", "Tình cảm lãng mạn"
];

interface Props {
  lang: Language;
  onContinue: (prompt: string, genres: string[], themes: string[]) => void;
}

export function Phase1Idea({ lang, onContinue }: Props) {
  const [prompt, setPrompt] = useState("");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [genreFilter, setGenreFilter] = useState("");

  const t = translations[lang];

  const toggleGenre = (g: string) => {
    setSelectedGenres((prev) =>
      prev.includes(g) ? prev.filter((item) => item !== g) : [...prev, g]
    );
  };

  const toggleTheme = (theme: string) => {
    setSelectedThemes((prev) =>
      prev.includes(theme) ? prev.filter((item) => item !== theme) : [...prev, theme]
    );
  };

  const handleNext = () => {
    if (!prompt.trim()) {
      alert(lang === 'vi' ? "Vui lòng nhập ý tưởng khởi đầu cho câu chuyện." : "Please enter your initial story concept.");
      return;
    }
    onContinue(prompt.trim(), selectedGenres, selectedThemes);
  };

  const filteredGenres = PRESET_GENRES.filter((g) =>
    g.toLowerCase().includes(genreFilter.toLowerCase())
  );

  return (
    <div className="max-w-3xl mx-auto py-8 px-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          {t.step1_title}
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {lang === 'vi' ? "Chọn thể loại, chủ đề và phác thảo sơ lược ý tưởng của bạn." : "Select genres, trending themes, and jot down your core story spark."}
        </p>
      </div>

      {/* Genres */}
      <div className="mb-6">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
          {t.genres_label}
        </label>
        <div className="relative mb-3">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={genreFilter}
            onChange={(e) => setGenreFilter(e.target.value)}
            placeholder={t.search_genre}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
          {filteredGenres.map((g) => {
            const isSelected = selectedGenres.includes(g);
            return (
              <button
                key={g}
                onClick={() => toggleGenre(g)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  isSelected
                    ? "bg-brand-700 text-white shadow-sm"
                    : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-400"
                }`}
              >
                {g}
              </button>
            );
          })}
        </div>
      </div>

      {/* Themes */}
      <div className="mb-6">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
          {t.themes_label}
        </label>
        <div className="flex flex-wrap gap-1.5">
          {PRESET_THEMES.map((theme) => {
            const isSelected = selectedThemes.includes(theme);
            return (
              <button
                key={theme}
                onClick={() => toggleTheme(theme)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-amber-600 text-white shadow-sm"
                    : "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50 hover:border-amber-400"
                }`}
              >
                🔥 {theme}
              </button>
            );
          })}
        </div>
      </div>

      {/* Prompt Area */}
      <div className="mb-6">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
          {lang === 'vi' ? "Ý tưởng cốt truyện ban đầu:" : "Initial story prompt:"}
        </label>
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={t.prompt_placeholder}
          className="w-full p-4 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm leading-relaxed"
        />
      </div>

      <button
        onClick={handleNext}
        className="w-full py-3.5 rounded-xl font-bold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 shadow-md transition-all flex items-center justify-center gap-2"
      >
        <span>{t.continue_btn}</span>
      </button>
    </div>
  );
}
