"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Image from "next/image";
import { DongSonDrum } from "./DongSonDrum";

interface WeavesilkIntroProps {
  /** Target duration in milliseconds (default: 6200ms) */
  duration?: number;
  /** Callback fired after transition into the application completes */
  onComplete?: () => void;
  /** Force play even if already seen in current session (useful for preview/testing) */
  forcePlay?: boolean;
}

const STORAGE_KEY = "narrai_intro_seen";

/**
 * WeavesilkIntro: Dong Son Bronze Drum & NarrAI Light Reveal
 *
 * Choreography:
 * 1. PHASE 1 — DARK AWAKENING (0.0s - 1.0s):
 *    Deep black viewport. Delicate silver-white Bézier silk filaments emerge from the boundaries, drifting into dark space.
 * 2. PHASE 2 — LIGHT FLOW (1.0s - 2.2s):
 *    Multi-axis symmetrical light filaments curve and flow toward the center, forming the first faint concentric outer rings.
 * 3. PHASE 3 — DRUM FORMATION (2.2s - 4.3s):
 *    Orderly convergence of light tracing out the authentic Dong Son bronze drum:
 *    - Concentric geometric boundary bands (sawtooth, tangent dotted circles).
 *    - 14-Ray central Sun blazing outward from the core.
 *    - 8 Stylized flying Chim Lạc birds etched into soaring counter-clockwise flight.
 *    - Full drum face completes with delicate silver-white luminescence.
 * 4. PHASE 4 — THE LIGHT PULSE (4.3s - 5.1s):
 *    A radiant silver wave ripples from the central sun outward across the concentric rings, softly illuminating each tier.
 * 5. PHASE 5 — NARR AI REVEAL (5.1s - 5.9s):
 *    Official NARR AI logo and typography fade in below the drum with silver sheen flare and pristine branding.
 * 6. PHASE 6 — TRANSITION TO HOMEPAGE (5.9s - 6.6s):
 *    Smooth dissolve into the homepage without reload or blank flash.
 */
