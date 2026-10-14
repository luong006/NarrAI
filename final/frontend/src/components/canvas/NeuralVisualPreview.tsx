"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";

export type NeuralStyleMode = "manga_ink" | "dong_ho" | "cyber_neon" | "ethereal_novel";

interface StyleConfig {
  id: NeuralStyleMode;
  nameVi: string;
  nameEn: string;
  descriptionVi: string;
  descriptionEn: string;
  badge: string;
}

export const STYLE_CONFIGS: Record<NeuralStyleMode, StyleConfig> = {
  manga_ink: {
    id: "manga_ink",
    nameVi: "Manga Shonen & Screentone",
    nameEn: "Manga Monochrome & Screentone",
    descriptionVi: "Đơn sắc thuần túy, tương phản cao, nét viền và screentone chuẩn mực.",
    descriptionEn: "High-contrast monochrome lineart with halftone screentone shading.",
    badge: "[100% Monochrome]",
  },
  dong_ho: {
    id: "dong_ho",
    nameVi: "Tranh Dân Gian Đông Hồ",
    nameEn: "Dong Ho Folk Woodblock",
    descriptionVi: "Họa sắc hoa dành dành, điệp xà cừ, chàm cổ phong Đại Việt.",
    descriptionEn: "Traditional Vietnamese mineral pigments, organic textures, and woodblock grain.",
    badge: "[Vietnamese Heritage]",
  },
  cyber_neon: {
    id: "cyber_neon",
    nameVi: "Cyberpunk Thăng Long 2099",
    nameEn: "Cyberpunk Neon Matrix",
    descriptionVi: "Ma trận sóng nơ-ron điện toán, ánh sáng huỳnh quang và lưới điện tử.",
    descriptionEn: "Futuristic synthetic neural grid, cyan/magenta pulses, and scanlines.",
    badge: "[Synthetic Matrix]",
  },
  ethereal_novel: {
    id: "ethereal_novel",
    nameVi: "Light Novel Huyền Mộng",
    nameEn: "Ethereal Light Novel",
    descriptionVi: "Khuếch tán màu nước dịu nhẹ, ánh sáng hoàng hôn và hạt sáng lơ lửng.",
    descriptionEn: "Dreamy watercolor diffusion with golden hour bloom and particulate dispersion.",
    badge: "[Dreamy Bloom]",
  },
};

interface Props {
  lang?: "vi" | "en";
  className?: string;
  initialStyle?: NeuralStyleMode;
  resolution?: number;
  onTextureGenerated?: (canvas: HTMLCanvasElement) => void;
}

