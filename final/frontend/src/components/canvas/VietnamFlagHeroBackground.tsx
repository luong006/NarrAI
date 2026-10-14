"use client";

import React, { useEffect, useRef } from "react";

interface VietnamFlagHeroBackgroundProps {
  /** Optional container class name */
  className?: string;
  /** Whether animation is paused */
  paused?: boolean;
}

/**
 * VietnamFlagHeroBackground
 *
 * Generative Light Ribbon Background for NARR AI Landing Hero:
 * 1. Warm milky white background (#FAF7F2).
 * 2. Crimson light ribbon streams sweeping and weaving the rectangular Vietnam Flag (2:3 standard ratio).
 * 3. Pure yellow light ribbon streams converging and tracing the canonical 5-pointed star in solid yellow (#FFFF00).
 * 4. Ambient silk wave dynamics, luminous glow, and trailing light embers.
 */
export function VietnamFlagHeroBackground({
  className = "",
  paused = false,
}: VietnamFlagHeroBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const flagContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || paused) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 960);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      height = canvas.height = canvas.parentElement?.clientHeight || 960;
      if (ctx) {
        ctx.fillStyle = "#FAF7F2";
        ctx.fillRect(0, 0, width, height);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    // Compute Flag 2:3 geometric boundary & Star 10 vertices
    function getFlagTargets(cx: number, cy: number, flagW: number, flagH: number) {
      const halfW = flagW / 2;
      const halfH = flagH / 2;

      const rectCorners = [
        { x: cx - halfW, y: cy - halfH }, // Top-Left
        { x: cx, y: cy - halfH },         // Top-Mid
        { x: cx + halfW, y: cy - halfH }, // Top-Right
        { x: cx + halfW, y: cy },         // Right-Mid
        { x: cx + halfW, y: cy + halfH }, // Bottom-Right
        { x: cx, y: cy + halfH },         // Bottom-Mid
        { x: cx - halfW, y: cy + halfH }, // Bottom-Left
        { x: cx - halfW, y: cy },         // Left-Mid
      ];

      const starR = flagH * 0.32;
      const starPts: { x: number; y: number }[] = [];
      for (let i = 0; i < 10; i++) {
        const rad = i % 2 === 0 ? starR : starR * 0.39;
        const angle = -Math.PI / 2 + (i * Math.PI) / 5;
        starPts.push({
          x: cx + rad * Math.cos(angle),
          y: cy + rad * Math.sin(angle),
        });
      }

      return { rectCorners, starPts };
    }

    // Ribbon particle representation
    class RibbonParticle {
      type: "red-border" | "red-fill" | "yellow-star";
      index: number;
      history: { x: number; y: number }[];
      maxLen: number;
      currX: number;
      currY: number;
      phase: number;
      speed: number;

      constructor(type: "red-border" | "red-fill" | "yellow-star", index: number) {
        this.type = type;
        this.index = index;
        this.history = [];
        this.maxLen = 36;
        this.currX = 0;
        this.currY = 0;
        this.phase = Math.random() * Math.PI * 2;
        this.speed = 1.0 + Math.random() * 0.4;
      }

      update(
        elapsed: number,
        cx: number,
        cy: number,
        targets: { rectCorners: { x: number; y: number }[]; starPts: { x: number; y: number }[] },
        conv: number
      ) {
        const { rectCorners, starPts } = targets;
        let tx = 0;
        let ty = 0;

        if (this.type === "red-border") {
          const cornerIdx = this.index % rectCorners.length;
          const nextIdx = (cornerIdx + 1) % rectCorners.length;
          const p1 = rectCorners[cornerIdx];
          const p2 = rectCorners[nextIdx];
          const subT = (elapsed * 1.5 * this.speed + this.index * 0.25) % 1;

          const rectTargetX = p1.x + (p2.x - p1.x) * subT;
          const rectTargetY = p1.y + (p2.y - p1.y) * subT;

          const wanderX = cx + Math.cos(elapsed * 0.8 + this.phase) * (width * 0.48);
          const wanderY = cy + Math.sin(elapsed * 0.7 + this.phase) * (height * 0.42);

          tx = wanderX * (1 - conv) + rectTargetX * conv;
          ty = wanderY * (1 - conv) + rectTargetY * conv;
        } else if (this.type === "red-fill") {
          const spanW = Math.min(width * 0.65, 420);
          const spanH = spanW * (2 / 3);
          const rectTargetX = cx + Math.sin(elapsed * 1.8 + this.index) * spanW * 0.44;
          const rectTargetY = cy + Math.cos(elapsed * 1.4 + this.index) * spanH * 0.44;

          const wanderX = cx + Math.sin(elapsed * 0.9 + this.phase) * (width * 0.5);
          const wanderY = cy + Math.cos(elapsed * 0.8 + this.phase) * (height * 0.4);

          tx = wanderX * (1 - conv) + rectTargetX * conv;
          ty = wanderY * (1 - conv) + rectTargetY * conv;
        } else {
          // Yellow Star ribbons
          const ptIdx = this.index % starPts.length;
          const nextIdx = (ptIdx + 1) % starPts.length;
          const sp1 = starPts[ptIdx];
          const sp2 = starPts[nextIdx];
          const subT = (elapsed * 2.2 * this.speed + this.index * 0.3) % 1;

          const starTargetX = sp1.x + (sp2.x - sp1.x) * subT;
          const starTargetY = sp1.y + (sp2.y - sp1.y) * subT;

          const wanderX = cx + Math.cos(elapsed * 1.2 + this.phase) * (width * 0.45);
          const wanderY = cy + Math.sin(elapsed * 1.1 + this.phase) * (height * 0.4);

          tx = wanderX * (1 - conv) + starTargetX * conv;
          ty = wanderY * (1 - conv) + starTargetY * conv;
        }

        if (this.history.length === 0) {
          this.currX = tx;
          this.currY = ty;
        } else {
          this.currX += (tx - this.currX) * 0.16;
          this.currY += (ty - this.currY) * 0.16;
        }

        this.history.unshift({ x: this.currX, y: this.currY });
        if (this.history.length > this.maxLen) {
          this.history.pop();
        }
      }

      draw(c: CanvasRenderingContext2D) {
        if (this.history.length < 3) return;
        const isYellow = this.type === "yellow-star";

        c.save();
        c.lineCap = "round";
        c.lineJoin = "round";

        const passes = isYellow ? [14, 6, 2] : [20, 8, 2.5];

        for (let p = 0; p < passes.length; p++) {
          const w = passes[p];
          c.beginPath();
          c.moveTo(this.history[0].x, this.history[0].y);

          for (let i = 1; i < this.history.length - 1; i++) {
            const xc = (this.history[i].x + this.history[i + 1].x) * 0.5;
            const yc = (this.history[i].y + this.history[i + 1].y) * 0.5;
            c.quadraticCurveTo(this.history[i].x, this.history[i].y, xc, yc);
          }

          if (isYellow) {
            if (w === 14) {
              c.strokeStyle = "rgba(255, 255, 0, 0.22)";
              c.shadowColor = "#FFFF00";
              c.shadowBlur = 16;
            } else if (w === 6) {
              c.strokeStyle = "rgba(255, 255, 0, 0.65)";
              c.shadowColor = "#FFFF00";
              c.shadowBlur = 10;
            } else {
              c.strokeStyle = "#FFFF00";
              c.shadowBlur = 4;
            }
          } else {
            if (w === 20) {
              c.strokeStyle = "rgba(218, 37, 29, 0.18)";
              c.shadowColor = "#DC2626";
              c.shadowBlur = 20;
            } else if (w === 8) {
              c.strokeStyle = "rgba(220, 38, 38, 0.4)";
              c.shadowColor = "#EF4444";
              c.shadowBlur = 10;
            } else {
              c.strokeStyle = "rgba(239, 68, 68, 0.8)";
              c.shadowBlur = 4;
            }
          }

          c.lineWidth = w;
          c.stroke();
        }

        // Luminous spark head
        const head = this.history[0];
        c.fillStyle = isYellow ? "#FFFF00" : "#DC2626";
        c.shadowColor = isYellow ? "#FFFF00" : "#EF4444";
        c.shadowBlur = 12;
        c.beginPath();
        c.arc(head.x, head.y, isYellow ? 3.2 : 2.5, 0, Math.PI * 2);
        c.fill();

        c.restore();
      }
    }

    const ribbons: RibbonParticle[] = [];
    for (let i = 0; i < 8; i++) ribbons.push(new RibbonParticle("red-border", i));
    for (let i = 0; i < 6; i++) ribbons.push(new RibbonParticle("red-fill", i));
    for (let i = 0; i < 10; i++) ribbons.push(new RibbonParticle("yellow-star", i));

    const startTime = performance.now();

    const render = (now: number) => {
      const elapsed = (now - startTime) / 1000;
      const cx = width / 2;
      const cy = height * 0.38; // Positioned behind the hero visual focal area

      const conv = Math.min(1.0, Math.max(0, (elapsed - 0.8) / 2.6));

      // Soft persistence decay on milky white background
      ctx.save();
      ctx.fillStyle = elapsed > 4.5 ? "rgba(250, 247, 242, 0.05)" : "rgba(250, 247, 242, 0.028)";
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      // Flag geometry calculations
      const flagW = Math.min(width * 0.72, 460);
      const flagH = flagW * (2 / 3);
      const targets = getFlagTargets(cx, cy, flagW, flagH);

      // Ambient radial red glow
      const redGlow = ctx.createRadialGradient(cx, cy, 30, cx, cy, flagW * 0.8);
      redGlow.addColorStop(0, `rgba(218, 37, 29, ${0.12 + conv * 0.2})`);
      redGlow.addColorStop(0.5, `rgba(185, 28, 28, ${0.06 + conv * 0.1})`);
      redGlow.addColorStop(1, "rgba(250, 247, 242, 0)");
      ctx.fillStyle = redGlow;
      ctx.fillRect(0, 0, width, height);

      // Update & Draw ribbons
      ribbons.forEach((r) => {
        r.update(elapsed, cx, cy, targets, conv);
        r.draw(ctx);
      });

      // Update Flag DOM element opacity
      if (flagContainerRef.current) {
        if (elapsed >= 0.8) {
          const op = Math.min(1.0, (elapsed - 0.8) / 2.6);
          flagContainerRef.current.style.opacity = (op * 0.95).toString();
          const breathe = 0.95 + op * 0.05 + Math.sin(elapsed * 1.6) * 0.012;
          flagContainerRef.current.style.transform = `scale(${breathe})`;
        } else {
          flagContainerRef.current.style.opacity = "0";
          flagContainerRef.current.style.transform = "scale(0.9)";
        }
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      window.removeEventListener("resize", handleResize);
    };
  }, [paused]);

  return (
    <div
      className={`absolute inset-x-0 top-0 h-[960px] pointer-events-none overflow-hidden z-0 select-none bg-[#FAF7F2] ${className}`}
      aria-hidden="true"
    >
      {/* 1. Procedural Light Ribbons Canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full block" />

      {/* 2. Converged National Vietnam Flag Layer */}
      <div
        ref={flagContainerRef}
        className="absolute inset-0 flex items-center justify-center pointer-events-none transition-all duration-700"
        style={{
          top: "-12%", // Vertically aligned to center with hero content
          opacity: 0,
          transform: "scale(0.9)",
          filter:
            "drop-shadow(0 8px 30px rgba(218, 37, 29, 0.4)) drop-shadow(0 2px 25px rgba(255, 235, 59, 0.45))",
        }}
      >
        <div className="relative w-[340px] h-[226px] sm:w-[460px] sm:h-[306px] rounded-xl overflow-hidden border border-red-500/50 shadow-[0_8px_40px_rgba(218,37,29,0.35)]">
          {/* Standard Red Flag Field (#DA251D - Chuẩn Quốc kỳ Việt Nam) */}
          <div className="absolute inset-0 bg-[#DA251D]" />

          {/* Gentle Silk Wave Shimmer Overlay */}
          <div className="absolute inset-0 opacity-25 bg-gradient-to-tr from-amber-400/25 via-transparent to-red-950/20" />

          {/* Pure Solid Yellow 5-Pointed Star in Center (CHỈ MỘT MÀU VÀNG #FFFF00) */}
          <div className="absolute inset-0 flex items-center justify-center">
            <svg
              viewBox="0 0 300 300"
              className="w-32 h-32 sm:w-44 sm:h-44 overflow-visible filter drop-shadow-[0_0_14px_rgba(255,255,0,0.85)]"
            >
              {/* Solid Pure Yellow Star Polygon (R=75, r=29.2, center=150,150) */}
              <polygon
                points="
                  150,75
                  167,127
                  221,127
                  177,159
                  194,211
                  150,179
                  106,211
                  123,159
                  79,127
                  133,127
                "
                fill="#FFFF00"
              />
            </svg>
          </div>

          {/* Glowing Silk Border Sweep */}
          <div className="absolute inset-0 border border-yellow-300/30 rounded-xl pointer-events-none" />
        </div>
      </div>

      {/* 3. Soft gradient vignettes to blend seamlessly into lower sections */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#FAF7F2]/40 via-transparent to-[#FAF7F2] pointer-events-none" />
    </div>
  );
}

export default VietnamFlagHeroBackground;
