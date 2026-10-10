'use client';

import React, { useEffect, useRef, useState } from 'react';

/**
 * ThreeAmbientCanvas (Layer 0 Ambient WebGL Engine)
 *
 * Architecture:
 * - Single Shared WebGL Context (fixed, inset: 0, z-index: 0, pointer-events: none)
 * - Zero external dependencies (~12KB native WebGL GLSL shader pipeline)
 * - Procedural Dong Son Drum motif:
 *     * 14-ray sacred solar star core
 *     * Concentric geometric bands (bead rings, triangular sawteeth, water wave spirals)
 *     * Chim Lac (sacred bird) counter-clockwise flight path
 *     * Oblique 3D pitch perspective
 * - 3D Interactive Floating Particle Field:
 *     * 350 particles in normalized 3D volume
 *     * Cursor repulsion vector field + organic Brownian drift
 * - Resource Optimization (Strict 0.0% CPU/GPU when idle/hidden):
 *     * document.visibilitychange listener halts render loop when tab is hidden
 *     * IntersectionObserver pauses render loop when canvas is off-screen
 *     * 8-second idle watchdog puts render loop to sleep until user movement
 *     * webglcontextlost & webglcontextrestored resilience
 * - Graceful Degradation:
 *     * Detects prefers-reduced-motion or navigator.hardwareConcurrency <= 2
 *     * Falls back cleanly to pure CSS ambient gradient
 * - SSR Safe with hydration guards
 */

// Shaders for procedural Dong Son drum background quad
const DRUM_VS = `
attribute vec2 a_position;
varying vec2 v_uv;
void main() {
  v_uv = (a_position + 1.0) * 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const DRUM_FS = `
precision mediump float;
varying vec2 v_uv;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;
uniform float u_is_dark;

#define PI 3.14159265359

void main() {
  vec2 st = gl_FragCoord.xy / u_resolution.xy;
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);

  // 3D Perspective tilt (oblique angle view)
  vec2 p = uv;
  p.y = p.y * 1.32 + 0.18;
  p.x += (u_mouse.x - 0.5) * 0.08;
  p.y += (u_mouse.y - 0.5) * 0.05;

  float r = length(p);
  float theta = atan(p.y, p.x) + u_time * 0.015;

  // 1. Center Sun (14 rays)
  float sunDisc = smoothstep(0.085, 0.080, r);
  float raysRaw = cos(14.0 * theta);
  float sunRays = smoothstep(0.075, 0.165, r) * smoothstep(0.22, 0.165, r) * pow(max(0.0, raysRaw), 3.2);

  // 2. Concentric Bead / Dot Rings
  float ring1 = smoothstep(0.0035, 0.0, abs(r - 0.23));
  float dots1 = smoothstep(0.0035, 0.0, abs(r - 0.26)) * step(0.25, sin(56.0 * theta));

  // 3. Sawtooth / Triangle Geometric Band
  float sawTrack = smoothstep(0.014, 0.0, abs(r - 0.31));
  float sawAngle = mod(theta * 42.0, 2.0 * PI);
  float saw = sawTrack * smoothstep(0.0, 0.8, sin(sawAngle + sin(r * 110.0)));

  // 4. Sacred Flying Lac Birds (Chim Lạc - counter-clockwise flight)
  float birdTrack = smoothstep(0.045, 0.0, abs(r - 0.40));
  float birdAngle = mod(theta * 6.0, 2.0 * PI);
  float birdBody = smoothstep(0.9, 0.2, abs(birdAngle - 1.4));
  float birdWing = smoothstep(0.4, 0.0, abs(birdAngle - 1.8)) * step(0.40, r);
  float birdShape = birdTrack * max(birdBody, birdWing * 0.8);

  // 5. Water Wave Spirals / Outer Decorative Borders
  float ringOuter1 = smoothstep(0.0035, 0.0, abs(r - 0.48));
  float spirals = smoothstep(0.004, 0.0, abs(r - 0.53)) * step(0.3, sin(72.0 * theta + r * 60.0));
  float ringOuter2 = smoothstep(0.0035, 0.0, abs(r - 0.58));
  float ringOuter3 = smoothstep(0.0045, 0.0, abs(r - 0.63));

  // Aggregate Dong Son Drum Pattern
  float motif = sunDisc * 0.85 
              + sunRays * 0.95 
              + ring1 * 0.65 
              + dots1 * 0.75 
              + saw * 0.55 
              + birdShape * 0.85 
              + ringOuter1 * 0.6 
              + spirals * 0.7 
              + ringOuter2 * 0.6 
              + ringOuter3 * 0.75;

  // Atmospheric radial falloff towards screen boundary
  float vignette = smoothstep(0.72, 0.28, r);
  motif *= vignette;

  // Dynamic Theme Palette:
  // Dark Mode: Ancient Dong Son bronze gold with subtle jade undertones
  // Light Mode: Majestic indigo-slate platinum
  vec3 bronzeGold = vec3(0.90, 0.64, 0.22);
  vec3 bronzeAmbient = vec3(0.04, 0.12, 0.16);
  vec3 indigoSlate = vec3(0.38, 0.46, 0.76);
  vec3 slateAmbient = vec3(0.94, 0.96, 0.98);

  vec3 baseColor = mix(slateAmbient, bronzeAmbient, u_is_dark);
  vec3 motifColor = mix(indigoSlate, bronzeGold, u_is_dark);

  float motifAlpha = mix(0.045, 0.085, u_is_dark);
  vec3 finalColor = mix(baseColor, motifColor, motif * motifAlpha);

  gl_FragColor = vec4(finalColor, motif * motifAlpha);
}
`;

// Shaders for 3D Interactive Floating Particles
const PARTICLE_VS = `
attribute vec3 a_position;
attribute float a_alpha;
uniform vec2 u_resolution;
uniform float u_dpr;
varying float v_alpha;

