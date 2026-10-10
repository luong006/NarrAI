'use client';

import { useState, useEffect, useRef } from 'react';

/**
 * Closed-form Euler Damped Harmonic Oscillator Engine
 *
 * Physics Equation:
 *   F = -k * (x - x_target) - c * v
 *   a = F / m
 *   v_next = v + a * dt
 *   x_next = x + v_next * dt
 *
 * Parameters:
 *   - k: Spring stiffness (default: 240)
 *   - c: Damping coefficient (default: 16)
 *   - m: Mass (default: 1.0)
 */

export interface SpringConfig {
  stiffness?: number; // k
  damping?: number;   // c
  mass?: number;      // m
  precision?: number; // stopping threshold epsilon
}

const DEFAULT_CONFIG: Required<SpringConfig> = {
  stiffness: 240,
  damping: 16,
  mass: 1.0,
  precision: 0.001,
};

export class DampedHarmonicOscillator {
  private x: number;
  private target: number;
  private v: number;
  private k: number;
  private c: number;
  private m: number;
  private precision: number;

  constructor(initialValue: number = 0, config?: SpringConfig) {
    const cfg = { ...DEFAULT_CONFIG, ...config };
    this.x = initialValue;
    this.target = initialValue;
    this.v = 0;
    this.k = cfg.stiffness;
    this.c = cfg.damping;
    this.m = cfg.mass;
    this.precision = cfg.precision;
  }

  public setTarget(newTarget: number): void {
    this.target = newTarget;
  }

  public snapTo(value: number): void {
    this.x = value;
    this.target = value;
    this.v = 0;
  }

  public applyImpulse(velocityImpulse: number): void {
    this.v += velocityImpulse;
  }

  public step(dt: number = 1 / 60): { value: number; isSettled: boolean } {
    // Clamp dt to avoid instability on frame spikes
    const clampedDt = Math.min(dt, 0.033);

    const displacement = this.x - this.target;
    const springForce = -this.k * displacement;
    const dampingForce = -this.c * this.v;
    const totalForce = springForce + dampingForce;

    const acceleration = totalForce / this.m;
    this.v += acceleration * clampedDt;
    this.x += this.v * clampedDt;

    const isSettled =
      Math.abs(this.v) < this.precision &&
      Math.abs(this.x - this.target) < this.precision;

    if (isSettled) {
      this.x = this.target;
      this.v = 0;
    }

    return { value: this.x, isSettled };
  }

  public getValue(): number {
    return this.x;
  }

  public getVelocity(): number {
    return this.v;
  }

  public isAtTarget(): boolean {
    return Math.abs(this.x - this.target) < this.precision && Math.abs(this.v) < this.precision;
  }
}

/**
 * React hook driving a continuous spring animation toward target value
 */
export function useSpring(
  targetValue: number,
  config?: SpringConfig,
  initialValue?: number
): number {
  const [currentValue, setCurrentValue] = useState<number>(
    initialValue !== undefined ? initialValue : targetValue
  );

  const oscillatorRef = useRef<DampedHarmonicOscillator | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);

  if (!oscillatorRef.current) {
    oscillatorRef.current = new DampedHarmonicOscillator(
      initialValue !== undefined ? initialValue : targetValue,
      config
    );
  }

  useEffect(() => {
    const osc = oscillatorRef.current;
    if (!osc) return;

    osc.setTarget(targetValue);

    // Cancel existing animation frame
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }

    lastTimeRef.current = performance.now();

    function loop(time: number) {
      const dt = (time - lastTimeRef.current) / 1000;
      lastTimeRef.current = time;

      const { value, isSettled } = osc!.step(dt);
      setCurrentValue(value);

      if (!isSettled) {
        rafRef.current = requestAnimationFrame(loop);
      } else {
        rafRef.current = null;
      }
    }

    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [targetValue]);

  return currentValue;
}
