"use client";

import React, { useState } from "react";
import Image from "next/image";
import { translations, Language } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { VietnamFlagHeroBackground } from "@/components/canvas/VietnamFlagHeroBackground";

interface Props {
  lang: Language;
  onLanguageChange: (lang: Language) => void;
  onOpenAuth: () => void;
  onExploreCommunity?: () => void;
  onNavigateStudio?: (studio: "editor" | "comic" | "lore" | "motion") => void;
}

export function LandingView({ lang, onLanguageChange, onOpenAuth, onExploreCommunity, onNavigateStudio }: Props) {
  const t = translations[lang];
  const [activeHeroTab, setActiveHeroTab] = useState<"prose" | "manga">("manga");
  const [activeWorldIdx, setActiveWorldIdx] = useState<number>(0);

  const featuredWorlds = [
    {
      id: "dai-viet",
      title: lang === "vi" ? "Đại Việt Cổ Phong (1279 - 1428)" : "Ancient Dai Viet (1279 - 1428)",
      period: lang === "vi" ? "Thời Trần - Hậu Lê" : "Tran & Later Le Dynasties",
      image: "/assets/landing/world_warrior_rain.png",
      desc:
        lang === "vi"
          ? "Thế giới dã sử hào hùng nơi các hiệp sĩ áo tơi nón lá, nghĩa quân bến sông gìn giữ giang sơn giữa phong ba thời loạn."
          : "An epic historical realm of rain-swept river warriors, conical hats, and martial heroes defending the sovereign frontier.",
      tags: lang === "vi" ? ["Chính sử chuẩn mực", "Áo giao lĩnh & Nón lá", "Thủy chiến bến sông"] : ["Strict History", "Traditional Robes", "River Warfare"],
    },
    {
      id: "dan-gian",
      title: lang === "vi" ? "Thần Thoại & Dân Gian Rừng Thiêng" : "Folklore & Sacred Forests",
      period: lang === "vi" ? "Huyền tích Cổ tích Việt" : "Vietnamese Myth & Legends",
      image: "/assets/landing/folktale_child_roots.png",
      desc:
        lang === "vi"
          ? "Rừng sâu đại ngàn, cổ thụ ngàn năm và những huyền tích dân gian như Thạch Sanh, Chử Đồng Tử với ma thuật cội nguồn."
          : "Ancient deep forests, sacred banyan roots, and folklore legends echoing through generations with ancestral primal magic.",
      tags: lang === "vi" ? ["Cổ tích tái hiện", "Cổ thụ & Thần thú", "Bảo pháp dân gian"] : ["Reimagined Folktale", "Sacred Trees", "Ancient Relics"],
    },
    {
      id: "bach-dang",
      title: lang === "vi" ? "Bạch Đằng Dạ Chiến (Manga Trắng Đen)" : "Bach Dang Night Battle (B&W Manga)",
      period: lang === "vi" ? "Thủy chiến Dã sử" : "Naval Historical Battle",
      image: "/assets/landing/manga_battle_scene.png",
      desc:
        lang === "vi"
          ? "Bãi cọc ngầm huyền thoại xé toang chiến thuyền giặc trong đêm giông bão, phân khung kịch tính theo phong cách manga tương phản cao."
          : "Legendary sunken stakes tearing into enemy armada beneath thunderous skies, storyboarded in high-contrast manga inking.",
      tags: lang === "vi" ? ["Trận địa cọc ngầm", "Mực truyện tranh tương phản", "Góc máy điện ảnh"] : ["Sunken Stakes", "High-Contrast Inking", "Cinematic Angles"],
    },
  ];

  const recentProjects = [
    {
      title: lang === "vi" ? "Chiến Thần Bạch Đằng" : "Warlord of Bach Dang",
      genre: lang === "vi" ? "Dã sử · Thủy chiến · Manga đen trắng" : "Historical Fiction · Naval Battle · B&W Manga",
      image: "/assets/landing/story_bach_dang_epic.png",
      stats: lang === "vi" ? "4 Chương · 18 Khung manga" : "4 Chapters · 18 Manga panels",
      progress: "92%",
      synopsis:
        lang === "vi"
          ? "Đoàn thuyền xé toang màn sương mù dày đặc bến Bạch Đằng, trận địa cọc ngầm chuẩn bị đóng dấu định mệnh cho quân giặc phương Bắc..."
          : "War galleys pierce the thick river mist along the Bach Dang River as hidden stake barriers prepare to seal the northern armada's fate...",
      tag: "[MANGA STORYBOARD]",
    },
    {
      title: lang === "vi" ? "Bóng Kiếm Đêm Mưa" : "Sword in the Rain",
      genre: lang === "vi" ? "Kiếm hiệp Cổ phong · Tiểu thuyết" : "Historical Wuxia · Epic Prose",
      image: "/assets/landing/story_bong_kiem_dem_mua.png",
      stats: lang === "vi" ? "8 Chương · 14,200 từ" : "8 Chapters · 14,200 words",
      progress: "100%",
      synopsis:
        lang === "vi"
          ? "Kiếm khách áo tơi nón lá lặng lẽ đứng giữa bến đò đêm mưa lạnh. Một đường kiếm quyết định ân oán gia tộc mười năm chôn giấu..."
          : "A lone swordsman in a rain-soaked straw cloak waits at the ferry landing. A single slash to resolve a decade of clan vengeance...",
      tag: "[STORY LAB]",
    },
    {
      title: lang === "vi" ? "Huyền Tích Nàng Thiềm" : "Legend of Lady Thiem",
      genre: lang === "vi" ? "Dân gian Huyền ảo · Thiết kế nhân vật" : "Mythic Fantasy · Character Dossier",
      image: "/assets/landing/story_huyen_tich_nang_thiem.png",
      stats: lang === "vi" ? "6 Nhân vật · 1 Lore Bible" : "6 Characters · 1 Lore Bible",
      progress: "85%",
      synopsis:
        lang === "vi"
          ? "Hồ sơ tạo hình nàng thiếu nữ mang phong thái cung đình với áo dài truyền thống thêu chỉ vàng, ẩn chứa phong ấn linh thú gia tộc..."
          : "Design sheet of a noble maiden in golden embroidered traditional attire, harboring the ancient celestial seal of her lineage...",
      tag: "[CHARACTER & LORE]",
    },
    {
      title: lang === "vi" ? "Thạch Sanh: Ký Sự Rừng Sâu" : "Thach Sanh: Forest Chronicles",
      genre: lang === "vi" ? "Cổ tích tái hiện · Shonen Manga" : "Folklore Adaptation · Shonen Manga",
      image: "/assets/landing/story_thach_sanh_hero.png",
      stats: lang === "vi" ? "3 Chương · 12 Khung manga" : "3 Chapters · 12 Manga panels",
      progress: "70%",
      synopsis:
        lang === "vi"
          ? "Dưới bóng cổ thụ bạt ngàn của rừng thiêng, chàng tiều phu mồ côi bắt đầu cảm nhận nguồn linh lực vô tận thức tỉnh trong cơ thể..."
          : "Beneath the massive ancient roots of the sacred forest, an orphan woodcutter begins to feel ancestral primordial power awakening...",
      tag: "[MOTION STUDIO]",
    },
  ];

  return (
    <main
      className="landing-backdrop min-h-screen px-2.5 py-2.5 sm:px-6 sm:py-6 text-neutral-900 bg-[#F4EFE6] font-sans relative overflow-hidden"
      style={{ backgroundColor: "#F4EFE6" }}
    >
      <div
        className="landing-shell relative mx-auto max-w-[1440px] overflow-hidden rounded-2xl border border-neutral-300/80 bg-[#FAF7F2] shadow-2xl backdrop-blur-sm"
        style={{ backgroundColor: "#FAF7F2" }}
      >
        
        {/* ========================================================= */}
        {/* VIETNAM FLAG LIGHT RIBBONS GENERATIVE HERO BACKGROUND */}
        {/* ========================================================= */}
        <VietnamFlagHeroBackground />

        {/* ========================================================= */}
        {/* HEADER / NAVIGATION BAR */}
        {/* ========================================================= */}
        <header className="sticky top-0 z-40 border-b border-neutral-200/80 bg-[#FAF7F2]/90 backdrop-blur-md">
          <nav
            aria-label={lang === "vi" ? "Điều hướng chính" : "Main navigation"}
            className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3.5 sm:px-8 lg:px-10"
          >
            {/* Logo Brand with Instant Replay Trigger */}
            <button
              type="button"
              onClick={() => {
                window.scrollTo({ top: 0, behavior: "smooth" });
                window.dispatchEvent(new CustomEvent("narrai:replay-intro"));
              }}
              className="flex shrink-0 items-center gap-3 text-left cursor-pointer group rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400"
              title={lang === "vi" ? "Nhấp để phát lại hiệu ứng WeaveSilk Intro" : "Click to replay WeaveSilk cinematic intro"}
              aria-label="NarrAI Home"
            >
              <div className="relative h-9 w-9 rounded-md overflow-hidden bg-white border border-neutral-300 group-hover:border-neutral-500 transition-colors shadow-sm">
                <Image
                  src="/assets/narrai_emblem.png"
                  alt="NARR AI Official Emblem"
                  fill
                  className="object-contain p-0.5 filter brightness-[0.2] contrast-[1.4] group-hover:scale-105 transition-transform"
                  priority
                />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-lg sm:text-xl font-bold tracking-widest uppercase text-neutral-950">
                    NarrAI
                  </span>
                  <span className="rounded border border-amber-400/60 bg-amber-50 px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase tracking-wider text-amber-900">
                    {t.pro_badge}
                  </span>
                </div>
                <span className="hidden sm:inline text-[9px] font-mono tracking-wider text-neutral-600 uppercase">
                  AI Novel & Manga Studio
                </span>
              </div>
            </button>

            {/* Quick In-page Navigation Anchors (Desktop) */}
            <div className="hidden lg:flex items-center gap-6 font-mono text-xs uppercase tracking-wider text-neutral-700">
              <a
                href="#studios"
                className="hover:text-black transition-colors"
              >
                {t.nav_studios}
              </a>
              <a
                href="#recent-projects"
                className="hover:text-black transition-colors"
              >
                {t.nav_recent_projects}
              </a>
              <a
                href="#featured-worlds"
                className="hover:text-black transition-colors"
              >
                {t.nav_featured_worlds}
              </a>
              <a
                href="#heritage"
                className="hover:text-black transition-colors"
              >
                {t.nav_heritage}
              </a>
            </div>

            {/* Controls & Primary Action */}
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => {
                  window.scrollTo({ top: 0, behavior: "smooth" });
                  window.dispatchEvent(new CustomEvent("narrai:replay-intro"));
                }}
                className="hidden sm:inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-mono font-bold uppercase tracking-wider border border-amber-400/80 bg-amber-50 hover:bg-amber-100 text-amber-900 shadow-xs transition-all cursor-pointer"
                title={lang === "vi" ? "Xem hiệu ứng Intro Trống Đồng Đông Sơn" : "Play Dong Son Drum Intro"}
              >
                <span>↻</span>
                <span>{lang === "vi" ? "Intro Trống Đồng" : "Drum Intro"}</span>
              </button>
              <LanguageSwitcher currentLang={lang} onLanguageChange={onLanguageChange} />
              <button
                type="button"
                onClick={onOpenAuth}
                className="rounded-lg px-4 py-2 text-xs font-mono font-bold uppercase tracking-wider bg-neutral-950 text-white hover:bg-neutral-800 shadow-md transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neutral-900"
              >
                {t.login}
              </button>
            </div>
          </nav>
        </header>

        {/* ========================================================= */}
        {/* HERO SECTION */}
        {/* ========================================================= */}
        <section className="relative z-10 mx-auto max-w-7xl px-4 pb-14 pt-8 sm:px-8 sm:pb-20 sm:pt-12 lg:px-10 lg:pb-24 lg:pt-14">
          <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:gap-12">
            
            {/* Left: Headline, Value Proposition, Action CTAs */}
            <div className="text-center lg:text-left">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white/90 px-3.5 py-1 text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-800 shadow-sm backdrop-blur-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-red-600 animate-pulse" />
                <span>[GEN-AI NARRATIVE PLATFORM]</span>
                <span>—</span>
                <span>{t.hero_badge}</span>
              </div>

              <h1 className="font-serif text-3xl font-bold leading-[1.2] tracking-tight sm:text-5xl lg:text-6xl text-neutral-950">
                {t.hero_title}
              </h1>

              <p className="mt-5 max-w-xl mx-auto lg:mx-0 text-base leading-relaxed text-neutral-700 font-medium sm:text-lg">
                {t.hero_sub}
              </p>

              {/* CTAs */}
              <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center lg:justify-start">
                <button
                  type="button"
                  onClick={onOpenAuth}
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg px-7 py-3.5 text-sm font-mono font-bold uppercase tracking-wider bg-neutral-950 text-white hover:bg-neutral-800 transition-all shadow-xl cursor-pointer"
                >
                  <span>{t.hero_cta}</span>
                  <span className="text-xs">➔</span>
                </button>
                <a
                  href="#recent-projects"
                  className="inline-flex min-h-12 items-center justify-center rounded-lg border border-neutral-300 bg-white/90 px-5 py-3.5 text-sm font-mono font-bold uppercase tracking-wider text-neutral-900 hover:bg-white shadow-sm transition-colors text-center"
                >
                  {lang === "vi" ? "Xem Dự Án Mẫu" : "View Sample Works"}
                </a>
              </div>

              {/* Verified Trust Stats */}
              <div className="mt-8 grid grid-cols-3 gap-3 border-t border-neutral-300/80 pt-5 text-center lg:text-left">
                <div>
                  <div className="font-serif text-lg sm:text-xl font-bold text-neutral-950">
                    35,000+
                  </div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-600 font-medium">
                    {lang === "vi" ? "Từ bản thảo AI" : "Prose drafted"}
                  </div>
                </div>
                <div>
                  <div className="font-serif text-lg sm:text-xl font-bold text-neutral-950">
                    1,200+
                  </div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-600 font-medium">
                    {lang === "vi" ? "Khung manga mực" : "Manga panels"}
                  </div>
                </div>
                <div>
                  <div className="font-serif text-lg sm:text-xl font-bold text-neutral-950">
                    100%
                  </div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-600 font-medium">
                    {lang === "vi" ? "Bản quyền tác giả" : "Creator IP"}
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Integrated Dual-Media Showcase Preview (Prose + Manga Panel) */}
            <div className="relative mx-auto w-full max-w-[540px]">
              <div className="relative rounded-2xl border border-neutral-200/90 bg-white/92 backdrop-blur-md p-3 sm:p-5 shadow-2xl overflow-hidden">
                
                {/* Live Preview Header with Tabs */}
                <div className="flex items-center justify-between border-b border-neutral-200/80 pb-3 mb-3">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-red-500" />
                    <span className="h-2 w-2 rounded-full bg-yellow-400" />
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    <span className="ml-2 font-mono text-[10px] uppercase tracking-widest text-neutral-600 font-bold">
                      {t.live_preview_badge}
                    </span>
                  </div>

                  {/* Mode switcher tab buttons */}
                  <div className="flex rounded-md border border-neutral-200 bg-neutral-100 p-0.5 text-[10px] font-mono font-bold">
                    <button
                      type="button"
                      onClick={() => setActiveHeroTab("manga")}
                      className={`px-2.5 py-1 rounded transition-colors ${
                        activeHeroTab === "manga"
                          ? "bg-neutral-950 text-white shadow-sm"
                          : "text-neutral-600 hover:text-neutral-950"
                      }`}
                    >
                      Manga Panel
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveHeroTab("prose")}
                      className={`px-2.5 py-1 rounded transition-colors ${
                        activeHeroTab === "prose"
                          ? "bg-neutral-950 text-white shadow-sm"
                          : "text-neutral-600 hover:text-neutral-950"
                      }`}
                    >
                      Bản Thảo
                    </button>
                  </div>
                </div>

                {/* Tab A: Manga Adaptation Interactive View */}
                {activeHeroTab === "manga" ? (
                  <div className="space-y-3">
                    {/* Main Establishing Battle Panel */}
                    <div className="relative aspect-[16/10] w-full rounded-xl overflow-hidden border border-neutral-200 bg-black group shadow-sm">
                      <Image
                        src="/assets/landing/hero_preview_panel_01_battle.png"
                        alt="Chiến trận bãi cọc Bạch Đằng - Manga Studio"
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-500"
                        priority
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                      <div className="absolute bottom-2.5 left-3 right-3 flex items-end justify-between">
                        <div>
                          <span className="inline-block px-1.5 py-0.5 rounded bg-black/80 text-[9px] font-mono text-white font-bold tracking-widest border border-white/20 mb-1">
                            [PANEL 01 · GÓC RỘNG]
                          </span>
                          <p className="text-xs font-serif italic text-white/95 line-clamp-1">
                            "Mặt nước dậy sóng, hàng cọc nhọn vươn lên đón đợi đại quân..."
                          </p>
                        </div>
                        <span className="text-[10px] font-mono text-neutral-300 font-bold">
                          100% INK
                        </span>
                      </div>
                    </div>

                    {/* Secondary Dual Inset Strip */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="relative aspect-[4/3] rounded-lg overflow-hidden border border-neutral-200 bg-neutral-900 group shadow-sm">
                        <Image
                          src="/assets/landing/hero_preview_panel_lore_thiem.png"
                          alt="Nhân vật cổ trang Việt - Character Lore"
                          fill
                          className="object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent pointer-events-none" />
                        <span className="absolute bottom-1.5 left-2 px-1 rounded bg-black/80 text-[8px] font-mono text-white font-bold border border-white/20">
                          [LORE: NÀNG THIỀM]
                        </span>
                      </div>

                      <div className="relative aspect-[4/3] rounded-lg overflow-hidden border border-neutral-200 bg-neutral-900 group shadow-sm">
                        <Image
                          src="/assets/landing/hero_preview_panel_02_close.png"
                          alt="Chân dung manga hiệp nữ"
                          fill
                          className="object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent pointer-events-none" />
                        <span className="absolute bottom-1.5 left-2 px-1 rounded bg-black/80 text-[8px] font-mono text-white font-bold border border-white/20">
                          [PANEL 02: CẬN CẢNH]
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Tab B: Prose Manuscript View */
                  <div className="rounded-xl border border-neutral-200 bg-white p-4 space-y-3 font-serif shadow-sm">
                    <div className="flex items-center justify-between border-b border-neutral-200 pb-2">
                      <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-bold">
                        BẢN THẢO CHƯƠNG 01 · DÃ SỬ
                      </span>
                      <span className="text-[10px] font-mono text-emerald-600 font-bold">
                        ● Đang đồng bộ với Copilot
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-neutral-950">
                      Hồi 1: Đêm Trăng Cửa Sông Bạch Đằng
                    </h3>

                    <p className="text-xs leading-relaxed text-neutral-700">
                      Mưa lất phất trên bến đò Vạn Kiếp. Nước triều bắt đầu rút về phía biển lớn, để lộ những đầu cọc gỗ lim đen bóng ngâm mình trong dòng phù sa nghìn năm. 
                      Người tráng sĩ khoác chiếc áo tơi nón lá, bàn tay ghì chặt chuôi kiếm cổ. Đôi mắt chàng hướng ra dòng sông mênh mông, nơi gió đông bắc đang dồn dập kéo tới...
                    </p>

                    <div className="rounded border border-neutral-200 bg-neutral-50 p-2.5 font-mono text-[11px] text-neutral-700">
                      <span className="font-bold text-neutral-950">🤖 Gợi ý Co-pilot: </span>
                      <span>"Tăng thêm nhịp thở kịch tính của quân sĩ trước giờ phục kích."</span>
                    </div>
                  </div>
                )}

                {/* Footer conversion prompt */}
                <div className="mt-3 pt-2.5 border-t border-neutral-200 flex items-center justify-between text-[11px] font-mono text-neutral-600">
                  <span>[TỰ ĐỘNG CHUYỂN THỂ]</span>
                  <button
                    type="button"
                    onClick={onOpenAuth}
                    className="text-neutral-950 font-bold hover:underline cursor-pointer"
                  >
                    {lang === "vi" ? "Thử nghiệm phân khung ngay ➔" : "Try storyboard now ➔"}
                  </button>
                </div>
              </div>
            </div>

          </div>
        </section>


        {/* ========================================================= */}
        {/* 4 CORE STUDIOS (THẺ CHỨC NĂNG) */}
        {/* ========================================================= */}
        <section
          id="studios"
          className="relative z-10 mx-auto max-w-7xl px-4 pb-16 sm:px-8 sm:pb-20 lg:px-10 border-t border-neutral-300/80 pt-12 bg-[#FAF7F2]"
        >
          <div className="mb-10 text-center max-w-3xl mx-auto">
            <p className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-500">
              {t.studios_section_eyebrow}
            </p>
            <h2 className="mt-2 font-serif text-2xl font-bold tracking-tight text-neutral-950 sm:text-4xl">
              {t.studios_section_title}
            </h2>
            <p className="mt-3 text-sm sm:text-base text-neutral-600">
              {t.studios_section_sub}
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            
            {/* Studio 1: Story Lab */}
            <div className="group rounded-xl border border-neutral-300/80 bg-white/90 p-5 hover:border-neutral-950 transition-all shadow-sm hover:shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-3">
                  <span>{t.studio_story_tag}</span>
                  <span className="rounded bg-neutral-100 border border-neutral-200 px-1.5 py-0.5 text-neutral-700">[01]</span>
                </div>
                <div className="relative aspect-[16/10] w-full rounded-lg overflow-hidden border border-neutral-200 bg-neutral-50/70 p-3 mb-4 flex flex-col justify-between">
                  <div className="space-y-1">
                    <div className="h-1.5 w-12 bg-neutral-400 rounded" />
                    <div className="h-2 w-full bg-neutral-200 rounded" />
                    <div className="h-2 w-4/5 bg-neutral-200 rounded" />
                    <div className="h-2 w-2/3 bg-neutral-200 rounded" />
                  </div>
                  <div className="rounded bg-white border border-neutral-200/80 p-1.5 text-[9px] font-mono text-neutral-600 flex items-center justify-between shadow-xs">
                    <span>AI Co-pilot</span>
                    <span className="text-emerald-600 font-bold">Ready</span>
                  </div>
                </div>
                <h3 className="font-serif text-lg font-bold text-neutral-950">
                  {t.studio_story_name}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-neutral-600">
                  {t.studio_story_desc}
                </p>
              </div>
              <button
                type="button"
                onClick={() => (onNavigateStudio ? onNavigateStudio("editor") : onOpenAuth())}
                className="mt-5 inline-flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-neutral-950 border-t border-neutral-200 pt-3 group-hover:underline cursor-pointer"
              >
                <span>{lang === "vi" ? "Mở Story Lab" : "Open Story Lab"}</span>
                <span>➔</span>
              </button>
            </div>

            {/* Studio 2: Manga Studio */}
            <div className="group rounded-xl border border-neutral-300/80 bg-white/90 p-5 hover:border-neutral-950 transition-all shadow-sm hover:shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-3">
                  <span>{t.studio_manga_tag}</span>
                  <span className="rounded bg-neutral-100 border border-neutral-200 px-1.5 py-0.5 text-neutral-700">[02]</span>
                </div>
                <div className="relative aspect-[16/10] w-full rounded-lg overflow-hidden border border-neutral-200 bg-neutral-900 mb-4 group-hover:scale-[1.02] transition-transform">
                  <Image
                    src="/assets/landing/manga_heroine_portrait.png"
                    alt="Manga Studio Showcase"
                    fill
                    className="object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                  <span className="absolute bottom-1.5 left-2 px-1 rounded bg-black/80 text-[8px] font-mono text-white border border-white/20">
                    B&W Inking
                  </span>
                </div>
                <h3 className="font-serif text-lg font-bold text-neutral-950">
                  {t.studio_manga_name}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-neutral-600">
                  {t.studio_manga_desc}
                </p>
              </div>
              <button
                type="button"
                onClick={() => (onNavigateStudio ? onNavigateStudio("comic") : onOpenAuth())}
                className="mt-5 inline-flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-neutral-950 border-t border-neutral-200 pt-3 group-hover:underline cursor-pointer"
              >
                <span>{lang === "vi" ? "Mở Manga Studio" : "Open Manga Studio"}</span>
                <span>➔</span>
              </button>
            </div>

            {/* Studio 3: Character & Lore */}
            <div className="group rounded-xl border border-neutral-300/80 bg-white/90 p-5 hover:border-neutral-950 transition-all shadow-sm hover:shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-3">
                  <span>{t.studio_lore_tag}</span>
                  <span className="rounded bg-neutral-100 border border-neutral-200 px-1.5 py-0.5 text-neutral-700">[03]</span>
                </div>
                <div className="relative aspect-[16/10] w-full rounded-lg overflow-hidden border border-neutral-200 bg-neutral-900 mb-4 group-hover:scale-[1.02] transition-transform">
                  <Image
                    src="/assets/landing/hero_character_aodai.png"
                    alt="Character Lore Showcase"
                    fill
                    className="object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                  <span className="absolute bottom-1.5 left-2 px-1 rounded bg-black/80 text-[8px] font-mono text-white border border-white/20">
                    Lore Dossier
                  </span>
                </div>
                <h3 className="font-serif text-lg font-bold text-neutral-950">
                  {t.studio_lore_name}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-neutral-600">
                  {t.studio_lore_desc}
                </p>
              </div>
              <button
                type="button"
                onClick={() => (onNavigateStudio ? onNavigateStudio("lore") : onOpenAuth())}
                className="mt-5 inline-flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-neutral-950 border-t border-neutral-200 pt-3 group-hover:underline cursor-pointer"
              >
                <span>{lang === "vi" ? "Khám phá Lore" : "Explore Lore"}</span>
                <span>➔</span>
              </button>
            </div>

            {/* Studio 4: Motion Studio */}
            <div className="group rounded-xl border border-neutral-300/80 bg-white/90 p-5 hover:border-neutral-950 transition-all shadow-sm hover:shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-3">
                  <span>{t.studio_motion_tag}</span>
                  <span className="rounded bg-neutral-100 border border-neutral-200 px-1.5 py-0.5 text-neutral-700">[04]</span>
                </div>
                <div className="relative aspect-[16/10] w-full rounded-lg overflow-hidden border border-neutral-200 bg-neutral-900 mb-4 group-hover:scale-[1.02] transition-transform">
                  <Image
                    src="/assets/landing/world_warrior_rain.png"
                    alt="Motion Studio Showcase"
                    fill
                    className="object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                  <span className="absolute bottom-1.5 left-2 px-1 rounded bg-black/80 text-[8px] font-mono text-white border border-white/20">
                    Cinematic FX
                  </span>
                </div>
                <h3 className="font-serif text-lg font-bold text-neutral-950">
                  {t.studio_motion_name}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-neutral-600">
                  {t.studio_motion_desc}
                </p>
              </div>
              <button
                type="button"
                onClick={() => (onNavigateStudio ? onNavigateStudio("motion") : onOpenAuth())}
                className="mt-5 inline-flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-neutral-950 border-t border-neutral-200 pt-3 group-hover:underline cursor-pointer"
              >
                <span>{lang === "vi" ? "Trải nghiệm Motion" : "Try Motion FX"}</span>
                <span>➔</span>
              </button>
            </div>

          </div>
        </section>

        {/* ========================================================= */}
        {/* RECENT PROJECTS / DRAFTS SHOWCASE */}
        {/* ========================================================= */}
        <section
          id="recent-projects"
          className="relative z-10 mx-auto max-w-7xl px-4 pb-16 sm:px-8 sm:pb-20 lg:px-10 border-t border-neutral-300/80 pt-12 bg-[#FAF7F2]"
        >
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <p className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-500">
                {t.recent_projects_eyebrow}
              </p>
              <h2 className="mt-2 font-serif text-2xl font-bold tracking-tight text-neutral-950 sm:text-3xl">
                {t.recent_projects_title}
              </h2>
              <p className="mt-2 text-sm text-neutral-600 max-w-xl">
                {t.recent_projects_sub}
              </p>
            </div>
            <button
              type="button"
              onClick={onOpenAuth}
              className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-4 py-2 text-xs font-mono font-bold uppercase tracking-wider text-neutral-900 hover:bg-neutral-100 hover:border-neutral-900 transition-colors shrink-0 shadow-sm cursor-pointer"
            >
              <span>{lang === "vi" ? "Bắt đầu dự án mới" : "Start New Project"}</span>
              <span>➔</span>
            </button>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {recentProjects.map((project, idx) => (
              <div
                key={idx}
                onClick={onOpenAuth}
                className="group rounded-xl border border-neutral-300/80 bg-white overflow-hidden shadow-sm hover:shadow-xl hover:border-neutral-900 transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="relative aspect-[16/10] w-full overflow-hidden bg-neutral-900">
                    <Image
                      src={project.image}
                      alt={project.title}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                    <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-black/80 text-[9px] font-mono font-bold text-white border border-white/20">
                      {project.tag}
                    </span>
                    <span className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-white/95 text-[9px] font-mono font-bold text-neutral-900 shadow-sm">
                      {project.progress}
                    </span>
                  </div>

                  <div className="p-4">
                    <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block">
                      {project.genre}
                    </span>
                    <h3 className="font-serif text-base font-bold text-neutral-950 mt-1 group-hover:underline">
                      {project.title}
                    </h3>
                    <p className="mt-2 text-xs leading-relaxed text-neutral-600 line-clamp-2">
                      {project.synopsis}
                    </p>
                  </div>
                </div>

                <div className="px-4 pb-4 pt-2 border-t border-neutral-100 flex items-center justify-between text-[11px] font-mono text-neutral-500">
                  <span>{project.stats}</span>
                  <span className="font-bold text-neutral-950 group-hover:translate-x-1 transition-transform">
                    {lang === "vi" ? "Xem ➔" : "View ➔"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ========================================================= */}
        {/* FEATURED WORLDS SECTION (WORLD BUILDING) */}
        {/* ========================================================= */}
        <section
          id="featured-worlds"
          className="relative z-10 mx-auto max-w-7xl px-4 pb-16 sm:px-8 sm:pb-20 lg:px-10 border-t border-neutral-300/80 pt-12 bg-[#FAF7F2]"
        >
          <div className="mb-8">
            <p className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-500">
              {t.featured_worlds_eyebrow}
            </p>
            <h2 className="mt-2 font-serif text-2xl font-bold tracking-tight text-neutral-950 sm:text-3xl">
              {t.featured_worlds_title}
            </h2>
            <p className="mt-2 text-sm text-neutral-600 max-w-2xl">
              {t.featured_worlds_sub}
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {featuredWorlds.map((world, idx) => (
              <div
                key={world.id}
                onClick={() => {
                  setActiveWorldIdx(idx);
                  onOpenAuth();
                }}
                className={`group relative rounded-xl border overflow-hidden p-5 transition-all cursor-pointer flex flex-col justify-between ${
                  activeWorldIdx === idx
                    ? "border-neutral-950 bg-[#FDFBF7] shadow-xl ring-1 ring-neutral-950/10"
                    : "border-neutral-300/80 bg-white hover:border-neutral-500 shadow-sm"
                }`}
              >
                <div>
                  <div className="relative aspect-[16/9] w-full rounded-lg overflow-hidden border border-neutral-200 bg-neutral-900 mb-4 group-hover:scale-[1.02] transition-transform duration-500">
                    <Image
                      src={world.image}
                      alt={world.title}
                      fill
                      className="object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                    <span className="absolute bottom-2 left-2 px-1.5 py-0.5 rounded bg-black/80 text-[9px] font-mono text-white border border-white/20">
                      {world.period}
                    </span>
                  </div>

                  <h3 className="font-serif text-lg font-bold text-neutral-950 group-hover:underline">
                    {world.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-neutral-600">
                    {world.desc}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-neutral-200 space-y-3">
                  <div className="flex flex-wrap gap-1.5">
                    {world.tags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        className="rounded border border-neutral-200 bg-neutral-100 px-2 py-0.5 text-[9px] font-mono font-bold text-neutral-700"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono font-bold text-neutral-950">
                    <span>{lang === "vi" ? "Áp dụng vào bản thảo" : "Load World Preset"}</span>
                    <span>➔</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ========================================================= */}
        {/* HERITAGE, ETHICS & SAFETY GUARANTEE */}
        {/* ========================================================= */}
        <section
          id="heritage"
          aria-labelledby="heritage-heading"
          className="relative z-10 mx-auto max-w-7xl px-4 pb-14 sm:px-8 sm:pb-16 lg:px-10 border-t border-neutral-300/80 pt-12 bg-[#FAF7F2]"
        >
          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:gap-14">
            <div className="max-w-xl">
              <p className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-500">
                {t.heritage_eyebrow}
              </p>
              <h2
                id="heritage-heading"
                className="mt-3 font-serif text-2xl font-bold leading-tight tracking-tight text-neutral-950 sm:text-3xl"
              >
                {t.heritage_title}
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-neutral-600">
                {t.heritage_desc}
              </p>
              <button
                type="button"
                onClick={onOpenAuth}
                className="mt-5 inline-flex items-center gap-2 text-sm font-mono font-bold uppercase tracking-wider text-neutral-950 underline hover:opacity-80 transition-opacity cursor-pointer"
              >
                <span>{t.heritage_cta}</span>
                <span>➔</span>
              </button>
            </div>

            <div className="divide-y divide-neutral-200">
              {[
                { number: "[01]", title: t.heritage_history_title, description: t.heritage_history_desc },
                { number: "[02]", title: t.heritage_culture_title, description: t.heritage_culture_desc },
                { number: "[03]", title: t.heritage_community_title, description: t.heritage_community_desc },
              ].map((item) => (
                <article key={item.number} className="grid grid-cols-[3rem_1fr] gap-3 py-4 first:pt-0 last:pb-0">
                  <span className="pt-0.5 text-xs font-mono font-bold text-neutral-500">
                    {item.number}
                  </span>
                  <div>
                    <h3 className="font-serif text-base font-bold text-neutral-950">
                      {item.title}
                    </h3>
                    <p className="mt-1 text-sm leading-relaxed text-neutral-600">
                      {item.description}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          {/* Bottom Security Assurance Banner */}
          <div className="mt-10 flex flex-col items-start justify-between gap-4 rounded-xl border border-amber-300/80 bg-[#FFFDF8] p-5 sm:flex-row sm:items-center shadow-sm">
            <div className="flex items-start gap-3">
              <span className="px-2 py-0.5 text-xs font-mono font-bold border border-amber-300 bg-amber-50 text-amber-900 rounded shrink-0">
                [BẢO ĐẢM IP]
              </span>
              <div>
                <h3 className="font-serif text-base font-bold text-neutral-950">
                  {lang === "vi" ? "Sáng tác với sự an tâm tuyệt đối" : "Create with complete confidence"}
                </h3>
                <p className="mt-1 text-xs sm:text-sm text-neutral-600">
                  {lang === "vi"
                    ? "Toàn bộ cốt truyện, nhân vật và khung manga thuộc quyền sở hữu trí tuệ 100% của tác giả. Hệ thống có cơ chế kiểm duyệt nội dung văn hóa và tự động lưu dự phòng."
                    : "All narratives, characters, and manga storyboards are 100% owned by the creator. Cultural guardrails and automated draft backups ensure safe storytelling."}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onExploreCommunity ?? onOpenAuth}
              className="inline-flex shrink-0 items-center rounded-lg border border-neutral-300 bg-white px-4 py-2 text-xs font-mono font-bold uppercase tracking-wider text-neutral-900 hover:bg-neutral-100 transition-colors shadow-sm cursor-pointer"
            >
              {lang === "vi" ? "Gặp gỡ cộng đồng" : "Meet Community"}
            </button>
          </div>
        </section>

        {/* ========================================================= */}
        {/* FOOTER */}
        {/* ========================================================= */}
        <footer className="relative z-10 border-t border-neutral-300/80 px-5 py-6 text-center text-xs font-mono text-neutral-600 bg-[#FAF7F2]">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 max-w-7xl mx-auto">
            <span>{t.footer_copyright}</span>
            <div className="flex items-center gap-4 text-[11px] text-neutral-600">
              <a href="#studios" className="hover:text-neutral-950 hover:underline">Story Lab</a>
              <a href="#studios" className="hover:text-neutral-950 hover:underline">Manga Studio</a>
              <a href="#studios" className="hover:text-neutral-950 hover:underline">Character Lore</a>
              <a href="#studios" className="hover:text-neutral-950 hover:underline">Motion Studio</a>
            </div>
          </div>
        </footer>

      </div>
    </main>
  );
}

export default LandingView;
