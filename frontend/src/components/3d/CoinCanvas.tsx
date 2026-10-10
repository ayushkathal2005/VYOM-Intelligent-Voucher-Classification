"use client";

import React, { useState, useRef, useEffect, Suspense, Component, ErrorInfo, ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment } from "@react-three/drei";
import * as THREE from "three";
import { GoldCoin } from "./GoldCoin";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class WebGLErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn("WebGL 3D Coin fallback triggered:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

function CoinFallback() {
  return (
    <div className="w-full h-full flex items-center justify-center bg-[#0B0805] relative overflow-hidden">
      <div className="w-48 h-48 rounded-full border-2 border-[rgba(191,145,51,0.4)] bg-[#11100E] flex items-center justify-center shadow-xl shadow-[#F0AE2C]/10 animate-pulse">
        <div className="w-40 h-40 rounded-full border border-[rgba(191,145,51,0.3)] bg-gradient-to-tr from-[#9D7019]/40 via-[#F0AE2C]/20 to-transparent flex items-center justify-center">
          <span className="font-serif text-3xl font-bold text-[#F0AE2C]">VYOM</span>
        </div>
      </div>
    </div>
  );
}

interface CoinCanvasProps {
  onIntroComplete?: () => void;
  className?: string;
}

export function CoinCanvas({ onIntroComplete, className = "" }: CoinCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const [pointer, setPointer] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [isMounted, setIsMounted] = useState<boolean>(false);

  // Check reduced motion preference & client mount
  useEffect(() => {
    setIsMounted(true);
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  // Pointer movement tracking relative to container center
  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    setPointer({ x, y });
  };

  const handlePointerEnter = () => {
    setIsHovered(true);
  };

  const handlePointerLeave = () => {
    setIsHovered(false);
    setPointer({ x: 0, y: 0 });
  };

  // Mobile touch tap interaction without interfering with scrolling
  const handleTouchStart = () => {
    setIsHovered(true);
  };

  const handleTouchEnd = () => {
    setTimeout(() => {
      setIsHovered(false);
    }, 1200);
  };

  if (!isMounted) {
    return (
      <div className={`relative w-full max-w-[500px] aspect-square rounded-2xl overflow-hidden border border-[rgba(191,145,51,0.2)] bg-[#0B0805] shadow-2xl shadow-black/80 ${className}`}>
        <CoinFallback />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onPointerMove={handlePointerMove}
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      className={`relative w-full max-w-[500px] aspect-square rounded-2xl overflow-hidden border border-[rgba(191,145,51,0.2)] bg-[#0B0805] shadow-2xl shadow-black/80 group select-none cursor-grab active:cursor-grabbing ${className}`}
      aria-label="Interactive 3D Gold Coin representing financial transaction intelligence"
    >
      <WebGLErrorBoundary fallback={<CoinFallback />}>
        <Suspense fallback={<CoinFallback />}>
          <Canvas
            camera={{ position: [0, 0, 4.3], fov: 40 }}
            gl={{
              antialias: true,
              alpha: true,
              toneMapping: THREE.ACESFilmicToneMapping,
              toneMappingExposure: 1.15,
            }}
            dpr={[1, 2]}
            className="w-full h-full"
          >
            {/* Cinematic studio lighting setup */}
            <ambientLight intensity={0.5} />
            <directionalLight
              position={[4, 6, 5]}
              intensity={2.4}
              color="#FFF6E5"
            />
            <directionalLight
              position={[-4, -2, -3]}
              intensity={0.9}
              color="#B3801B"
            />
            {/* Direct front face relief light */}
            <pointLight
              position={[0, 0, 3.8]}
              intensity={1.6}
              color="#F0AE2C"
            />
            {/* Back rim light for coin milled edge silhouette */}
            <pointLight
              position={[0, 3.5, -3.5]}
              intensity={3.0}
              color="#FFE8A3"
            />

            {/* HDR environment reflection for authentic metallic gold */}
            <Environment preset="city" environmentIntensity={0.85} />

            {/* The 3D Gold Coin */}
            <GoldCoin
              isHovered={isHovered}
              pointer={pointer}
              onIntroComplete={onIntroComplete}
              reducedMotion={reducedMotion}
            />
          </Canvas>
        </Suspense>
      </WebGLErrorBoundary>

      {/* Subtle vignette border gradient */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#050505]/70 via-transparent to-transparent pointer-events-none" />

      {/* Floating indicator tag inside frame matching reference */}
      <div className="absolute bottom-6 left-6 right-6 flex items-center justify-between px-4 py-2.5 rounded bg-[#0B0805]/85 backdrop-blur-md border border-[rgba(191,145,51,0.25)] pointer-events-none transition-opacity duration-300">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C] animate-pulse" />
          <span className="text-[11px] uppercase tracking-wider font-semibold text-[#F4EBDD]">
            Voucher Intelligence
          </span>
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-[#A69A87]">
          27 Authoritative Classes
        </span>
      </div>
    </div>
  );
}
