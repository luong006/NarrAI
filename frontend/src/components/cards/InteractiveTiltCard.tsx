'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';

/**
 * InteractiveTiltCard (Layer 1 Core Semantic DOM 3D Compositor)
 *
 * Architecture:
 * - CSS 3D Transforms (perspective: 1000px, transform-style: preserve-3d)
 * - Parallax tilt tracking cursor offset (rotateX, rotateY, scale3d)
 * - Multi-plane z-elevation support (translateZ(28px), translateZ(48px))
 * - Dynamic specular glare overlay tracking cursor angle
 * - 60 FPS Compositor execution isolated from WebGL canvas
 * - Graceful degradation for prefers-reduced-motion and low-end hardware
 */

export interface InteractiveTiltCardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  maxTilt?: number; // Maximum tilt angle in degrees (default: 10)
  perspective?: number; // Perspective distance in px (default: 1000)
  scale?: number; // Scale on hover (default: 1.02)
  glare?: boolean; // Enable specular glare reflection (default: true)
  glareMaxOpacity?: number; // Max glare opacity (default: 0.22)
  disabled?: boolean;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
}

export function InteractiveTiltCard({
  children,
  className = '',
  style,
  maxTilt = 10,
  perspective = 1000,
  scale = 1.02,
  glare = true,
  glareMaxOpacity = 0.22,
  disabled = false,
  onClick,
}: InteractiveTiltCardProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [transformStyle, setTransformStyle] = useState<string>('');
  const [glareStyle, setGlareStyle] = useState<React.CSSProperties>({ opacity: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const [isDegraded, setIsDegraded] = useState(false);

  // Check hardware capabilities & user motion preference
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
    const isLowConcurrency = typeof navigator !== 'undefined' && navigator.hardwareConcurrency !== undefined && navigator.hardwareConcurrency <= 2;
    if (reducedMotion || isLowConcurrency) {
      setIsDegraded(true);
    }
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (disabled || isDegraded) return;
      const card = cardRef.current;
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      // Cursor coordinates relative to card center, normalized to [-1, 1]
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const normX = (mouseX - width / 2) / (width / 2);
      const normY = (mouseY - height / 2) / (height / 2);

      // Inverted Y for intuitive physical tilt
      const rotX = (-normY * maxTilt).toFixed(2);
      const rotY = (normX * maxTilt).toFixed(2);

      setTransformStyle(
        `perspective(${perspective}px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(${scale}, ${scale}, ${scale})`
      );

      if (glare) {
        const glareX = ((normX * 0.5 + 0.5) * 100).toFixed(1);
        const glareY = ((normY * 0.5 + 0.5) * 100).toFixed(1);
        setGlareStyle({
          opacity: glareMaxOpacity,
          background: `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0.08) 35%, transparent 70%)`,
        });
      }
    },
    [disabled, isDegraded, maxTilt, perspective, scale, glare, glareMaxOpacity]
  );

  const handleMouseEnter = useCallback(() => {
    if (disabled || isDegraded) return;
    setIsHovered(true);
  }, [disabled, isDegraded]);

  const handleMouseLeave = useCallback(() => {
    if (disabled || isDegraded) return;
    setIsHovered(false);
    // Smooth spring-like return to resting plane
    setTransformStyle(`perspective(${perspective}px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`);
    if (glare) {
      setGlareStyle({ opacity: 0 });
    }
  }, [disabled, isDegraded, perspective, glare]);

  // Graceful degradation mode: standard flat elevation without 3D perspective
  if (disabled || isDegraded) {
    return (
      <div
        ref={cardRef}
        className={`transition-transform duration-200 hover:-translate-y-1 ${className}`}
        style={style}
        onClick={onClick}
      >
        {children}
      </div>
    );
  }

  return (
    <div
      ref={cardRef}
      className={`relative select-none ${className}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{
        transform: transformStyle || `perspective(${perspective}px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`,
        transformStyle: 'preserve-3d',
        transition: isHovered
          ? 'transform 0.08s ease-out'
          : 'transform 0.45s cubic-bezier(0.23, 1, 0.32, 1)',
        willChange: 'transform',
        ...style,
      }}
    >
      {/* Elevated Child Plane */}
      <div className="w-full h-full" style={{ transformStyle: 'preserve-3d' }}>
        {children}
      </div>

      {/* Specular Glare Reflection Overlay */}
      {glare && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 rounded-[inherit] overflow-hidden transition-opacity duration-300"
          style={{
            ...glareStyle,
            mixBlendMode: 'overlay',
            zIndex: 35,
          }}
        />
      )}
    </div>
  );
}

export default InteractiveTiltCard;
