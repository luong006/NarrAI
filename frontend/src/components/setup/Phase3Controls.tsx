"use client";

import { useState } from "react";
import { translations, Language } from "@/lib/i18n";
import { StoryLength, CreativityLevel, PacingLevel } from "@/lib/types";
import { Sliders, Sparkles } from "lucide-react";

interface Props {
  lang: Language;
  onStartWriting: (length: StoryLength, creativity: CreativityLevel, pacing: PacingLevel) => void;
  loading: boolean;
}

export function Phase3Controls({ lang, onStartWriting, loading }: Props) {
  const [lengthIndex, setLengthIndex] = useState(2); // 1=short, 2=medium, 3=long
  const [creativity, setCreativity] = useState<CreativityLevel>(2);
  const [pacing, setPacing] = useState<PacingLevel>(2);

  const t = translations[lang];

  const getLengthKey = (): StoryLength => {
    if (lengthIndex === 1) return "short";
    if (lengthIndex === 3) return "long";
    return "medium";
  };

  const getLengthLabel = () => {
    if (lengthIndex === 1) return t.val_short;
    if (lengthIndex === 3) return t.val_long;
    return t.val_med;
  };

  const getCreativityLabel = () => {
    if (creativity === 1) return t.val_logic;
    if (creativity === 3) return t.val_crazy;
    return t.val_bal;
  };

  const getPacingLabel = () => {
    if (pacing === 1) return t.val_slow;
    if (pacing === 3) return t.val_fast;
    return t.val_bal;
  };

  return (
    <div className="max-w-xl mx-auto py-12 px-6">
      <div className="mb-8 text-center">
        <div className="w-12 h-12 rounded-2xl bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 flex items-center justify-center mx-auto mb-3">
          <Sliders className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          {t.step3_title}
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {lang === 'vi' ? "Thiết lập cấu hình văn phong trước khi AI bắt đầu chấp bút chương đầu tiên." : "Configure story parameters before AI begins drafting chapter 1."}
        </p>
      </div>

      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6 mb-8">
        {/* Story Length Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">{t.story_length}</span>
            <span className="text-xs font-bold text-brand-700 dark:text-brand-400">{getLengthLabel()}</span>
          </div>
          <input
            type="range"
            min={1}
            max={3}
            value={lengthIndex}
            onChange={(e) => setLengthIndex(Number(e.target.value))}
            className="w-full accent-brand-700 h-2 bg-slate-200 dark:bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* Creativity Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">{t.creativity}</span>
            <span className="text-xs font-bold text-amber-600 dark:text-amber-400">{getCreativityLabel()}</span>
          </div>
          <input
            type="range"
            min={1}
            max={3}
            value={creativity}
            onChange={(e) => setCreativity(Number(e.target.value) as CreativityLevel)}
            className="w-full accent-amber-600 h-2 bg-slate-200 dark:bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* Pacing Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">{t.pacing}</span>
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">{getPacingLabel()}</span>
          </div>
          <input
            type="range"
            min={1}
            max={3}
            value={pacing}
            onChange={(e) => setPacing(Number(e.target.value) as PacingLevel)}
            className="w-full accent-emerald-600 h-2 bg-slate-200 dark:bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>
      </div>

      <button
        onClick={() => onStartWriting(getLengthKey(), creativity, pacing)}
        disabled={loading}
        className="w-full py-4 rounded-xl font-bold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 shadow-lg shadow-indigo-500/25 transition-all flex items-center justify-center gap-2 text-base disabled:opacity-50"
      >
        <Sparkles className="w-5 h-5" />
        <span>{loading ? t.loading : t.start_writing_btn}</span>
      </button>
    </div>
  );
}
