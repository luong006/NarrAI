"use client";

import React, { useEffect, useRef, useState } from "react";

interface Props {
  /** Optional custom class name */
  className?: string;
  /** Intensity of the animation: 0.1 (very subtle) to 1.0 (vivid) */
  intensity?: number;
  /** Whether mouse movement influences the silk movement */
  interactive?: boolean;
}

/**
 * AnimatedWeavesilkBackground
 *
 * Cinematic generative art background that combines:
 * 1. The official symmetrical WeaveSilk asset (/assets/weavesilk_bg.png) with breathing & undulating silk fiber currents.
 * 2. An organic Canvas 2D particle & ribbon flow with 6-fold radial symmetry flowing toward the central mandala.
 * 3. Luminous breathing core at the center matching the nucleus of the flower.
 * 4. Ultra-smooth 60fps performance with pointer-events-none so chat & cards remain 100% interactive.
 */
export function AnimatedWeavesilkBackground({
  className = "",
  intensity = 0.8,
  interactive = true,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Mouse coordinates with smooth damping
  const mouseRef = useRef({
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    active: false,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handleMotionChange = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handleMotionChange);

    return () => mediaQuery.removeEventListener("change", handleMotionChange);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || reducedMotion) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = canvas.offsetWidth || window.innerWidth);
    let height = (canvas.height = canvas.offsetHeight || window.innerHeight);

    // Particle / Silk strand state
    interface SilkPoint {
      angle: number;
      radius: number;
      speed: number;
      seed: number;
      alpha: number;
      length: number;
    }

    const strandsCount = Math.floor(28 * intensity);
    const strands: SilkPoint[] = [];

    const symmetry = 6; // 6-fold symmetry matching the 6-petal silk mandala

    for (let i = 0; i < strandsCount; i++) {
      strands.push({
        angle: (i / strandsCount) * (Math.PI * 2),
        radius: 80 + Math.random() * (Math.min(width, height) * 0.48),
        speed: 0.15 + Math.random() * 0.35,
        seed: Math.random() * 1000,
        alpha: 0.08 + Math.random() * 0.22,
        length: 25 + Math.random() * 50,
      });
    }

    // Handle Resize
    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth || window.innerWidth;
      height = canvas.height = canvas.offsetHeight || window.innerHeight;
    };

    window.addEventListener("resize", handleResize);

    // Handle mouse tracking
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current || !interactive) return;
      const rect = containerRef.current.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const normY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      mouseRef.current.targetX = normX;
      mouseRef.current.targetY = normY;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.targetX = 0;
      mouseRef.current.targetY = 0;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);

    let time = 0;

    const render = () => {
      time += 0.008;

      // Smooth mouse damping
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

      // Soft fading clear to create silky light persistence
      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2 + mouseRef.current.x * 25;
      const centerY = height / 2 + mouseRef.current.y * 25;

      ctx.save();
      ctx.translate(centerX, centerY);

      // Render 6-fold symmetrical dynamic silk wisps
      for (let sym = 0; sym < symmetry; sym++) {
        ctx.save();
        ctx.rotate((sym * (Math.PI * 2)) / symmetry);

        for (let i = 0; i < strands.length; i++) {
          const s = strands[i];

          // Animate radius gently breathing
          const rOffset = Math.sin(time * 0.8 + s.seed) * 35;
          const currentRadius = s.radius + rOffset;

          // Animate undulating angle
          const angleWobble = Math.sin(time * s.speed + s.seed * 0.1) * 0.18;
          const currentAngle = s.angle + angleWobble;

          const x1 = Math.cos(currentAngle) * currentRadius;
          const y1 = Math.sin(currentAngle) * currentRadius;

          // Control point for smooth curved Bézier silk thread
          const cpAngle = currentAngle + 0.25 * Math.cos(time + s.seed);
          const cpRadius = currentRadius * 0.75 + Math.sin(time * 1.2 + s.seed) * 20;
          const cpx = Math.cos(cpAngle) * cpRadius;
          const cpy = Math.sin(cpAngle) * cpRadius;

          const x2 = Math.cos(currentAngle + 0.4) * (currentRadius * 0.5);
          const y2 = Math.sin(currentAngle + 0.4) * (currentRadius * 0.5);

          // Draw silk curve
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.quadraticCurveTo(cpx, cpy, x2, y2);

          const glowAlpha = s.alpha * (0.6 + 0.4 * Math.sin(time * 1.5 + s.seed));
          ctx.strokeStyle = `rgba(180, 140, 90, ${(glowAlpha * 0.35).toFixed(3)})`;
          ctx.lineWidth = 0.8;
          ctx.shadowColor = "rgba(200, 160, 100, 0.25)";
          ctx.shadowBlur = 3;
          ctx.stroke();
        }

        ctx.restore();
      }

      ctx.restore();

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [intensity, interactive, reducedMotion]);

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 pointer-events-none overflow-hidden select-none bg-[#FAF7F2] ${className}`}
      aria-hidden="true"
    >
      {/* 1. LAYER A: Primary WeaveSilk Base Layer (Inverted warm lacquer threads on milky white paper) */}
      <div
        className="absolute inset-0 bg-center bg-cover bg-no-repeat transition-all duration-1000 ease-out"
        style={{
          backgroundImage: "url('/assets/weavesilk_bg.png')",
          backgroundPosition: "center center",
          filter: "invert(0.96) sepia(0.2) hue-rotate(350deg) contrast(1.1)",
          mixBlendMode: "multiply",
          opacity: 0.16,
          animation: reducedMotion
            ? "none"
            : "weavesilk-breathe 14s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate",
        }}
      />

      {/* 2. LAYER B: Secondary Undulating Silk Ribbon Currents */}
      {!reducedMotion && (
        <div
          className="absolute inset-0 bg-center bg-cover bg-no-repeat"
          style={{
            backgroundImage: "url('/assets/weavesilk_bg.png')",
            backgroundPosition: "center center",
            animation:
              "weavesilk-undulate 18s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate",
            filter: "invert(0.96) sepia(0.25) contrast(1.15)",
            mixBlendMode: "multiply",
            opacity: 0.12,
          }}
        />
      )}

      {/* 3. LAYER C: Dynamic 6-Fold Generative Canvas Ribbons */}
      {!reducedMotion && (
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full opacity-60 pointer-events-none"
        />
      )}

      {/* 4. LAYER D: Pulsing Central Mandala Aura (soft warm glow) */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 sm:w-96 sm:h-96 rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(circle, rgba(212,175,55,0.14) 0%, rgba(212,175,55,0.04) 35%, transparent 70%)",
          animation: reducedMotion
            ? "none"
            : "weavesilk-core-pulse 6s ease-in-out infinite",
        }}
      />

      {/* 5. LAYER E: Vignette & Lighting Gradients (Seamless blending into #FAF7F2) */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#FAF7F2]/90 via-transparent to-[#FAF7F2]/80 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#FAF7F2]/60 via-transparent to-[#FAF7F2]/60 pointer-events-none" />

      {/* Global Embedded Keyframes for buttery-smooth GPU animation */}
      <style jsx global>{`
        @keyframes weavesilk-breathe {
          0% {
            transform: scale(1) translate3d(0, 0, 0);
            opacity: 0.45;
          }
          50% {
            transform: scale(1.045) translate3d(0.5%, -0.5%, 0);
            opacity: 0.65;
          }
          100% {
            transform: scale(1.02) translate3d(-0.5%, 0.5%, 0);
            opacity: 0.52;
          }
        }

        @keyframes weavesilk-undulate {
          0% {
            transform: scale(1.04) rotate(0deg);
            opacity: 0.35;
          }
          50% {
            transform: scale(0.98) rotate(1.2deg);
            opacity: 0.6;
          }
          100% {
            transform: scale(1.05) rotate(-1.2deg);
            opacity: 0.4;
          }
        }

        @keyframes weavesilk-core-pulse {
          0% {
            transform: translate(-50%, -50%) scale(0.85);
            opacity: 0.3;
          }
          50% {
            transform: translate(-50%, -50%) scale(1.25);
            opacity: 0.7;
          }
          100% {
            transform: translate(-50%, -50%) scale(0.85);
            opacity: 0.3;
          }
        }
      `}</style>
    </div>
  );
}
