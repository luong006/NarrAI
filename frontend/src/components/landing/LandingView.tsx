"use client";

import { translations, Language } from "@/lib/i18n";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { Sparkles, Bot, Edit3, Image as ImageIcon, ArrowRight } from "lucide-react";
import { InteractiveTiltCard } from "@/components/cards/InteractiveTiltCard";
import { CoinBadgeMorphicon } from "@/components/morphicons/CoinBadgeMorphicon";
import { LikeButtonMorphicon } from "@/components/morphicons/LikeButtonMorphicon";
import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";

interface Props {
  lang: Language;
  onLanguageChange: (lang: Language) => void;
  onOpenAuth: () => void;
}

export function LandingView({ lang, onLanguageChange, onOpenAuth }: Props) {
  const t = translations[lang];

  return (
    <div className="min-h-screen bg-slate-50/75 dark:bg-slate-950/75 backdrop-blur-[1px] text-slate-900 dark:text-white transition-colors">
      {/* Top Navbar */}
      <nav className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-brand-700 flex items-center justify-center text-white font-bold text-lg shadow-md">
            N
          </div>
          <span className="font-bold text-xl tracking-tight">
            NarrAI{" "}
            <span className="text-xs uppercase font-extrabold px-1.5 py-0.5 rounded bg-brand-100 text-brand-800 dark:bg-brand-900 dark:text-brand-300">
              {t.pro_badge}
            </span>
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Layer 2 SVG Morphicon: Coin Balance Badge */}
          <CoinBadgeMorphicon
            balance={100}
            onClick={onOpenAuth}
            lang={lang}
            size="sm"
            isInteractive={true}
          />
          <LanguageSwitcher currentLang={lang} onLanguageChange={onLanguageChange} />
          <ThemeToggle lang={lang} />
          <button
            onClick={onOpenAuth}
            className="px-4 py-2 text-sm font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-white dark:text-slate-950 text-white dark:hover:bg-slate-200 shadow-sm transition-all"
          >
            {t.login}
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-12 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-50/90 dark:bg-indigo-950/60 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-900 mb-6 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>{t.hero_badge}</span>
          <LikeButtonMorphicon size="sm" showCount={false} className="ml-1" />
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.15] mb-6 text-slate-900 dark:text-white max-w-4xl mx-auto">
          {t.hero_title}
        </h1>

        <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          {t.hero_sub}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onOpenAuth}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-white bg-brand-700 hover:bg-brand-800 shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
          >
            <span>{t.hero_cta}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* AI Art & Neural Style Preview Showcase (Feature 30) */}
      <section className="max-w-4xl mx-auto px-6 pb-12">
        <NeuralVisualPreview lang={lang} />
      </section>


      {/* Features Grid: Layer 1 Interactive 3D Tilt Cards */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-xs uppercase font-extrabold text-brand-700 dark:text-brand-400 tracking-widest text-center mb-10">
          {t.features_section_title}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <InteractiveTiltCard maxTilt={8} perspective={1000} scale={1.02} glare={true} className="rounded-2xl h-full">
            <div className="p-8 rounded-2xl bg-white/90 dark:bg-slate-900/90 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all h-full">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-brand-700 dark:text-brand-400 mb-5">
                <Bot className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{t.feat1_title}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{t.feat1_desc}</p>
            </div>
          </InteractiveTiltCard>

          <InteractiveTiltCard maxTilt={8} perspective={1000} scale={1.02} glare={true} className="rounded-2xl h-full">
            <div className="p-8 rounded-2xl bg-white/90 dark:bg-slate-900/90 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all h-full">
              <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950 flex items-center justify-center text-amber-600 dark:text-amber-400 mb-5">
                <Edit3 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{t.feat2_title}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{t.feat2_desc}</p>
            </div>
          </InteractiveTiltCard>

          <InteractiveTiltCard maxTilt={8} perspective={1000} scale={1.02} glare={true} className="rounded-2xl h-full">
            <div className="p-8 rounded-2xl bg-white/90 dark:bg-slate-900/90 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all h-full">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-5">
                <ImageIcon className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{t.feat3_title}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{t.feat3_desc}</p>
            </div>
          </InteractiveTiltCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-10 border-t border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
        <p>{t.footer_copyright}</p>
      </footer>
    </div>
  );
}
