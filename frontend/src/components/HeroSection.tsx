"use client";

import React from "react";
import Image from "next/image";
import { Button } from "./ui/Button";

interface HeroSectionProps {
  onLaunchClick?: () => void;
}

export function HeroSection({ onLaunchClick }: HeroSectionProps) {
  return (
    <section className="relative min-h-screen pt-28 pb-16 flex items-center justify-center overflow-hidden bg-[#050505]">
      {/* Background ambient gold gradient glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-[#F0AE2C]/[0.04] rounded-full blur-[140px] pointer-events-none"
        aria-hidden="true"
      />

      <div className="max-w-7xl mx-auto px-6 sm:px-8 w-full relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Editorial Headline & Copy */}
          <div className="lg:col-span-6 flex flex-col justify-center space-y-8 text-left">
            {/* Fine uppercase section label */}
            <div className="inline-flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-[#F0AE2C]" />
              <span className="text-[11px] uppercase tracking-[0.25em] font-semibold text-[#A69A87]">
                Intelligent Accounting Engine
              </span>
            </div>

            {/* Large editorial headline */}
            <h1 className="font-serif text-5xl sm:text-6xl xl:text-7xl font-bold tracking-tight text-[#F4EBDD] leading-[1.08]">
              Your books.
              <br />
              <span className="italic font-normal text-[#F4EBDD]/90">Understood</span> by{" "}
              <span className="text-[#F0AE2C] underline decoration-[rgba(191,145,51,0.3)] underline-offset-8">
                AI.
              </span>
            </h1>

            {/* Short explanatory paragraph */}
            <p className="text-base sm:text-lg text-[#A69A87] leading-relaxed max-w-xl font-normal">
              Transform structured transactions into intelligent voucher
              classifications. Resolve ambiguity, inspect confidence, and export
              accounting-ready results using Gemma&nbsp;4 through the official
              Gemini&nbsp;API.
            </p>

            {/* Primary Gold CTA & Secondary Action */}
            <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <Button
                variant="gold"
                size="lg"
                onClick={onLaunchClick || (() => {
                  const target = document.getElementById("overview");
                  if (target) target.scrollIntoView({ behavior: "smooth" });
                })}
                className="group shadow-xl shadow-[#F0AE2C]/15"
                id="btn-hero-launch"
              >
                <span>LAUNCH CLASSIFIER</span>
                <span className="ml-2 group-hover:translate-x-1 transition-transform">
                  &rarr;
                </span>
              </Button>

              <a
                href="#architecture"
                className="inline-flex items-center justify-center px-6 py-4 text-sm font-medium tracking-wide text-[#F4EBDD] bg-[#11100E] border border-[rgba(191,145,51,0.2)] hover:border-[#F0AE2C]/40 hover:bg-[#1a1814] rounded-sm transition-all focus-visible:outline-2 focus-visible:outline-[#F0AE2C]"
              >
                EXPLORE ARCHITECTURE
              </a>
            </div>

            {/* Minimal circular controls & metadata */}
            <div className="pt-6 border-t border-[rgba(191,145,51,0.12)] flex items-center justify-between max-w-md">
              <div className="flex items-center gap-3">
                <a
                  href="https://github.com/ayushkathal2005/VYOM-Intelligent-Voucher-Classification-Using-Open-Source-LLMs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-[#11100E] border border-[rgba(191,145,51,0.2)] flex items-center justify-center text-[#A69A87] hover:text-[#F0AE2C] hover:border-[#F0AE2C]/50 transition-colors focus-visible:outline-none"
                  aria-label="GitHub Repository"
                >
                  <svg
                    className="w-4 h-4 fill-current"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                </a>

                <a
                  href="#status"
                  className="w-10 h-10 rounded-full bg-[#11100E] border border-[rgba(191,145,51,0.2)] flex items-center justify-center text-[#A69A87] hover:text-[#F0AE2C] hover:border-[#F0AE2C]/50 transition-colors focus-visible:outline-none"
                  aria-label="API System Status"
                >
                  <svg
                    className="w-4 h-4 fill-none stroke-current"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </a>
              </div>

              <div className="text-right">
                <span className="block text-xs uppercase tracking-wider text-[#A69A87]">
                  Model Designation
                </span>
                <span className="font-mono text-xs text-[#F0AE2C]">
                  Gemma 4 &bull; Gemini API
                </span>
              </div>
            </div>
          </div>

          {/* Right Column / Center: Dominant Cinematic Glass-Jar Visual */}
          <div className="lg:col-span-6 flex items-center justify-center relative">
            {/* Ambient luxury halo behind jar */}
            <div className="absolute inset-0 bg-radial from-[#F0AE2C]/15 via-transparent to-transparent rounded-full filter blur-3xl scale-95 pointer-events-none" />

            <div className="relative w-full max-w-[500px] aspect-square rounded-2xl overflow-hidden border border-[rgba(191,145,51,0.2)] bg-[#0B0805] shadow-2xl shadow-black/80 group">
              <Image
                src="/hero-glass-jar.jpg"
                alt="Cinematic luxury glass vessel illuminating financial accounting intelligence"
                width={700}
                height={700}
                priority
                className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.02]"
              />

              {/* Glass subtle overlay reflection */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#050505]/80 via-transparent to-transparent pointer-events-none" />

              {/* Minimal floating indicator tag inside glass frame */}
              <div className="absolute bottom-6 left-6 right-6 flex items-center justify-between px-4 py-2.5 rounded bg-[#0B0805]/80 backdrop-blur-md border border-[rgba(191,145,51,0.25)]">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C]" />
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-[#F4EBDD]">
                    Voucher Intelligence
                  </span>
                </div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#A69A87]">
                  27 Authoritative Classes
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
