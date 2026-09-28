'use client';

import React, { useRef, useEffect, useState } from 'react';
import { DampedHarmonicOscillator } from './springPhysics';

/**
 * ModelSelectorMorphicon (Layer 2 SVG Micro-Interaction)
 *
 * Architecture:
 * - Morphing between 3 AI Creation Tiers:
 *     * Flash ⚡: Speedy drafting & nimble brainstorming (Emerald / Cyan)
 *     * Versatile 🌟: Multi-perspective & nuanced narrative depth (Purple / Indigo)
 *     * Master 👑: Monumental prose & canonical worldbuilding (Royal Gold / Amber)
 * - Spring-driven sliding background capsule using Euler damped oscillator
 * - Tactile vector scaling and glow interpolation
 * - SSR safe and keyboard accessible
 */

export type ModelTier = 'flash' | 'versatile' | 'master';

export interface ModelSelectorMorphiconProps {
  selectedTier?: ModelTier;
  onSelectTier?: (tier: ModelTier) => void;
  className?: string;
  lang?: 'vi' | 'en';
}

interface TierMeta {
  id: ModelTier;
  icon: string;
  nameVi: string;
  nameEn: string;
  descVi: string;
  descEn: string;
  activeColor: string;
  badgeBg: string;
}

const TIERS: TierMeta[] = [
  {
    id: 'flash',
    icon: 'lightning',
    nameVi: 'Flash',
    nameEn: 'Flash',
    descVi: 'Tốc độ cao & Phản hồi nhanh',
    descEn: 'High-speed drafting',
    activeColor: 'text-emerald-600 dark:text-emerald-400',
    badgeBg: 'bg-emerald-500/15 border-emerald-400/50 dark:border-emerald-500/40',
  },
  {
    id: 'versatile',
    icon: 'star',
    nameVi: 'Versatile',
    nameEn: 'Versatile',
    descVi: 'Toàn năng & Chiều sâu tâm lý',
    descEn: 'Nuanced & deep narrative',
    activeColor: 'text-indigo-600 dark:text-indigo-400',
    badgeBg: 'bg-indigo-500/15 border-indigo-400/50 dark:border-indigo-500/40',
  },
  {
    id: 'master',
    icon: 'crown',
    nameVi: 'Master',
    nameEn: 'Master',
    descVi: 'Bậc thầy & Văn phong kinh điển',
    descEn: 'Masterpiece literature',
    activeColor: 'text-amber-600 dark:text-amber-400',
    badgeBg: 'bg-amber-500/15 border-amber-400/50 dark:border-amber-500/40',
  },
];

