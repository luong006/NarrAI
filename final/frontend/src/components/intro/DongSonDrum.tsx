"use client";

import React, { useMemo } from "react";

interface DongSonDrumProps {
  /** Size in pixels (viewBox is 600x600) */
  size?: number;
  /**
   * Formation progress: 0 to 1
   * 0.0 -> 0.2: Outer boundary rings
   * 0.2 -> 0.4: Concentric geometric bands (sawtooth, dots)
   * 0.4 -> 0.6: 14-Ray central Sun ignites
   * 0.6 -> 0.85: 8 Chim Lạc birds traced by light
   * 0.85 -> 1.0: Full drum face luminous lock
   */
  progress: number;
  /**
   * Pulse wave progress: 0 to 1 (when progress >= 0.85)
   * Radiates outward from the sun across the rings
   */
  pulseProgress?: number;
  /** Active highlight glow intensity */
  glowIntensity?: number;
}

/**
 * Procedural SVG Dong Son Bronze Drum Face (Mặt Trống Đồng Đông Sơn)
 *
 * Meticulously modeled after the canonical Ngọc Lũ & Đông Sơn bronze drum iconography:
 * 1. 14-ray central Sun with inter-ray feather chevrons.
 * 2. Concentric geometric bands: radial ticks, sawtooth (răng cưa), tangent dotted circles.
 * 3. 8 stylized Flying Chim Lạc birds (Chim Lạc bay ngược chiều kim đồng hồ).
 * 4. Concentric boundary rings and outer rim.
 *
 * Animated with stroke-dashoffset & opacity driven by progress.
 */
