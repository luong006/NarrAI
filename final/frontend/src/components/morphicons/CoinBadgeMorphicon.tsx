'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DampedHarmonicOscillator } from './springPhysics';

/**
 * CoinBadgeMorphicon (Layer 2 SVG Micro-Interaction)
 *
 * Architecture:
 * - 3D Spinning Golden Coin rotating on Y-axis
 * - Morphing expand/collapse into pill capsule balance badge
 * - Damped harmonic oscillator driving continuous velocity & bounce
 * - Smooth rolling counter when balance changes
 * - Fully accessible button element with keyboard triggers
 */

export interface CoinBadgeMorphiconProps {
  balance?: number;
  onClick?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  isInteractive?: boolean;
  lang?: 'vi' | 'en';
}

export function CoinBadgeMorphicon({
  balance = 100,
  onClick,
  className = '',
  size = 'md',
  isInteractive = true,
  lang = 'vi',
}: CoinBadgeMorphiconProps) {
  const [displayBalance, setDisplayBalance] = useState<number>(balance);
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const [isFlashing, setIsFlashing] = useState<boolean>(false);
  const [coinAngle, setCoinAngle] = useState<number>(0);
  const [capsuleScale, setCapsuleScale] = useState<number>(1.0);

  const prevBalanceRef = useRef<number>(balance);
  const springScaleRef = useRef<DampedHarmonicOscillator | null>(null);
  const rafRef = useRef<number | null>(null);
  const spinSpeedRef = useRef<number>(0.02);
  const targetSpinSpeedRef = useRef<number>(0.02);
  const lastTimeRef = useRef<number>(0);

  // Initialize spring oscillator for capsule bounce
  if (!springScaleRef.current) {
    springScaleRef.current = new DampedHarmonicOscillator(1.0, {
      stiffness: 260,
      damping: 15,
      mass: 1.0,
      precision: 0.001,
    });
  }

  // Handle balance change with rolling counter & spring pulse
  useEffect(() => {
    if (balance !== prevBalanceRef.current) {
      const isDeduction = balance < prevBalanceRef.current;
      prevBalanceRef.current = balance;
      setIsFlashing(true);

      // Accelerate spin on transaction
      spinSpeedRef.current = isDeduction ? 0.25 : 0.35;
      springScaleRef.current?.applyImpulse(0.2);

      const start = displayBalance;
      const end = balance;
      const duration = 600; // ms
      const startTime = performance.now();

      const rollCounter = (now: number) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1.0);
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (end - start) * ease);
        setDisplayBalance(current);

        if (progress < 1.0) {
          requestAnimationFrame(rollCounter);
        } else {
          setDisplayBalance(end);
          setIsFlashing(false);
        }
      };
      requestAnimationFrame(rollCounter);
    }
  }, [balance, displayBalance]);

  // Spin animation loop
  useEffect(() => {
    lastTimeRef.current = performance.now();

    const spinLoop = (now: number) => {
      const dt = Math.min((now - lastTimeRef.current) / 1000, 0.05);
      lastTimeRef.current = now;

      // Smoothly relax spin speed back to target
      spinSpeedRef.current += (targetSpinSpeedRef.current - spinSpeedRef.current) * 0.05;
      setCoinAngle((prev) => (prev + spinSpeedRef.current * (dt * 60)) % (Math.PI * 2));

      // Step capsule spring
      if (springScaleRef.current) {
        const { value } = springScaleRef.current.step(dt);
        setCapsuleScale(value);
      }

      rafRef.current = requestAnimationFrame(spinLoop);
    };

    rafRef.current = requestAnimationFrame(spinLoop);

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, []);

  const handleMouseEnter = () => {
    setIsHovered(true);
    targetSpinSpeedRef.current = 0.12;
    springScaleRef.current?.setTarget(1.04);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    targetSpinSpeedRef.current = 0.02;
    springScaleRef.current?.setTarget(1.0);
  };

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    // High-speed tactile burst on click
    spinSpeedRef.current = 0.45;
    springScaleRef.current?.applyImpulse(0.25);
    onClick?.();
  };

  const dimensions = {
    sm: { height: 'h-7', px: 'px-2.5', iconSize: 18, text: 'text-xs', gap: 'gap-1.5' },
    md: { height: 'h-8 sm:h-9', px: 'px-3 sm:px-3.5', iconSize: 22, text: 'text-xs sm:text-sm', gap: 'gap-2' },
    lg: { height: 'h-10 sm:h-11', px: 'px-4', iconSize: 26, text: 'text-sm sm:text-base', gap: 'gap-2.5' },
  }[size];

  // 3D Coin X-scale for simulated Y-axis rotation
  const cosAngle = Math.cos(coinAngle);
  const absCos = Math.abs(cosAngle);
  const isFront = cosAngle >= 0;

  return (
    <button
      type="button"
      onClick={isInteractive ? handleClick : undefined}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      disabled={!isInteractive}
      aria-label={`${lang === 'vi' ? 'Số dư:' : 'Balance:'} ${displayBalance} ${lang === 'vi' ? 'Xu' : 'Coins'}`}
      className={`relative inline-flex items-center ${dimensions.height} ${dimensions.px} ${dimensions.gap} rounded-full border shadow-sm select-none font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/60 ${
        isFlashing
          ? 'bg-amber-100 border-amber-400 text-amber-900 dark:bg-amber-950/80 dark:border-amber-500 dark:text-amber-200'
          : 'bg-gradient-to-r from-amber-500/10 via-amber-400/10 to-amber-500/15 hover:from-amber-500/20 hover:to-amber-500/25 border-amber-300/80 dark:border-amber-500/40 text-amber-900 dark:text-amber-200 shadow-amber-500/5'
      } ${isInteractive ? 'cursor-pointer' : 'cursor-default'} ${className}`}
      style={{
        transform: `scale(${capsuleScale.toFixed(3)})`,
      }}
    >
      {/* 3D Spinning Golden Coin */}
      <div
        className="relative shrink-0 flex items-center justify-center"
        style={{
          width: dimensions.iconSize,
          height: dimensions.iconSize,
          perspective: '400px',
        }}
      >
        <svg
          width={dimensions.iconSize}
          height={dimensions.iconSize}
          viewBox="0 0 32 32"
          fill="none"
          className="transition-transform duration-75"
          style={{
            transform: `scaleX(${cosAngle.toFixed(3)})`,
            filter: 'drop-shadow(0 1px 3px rgba(217, 119, 6, 0.4))',
          }}
        >
          <defs>
            <linearGradient id="coinGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fef3c7" />
              <stop offset="35%" stopColor="#f59e0b" />
              <stop offset="70%" stopColor="#d97706" />
              <stop offset="100%" stopColor="#b45309" />
            </linearGradient>
            <linearGradient id="coinRimGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#fbbf24" />
              <stop offset="100%" stopColor="#78350f" />
            </linearGradient>
          </defs>

          {/* Outer Coin Disk */}
          <circle cx="16" cy="16" r="14.5" fill="url(#coinGrad)" stroke="url(#coinRimGrad)" strokeWidth="1.5" />

          {/* Inner Beaded Rim */}
          <circle cx="16" cy="16" r="11" fill="none" stroke="#fef3c7" strokeWidth="0.8" strokeDasharray="1.5 1.5" />

          {/* Center Monogram: Star / Xu glyph */}
          {isFront ? (
            <path
              d="M16 8.5L18.2 13L23.2 13.7L19.6 17.2L20.5 22.2L16 19.8L11.5 22.2L12.4 17.2L8.8 13.7L13.8 13L16 8.5Z"
              fill="#fef3c7"
              stroke="#78350f"
              strokeWidth="0.6"
            />
          ) : (
            <text
              x="16"
              y="20"
              textAnchor="middle"
              fill="#fef3c7"
              fontSize="11"
              fontWeight="900"
              fontFamily="sans-serif"
            >
              N
            </text>
          )}
        </svg>
      </div>

      {/* Animated Balance Pill Counter */}
      <span className={`tabular-nums ${dimensions.text} font-bold tracking-tight flex items-center gap-1`}>
        <span className={isFlashing ? 'scale-110 text-amber-600 dark:text-amber-300 transition-transform' : ''}>
          {displayBalance.toLocaleString()}
        </span>
        <span className="text-[11px] sm:text-xs font-semibold opacity-80 uppercase">
          {lang === 'vi' ? 'Xu' : 'Coins'}
        </span>
      </span>

      {/* Micro Plus Accent when interactive */}
      {isInteractive && (
        <span
          className="text-amber-600 dark:text-amber-400 opacity-60 group-hover:opacity-100 transition-opacity text-xs font-bold -ml-0.5"
          title={lang === 'vi' ? 'Nạp thêm xu' : 'Top up coins'}
        >
          +
        </span>
      )}
    </button>
  );
}

export default CoinBadgeMorphicon;