export function WeavesilkIntro({
  duration = 6200,
  onComplete,
  forcePlay = false,
}: WeavesilkIntroProps) {
  const [isReadyToPlay, setIsReadyToPlay] = useState<boolean>(true);
  const [isExiting, setIsExiting] = useState<boolean>(false);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);

  // Progressive Stage Progress States
  const [drumProgress, setDrumProgress] = useState<number>(0); // 0 -> 1 (Formation)
  const [pulseProgress, setPulseProgress] = useState<number>(0); // 0 -> 1 (Radial Light Pulse)
  const [logoProgress, setLogoProgress] = useState<number>(0); // 0 -> 1 (Logo Fade In)
  const [isSilverFlashing, setIsSilverFlashing] = useState<boolean>(false);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const isExitingRef = useRef<boolean>(false);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Mouse tracking for gentle atmospheric tilt
  const mouseRef = useRef<{
    currX: number;
    currY: number;
    targetX: number;
    targetY: number;
    hasInteraction: boolean;
  }>({
    currX: 0,
    currY: 0,
    targetX: 0,
    targetY: 0,
    hasInteraction: false,
  });

  // Check session storage & query parameters
  useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      const params = new URLSearchParams(window.location.search);
      const isParamForced = params.has("intro") || params.get("preview_intro") === "1";
      const isLocalhost =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1";

      // Always play intro on load (with instant "Bỏ qua" button available)
      if (params.get("no_intro") === "1") {
        setIsComplete(true);
        onComplete?.();
        return;
      }

      // Check prefers-reduced-motion
      const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      if (motionQuery.matches) {
        setReducedMotion(true);
      }

      setIsReadyToPlay(true);
    } catch {
      setIsReadyToPlay(true);
    }

    // Allow replaying via custom event
    const handleReplayEvent = () => {
      setIsComplete(false);
      setIsExiting(false);
      setDrumProgress(0);
      setPulseProgress(0);
      setLogoProgress(0);
      setIsSilverFlashing(false);
      isExitingRef.current = false;
      setIsReadyToPlay(true);
    };

    window.addEventListener("narrai:replay-intro", handleReplayEvent);
    return () => {
      window.removeEventListener("narrai:replay-intro", handleReplayEvent);
    };
  }, [forcePlay, onComplete]);

  // Finish and dismiss intro
  const finishIntro = useCallback(
    (immediate = false) => {
      if (isExitingRef.current) return;
      isExitingRef.current = true;
      setIsExiting(true);

      try {
        sessionStorage.setItem(STORAGE_KEY, "true");
      } catch {
        // Ignore storage exceptions
      }

      const fadeDuration = immediate ? 350 : 850;
      setTimeout(() => {
        setIsComplete(true);
        if (animFrameIdRef.current) {
          cancelAnimationFrame(animFrameIdRef.current);
          animFrameIdRef.current = null;
        }
        onComplete?.();
      }, fadeDuration);
    },
    [onComplete]
  );

  const handleSkip = useCallback(() => {
    finishIntro(true);
  }, [finishIntro]);

  // Canvas & Procedural Weavesilk Animation Loop
  useEffect(() => {
    if (!isReadyToPlay || isComplete) return;

    // Reduced motion handling
    if (reducedMotion) {
      setDrumProgress(1);
      setLogoProgress(1);
      const exitTimer = setTimeout(() => finishIntro(false), 2400);
      return () => clearTimeout(exitTimer);
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext("2d", { alpha: true });
    } catch {
      finishIntro(true);
      return;
    }

    if (!ctx) {
      finishIntro(true);
      return;
    }

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      if (ctx) {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);
        ctx.fillStyle = "#FAF7F2";
        ctx.fillRect(0, 0, width, height);
      }
    };

    handleResize();

    try {
      resizeObserverRef.current = new ResizeObserver(() => handleResize());
      resizeObserverRef.current.observe(document.body);
    } catch {
      window.addEventListener("resize", handleResize);
    }

    // Pointer move listener
    const onPointerMove = (e: PointerEvent) => {
      const cx = width / 2;
      const cy = height / 2;
      mouseRef.current.targetX = (e.clientX - cx) * 0.15;
      mouseRef.current.targetY = (e.clientY - cy) * 0.15;
      mouseRef.current.hasInteraction = true;
    };
    window.addEventListener("pointermove", onPointerMove, { passive: true });

    // Mathematical parameters for Weavesilk filaments
    const NUM_SYMMETRIES = 6;
    const STRANDS = [-2, -1, 0, 1, 2];
    const NUM_EMITTERS = 2;

    interface EmitterPoint {
      x: number;
      y: number;
    }

    const emitterHistories: Array<Array<{ p0: EmitterPoint; p1: EmitterPoint }>> = [];
    for (let e = 0; e < NUM_EMITTERS; e++) {
      const strandsList: Array<{ p0: EmitterPoint; p1: EmitterPoint }> = [];
      for (let s = 0; s < STRANDS.length; s++) {
        strandsList.push({
          p0: { x: 0, y: 0 },
          p1: { x: 0, y: 0 },
        });
      }
      emitterHistories.push(strandsList);
    }

    // Circular drum tracer orbits
    const drumRimTracer: { angle: number } = { angle: 0 };
    const drumBirdTracer: { angle: number } = { angle: 0 };

    const startTime = performance.now();
    let hasInitializedPoints = false;
    let hasTriggeredFlash = false;

    // Render loop
    const render = (now: number) => {
      if (isExitingRef.current) return;

      const elapsed = (now - startTime) / 1000; // seconds

      // ==============================================================
      // TIMELINE ORCHESTRATION (Phases 1 through 6)
      // ==============================================================

      // Phase 2 -> 3: Drum Formation (1.0s to 4.3s)
      if (elapsed < 1.0) {
        setDrumProgress(0);
      } else if (elapsed >= 1.0 && elapsed < 4.3) {
        const dp = Math.min(1.0, (elapsed - 1.0) / 3.3);
        setDrumProgress(dp);
      } else if (elapsed >= 4.3 && drumProgress < 1) {
        setDrumProgress(1);
      }

      // Phase 4: Light Pulse (4.35s to 5.05s)
      if (elapsed >= 4.35 && elapsed <= 5.05) {
        const pp = (elapsed - 4.35) / 0.7;
        setPulseProgress(pp);
      } else if (elapsed > 5.05 && pulseProgress > 0) {
        setPulseProgress(0);
      }

      // Phase 5: NARR AI Logo Reveal (5.1s to 5.8s)
      if (elapsed >= 5.1 && elapsed <= 5.8) {
        const lp = Math.min(1.0, (elapsed - 5.1) / 0.65);
        setLogoProgress(lp);
      } else if (elapsed > 5.8 && logoProgress < 1) {
        setLogoProgress(1);
      }

      // Silver Sheen Flash (5.35s)
      if (elapsed >= 5.35 && !hasTriggeredFlash) {
        hasTriggeredFlash = true;
        setIsSilverFlashing(true);
        setTimeout(() => setIsSilverFlashing(false), 450);
      }

      // Phase 6: Transition to Homepage (5.95s)
      if (elapsed >= 5.95) {
        finishIntro(false);
        return;
      }

      if (!ctx) return;

      // Mouse smooth interpolation
      const mouse = mouseRef.current;
      mouse.currX += (mouse.targetX - mouse.currX) * 0.04;
      mouse.currY += (mouse.targetY - mouse.currY) * 0.04;

      const cx = width / 2;
      const cy = height / 2 - 35; // Centered around drum face position
      const maxR = Math.min(width, height) * 0.44;

      // Soft persistence decay for milky white gossamer silk background
      ctx.save();
      ctx.globalCompositeOperation = "source-over";
      const decayAlpha = elapsed > 4.6 ? "rgba(250, 247, 242, 0.05)" : "rgba(250, 247, 242, 0.02)";
      ctx.fillStyle = decayAlpha;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      // Source-over layering for imperial gold & cinnabar red silk ribbons
      ctx.save();
      ctx.globalCompositeOperation = "source-over";

      // --- SECTION 1: INGRESS WEAVESILK RIBBONS FROM BOUNDARIES ---
      let radiusProgress = Math.min(1.0, elapsed / 2.4);
      radiusProgress =
        radiusProgress < 0.5
          ? 4 * radiusProgress * radiusProgress * radiusProgress
          : 1 - Math.pow(-2 * radiusProgress + 2, 3) / 2;

      let dispersionRadius = 0;
      let dispersionFade = 1.0;
      if (elapsed > 4.6) {
        const dispT = (elapsed - 4.6) / 0.9;
        dispersionRadius = dispT * 60;
        dispersionFade = Math.max(0, 1.0 - dispT * 1.2);
      }

      const ingressBaseR = maxR * (0.95 - 0.75 * radiusProgress) + dispersionRadius;

      for (let e = 0; e < NUM_EMITTERS; e++) {
        const sign = e === 0 ? 1 : -1;
        const phaseShift = e * (Math.PI / 2.1);

        const rOsc =
          ingressBaseR *
          (0.85 + 0.25 * Math.sin(elapsed * 1.2 * sign + phaseShift));

        const theta =
          elapsed * 0.65 * sign +
          0.3 * Math.sin(elapsed * 1.5 + phaseShift);

        const mouseFactor = (rOsc / maxR) * (mouse.hasInteraction ? 1.0 : 0.0);
        const px = rOsc * Math.cos(theta) + mouse.currX * mouseFactor;
        const py = rOsc * Math.sin(theta) + mouse.currY * mouseFactor;

        const dt = 0.018;
        const rPrev =
          (maxR * (0.95 - 0.75 * Math.max(0, radiusProgress - 0.01)) + dispersionRadius) *
          (0.85 + 0.25 * Math.sin((elapsed - dt) * 1.2 * sign + phaseShift));
        const thetaPrev =
          (elapsed - dt) * 0.65 * sign +
          0.3 * Math.sin((elapsed - dt) * 1.5 + phaseShift);

        const pxPrev = rPrev * Math.cos(thetaPrev) + mouse.currX * mouseFactor;
        const pyPrev = rPrev * Math.sin(thetaPrev) + mouse.currY * mouseFactor;

        const vx = px - pxPrev;
        const vy = py - pyPrev;
        const vLen = Math.hypot(vx, vy) || 1;
        const nx = -vy / vLen;
        const ny = vx / vLen;

        for (let sIdx = 0; sIdx < STRANDS.length; sIdx++) {
          const s = STRANDS[sIdx];
          const strandOffset =
            s * 4.5 * (0.85 + 0.35 * Math.sin(elapsed * 4.0 + s * 0.7));

          const curStrandX = px + nx * strandOffset;
          const curStrandY = py + ny * strandOffset;

          const history = emitterHistories[e][sIdx];

          if (!hasInitializedPoints) {
            history.p0 = { x: curStrandX, y: curStrandY };
            history.p1 = { x: curStrandX, y: curStrandY };
            continue;
          }

          const p0 = history.p0;
          const p1 = history.p1;
          const p2 = { x: curStrandX, y: curStrandY };

          const mid0X = (p0.x + p1.x) * 0.5;
          const mid0Y = (p0.y + p1.y) * 0.5;
          const mid1X = (p1.x + p2.x) * 0.5;
          const mid1Y = (p1.y + p2.y) * 0.5;

          const isCenterStrand = s === 0;
          const isMidStrand = Math.abs(s) === 1;

          const isGold = e === 0;
          const baseAlpha = isCenterStrand ? 0.38 : isMidStrand ? 0.22 : 0.12;
          const fadeMult = Math.min(1.0, elapsed / 0.5) * dispersionFade;
          const finalAlpha = (baseAlpha * fadeMult).toFixed(4);

          if (isGold) {
            // Golden Yellow silk ribbon stream
            ctx.strokeStyle = isCenterStrand
              ? `rgba(217, 119, 6, ${finalAlpha})`
              : isMidStrand
              ? `rgba(245, 158, 11, ${finalAlpha})`
              : `rgba(251, 191, 36, ${finalAlpha})`;
            ctx.shadowColor = `rgba(245, 158, 11, ${Number(finalAlpha) * 0.7})`;
          } else {
            // Crimson Red silk ribbon stream
            ctx.strokeStyle = isCenterStrand
              ? `rgba(220, 38, 38, ${finalAlpha})`
              : isMidStrand
              ? `rgba(185, 28, 28, ${finalAlpha})`
              : `rgba(225, 29, 72, ${finalAlpha})`;
            ctx.shadowColor = `rgba(220, 38, 38, ${Number(finalAlpha) * 0.7})`;
          }

          ctx.lineWidth = isCenterStrand ? 1.6 : isMidStrand ? 1.1 : 0.7;
          ctx.shadowBlur = isCenterStrand ? 6 : 3;

          for (let k = 0; k < NUM_SYMMETRIES; k++) {
            const rot = (k * 2 * Math.PI) / NUM_SYMMETRIES;
            const cos = Math.cos(rot);
            const sin = Math.sin(rot);

            ctx.beginPath();
            ctx.moveTo(cx + mid0X * cos - mid0Y * sin, cy + mid0X * sin + mid0Y * cos);
            ctx.quadraticCurveTo(
              cx + p1.x * cos - p1.y * sin,
              cy + p1.x * sin + p1.y * cos,
              cx + mid1X * cos - mid1Y * sin,
              cy + mid1X * sin + mid1Y * cos
            );
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(cx + -mid0X * cos - mid0Y * sin, cy + -mid0X * sin + mid0Y * cos);
            ctx.quadraticCurveTo(
              cx + -p1.x * cos - p1.y * sin,
              cy + -p1.x * sin + p1.y * cos,
              cx + -mid1X * cos - mid1Y * sin,
              cy + -mid1X * sin + mid1Y * cos
            );
            ctx.stroke();
          }

          history.p0 = p1;
          history.p1 = p2;
        }
      }

      // --- SECTION 2: SYNTHESIS TRACERS DRAWING DONG SON DRUM ---
      // During 2.2s - 4.4s: Light tracers circle around the drum's rim and Chim Lạc track
      if (elapsed >= 2.0 && elapsed <= 4.5) {
        drumRimTracer.angle += 0.08;
        drumBirdTracer.angle -= 0.06; // Counter-clockwise for Chim Lac

        const drumRadius = Math.min(width, height) * 0.26;
        const tracerR1 = drumRadius * 0.95;
        const tracerR2 = drumRadius * 0.62;

        const tx1 = cx + tracerR1 * Math.cos(drumRimTracer.angle);
        const ty1 = cy + tracerR1 * Math.sin(drumRimTracer.angle);

        const tx2 = cx + tracerR2 * Math.cos(drumBirdTracer.angle);
        const ty2 = cy + tracerR2 * Math.sin(drumBirdTracer.angle);

        ctx.save();
        // Golden tracer on outer rim
        ctx.fillStyle = "rgba(217, 119, 6, 0.95)";
        ctx.shadowColor = "rgba(245, 158, 11, 0.9)";
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(tx1, ty1, 2.8, 0, Math.PI * 2);
        ctx.fill();

        // Crimson tracer on Chim Lac track
        ctx.fillStyle = "rgba(220, 38, 38, 0.95)";
        ctx.shadowColor = "rgba(239, 68, 68, 0.9)";
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(tx2, ty2, 2.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      hasInitializedPoints = true;
      ctx.restore();

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    animFrameIdRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("pointermove", onPointerMove);
    };
  }, [isReadyToPlay, isComplete, reducedMotion, duration, finishIntro]);

  if (!isReadyToPlay || isComplete) {
    return null;
  }

  return (
    <div
      role="region"
      aria-label="NarrAI Dong Son Bronze Drum Intro"
      className={`fixed inset-0 z-[99999] overflow-hidden bg-[#FAF7F2] select-none transition-opacity duration-900 ease-out font-sans ${
        isExiting ? "opacity-0 pointer-events-none" : "opacity-100 pointer-events-auto"
      }`}
    >
      {/* 1. Procedural Weavesilk Canvas Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 block w-full h-full cursor-default"
        aria-hidden="true"
      />

      {/* 2. Accessible Skip Button ("Bỏ qua") */}
      <div className="absolute top-5 right-5 sm:top-7 sm:right-7 z-30">
        <button
          type="button"
          onClick={handleSkip}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleSkip();
            }
          }}
          className="px-4 py-1.5 rounded-full font-mono text-[11px] sm:text-xs tracking-[0.22em] uppercase text-neutral-700 hover:text-black bg-white/85 hover:bg-white border border-neutral-300 hover:border-neutral-400 backdrop-blur-md transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500/50 select-none shadow-sm"
          aria-label="Bỏ qua phần giới thiệu (Skip intro)"
        >
          Bỏ qua
        </button>
      </div>

      {/* 3. Centerpiece: Dong Son Bronze Drum & NARR AI Official Logo */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10 px-4">
        {/* Atmospheric ambient soft glow behind Drum (Amber Gold & Cinnabar Red) */}
        <div
          className={`absolute w-80 h-80 sm:w-[480px] sm:h-[480px] rounded-full bg-gradient-to-tr from-amber-400/25 via-red-400/20 to-amber-300/25 blur-3xl pointer-events-none transition-opacity duration-1000 ${
            drumProgress > 0.25 ? "opacity-100" : "opacity-0"
          }`}
          aria-hidden="true"
        />

        {/* Central Dong Son Bronze Drum (Light-forged vector patterns in Gold & Red) */}
        <div
          className={`relative transition-all duration-700 ${
            pulseProgress > 0
              ? "scale-[1.025] filter brightness-[1.12]"
              : drumProgress >= 0.95
              ? "scale-100 filter brightness-100"
              : "scale-100 filter brightness-[0.98]"
          }`}
        >
          <DongSonDrum
            size={typeof window !== "undefined" && window.innerWidth < 640 ? 290 : 360}
            progress={drumProgress}
            pulseProgress={pulseProgress}
            glowIntensity={pulseProgress > 0 ? 1.6 : 1.0}
          />
        </div>

        {/* Official NARR AI Logo & Tagline (Phase 5 Reveal below the Drum) */}
        <div
          className={`mt-4 sm:mt-5 flex flex-col items-center gap-2 transition-all duration-700 ${
            logoProgress > 0 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"
          } ${
            isSilverFlashing
              ? "filter brightness-[1.05] drop-shadow-[0_4px_22px_rgba(220,38,38,0.35)]"
              : "drop-shadow-[0_2px_12px_rgba(217,119,6,0.22)]"
          }`}
        >
          {/* Logo container with Official Emblem & Typography */}
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8 sm:w-9 sm:h-9">
              <Image
                src="/assets/narrai_emblem.png"
                alt="NARR AI Official Emblem"
                fill
                className="object-contain filter brightness-[0.18] contrast-[1.4]"
                priority
              />
            </div>
            <div className="relative w-[130px] h-[26px] sm:w-[150px] sm:h-[30px]">
              <Image
                src="/assets/narrai_text.png"
                alt="NARR AI Typography"
                fill
                className="object-contain filter brightness-[0.18] contrast-[1.4]"
                priority
              />
            </div>
          </div>

          {/* Subtitle / Tagline */}
          <div className="flex items-center gap-2 font-mono text-[9px] sm:text-[10px] tracking-[0.26em] uppercase text-neutral-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />
            <span>AI Novel & Manga Studio</span>
          </div>

          {/* Golden-Crimson Sheen Flare Overlay */}
          {isSilverFlashing && (
            <div
              className="absolute inset-0 overflow-hidden pointer-events-none"
              aria-hidden="true"
            >
              <div
                className="w-full h-full animate-sheen-sweep"
                style={{
                  background:
                    "linear-gradient(115deg, transparent 20%, rgba(245,158,11,0.28) 48%, rgba(220,38,38,0.32) 52%, transparent 75%)",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default WeavesilkIntro;