export function ModelSelectorMorphicon({
  selectedTier = 'versatile',
  onSelectTier,
  className = '',
  lang = 'vi',
}: ModelSelectorMorphiconProps) {
  const [currentTier, setCurrentTier] = useState<ModelTier>(selectedTier);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const buttonsRef = useRef<(HTMLButtonElement | null)[]>([]);

  // Sliding indicator physical state
  const [pillLeft, setPillLeft] = useState<number>(0);
  const [pillWidth, setPillWidth] = useState<number>(0);

  const springLeftRef = useRef<DampedHarmonicOscillator | null>(null);
  const springWidthRef = useRef<DampedHarmonicOscillator | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);

  // Initialize spring oscillators (stiffness 240, damping 18)
  if (!springLeftRef.current) {
    springLeftRef.current = new DampedHarmonicOscillator(0, {
      stiffness: 240,
      damping: 18,
      mass: 1.0,
      precision: 0.1,
    });
  }
  if (!springWidthRef.current) {
    springWidthRef.current = new DampedHarmonicOscillator(0, {
      stiffness: 240,
      damping: 18,
      mass: 1.0,
      precision: 0.1,
    });
  }

  // Sync internal tier when prop changes
  useEffect(() => {
    setCurrentTier(selectedTier);
  }, [selectedTier]);

  // Measure & update target indicator position
  useEffect(() => {
    const activeIndex = TIERS.findIndex((t) => t.id === currentTier);
    const targetBtn = buttonsRef.current[activeIndex];
    const container = containerRef.current;

    if (targetBtn && container) {
      const containerRect = container.getBoundingClientRect();
      const btnRect = targetBtn.getBoundingClientRect();
      const targetLeft = btnRect.left - containerRect.left;
      const targetW = btnRect.width;

      const sLeft = springLeftRef.current;
      const sWidth = springWidthRef.current;
      if (sLeft && sWidth) {
        sLeft.setTarget(targetLeft);
        sWidth.setTarget(targetW);

        // Cancel previous loop
        if (rafRef.current !== null) {
          cancelAnimationFrame(rafRef.current);
        }
        lastTimeRef.current = performance.now();

        const stepSpring = (now: number) => {
          const dt = Math.min((now - lastTimeRef.current) / 1000, 0.05);
          lastTimeRef.current = now;

          const resL = sLeft!.step(dt);
          const resW = sWidth!.step(dt);

          setPillLeft(resL.value);
          setPillWidth(resW.value);

          if (!resL.isSettled || !resW.isSettled) {
            rafRef.current = requestAnimationFrame(stepSpring);
          } else {
            rafRef.current = null;
          }
        };

        rafRef.current = requestAnimationFrame(stepSpring);
      }
    }
  }, [currentTier]);

  const handleSelect = (tier: ModelTier) => {
    setCurrentTier(tier);
    onSelectTier?.(tier);
  };

  useEffect(() => {
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      role="radiogroup"
      aria-label={lang === 'vi' ? 'Chọn cấp độ mô hình AI' : 'Select AI model tier'}
      className={`relative inline-flex items-center p-1 rounded-xl bg-slate-100/90 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 shadow-inner select-none ${className}`}
    >
      {/* Spring Animated Active Indicator Pill */}
      {pillWidth > 0 && (
        <div
          aria-hidden="true"
          className="absolute top-1 bottom-1 rounded-lg bg-white dark:bg-slate-900 shadow-sm border border-slate-200/80 dark:border-slate-700 transition-colors pointer-events-none"
          style={{
            transform: `translateX(${pillLeft.toFixed(1)}px)`,
            width: `${pillWidth.toFixed(1)}px`,
          }}
        />
      )}

      {/* Tier Radio Buttons */}
      {TIERS.map((tier, idx) => {
        const isSelected = tier.id === currentTier;
        return (
          <button
            key={tier.id}
            ref={(el) => {
              buttonsRef.current[idx] = el;
            }}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => handleSelect(tier.id)}
            title={lang === 'vi' ? tier.descVi : tier.descEn}
            className={`relative z-10 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${
              isSelected
                ? `${tier.activeColor} font-bold`
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {/* Morphing Vector Icon */}
            <TierIcon type={tier.icon} isSelected={isSelected} />

            <span>{lang === 'vi' ? tier.nameVi : tier.nameEn}</span>
          </button>
        );
      })}
    </div>
  );
}

function TierIcon({ type, isSelected }: { type: string; isSelected: boolean }) {
  const scale = isSelected ? 'scale-110' : 'scale-95 opacity-70';

  if (type === 'lightning') {
    // Flash ⚡
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill={isSelected ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`transition-all duration-200 ${scale}`}
      >
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    );
  }

  if (type === 'star') {
    // Versatile 🌟 (8-point radiant star)
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill={isSelected ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`transition-all duration-200 ${scale}`}
      >
        <path d="M12 2l2.4 6.6L21 11l-5.4 4.4L17 22l-5-3.6L7 22l1.4-6.6L3 11l6.6-2.4z" />
      </svg>
    );
  }

  // Master 👑 (Imperial 5-peak crown)
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill={isSelected ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`transition-all duration-200 ${scale}`}
    >
      <path d="M2 4l3 12h14l3-12-5 6-5-8-5 8z" />
      <path d="M5 20h14" />
    </svg>
  );
}

export default ModelSelectorMorphicon;