void main() {
  v_alpha = a_alpha;
  // Size attenuates with simulated depth z [-1, 1]
  float depthScale = 1.0 - a_position.z * 0.45;
  gl_PointSize = max(2.0, depthScale * 3.8 * u_dpr);
  gl_Position = vec4(a_position.xy, a_position.z * 0.3, 1.0);
}
`;

const PARTICLE_FS = `
precision mediump float;
varying float v_alpha;
uniform float u_is_dark;

void main() {
  vec2 coord = gl_PointCoord - vec2(0.5);
  float dist = length(coord);
  if (dist > 0.5) {
    discard;
  }
  // Soft radial glow
  float glow = pow(1.0 - dist * 2.0, 1.7);

  vec3 goldLight = vec3(1.0, 0.82, 0.45);
  vec3 indigoLight = vec3(0.38, 0.52, 0.95);
  vec3 particleColor = mix(indigoLight, goldLight, u_is_dark);

  float alpha = glow * v_alpha * mix(0.40, 0.65, u_is_dark);
  gl_FragColor = vec4(particleColor, alpha);
}
`;

interface Particle {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  baseAlpha: number;
  alpha: number;
  seed: number;
}

export function ThreeAmbientCanvas() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [mounted, setMounted] = useState(false);
  const [isDegraded, setIsDegraded] = useState(false);

  useEffect(() => {
    setMounted(true);

    // 1. Hardware & Motion Degradation Check
    if (typeof window !== 'undefined') {
      const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
      const isLowCore = typeof navigator !== 'undefined' && navigator.hardwareConcurrency !== undefined && navigator.hardwareConcurrency <= 2;
      if (prefersReducedMotion || isLowCore) {
        setIsDegraded(true);
        return;
      }
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    // 2. Initialize WebGL Context
    let gl: WebGLRenderingContext | null = null;
    try {
      gl = canvas.getContext('webgl', {
        alpha: true,
        antialias: false,
        powerPreference: 'low-power',
        preserveDrawingBuffer: false,
      }) || (canvas.getContext('experimental-webgl') as WebGLRenderingContext | null);
    } catch {
      gl = null;
    }

    if (!gl) {
      setIsDegraded(true);
      return;
    }

    // Helper: Compile shader
    const compileShader = (glContext: WebGLRenderingContext, type: number, src: string): WebGLShader | null => {
      const s = glContext.createShader(type);
      if (!s) return null;
      glContext.shaderSource(s, src);
      glContext.compileShader(s);
      if (!glContext.getShaderParameter(s, glContext.COMPILE_STATUS)) {
        console.warn('GLSL Compile error:', glContext.getShaderInfoLog(s));
        glContext.deleteShader(s);
        return null;
      }
      return s;
    };

    // Helper: Create program
    const createProgram = (glContext: WebGLRenderingContext, vsSrc: string, fsSrc: string): WebGLProgram | null => {
      const vs = compileShader(glContext, glContext.VERTEX_SHADER, vsSrc);
      const fs = compileShader(glContext, glContext.FRAGMENT_SHADER, fsSrc);
      if (!vs || !fs) return null;
      const p = glContext.createProgram();
      if (!p) return null;
      glContext.attachShader(p, vs);
      glContext.attachShader(p, fs);
      glContext.linkProgram(p);
      if (!glContext.getShaderParameter(p, glContext.LINK_STATUS)) {
        console.warn('Program link error:', glContext.getShaderInfoLog(p));
        glContext.deleteProgram(p);
        return null;
      }
      return p;
    };

    // Build Shader Programs
    let drumProgram = createProgram(gl, DRUM_VS, DRUM_FS);
    let particleProgram = createProgram(gl, PARTICLE_VS, PARTICLE_FS);

    if (!drumProgram || !particleProgram) {
      setIsDegraded(true);
      return;
    }

    // Fullscreen Quad Buffer for Drum Motif
    const quadVertices = new Float32Array([
      -1.0, -1.0,
       1.0, -1.0,
      -1.0,  1.0,
      -1.0,  1.0,
       1.0, -1.0,
       1.0,  1.0,
    ]);
    const quadBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, quadVertices, gl.STATIC_DRAW);

    // Particle Setup (350 floating 3D points)
    const PARTICLE_COUNT = 350;
    const particles: Particle[] = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: (Math.random() * 2 - 1),
        y: (Math.random() * 2 - 1),
        z: (Math.random() * 2 - 1),
        vx: (Math.random() - 0.5) * 0.0006,
        vy: (Math.random() - 0.5) * 0.0006,
        vz: (Math.random() - 0.5) * 0.0004,
        baseAlpha: 0.25 + Math.random() * 0.65,
        alpha: 0.5,
        seed: Math.random() * 100,
      });
    }

    const particlePositions = new Float32Array(PARTICLE_COUNT * 3);
    const particleAlphas = new Float32Array(PARTICLE_COUNT);

    const particlePosBuffer = gl.createBuffer();
    const particleAlphaBuffer = gl.createBuffer();

    // Interaction State
    const mouse = { x: 0.5, y: 0.5, targetX: 0.5, targetY: 0.5 };
    let lastActivityTime = performance.now();
    let isTabVisible = !document.hidden;
    let isInViewport = true;
    let rafId: number | null = null;
    let isDark = document.documentElement.classList.contains('dark') ? 1.0 : 0.0;

    // Theme Observer
    const themeObserver = new MutationObserver(() => {
      isDark = document.documentElement.classList.contains('dark') ? 1.0 : 0.0;
      wakeRenderLoop();
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

    // Render loop function declarations
    let stopRenderLoop: () => void;
    let startRenderLoop: () => void;
    let wakeRenderLoop: () => void;
    let render: (timestamp: number) => void;

    // Resize Handler
    const handleResize = () => {
      if (!canvas || !gl) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const width = window.innerWidth;
      const height = window.innerHeight;
      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        gl.viewport(0, 0, canvas.width, canvas.height);
        wakeRenderLoop();
      }
    };
    window.addEventListener('resize', handleResize, { passive: true });
    handleResize();

    // Mouse & Activity Listeners
    const handlePointerMove = (e: MouseEvent | TouchEvent) => {
      lastActivityTime = performance.now();
      let clientX = 0;
      let clientY = 0;
      if ('touches' in e && e.touches.length > 0) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
      } else if ('clientX' in e) {
        clientX = e.clientX;
        clientY = e.clientY;
      }
      mouse.targetX = clientX / window.innerWidth;
      mouse.targetY = 1.0 - clientY / window.innerHeight;
      wakeRenderLoop();
    };

    const handleActivity = () => {
      lastActivityTime = performance.now();
      wakeRenderLoop();
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    window.addEventListener('touchstart', handlePointerMove, { passive: true });
    window.addEventListener('scroll', handleActivity, { passive: true });
    window.addEventListener('keydown', handleActivity, { passive: true });

    // Render Loop with Auto-Pause to 0.0% CPU/GPU
    stopRenderLoop = () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    };

    startRenderLoop = () => {
      if (rafId === null && isTabVisible && isInViewport) {
        rafId = requestAnimationFrame(render);
      }
    };

    wakeRenderLoop = () => {
      lastActivityTime = performance.now();
      startRenderLoop();
    };

    const IDLE_TIMEOUT_MS = 8000;

    render = (timestamp: number) => {
      if (!gl || !canvas || !drumProgram || !particleProgram) return;

      // Check Idle Sleep
      if (timestamp - lastActivityTime > IDLE_TIMEOUT_MS) {
        stopRenderLoop();
        return;
      }

      // Smooth mouse interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.06;
      mouse.y += (mouse.targetY - mouse.y) * 0.06;

      const timeSec = timestamp * 0.001;
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

      // WebGL State Configuration
      gl.clearColor(0.0, 0.0, 0.0, 0.0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      // --- PASS 1: Draw Procedural Dong Son Drum Quad ---
      gl.useProgram(drumProgram);

      const uRes = gl.getUniformLocation(drumProgram, 'u_resolution');
      const uTime = gl.getUniformLocation(drumProgram, 'u_time');
      const uMouse = gl.getUniformLocation(drumProgram, 'u_mouse');
      const uDark = gl.getUniformLocation(drumProgram, 'u_is_dark');

      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, timeSec);
      gl.uniform2f(uMouse, mouse.x, mouse.y);
      gl.uniform1f(uDark, isDark);

      const aPosDrum = gl.getAttribLocation(drumProgram, 'a_position');
      gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
      gl.enableVertexAttribArray(aPosDrum);
      gl.vertexAttribPointer(aPosDrum, 2, gl.FLOAT, false, 0, 0);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
      gl.disableVertexAttribArray(aPosDrum);

      // --- PASS 2: Simulate & Draw 3D Interactive Floating Particles ---
      const mouseNDC_X = (mouse.x - 0.5) * 2.0;
      const mouseNDC_Y = (mouse.y - 0.5) * 2.0;

      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const p = particles[i];

        // Cursor Repulsion Vector Field
        const dx = p.x - mouseNDC_X;
        const dy = p.y - mouseNDC_Y;
        const distSq = dx * dx + dy * dy;
        const repelRadius = 0.28;

        if (distSq < repelRadius * repelRadius && distSq > 0.0001) {
          const dist = Math.sqrt(distSq);
          const force = (1.0 - dist / repelRadius) * 0.0028;
          p.vx += (dx / dist) * force;
          p.vy += (dy / dist) * force;
        }

        // Brownian Harmonic Oscillation
        p.vx += Math.sin(timeSec + p.seed) * 0.00004;
        p.vy += Math.cos(timeSec * 0.8 + p.seed) * 0.00004;

        // Damping velocity
        p.vx *= 0.985;
        p.vy *= 0.985;
        p.vz *= 0.99;

        p.x += p.vx;
        p.y += p.vy;
        p.z += p.vz;

        // Wrap around boundaries [-1.1, 1.1]
        if (p.x < -1.1) p.x = 1.1;
        if (p.x > 1.1) p.x = -1.1;
        if (p.y < -1.1) p.y = 1.1;
        if (p.y > 1.1) p.y = -1.1;
        if (p.z < -1.0) p.z = 1.0;
        if (p.z > 1.0) p.z = -1.0;

        p.alpha = p.baseAlpha * (0.7 + 0.3 * Math.sin(timeSec * 1.5 + p.seed));

        const idx3 = i * 3;
        particlePositions[idx3] = p.x;
        particlePositions[idx3 + 1] = p.y;
        particlePositions[idx3 + 2] = p.z;
        particleAlphas[i] = p.alpha;
      }

      gl.useProgram(particleProgram);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE); // Additive luminous blending

      const uResPart = gl.getUniformLocation(particleProgram, 'u_resolution');
      const uDprPart = gl.getUniformLocation(particleProgram, 'u_dpr');
      const uDarkPart = gl.getUniformLocation(particleProgram, 'u_is_dark');

      gl.uniform2f(uResPart, canvas.width, canvas.height);
      gl.uniform1f(uDprPart, dpr);
      gl.uniform1f(uDarkPart, isDark);

      // Bind positions
      const aPosPart = gl.getAttribLocation(particleProgram, 'a_position');
      gl.bindBuffer(gl.ARRAY_BUFFER, particlePosBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, particlePositions, gl.DYNAMIC_DRAW);
      gl.enableVertexAttribArray(aPosPart);
      gl.vertexAttribPointer(aPosPart, 3, gl.FLOAT, false, 0, 0);

      // Bind alphas
      const aAlphaPart = gl.getAttribLocation(particleProgram, 'a_alpha');
      gl.bindBuffer(gl.ARRAY_BUFFER, particleAlphaBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, particleAlphas, gl.DYNAMIC_DRAW);
      gl.enableVertexAttribArray(aAlphaPart);
      gl.vertexAttribPointer(aAlphaPart, 1, gl.FLOAT, false, 0, 0);

      gl.drawArrays(gl.POINTS, 0, PARTICLE_COUNT);

      gl.disableVertexAttribArray(aPosPart);
      gl.disableVertexAttribArray(aAlphaPart);

      // Continue render loop
      rafId = requestAnimationFrame(render);
    };

    // 3. Tab Visibility Handler (0.0% CPU when hidden)
    const handleVisibilityChange = () => {
      isTabVisible = !document.hidden;
      if (!isTabVisible) {
        stopRenderLoop();
      } else if (isInViewport) {
        wakeRenderLoop();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 4. Viewport Intersection Observer (0.0% CPU when off-screen)
    const observer = new IntersectionObserver(
      ([entry]) => {
        isInViewport = entry.isIntersecting;
        if (!isInViewport) {
          stopRenderLoop();
        } else if (isTabVisible) {
          wakeRenderLoop();
        }
      },
      { threshold: 0.02 }
    );
    observer.observe(canvas);

    // 5. WebGL Context Recovery Guard
    const handleContextLost = (e: Event) => {
      e.preventDefault();
      stopRenderLoop();
    };

    const handleContextRestored = () => {
      if (!canvas) return;
      gl = canvas.getContext('webgl') || (canvas.getContext('experimental-webgl') as WebGLRenderingContext | null);
      if (gl) {
        drumProgram = createProgram(gl, DRUM_VS, DRUM_FS);
        particleProgram = createProgram(gl, PARTICLE_VS, PARTICLE_FS);
        wakeRenderLoop();
      }
    };

    canvas.addEventListener('webglcontextlost', handleContextLost, false);
    canvas.addEventListener('webglcontextrestored', handleContextRestored, false);

    // Start initial render
    startRenderLoop();

    // Cleanup on unmount
    return () => {
      stopRenderLoop();
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('touchstart', handlePointerMove);
      window.removeEventListener('scroll', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      themeObserver.disconnect();
      observer.disconnect();

      if (canvas) {
        canvas.removeEventListener('webglcontextlost', handleContextLost);
        canvas.removeEventListener('webglcontextrestored', handleContextRestored);
      }
    };
  }, []);

  if (!mounted) {
    return null;
  }

  // Graceful degradation fallback: pure CSS ambient lighting
  if (isDegraded) {
    return (
      <div
        aria-hidden="true"
        className="fixed inset-0 z-0 pointer-events-none overflow-hidden transition-opacity duration-1000 opacity-60"
        style={{
          background: 'radial-gradient(circle at 50% 45%, rgba(217, 119, 6, 0.05) 0%, rgba(99, 102, 241, 0.03) 45%, transparent 70%)',
        }}
      />
    );
  }

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="fixed inset-0 z-0 pointer-events-none overflow-hidden select-none"
      style={{
        width: '100vw',
        height: '100vh',
      }}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
        style={{
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
}

export default ThreeAmbientCanvas;
