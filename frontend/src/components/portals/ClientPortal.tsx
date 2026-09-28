'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * ClientPortal (Layer 3 Glassmorphism Overlay & Portals)
 *
 * Architecture:
 * - Teleports modals directly into document.body via ReactDOM.createPortal
 * - Enforces `isolation: isolate` to guarantee a clean root Stacking Context
 * - Enforces z-index 50+ to eliminate z-fighting with CSS 3D cards and WebGL canvas
 * - Shields backdrop-filter: blur() from Chromium 3D clipping bugs
 * - 100% SSR-safe: returns null during server pre-rendering
 */

export interface ClientPortalProps {
  children: React.ReactNode;
  zIndex?: number;
  className?: string;
}

export function ClientPortal({
  children,
  zIndex = 50,
  className = '',
}: ClientPortalProps) {
  const [mounted, setMounted] = useState<boolean>(false);
  const portalRootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMounted(true);
    // Create dedicated wrapper div for this portal instance
    const div = document.createElement('div');
    div.className = `narrai-portal-root ${className}`.trim();
    div.style.isolation = 'isolate';
    div.style.position = 'relative';
    div.style.zIndex = String(zIndex);
    document.body.appendChild(div);
    portalRootRef.current = div;

    return () => {
      if (div.parentNode) {
        div.parentNode.removeChild(div);
      }
      portalRootRef.current = null;
    };
  }, [zIndex, className]);

  if (!mounted || !portalRootRef.current) {
    return null;
  }

  return createPortal(children, portalRootRef.current);
}

export default ClientPortal;
