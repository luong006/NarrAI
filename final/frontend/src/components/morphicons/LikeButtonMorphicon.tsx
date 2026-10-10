'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DampedHarmonicOscillator } from './springPhysics';

/**
 * LikeButtonMorphicon (Layer 2 SVG Micro-Interaction)
 *
 * Architecture:
 * - Subtle outline heart stroke morphs into radiant filled heart (#f43f5e)
 * - Spring physics bounce using Euler damped harmonic oscillator
 * - 8-ray micro-burst radial particle animation expanding to 22px
 * - Pure DOM Vector pipeline, zero WebGL/framer-motion dependencies
 */

export interface LikeButtonMorphiconProps {
  liked?: boolean;
  defaultLiked?: boolean;
  count?: number;
  onToggle?: (liked: boolean) => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  showCount?: boolean;
}

interface BurstParticle {
  angle: number; // in radians
  distance: number;
  scale: number;
  opacity: number;
}

export function LikeButtonMorphicon({
  liked: controlledLiked,
  defaultLiked = false,
  count,
  onToggle,
  size = 'md',
  className = '',
  showCount = true,
}: LikeButtonMorphiconProps) {
  const isControlled = controlledLiked !== undefined;
  const [internalLiked, setInternalLiked] = useState<boolean>(defaultLiked);
  const isLiked = isControlled ? controlledLiked : internalLiked;

  const [likeCount, setLikeCount] = useState<number | undefined>(count);
  const [scale, setScale] = useState<number>(1.0);
  const [burstParticles, setBurstParticles] = useState<BurstParticle[]>([]);
  const [isBursting, setIsBursting] = useState<boolean>(false);

  const springRef = useRef<DampedHarmonicOscillator | null>(null);
  const rafRef = useRef<number | null>(null);
  const burstRafRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);

  // Initialize spring with stiffness 280, damping 14
  if (!springRef.current) {
    springRef.current = new DampedHarmonicOscillator(1.0, {
      stiffness: 280,
      damping: 14,
      mass: 1.0,
      precision: 0.001,
    });
  }

  // Update count when prop changes
  useEffect(() => {
    if (count !== undefined) {
      setLikeCount(count);
    }
  }, [count]);

  const triggerSpringAnimation = useCallback(() => {
    const spring = springRef.current;
    if (!spring) return;

    // Apply instantaneous velocity impulse to initiate tactile pop
    spring.applyImpulse(2.4);
    spring.setTarget(1.0);

    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
    }
    lastTimeRef.current = performance.now();

    const step = (now: number) => {
      const dt = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;

      const { value, isSettled } = spring!.step(dt);
      setScale(value);

      if (!isSettled) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        rafRef.current = null;
        setScale(1.0);
      }
    };

    rafRef.current = requestAnimationFrame(step);
  }, []);

  const triggerBurst = useCallback(() => {
    // Cancel any existing burst animation frame before starting a new burst
    if (burstRafRef.current !== null) {
      cancelAnimationFrame(burstRafRef.current);
      burstRafRef.current = null;
    }

    // Generate 8 rays around 360 degrees
    const numRays = 8;
    const initialParticles: BurstParticle[] = [];
    for (let i = 0; i < numRays; i++) {
      initialParticles.push({
        angle: (i * 2 * Math.PI) / numRays,
        distance: 6,
        scale: 1.0,
        opacity: 1.0,
      });
    }
    setBurstParticles(initialParticles);
    setIsBursting(true);

    const startTime = performance.now();
    const duration = 400; // ms

    const animateBurst = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1.0);

      // Ease-out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      const updated = initialParticles.map((p) => ({
        ...p,
        distance: 6 + ease * 18, // expand to 24px
        scale: Math.max(0, 1.0 - progress * 1.2),
        opacity: Math.max(0, 1.0 - progress * 1.3),
      }));

      setBurstParticles(updated);

      if (progress < 1.0) {
        burstRafRef.current = requestAnimationFrame(animateBurst);
      } else {
        burstRafRef.current = null;
        setIsBursting(false);
        setBurstParticles([]);
      }
    };

    burstRafRef.current = requestAnimationFrame(animateBurst);
  }, []);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    const nextState = !isLiked;
    if (!isControlled) {
      setInternalLiked(nextState);
    }
    if (likeCount !== undefined) {
      setLikeCount((prev) => (prev !== undefined ? (nextState ? prev + 1 : Math.max(0, prev - 1)) : undefined));
    }

    triggerSpringAnimation();

    if (nextState) {
      triggerBurst();
    }

    onToggle?.(nextState);
  };

  useEffect(() => {
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
      if (burstRafRef.current !== null) {
        cancelAnimationFrame(burstRafRef.current);
      }
    };
  }, []);

  // Sizing definitions
  const dimensions = {
    sm: { icon: 16, box: 'h-7 px-2 text-xs', burstCenter: 8 },
    md: { icon: 20, box: 'h-8 px-2.5 text-sm', burstCenter: 10 },
    lg: { icon: 24, box: 'h-10 px-3 text-base', burstCenter: 12 },
  }[size];

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-pressed={isLiked}
      aria-label={isLiked ? 'Unlike' : 'Like'}
      className={`group relative inline-flex items-center gap-1.5 rounded-full font-medium transition-colors select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500/50 ${
        isLiked
          ? 'bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400'
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
      } ${dimensions.box} ${className}`}
    >
      {/* 8-Ray Micro-Burst Particle Canvas */}
      {isBursting && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute"
          style={{
            top: '50%',
            left: size === 'sm' ? '12px' : size === 'lg' ? '18px' : '15px',
            transform: 'translate(-50%, -50%)',
            width: 0,
            height: 0,
          }}
        >
          {burstParticles.map((particle, i) => {
            const x = Math.cos(particle.angle) * particle.distance;
            const y = Math.sin(particle.angle) * particle.distance;
            return (
              <span
                key={i}
                className="absolute rounded-full"
                style={{
                  width: '3.5px',
                  height: '3.5px',
                  backgroundColor: i % 2 === 0 ? '#f43f5e' : '#fbbf24',
                  transform: `translate(${x}px, ${y}px) scale(${particle.scale})`,
                  opacity: particle.opacity,
                  boxShadow: '0 0 4px rgba(244, 63, 94, 0.6)',
                }}
              />
            );
          })}
        </div>
      )}

      {/* Morphing Heart SVG */}
      <span
        className="inline-block transition-transform duration-75"
        style={{
          transform: `scale(${scale.toFixed(3)})`,
        }}
      >
        <svg
          width={dimensions.icon}
          height={dimensions.icon}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-colors duration-200"
        >
          <path
            d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
            fill={isLiked ? '#f43f5e' : 'none'}
            stroke={isLiked ? '#f43f5e' : 'currentColor'}
            className="transition-all duration-200"
            style={{
              filter: isLiked ? 'drop-shadow(0 2px 6px rgba(244, 63, 94, 0.45))' : 'none',
            }}
          />
        </svg>
      </span>

      {/* Counter */}
      {showCount && likeCount !== undefined && (
        <span
          className={`font-semibold tabular-nums text-xs sm:text-sm transition-transform duration-150 ${
            isLiked ? 'font-bold' : ''
          }`}
        >
          {likeCount}
        </span>
      )}
    </button>
  );
}

export default LikeButtonMorphicon;
