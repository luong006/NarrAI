"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Sparkles, RefreshCw, Play, Pause, Download, Palette, Zap, Layers } from "lucide-react";

export type NeuralStyleMode = "manga_ink" | "dong_ho" | "cyber_neon" | "ethereal_novel";

interface StyleConfig {
  id: NeuralStyleMode;
  nameVi: string;
  nameEn: string;
  descriptionVi: string;
  descriptionEn: string;
  colorTheme: string;
  badge: string;
}

export const STYLE_CONFIGS: Record<NeuralStyleMode, StyleConfig> = {
  manga_ink: {
    id: "manga_ink",
    nameVi: "Manga Shonen & Screentone",
    nameEn: "Manga Monochrome & Screentone",
    descriptionVi: "Đơn sắc thuần túy, tương phản cao, nét viền và screentone chuẩn mực.",
    descriptionEn: "High-contrast monochrome lineart with halftone screentone shading.",
    colorTheme: "from-zinc-900 via-neutral-700 to-zinc-400",
    badge: "100% Monochrome",
  },
  dong_ho: {
    id: "dong_ho",
    nameVi: "Tranh Dân Gian Đông Hồ",
    nameEn: "Dong Ho Folk Woodblock",
    descriptionVi: "Họa sắc hoa dành dành, điệp xà cừ, chàm cổ phong Đại Việt.",
    descriptionEn: "Traditional Vietnamese mineral pigments, organic textures, and woodblock grain.",
    colorTheme: "from-amber-700 via-emerald-800 to-rose-700",
    badge: "Vietnamese Heritage",
  },
  cyber_neon: {
    id: "cyber_neon",
    nameVi: "Cyberpunk Thăng Long 2099",
    nameEn: "Cyberpunk Neon Matrix",
    descriptionVi: "Ma trận sóng nơ-ron điện toán, ánh sáng huỳnh quang và lưới điện tử.",
    descriptionEn: "Futuristic synthetic neural grid, cyan/magenta pulses, and scanlines.",
    colorTheme: "from-cyan-500 via-purple-600 to-pink-500",
    badge: "Synthetic Matrix",
  },
  ethereal_novel: {
    id: "ethereal_novel",
    nameVi: "Light Novel Huyền Mộng",
    nameEn: "Ethereal Light Novel",
    descriptionVi: "Khuếch tán màu nước dịu nhẹ, ánh sáng hoàng hôn và hạt sáng lơ lửng.",
    descriptionEn: "Dreamy watercolor diffusion with golden hour bloom and particulate dispersion.",
    colorTheme: "from-indigo-400 via-rose-300 to-amber-200",
    badge: "Dreamy Bloom",
  },
};

interface Props {
  lang?: "vi" | "en";
  className?: string;
  initialStyle?: NeuralStyleMode;
  compact?: boolean;
}

/**
 * NeuralVisualPreview
 * Feature 30: Landing Page Neural Visual Effects
 *
 * Renders generative AI art textures and latent style previews on an isolated 2D canvas.
 * Explicitly avoids WebGL context initialization to prevent collision with Layer 0 ThreeAmbientCanvas.
 */