export function DongSonDrum({
  size = 460,
  progress = 1,
  pulseProgress = 0,
  glowIntensity = 1,
}: DongSonDrumProps) {
  const cx = 300;
  const cy = 300;

  // Sub-stage progresses
  // 1. Outer rim & boundary
  const pRim = Math.min(1, Math.max(0, progress / 0.3));
  // 2. Concentric geometric bands
  const pBands = Math.min(1, Math.max(0, (progress - 0.2) / 0.25));
  // 3. Central 14-ray sun
  const pSun = Math.min(1, Math.max(0, (progress - 0.38) / 0.25));
  // 4. Chim Lac birds
  const pBirds = Math.min(1, Math.max(0, (progress - 0.58) / 0.27));
  // 5. Drum completion & sheen
  const pFull = Math.min(1, Math.max(0, (progress - 0.82) / 0.18));

  // 1. Generate 14-Ray Sun + Inter-ray feathers
  const { sunRaysPath, interRayPaths } = useMemo(() => {
    const rayCount = 14;
    const rBase = 18;
    const rTip = 68;
    const dAngle = (Math.PI * 2) / rayCount;

    let raysD = "";
    const feathers: string[] = [];

    for (let i = 0; i < rayCount; i++) {
      const angle = i * dAngle - Math.PI / 2;
      const angleL = angle - dAngle * 0.32;
      const angleR = angle + dAngle * 0.32;

      const tipX = cx + rTip * Math.cos(angle);
      const tipY = cy + rTip * Math.sin(angle);
      const lx = cx + rBase * Math.cos(angleL);
      const ly = cy + rBase * Math.sin(angleL);
      const rx = cx + rBase * Math.cos(angleR);
      const ry = cy + rBase * Math.sin(angleR);

      raysD += `M ${lx.toFixed(2)} ${ly.toFixed(2)} L ${tipX.toFixed(2)} ${tipY.toFixed(2)} L ${rx.toFixed(2)} ${ry.toFixed(2)} Z `;

      // Inter-ray chevron feather
      const midAngle = angle + dAngle * 0.5;
      const fBaseX = cx + 28 * Math.cos(midAngle);
      const fBaseY = cy + 28 * Math.sin(midAngle);
      const fTipX = cx + 58 * Math.cos(midAngle);
      const fTipY = cy + 58 * Math.sin(midAngle);
      const fL = cx + 46 * Math.cos(midAngle - 0.08);
      const fLy = cy + 46 * Math.sin(midAngle - 0.08);
      const fR = cx + 46 * Math.cos(midAngle + 0.08);
      const fRy = cy + 46 * Math.sin(midAngle + 0.08);

      feathers.push(
        `M ${fBaseX.toFixed(2)} ${fBaseY.toFixed(2)} L ${fTipX.toFixed(2)} ${fTipY.toFixed(2)} M ${fL.toFixed(2)} ${fLy.toFixed(2)} L ${fTipX.toFixed(2)} ${fTipY.toFixed(2)} L ${fR.toFixed(2)} ${fRy.toFixed(2)}`
      );
    }

    return { sunRaysPath: raysD, interRayPaths: feathers };
  }, [cx, cy]);

  // 2. Generate Sawtooth (Răng cưa) zigzag bands
  const innerSawtooth = useMemo(() => {
    const teeth = 36;
    const rIn = 95;
    const rOut = 108;
    const dTheta = (Math.PI * 2) / teeth;
    let d = "";
    for (let i = 0; i < teeth; i++) {
      const th1 = i * dTheta;
      const thMid = th1 + dTheta * 0.5;
      const th2 = th1 + dTheta;

      const p1x = cx + rIn * Math.cos(th1);
      const p1y = cy + rIn * Math.sin(th1);
      const pMidX = cx + rOut * Math.cos(thMid);
      const pMidY = cy + rOut * Math.sin(thMid);
      const p2x = cx + rIn * Math.cos(th2);
      const p2y = cy + rIn * Math.sin(th2);

      d += `${i === 0 ? "M" : "L"} ${p1x.toFixed(2)} ${p1y.toFixed(2)} L ${pMidX.toFixed(2)} ${pMidY.toFixed(2)} L ${p2x.toFixed(2)} ${p2y.toFixed(2)} `;
    }
    return d + "Z";
  }, [cx, cy]);

  const outerSawtooth = useMemo(() => {
    const teeth = 54;
    const rIn = 224;
    const rOut = 238;
    const dTheta = (Math.PI * 2) / teeth;
    let d = "";
    for (let i = 0; i < teeth; i++) {
      const th1 = i * dTheta;
      const thMid = th1 + dTheta * 0.5;
      const th2 = th1 + dTheta;

      const p1x = cx + rIn * Math.cos(th1);
      const p1y = cy + rIn * Math.sin(th1);
      const pMidX = cx + rOut * Math.cos(thMid);
      const pMidY = cy + rOut * Math.sin(thMid);
      const p2x = cx + rIn * Math.cos(th2);
      const p2y = cy + rIn * Math.sin(th2);

      d += `${i === 0 ? "M" : "L"} ${p1x.toFixed(2)} ${p1y.toFixed(2)} L ${pMidX.toFixed(2)} ${pMidY.toFixed(2)} L ${p2x.toFixed(2)} ${p2y.toFixed(2)} `;
    }
    return d + "Z";
  }, [cx, cy]);

  // 3. Tangent Dotted Circles Band (Vòng tròn đồng tâm tiếp tuyến)
  const tangentCircles = useMemo(() => {
    const count = 20;
    const rTrack = 128;
    const rCirc = 5.5;
    const dTheta = (Math.PI * 2) / count;
    const list: { x: number; y: number; lineToX: number; lineToY: number }[] = [];

    for (let i = 0; i < count; i++) {
      const th = i * dTheta;
      const thNext = (i + 1) * dTheta;
      const x = cx + rTrack * Math.cos(th);
      const y = cy + rTrack * Math.sin(th);
      const nextX = cx + rTrack * Math.cos(thNext);
      const nextY = cy + rTrack * Math.sin(thNext);

      // Tangent connecting line
      const tX1 = x + rCirc * Math.cos(th + Math.PI / 2);
      const tY1 = y + rCirc * Math.sin(th + Math.PI / 2);
      const tX2 = nextX + rCirc * Math.cos(thNext - Math.PI / 2);
      const tY2 = nextY + rCirc * Math.sin(thNext - Math.PI / 2);

      list.push({ x, y, lineToX: tX2, lineToY: tY2 });
    }
    return { count, rCirc, list };
  }, [cx, cy]);

  // 4. Radial Tick Marks Bands (Vạch ngắn hướng tâm)
  const innerTicks = useMemo(() => {
    const count = 72;
    const r1 = 76;
    const r2 = 86;
    const dTheta = (Math.PI * 2) / count;
    let d = "";
    for (let i = 0; i < count; i++) {
      const th = i * dTheta;
      const x1 = cx + r1 * Math.cos(th);
      const y1 = cy + r1 * Math.sin(th);
      const x2 = cx + r2 * Math.cos(th);
      const y2 = cy + r2 * Math.sin(th);
      d += `M ${x1.toFixed(2)} ${y1.toFixed(2)} L ${x2.toFixed(2)} ${y2.toFixed(2)} `;
    }
    return d;
  }, [cx, cy]);

  const outerTicks = useMemo(() => {
    const count = 108;
    const r1 = 246;
    const r2 = 258;
    const dTheta = (Math.PI * 2) / count;
    let d = "";
    for (let i = 0; i < count; i++) {
      const th = i * dTheta;
      const x1 = cx + r1 * Math.cos(th);
      const y1 = cy + r1 * Math.sin(th);
      const x2 = cx + r2 * Math.cos(th);
      const y2 = cy + r2 * Math.sin(th);
      d += `M ${x1.toFixed(2)} ${y1.toFixed(2)} L ${x2.toFixed(2)} ${y2.toFixed(2)} `;
    }
    return d;
  }, [cx, cy]);

  // 5. Stylized Dong Son Chim Lạc Vector Path (Standard template oriented horizontally)
  // Normalized in a 100x60 local box with beak at right, long tail at left, swept wings upward
  const chimLacPath = useMemo(() => {
    return (
      "M 45 0 " + // Beak tip
      "C 36 -2, 28 -5, 20 -7 " + // Upper beak to head
      "C 15 -14, 8 -18, -2 -20 " + // Crest swept back
      "C -8 -22, -18 -24, -28 -24 " + // Crest tip
      "C -22 -19, -15 -15, -8 -13 " + // Crest underside
      "C -2 -11, 6 -8, 12 -6 " + // Back of head
      "C 8 -3, 2 2, -6 7 " + // Neck to upper wing joint
      "C -18 3, -32 -2, -48 -8 " + // Upper sweeping wing feathers
      "C -42 -2, -32 6, -22 12 " + // Wing mid-feather tier
      "C -36 12, -48 10, -60 6 " + // Extended wing tip
      "C -50 14, -38 18, -24 20 " + // Lower wing border to body
      "C -35 24, -50 26, -65 24 " + // Tail plume 1
      "C -55 28, -42 30, -28 29 " + // Tail plume 2
      "C -18 28, -8 24, 0 18 " + // Underbelly
      "C 8 14, 18 8, 28 3 " + // Lower neck to throat
      "C 34 2, 40 1, 45 0 Z" // Back to beak tip
    );
  }, []);

  // Compute 8 Flying Chim Lạc Placements
  const chimLacBirds = useMemo(() => {
    const count = 8;
    const rTrack = 182;
    const dTheta = (Math.PI * 2) / count;
    const birds: { index: number; transform: string }[] = [];

    for (let i = 0; i < count; i++) {
      // Counter-clockwise procession matching canonical Dong Son bronze drums
      const theta = -i * dTheta;
      const bx = cx + rTrack * Math.cos(theta);
      const by = cy + rTrack * Math.sin(theta);
      // Tangent angle so bird flies forward along circle
      const rot = (theta * 180) / Math.PI + 90;

      birds.push({
        index: i,
        transform: `translate(${bx.toFixed(2)}, ${by.toFixed(2)}) rotate(${rot.toFixed(2)}) scale(0.68)`,
      });
    }

    return birds;
  }, [cx, cy]);

  // Pulse wave styling calculation
  const pulseRadius = pulseProgress > 0 ? 30 + pulseProgress * 260 : 0;
  const pulseOpacity = pulseProgress > 0 ? (1 - pulseProgress) * 0.75 : 0;

  return (
    <div
      className="relative flex items-center justify-center select-none pointer-events-none"
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 600 600"
        className="w-full h-full overflow-visible"
        style={{
          filter: `drop-shadow(0 4px 18px rgba(220, 38, 38, ${0.22 * glowIntensity})) drop-shadow(0 2px 10px rgba(217, 119, 6, ${0.32 * glowIntensity}))`,
        }}
      >
        <defs>
          {/* Imperial Gold Gradient */}
          <linearGradient id="dongsonGold" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#D97706" stopOpacity="0.95" />
            <stop offset="50%" stopColor="#F59E0B" stopOpacity="1" />
            <stop offset="100%" stopColor="#B45309" stopOpacity="0.95" />
          </linearGradient>

          {/* Cinnabar Crimson Lacquer Gradient */}
          <linearGradient id="dongsonCrimson" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#DC2626" stopOpacity="0.95" />
            <stop offset="50%" stopColor="#B91C1C" stopOpacity="1" />
            <stop offset="100%" stopColor="#991B1B" stopOpacity="0.95" />
          </linearGradient>

          {/* Harmonious Gold to Crimson Blend */}
          <linearGradient id="goldRedBlend" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#EA580C" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#DC2626" stopOpacity="0.95" />
          </linearGradient>

          {/* Central Solar Aura (Gold & Crimson) */}
          <radialGradient id="sunAuraGold" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.55" />
            <stop offset="38%" stopColor="#DC2626" stopOpacity="0.25" />
            <stop offset="72%" stopColor="#F59E0B" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#FAF7F2" stopOpacity="0" />
          </radialGradient>

          {/* Soft Sheen Filter */}
          <filter id="lacquerSheen" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="1.2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* ============================================================== */}
        {/* TIER 1: OUTER BOUNDARY & RIM CIRCLES (Phase 3.1) */}
        {/* ============================================================== */}
        <g
          fill="none"
          strokeLinecap="round"
          style={{
            opacity: pRim,
            transition: "opacity 0.3s ease",
          }}
        >
          {/* Outermost Rim Circle - Imperial Gold */}
          <circle
            cx={cx}
            cy={cy}
            r="282"
            stroke="url(#dongsonGold)"
            strokeWidth="3.0"
            strokeDasharray="1772"
            strokeDashoffset={1772 * (1 - pRim)}
          />
          {/* Inner Double Rim - Lacquer Red & Gold */}
          <circle
            cx={cx}
            cy={cy}
            r="272"
            stroke="url(#dongsonCrimson)"
            strokeWidth="1.4"
            strokeDasharray="1709"
            strokeDashoffset={1709 * (1 - pRim)}
          />
          <circle
            cx={cx}
            cy={cy}
            r="266"
            stroke="url(#dongsonGold)"
            strokeWidth="0.9"
            strokeDasharray="1671"
            strokeDashoffset={1671 * (1 - pRim)}
          />

          {/* Outer Boundary Track (Enclosing outer ticks) */}
          <circle
            cx={cx}
            cy={cy}
            r="245"
            stroke="url(#dongsonCrimson)"
            strokeWidth="1.1"
            strokeDasharray="1539"
            strokeDashoffset={1539 * (1 - pRim)}
          />
        </g>

        {/* Outer Radial Ticks - Golden Ticks */}
        <path
          d={outerTicks}
          stroke="url(#dongsonGold)"
          strokeWidth="0.95"
          strokeLinecap="round"
          fill="none"
          style={{
            opacity: Math.max(0, pRim * 1.2 - 0.2),
            transition: "opacity 0.4s ease",
          }}
        />

        {/* ============================================================== */}
        {/* TIER 2: OUTER SAWTOOTH BAND (Phase 3.2) */}
        {/* ============================================================== */}
        <g
          style={{
            opacity: pBands,
            transition: "opacity 0.4s ease",
          }}
        >
          {/* Outer Sawtooth Circle Borders */}
          <circle cx={cx} cy={cy} r="238" stroke="url(#dongsonGold)" strokeWidth="1.0" fill="none" />
          <circle cx={cx} cy={cy} r="224" stroke="url(#dongsonGold)" strokeWidth="1.0" fill="none" />

          {/* Outer Sawtooth Zigzag */}
          <path
            d={outerSawtooth}
            stroke="url(#dongsonCrimson)"
            strokeWidth="1.2"
            fill="rgba(220, 38, 38, 0.08)"
            strokeLinejoin="round"
          />
        </g>

        {/* ============================================================== */}
        {/* TIER 3: CHIM LẠC BAND (Phase 3.4 - Sải cánh Lạc Việt) */}
        {/* ============================================================== */}
        <g
          style={{
            opacity: pBirds,
            transition: "opacity 0.5s ease",
          }}
        >
          {/* Boundary circles enclosing Chim Lac band */}
          <circle
            cx={cx}
            cy={cy}
            r="215"
            stroke="url(#dongsonGold)"
            strokeWidth="1.4"
            fill="none"
            strokeDasharray="4 3"
          />
          <circle
            cx={cx}
            cy={cy}
            r="150"
            stroke="url(#dongsonCrimson)"
            strokeWidth="1.4"
            fill="none"
            strokeDasharray="4 3"
          />

          {/* 8 Flying Chim Lac Birds - Crimson Silhouette with Gold Tint */}
          {chimLacBirds.map((bird) => (
            <g key={bird.index} transform={bird.transform}>
              {/* Chim Lac Vector Wing & Plume */}
              <path
                d={chimLacPath}
                stroke="url(#dongsonCrimson)"
                strokeWidth="1.8"
                fill="rgba(245, 158, 11, 0.24)"
                strokeLinejoin="round"
                filter="url(#lacquerSheen)"
              />
              {/* Eye of Chim Lac - Golden Sun Dot */}
              <circle cx="16" cy="-1" r="1.5" fill="#D97706" />
            </g>
          ))}
        </g>

        {/* ============================================================== */}
        {/* TIER 4: INNER GEOMETRIC BANDS (Tangents, Sawtooth, Ticks) */}
        {/* ============================================================== */}
        <g
          style={{
            opacity: pBands,
            transition: "opacity 0.4s ease",
          }}
        >
          {/* Tangent Dotted Circles Boundary */}
          <circle cx={cx} cy={cy} r="142" stroke="url(#dongsonGold)" strokeWidth="0.9" fill="none" />
          <circle cx={cx} cy={cy} r="118" stroke="url(#dongsonGold)" strokeWidth="0.9" fill="none" />

          {tangentCircles.list.map((tc, idx) => (
            <g key={idx}>
              <circle
                cx={tc.x}
                cy={tc.y}
                r={tangentCircles.rCirc}
                stroke="url(#dongsonCrimson)"
                strokeWidth="1.1"
                fill="rgba(245, 158, 11, 0.15)"
              />
              <circle cx={tc.x} cy={tc.y} r="1.6" fill="#DC2626" />
              {/* Tangent link */}
              <line
                x1={tc.x}
                y1={tc.y}
                x2={tc.lineToX}
                y2={tc.lineToY}
                stroke="rgba(217, 119, 6, 0.65)"
                strokeWidth="0.8"
              />
            </g>
          ))}

          {/* Inner Sawtooth Band */}
          <path
            d={innerSawtooth}
            stroke="url(#dongsonGold)"
            strokeWidth="1.1"
            fill="rgba(245, 158, 11, 0.12)"
            strokeLinejoin="round"
          />

          {/* Inner Ticks Band */}
          <circle cx={cx} cy={cy} r="86" stroke="url(#dongsonCrimson)" strokeWidth="0.9" fill="none" />
          <circle cx={cx} cy={cy} r="76" stroke="url(#dongsonCrimson)" strokeWidth="0.9" fill="none" />
          <path d={innerTicks} stroke="url(#dongsonCrimson)" strokeWidth="0.85" fill="none" />
        </g>

        {/* ============================================================== */}
        {/* TIER 5: CENTRAL 14-RAY SUN & PEACOCK FEATHERS (Phase 3.3) */}
        {/* ============================================================== */}
        <g
          style={{
            opacity: pSun,
            transition: "opacity 0.4s ease",
          }}
        >
          {/* Radiant Solar Aura */}
          <circle cx={cx} cy={cy} r="72" fill="url(#sunAuraGold)" pointerEvents="none" />

          {/* Inter-ray feather lines - Lacquer Red */}
          {interRayPaths.map((fPath, idx) => (
            <path
              key={idx}
              d={fPath}
              stroke="#DC2626"
              strokeWidth="1.0"
              fill="none"
              strokeLinecap="round"
            />
          ))}

          {/* 14 Sun Rays - Imperial Gold Rays */}
          <path
            d={sunRaysPath}
            stroke="url(#dongsonGold)"
            strokeWidth="1.7"
            fill="rgba(245, 158, 11, 0.38)"
            strokeLinejoin="round"
            filter="url(#lacquerSheen)"
          />

          {/* Sun Hub Concentric Center */}
          <circle cx={cx} cy={cy} r="18" stroke="url(#dongsonGold)" strokeWidth="1.6" fill="rgba(220, 38, 38, 0.12)" />
          <circle cx={cx} cy={cy} r="9" stroke="#DC2626" strokeWidth="1.3" fill="none" />
          <circle cx={cx} cy={cy} r="4" fill="#D97706" />
        </g>

        {/* ============================================================== */}
        {/* TIER 6: THE LIGHT PULSE WAVE (Phase 4) */}
        {/* ============================================================== */}
        {pulseProgress > 0 && (
          <circle
            cx={cx}
            cy={cy}
            r={pulseRadius}
            stroke="url(#goldRedBlend)"
            strokeWidth={3.5 * (1 - pulseProgress)}
            fill="none"
            style={{
              opacity: pulseOpacity,
              filter: "blur(2px)",
            }}
          />
        )}

        {/* Completed Drum Surface Ambient Shimmer */}
        {pFull > 0 && (
          <circle
            cx={cx}
            cy={cy}
            r="282"
            fill="none"
            stroke="rgba(245, 158, 11, 0.4)"
            strokeWidth="2.5"
            style={{
              opacity: pFull * 0.75,
              filter: "blur(3px)",
            }}
          />
        )}
      </svg>
    </div>
  );
}