export function NeuralVisualPreview({
  lang = "vi",
  className = "",
  initialStyle = "manga_ink",
  resolution = 128,
  onTextureGenerated,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [styleMode, setStyleMode] = useState<NeuralStyleMode>(initialStyle);
  const [seed, setSeed] = useState<number>(42);
  const [isAnimating, setIsAnimating] = useState<boolean>(true);
  const animFrameRef = useRef<number | null>(null);
  const timeRef = useRef<number>(0);

  const currentCfg = STYLE_CONFIGS[styleMode];

  // Procedural cellular/neural wave simulation
  const renderNeuralFrame = useCallback(
    (time: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      const imgData = ctx.createImageData(w, h);
      const data = imgData.data;

      const t = time * 0.001;

      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const idx = (y * w + x) * 4;
          const nx = (x / w) * 2 - 1;
          const ny = (y / h) * 2 - 1;

          // Cellular wave formula
          const wave1 = Math.sin(nx * 4.0 + t + seed * 0.1);
          const wave2 = Math.cos(ny * 4.0 - t * 0.8 + seed * 0.2);
          const wave3 = Math.sin((nx * nx + ny * ny) * 3.0 - t * 1.2);
          const val = (wave1 + wave2 + wave3) / 3.0; // [-1, 1]
          const norm = (val + 1) * 0.5; // [0, 1]

          if (styleMode === "manga_ink") {
            // Screentone dot pattern
            const dotGrid = (Math.sin(x * 1.2) * Math.cos(y * 1.2) + 1) * 0.5;
            const threshold = norm > 0.55 ? 1 : (dotGrid > 0.7 ? 0.8 : 0.1);
            const intensity = Math.floor(threshold * 255);
            data[idx] = intensity;
            data[idx + 1] = intensity;
            data[idx + 2] = intensity;
            data[idx + 3] = 255;
          } else if (styleMode === "dong_ho") {
            // Earthy woodblock grain
            data[idx] = Math.floor(norm * 180 + 40);
            data[idx + 1] = Math.floor(norm * 140 + 30);
            data[idx + 2] = Math.floor(norm * 100 + 20);
            data[idx + 3] = 255;
          } else if (styleMode === "cyber_neon") {
            // High contrast neon pulses
            data[idx] = Math.floor((1 - norm) * 255);
            data[idx + 1] = Math.floor(Math.sin(norm * Math.PI) * 240);
            data[idx + 2] = Math.floor(norm * 255);
            data[idx + 3] = 255;
          } else {
            // Ethereal diffuse pastel
            data[idx] = Math.floor(norm * 200 + 55);
            data[idx + 1] = Math.floor(norm * 180 + 75);
            data[idx + 2] = Math.floor(norm * 220 + 35);
            data[idx + 3] = 255;
          }
        }
      }

      ctx.putImageData(imgData, 0, 0);

      if (onTextureGenerated) {
        onTextureGenerated(canvas);
      }
    },
    [styleMode, seed, onTextureGenerated]
  );

  useEffect(() => {
    let active = true;

    const loop = (timestamp: number) => {
      if (!active) return;
      if (isAnimating) {
        timeRef.current = timestamp;
        renderNeuralFrame(timestamp);
      }
      animFrameRef.current = requestAnimationFrame(loop);
    };

    animFrameRef.current = requestAnimationFrame(loop);

    return () => {
      active = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isAnimating, renderNeuralFrame]);

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const a = document.createElement("a");
    a.download = `narr_neural_style_${styleMode}_${seed}.png`;
    a.href = canvas.toDataURL("image/png");
    a.click();
  };

  return (
    <div
      className={`rounded border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-black font-sans shadow-sm overflow-hidden transition-all ${className}`}
    >
      {/* Header Bar */}
      <div className="px-5 py-3.5 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between bg-neutral-50 dark:bg-neutral-900 font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-black font-bold text-black dark:text-white">
            [AI LAB]
          </span>
          <div>
            <h4 className="font-bold text-black dark:text-white uppercase tracking-wider flex items-center gap-1.5 font-sans">
              <span>{lang === "vi" ? "AI Art & Neural Style Laboratory" : "AI Art & Neural Style Lab"}</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded border border-neutral-300 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-800 text-black dark:text-white">
                TF.js
              </span>
            </h4>
            <p className="text-[11px] text-neutral-500 font-sans">
              {lang === "vi" ? currentCfg.nameVi : currentCfg.nameEn}
            </p>
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-black dark:text-white bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 px-2 py-0.5 rounded">
            {currentCfg.badge}
          </span>
        </div>
      </div>

      {/* Main Preview Area */}
      <div className="p-5 flex flex-col md:flex-row items-center gap-6">
        {/* Canvas Display Viewport */}
        <div className="relative group shrink-0">
          <div className="relative rounded overflow-hidden border border-neutral-300 dark:border-neutral-700 bg-black">
            <canvas
              ref={canvasRef}
              width={resolution}
              height={resolution}
              className="w-48 h-48 sm:w-56 sm:h-56 object-cover image-rendering-pixelated transform transition-transform duration-500 group-hover:scale-105"
            />
          </div>

          {/* Quick Action Overlay */}
          <div className="absolute bottom-2 right-2 flex items-center gap-1.5 font-mono text-xs">
            <button
              onClick={() => setIsAnimating(!isAnimating)}
              className="px-2 py-1 rounded bg-black/80 hover:bg-black text-white border border-neutral-700 transition-all"
              title={isAnimating ? (lang === "vi" ? "Tạm dừng" : "Pause") : (lang === "vi" ? "Tiếp tục" : "Play")}
            >
              {isAnimating ? "[Dừng]" : "[Chạy]"}
            </button>
            <button
              onClick={() => setSeed((s) => s + 1)}
              className="px-2 py-1 rounded bg-black/80 hover:bg-black text-white border border-neutral-700 transition-all"
              title={lang === "vi" ? "Đổi mầm ngẫu nhiên" : "Randomize Seed"}
            >
              [Mầm]
            </button>
            <button
              onClick={handleDownload}
              className="px-2 py-1 rounded bg-black/80 hover:bg-black text-white border border-neutral-700 transition-all"
              title={lang === "vi" ? "Tải ảnh về máy" : "Download Texture"}
            >
              [Tải]
            </button>
          </div>
        </div>

        {/* Style Controls & Metadata */}
        <div className="flex-1 w-full space-y-4">
          <div>
            <label className="text-xs font-mono font-bold text-black dark:text-white uppercase flex items-center gap-1.5 mb-2">
              <span>[{lang === "vi" ? "Trường phái mỹ thuật" : "Art Style"}]</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(Object.keys(STYLE_CONFIGS) as NeuralStyleMode[]).map((key) => {
                const cfg = STYLE_CONFIGS[key];
                const isActive = styleMode === key;
                return (
                  <button
                    key={key}
                    onClick={() => setStyleMode(key)}
                    className={`text-left p-2.5 rounded border text-xs font-mono transition-all ${
                      isActive
                        ? "border-black dark:border-white bg-black text-white dark:bg-white dark:text-black font-bold"
                        : "border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-900 text-black dark:text-white"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="truncate">{lang === "vi" ? cfg.nameVi : cfg.nameEn}</span>
                    </div>
                    <p className="text-[10px] opacity-70 font-sans line-clamp-1">
                      {lang === "vi" ? cfg.descriptionVi : cfg.descriptionEn}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Technical Specs Footer */}
          <div className="pt-2 border-t border-neutral-200 dark:border-neutral-800 flex flex-wrap items-center justify-between text-[11px] font-mono text-neutral-500 gap-2">
            <div className="flex items-center gap-3">
              <span>[Lớp: 128]</span>
              <span>[Seed: #{seed}]</span>
              <span>[Độ phân giải: {resolution}px]</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
export default NeuralVisualPreview;