export function NeuralVisualPreview({
  lang = "vi",
  className = "",
  initialStyle = "cyber_neon",
  compact = false,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [styleMode, setStyleMode] = useState<NeuralStyleMode>(initialStyle);
  const [isAnimating, setIsAnimating] = useState(true);
  const [seed, setSeed] = useState(1337);
  const [resolution, setResolution] = useState<number>(compact ? 128 : 160);
  const animFrameRef = useRef<number | null>(null);
  const timeRef = useRef<number>(0);

  // Deterministic seeded pseudorandom function
  const prng = useCallback((s: number) => {
    let t = (s += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }, []);

  /**
   * Generates a 2D procedural neural field slice on CPU.
   * Simulates multi-frequency Perlin-Gabor style projection.
   */
  const renderNeuralFrame = useCallback(
    (t: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      const imgData = ctx.createImageData(w, h);
      const data = imgData.data;

      const baseSeed = seed;
      const s1 = prng(baseSeed);
      const s2 = prng(baseSeed + 1);
      const s3 = prng(baseSeed + 2);

      const freqX = 3.5 + s1 * 2.0;
      const freqY = 3.5 + s2 * 2.0;

      for (let y = 0; y < h; y++) {
        const ny = (y / h) * 2 - 1;
        const rowOffset = y * w * 4;

        for (let x = 0; x < w; x++) {
          const nx = (x / w) * 2 - 1;
          const idx = rowOffset + x * 4;

          // Radial distance & angular coordinates
          const r = Math.sqrt(nx * nx + ny * ny);
          const theta = Math.atan2(ny, nx);

          // Harmonic wave equation with temporal drift
          const wave1 = Math.sin(nx * freqX + t * 0.8 + s1 * 6.28);
          const wave2 = Math.cos(ny * freqY - t * 0.6 + s2 * 6.28);
          const spiral = Math.sin(r * 8.0 - theta * 3.0 + t * 1.2);
          const neuralNoise = Math.sin(nx * 14.0 + ny * 14.0 + t * 0.3) * 0.25;

          // Composite neural activation potential in [-1.0, 1.0]
          const potential = (wave1 * 0.4 + wave2 * 0.4 + spiral * 0.35 + neuralNoise) / 1.4;
          const normPotential = Math.max(0, Math.min(1, (potential + 1) / 2));

          let rVal = 0;
          let gVal = 0;
          let bVal = 0;

          // Style Palette Mapping
          if (styleMode === "manga_ink") {
            // Pure monochrome screentone & ink wash
            const inkThreshold = 0.52 + Math.sin(x * 0.7) * Math.cos(y * 0.7) * 0.08;
            const isDot = (x % 4 === 0 && y % 4 === 0 && normPotential > 0.4) ||
                          (x % 2 === 0 && y % 2 === 0 && normPotential > 0.7);
            const val = normPotential < inkThreshold ? 15 : isDot ? 50 : 240;
            rVal = gVal = bVal = val;
          } else if (styleMode === "dong_ho") {
            // Woodblock pigment: Điệp xà cừ (seashell pearl), Chàm (indigo), Dành dành (ochre)
            const grain = (prng(x * 37 + y * 97 + baseSeed) - 0.5) * 25;
            if (normPotential < 0.35) {
              // Deep Indigo
              rVal = Math.max(0, 30 + grain);
              gVal = Math.max(0, 50 + grain);
              bVal = Math.max(0, 90 + grain);
            } else if (normPotential < 0.65) {
              // Cinnabar Red / Crimson
              rVal = Math.min(255, 185 + grain);
              gVal = Math.max(0, 55 + grain);
              bVal = Math.max(0, 45 + grain);
            } else {
              // Warm Pearl Ochre
              rVal = Math.min(255, 235 + grain);
              gVal = Math.min(255, 205 + grain);
              bVal = Math.min(255, 140 + grain);
            }
          } else if (styleMode === "cyber_neon") {
            // High-voltage Neon Cyan & Magenta with scanline pulses
            const scanline = y % 3 === 0 ? 0.75 : 1.0;
            const pulse = Math.sin(t * 2.0 + ny * 6.0) * 0.3;
            const cyan = Math.pow(normPotential, 1.4);
            const magenta = Math.pow(1 - normPotential, 1.6);

            rVal = Math.min(255, (magenta * 240 + pulse * 40) * scanline);
            gVal = Math.min(255, (cyan * 180 + magenta * 30) * scanline);
            bVal = Math.min(255, (cyan * 255 + magenta * 150) * scanline);
          } else {
            // Ethereal Light Novel: Pastel sunset & dreamy light dispersion
            const glow = Math.exp(-r * 1.8) * 0.6;
            rVal = Math.min(255, (normPotential * 220 + glow * 100));
            gVal = Math.min(255, (Math.sin(normPotential * 3.14) * 160 + glow * 80));
            bVal = Math.min(255, ((1 - normPotential) * 230 + glow * 120));
          }

          data[idx] = rVal;
          data[idx + 1] = gVal;
          data[idx + 2] = bVal;
          data[idx + 3] = 255;
        }
      }

      ctx.putImageData(imgData, 0, 0);
    },
    [prng, seed, styleMode]
  );

  // Animation Loop
  useEffect(() => {
    let active = true;

    const loop = () => {
      if (!active) return;
      if (isAnimating) {
        timeRef.current += 0.025;
      }
      renderNeuralFrame(timeRef.current);
      if (isAnimating) {
        animFrameRef.current = requestAnimationFrame(loop);
      }
    };

    if (isAnimating) {
      animFrameRef.current = requestAnimationFrame(loop);
    } else {
      renderNeuralFrame(timeRef.current);
    }

    return () => {
      active = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isAnimating, renderNeuralFrame]);

  // Download snapshot
  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement("a");
    link.download = `NarrAI_Neural_${styleMode}_${seed}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  const currentCfg = STYLE_CONFIGS[styleMode];

  return (
    <div
      className={`rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md shadow-xl overflow-hidden transition-all ${className}`}
    >
      {/* Header Bar */}
      <div className="px-5 py-3.5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-950/40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
              <span>{lang === "vi" ? "AI Art & Neural Style Laboratory" : "AI Art & Neural Style Lab"}</span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                TF.js CPU
              </span>
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {lang === "vi" ? currentCfg.nameVi : currentCfg.nameEn}
            </p>
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex items-center gap-2">
          <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
            <Zap className="w-3 h-3 text-indigo-500" />
            <span>Isolated 2D</span>
          </span>
          <span className="text-[10px] font-bold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/60 border border-brand-200/60 dark:border-brand-900 px-2 py-0.5 rounded">
            {currentCfg.badge}
          </span>
        </div>
      </div>

      {/* Main Preview Area */}
      <div className="p-5 flex flex-col md:flex-row items-center gap-6">
        {/* Canvas Display Viewport */}
        <div className="relative group shrink-0">
          <div className="relative rounded-xl overflow-hidden border border-slate-300 dark:border-slate-700 shadow-inner bg-slate-950">
            <canvas
              ref={canvasRef}
              width={resolution}
              height={resolution}
              className="w-48 h-48 sm:w-56 sm:h-56 object-cover image-rendering-pixelated transform transition-transform duration-500 group-hover:scale-105"
            />
            {/* Overlay Gradient Ring */}
            <div className="absolute inset-0 pointer-events-none ring-1 ring-inset ring-white/10 rounded-xl" />
          </div>

          {/* Quick Action Overlay */}
          <div className="absolute bottom-2 right-2 flex items-center gap-1.5">
            <button
              onClick={() => setIsAnimating(!isAnimating)}
              className="p-1.5 rounded-lg bg-black/60 hover:bg-black/80 text-white backdrop-blur-sm transition-all"
              title={isAnimating ? (lang === "vi" ? "Tạm dừng" : "Pause") : (lang === "vi" ? "Tiếp tục" : "Play")}
            >
              {isAnimating ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setSeed((s) => s + 1)}
              className="p-1.5 rounded-lg bg-black/60 hover:bg-black/80 text-white backdrop-blur-sm transition-all"
              title={lang === "vi" ? "Đổi mầm ngẫu nhiên" : "Randomize Seed"}
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 rounded-lg bg-black/60 hover:bg-black/80 text-white backdrop-blur-sm transition-all"
              title={lang === "vi" ? "Tải ảnh về máy" : "Download Texture"}
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Style Controls & Metadata */}
        <div className="flex-1 w-full space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2">
              <Palette className="w-3.5 h-3.5 text-indigo-500" />
              <span>{lang === "vi" ? "Trường phái mỹ thuật & Bộ lọc nơ-ron" : "Art Style & Neural Filter"}</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(Object.keys(STYLE_CONFIGS) as NeuralStyleMode[]).map((key) => {
                const cfg = STYLE_CONFIGS[key];
                const isActive = styleMode === key;
                return (
                  <button
                    key={key}
                    onClick={() => setStyleMode(key)}
                    className={`text-left p-2.5 rounded-xl border text-xs font-medium transition-all ${
                      isActive
                        ? "border-brand-500 bg-brand-50/70 dark:bg-brand-950/40 text-brand-900 dark:text-brand-200 shadow-sm"
                        : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold truncate">{lang === "vi" ? cfg.nameVi : cfg.nameEn}</span>
                      <span
                        className={`w-2 h-2 rounded-full bg-gradient-to-r ${cfg.colorTheme}`}
                      />
                    </div>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 line-clamp-1">
                      {lang === "vi" ? cfg.descriptionVi : cfg.descriptionEn}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Technical Specs Footer */}
          <div className="pt-2 border-t border-slate-200/80 dark:border-slate-800/80 flex flex-wrap items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 gap-2">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <Layers className="w-3 h-3 text-indigo-400" />
                <span>Dim: 128 (L2 Norm)</span>
              </span>
              <span>Seed: #{seed}</span>
              <span>Res: {resolution}px</span>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-slate-400">
                {lang === "vi" ? "Không xung đột WebGL Layer 0" : "0% WebGL Clash"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
