"use client";

import { translations, Language } from "@/lib/i18n";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { CoinBadgeMorphicon } from "@/components/morphicons/CoinBadgeMorphicon";
import { ArrowRight, Bot, Image as ImageIcon, LogIn, PenLine, ShieldCheck, Users } from "lucide-react";

interface Props {
  lang: Language;
  onLanguageChange: (lang: Language) => void;
  onOpenAuth: () => void;
  onExploreCommunity?: () => void;
}

export function LandingView({ lang, onLanguageChange, onOpenAuth, onExploreCommunity }: Props) {
  const t = translations[lang];

  return (
    <main className="landing-backdrop min-h-screen px-3 py-3 text-[#2c211e] transition-colors sm:px-6 sm:py-6 dark:text-[#eee6d9]">
      <div className="landing-shell mx-auto max-w-[1440px] overflow-hidden rounded-[1.25rem] border border-[#fffaf0]/70 bg-[#f7f3eb]/85 shadow-[0_18px_55px_rgba(62,48,37,0.11)] dark:border-[#564a40] dark:bg-[#28231f]/95">
        <nav
          aria-label={lang === "vi" ? "Điều hướng chính" : "Main navigation"}
          className="mx-auto flex max-w-7xl items-center justify-between gap-2 px-4 py-4 sm:gap-4 sm:px-8 lg:px-10"
        >
          <button
            type="button"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="flex shrink-0 items-center gap-2.5 rounded-lg text-left"
            aria-label="NarrAI"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#714033] font-serif text-lg font-bold text-[#fffaf0] sm:h-10 sm:w-10">
              N
            </span>
            <span className="font-serif text-lg font-bold tracking-tight sm:text-xl">NarrAI</span>
            <span className="hidden rounded-sm bg-[#e9dfd0] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#714033] dark:bg-[#45352c] dark:text-[#dfb79b] sm:inline">
              {t.pro_badge}
            </span>
          </button>

          <div className="landing-header-controls flex items-center gap-1.5 sm:gap-3">
            <div className="hidden sm:block">
              <CoinBadgeMorphicon
                balance={100}
                onClick={onOpenAuth}
                lang={lang}
                size="sm"
                isInteractive
              />
            </div>
            <LanguageSwitcher currentLang={lang} onLanguageChange={onLanguageChange} />
            <ThemeToggle lang={lang} />
            <button
              type="button"
              onClick={onOpenAuth}
              aria-label={t.login}
              className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#382622] text-sm font-semibold text-[#fffaf0] transition-colors hover:bg-[#573b32] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#9a654c] focus-visible:ring-offset-2 dark:bg-[#e5d6c5] dark:text-[#29211d] dark:hover:bg-white sm:h-auto sm:w-auto sm:px-4 sm:py-2"
            >
              <LogIn aria-hidden="true" className="h-4 w-4 sm:hidden" />
              <span className="hidden sm:inline">{t.login}</span>
            </button>
          </div>
        </nav>

        <section className="mx-auto grid max-w-7xl items-center gap-10 px-5 pb-14 pt-9 sm:px-8 sm:pb-20 sm:pt-12 lg:grid-cols-[0.95fr_1.05fr] lg:gap-14 lg:px-12 lg:pb-24 lg:pt-14">
          <div className="text-center lg:text-left">
            <p className="mb-5 inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[#805342] dark:text-[#d5a88e] sm:text-xs">
              <span className="h-px w-6 bg-[#a76b4c]" />
              {t.hero_badge}
            </p>
            <h1 className="mx-auto max-w-2xl font-serif text-4xl font-bold leading-[1.12] tracking-[-0.035em] text-[#30221e] dark:text-[#f3e9db] sm:text-5xl lg:mx-0 lg:text-6xl xl:text-[4.25rem]">
              {t.hero_title}
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-base leading-7 text-[#6d625b] dark:text-[#c3b8aa] sm:text-lg sm:leading-8 lg:mx-0">
              {t.hero_sub}
            </p>

            <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center lg:justify-start">
              <button
                type="button"
                onClick={onOpenAuth}
                className="group inline-flex min-h-12 items-center justify-center gap-3 rounded-md bg-[#714033] px-6 py-3.5 text-sm font-bold text-[#fffaf0] transition-colors hover:bg-[#573229] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#9a654c] focus-visible:ring-offset-2 dark:bg-[#b88669] dark:text-[#211915] dark:hover:bg-[#d2a487] sm:text-base"
              >
                <span>{t.hero_cta}</span>
                <ArrowRight aria-hidden="true" className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </button>
              <button
                type="button"
                onClick={onExploreCommunity ?? onOpenAuth}
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-md border border-[#c8bcb0] bg-transparent px-5 py-3.5 text-sm font-semibold text-[#493b34] transition-colors hover:border-[#947260] hover:bg-[#eee7dc] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#9a654c] focus-visible:ring-offset-2 dark:border-[#66584e] dark:text-[#e4d8c9] dark:hover:bg-[#3a312b] sm:text-base"
              >
                <Users aria-hidden="true" className="h-4 w-4 text-[#805342] dark:text-[#d5a88e]" />
                <span>{lang === "vi" ? "Khám phá cộng đồng" : "Explore the community"}</span>
              </button>
            </div>

            <p className="mt-6 text-xs font-medium text-[#82766c] dark:text-[#a99d90] sm:text-sm">
              {lang === "vi"
                ? "Phát triển ý tưởng · Viết và biên tập · Chuyển thể thành truyện tranh"
                : "Develop ideas · Write and edit · Adapt into comics"}
            </p>
          </div>

          <div
            className="relative mx-auto w-full max-w-[590px] px-2 pb-6 pt-2 sm:px-6"
            aria-label={lang === "vi" ? "Minh họa bản thảo và truyện tranh" : "Manuscript and comic illustration"}
          >
            <div className="landing-book-scene">
              <div className="landing-book">
                <div className="landing-book-page landing-book-page-left">
                  <span className="landing-book-eyebrow">{lang === "vi" ? "BẢN THẢO" : "MANUSCRIPT"}</span>
                  <h2>{lang === "vi" ? "Chương mở đầu" : "The first chapter"}</h2>
                  <span className="landing-book-rule" />
                  <span className="landing-book-line" />
                  <span className="landing-book-line" />
                  <span className="landing-book-line landing-book-line-short" />
                  <span className="landing-book-paragraph">
                    {lang === "vi"
                      ? "Mưa đổ xuống mái ngói cũ. Trong căn phòng nhỏ, một câu chuyện đang chờ được viết tiếp."
                      : "Rain fell on the old roof. In a quiet room, a story waited to be continued."}
                  </span>
                  <span className="landing-book-line" />
                  <span className="landing-book-line landing-book-line-mid" />
                </div>
                <div className="landing-book-page landing-book-page-right">
                  <span className="landing-book-eyebrow">{lang === "vi" ? "PHÁC THẢO CẢNH" : "SCENE NOTES"}</span>
                  <div className="landing-sketch-frame">
                    <div className="landing-sketch-window" />
                    <div className="landing-sketch-person" />
                    <div className="landing-sketch-chair" />
                  </div>
                  <span className="landing-book-caption">{lang === "vi" ? "Cảnh 01 · Đêm mưa" : "Scene 01 · Rainy night"}</span>
                  <span className="landing-book-line" />
                  <span className="landing-book-line landing-book-line-short" />
                  <span className="landing-book-paragraph">
                    {lang === "vi" ? "Nhân vật · Bối cảnh · Diễn biến" : "Character · Setting · Action"}
                  </span>
                </div>
              </div>
              <div className="landing-comic-note">
                <div className="landing-comic-panel">
                  <span className="landing-comic-moon" />
                  <span className="landing-comic-roof" />
                  <span className="landing-comic-figure" />
                </div>
                <div className="landing-comic-copy">
                  <span className="landing-book-eyebrow">MANGA</span>
                  <span>{lang === "vi" ? "Cùng một câu chuyện, một hình hài mới." : "The same story, in a new form."}</span>
                </div>
              </div>
              <span className="landing-scene-label">
                <PenLine aria-hidden="true" className="h-3.5 w-3.5" />
                {lang === "vi" ? "Từ trang viết đến khung truyện" : "From page to panel"}
              </span>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 pb-12 sm:px-8 sm:pb-16 lg:px-12">
          <div className="mb-6 border-b border-[#cfc4b8] pb-4 dark:border-[#51463d] sm:mb-8">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#805342] dark:text-[#d5a88e]">
              {t.features_section_title}
            </p>
            <h2 className="mt-2 font-serif text-2xl font-bold tracking-tight text-[#30221e] dark:text-[#f3e9db] sm:text-3xl">
              {lang === "vi" ? "Mọi chặng đường của câu chuyện" : "Every stage of your story"}
            </h2>
          </div>

          <div className="grid divide-y divide-[#cfc4b8] dark:divide-[#51463d] md:grid-cols-3 md:divide-x md:divide-y-0">
            <article className="py-5 md:py-2 md:pr-7">
              <div className="mb-4 flex items-center gap-3 text-[#805342] dark:text-[#d5a88e]">
                <Bot aria-hidden="true" className="h-5 w-5" />
                <span className="text-xs font-bold tracking-[0.12em]">01</span>
              </div>
              <h3 className="font-serif text-lg font-bold text-[#30221e] dark:text-[#f3e9db]">{t.feat1_title}</h3>
              <p className="mt-2 text-sm leading-6 text-[#6d625b] dark:text-[#c3b8aa]">{t.feat1_desc}</p>
            </article>

            <article className="py-5 md:px-7 md:py-2">
              <div className="mb-4 flex items-center gap-3 text-[#805342] dark:text-[#d5a88e]">
                <PenLine aria-hidden="true" className="h-5 w-5" />
                <span className="text-xs font-bold tracking-[0.12em]">02</span>
              </div>
              <h3 className="font-serif text-lg font-bold text-[#30221e] dark:text-[#f3e9db]">{t.feat2_title}</h3>
              <p className="mt-2 text-sm leading-6 text-[#6d625b] dark:text-[#c3b8aa]">{t.feat2_desc}</p>
            </article>

            <article className="py-5 md:py-2 md:pl-7">
              <div className="mb-4 flex items-center gap-3 text-[#805342] dark:text-[#d5a88e]">
                <ImageIcon aria-hidden="true" className="h-5 w-5" />
                <span className="text-xs font-bold tracking-[0.12em]">03</span>
              </div>
              <h3 className="font-serif text-lg font-bold text-[#30221e] dark:text-[#f3e9db]">{t.feat3_title}</h3>
              <p className="mt-2 text-sm leading-6 text-[#6d625b] dark:text-[#c3b8aa]">{t.feat3_desc}</p>
            </article>
          </div>

          <div className="mt-8 flex flex-col items-start justify-between gap-4 border-y border-[#cfc4b8] py-5 dark:border-[#51463d] sm:flex-row sm:items-center">
            <div className="flex items-start gap-3">
              <ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-[#61705a] dark:text-[#a9bd9d]" />
              <div>
                <h3 className="font-serif text-base font-bold text-[#30221e] dark:text-[#f3e9db]">
                  {lang === "vi" ? "Sáng tác với sự an tâm" : "Create with confidence"}
                </h3>
                <p className="mt-1 max-w-3xl text-sm leading-6 text-[#6d625b] dark:text-[#c3b8aa]">
                  {lang === "vi"
                    ? "Có thêm lớp kiểm tra nội dung lịch sử và hỗ trợ lưu bản nháp khi quá trình sinh truyện bị gián đoạn."
                    : "Historical-content checks and draft recovery help protect your work when generation is interrupted."}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onExploreCommunity ?? onOpenAuth}
              className="inline-flex shrink-0 items-center gap-2 rounded-md px-2 py-2 text-sm font-semibold text-[#714033] transition-colors hover:text-[#382622] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#9a654c] dark:text-[#d5a88e] dark:hover:text-[#f0c8ad]"
            >
              <Users aria-hidden="true" className="h-4 w-4" />
              {lang === "vi" ? "Gặp gỡ cộng đồng" : "Meet the community"}
              <ArrowRight aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
        </section>

        <footer className="border-t border-[#cfc4b8] px-5 py-6 text-center text-xs text-[#82766c] dark:border-[#51463d] dark:text-[#a99d90]">
          {t.footer_copyright}
        </footer>
      </div>
    </main>
  );
}
