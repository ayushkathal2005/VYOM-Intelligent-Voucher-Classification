"use client";

import React from "react";
import Link from "next/link";

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/85 backdrop-blur-md border-b border-[rgba(191,145,51,0.16)] transition-all">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 h-20 flex items-center justify-between">
        {/* Brand at top left */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-baseline gap-1 group focus-visible:outline-none"
            aria-label="VYOM+ Homepage"
          >
            <span className="font-serif text-2xl font-bold tracking-tight text-[#F4EBDD] group-hover:text-white transition-colors">
              VYOM
            </span>
            <span className="font-serif text-2xl font-bold text-[#F0AE2C]">
              +
            </span>
          </Link>

          <span className="hidden sm:inline-block h-4 w-[1px] bg-[rgba(191,145,51,0.25)] mx-1" />

          <span className="hidden sm:inline-block text-[11px] uppercase tracking-widest text-[#A69A87] font-medium">
            Financial Transaction Intelligence
          </span>
        </div>

        {/* Center navigation */}
        <nav className="hidden md:flex items-center gap-8 text-xs uppercase tracking-widest text-[#A69A87] font-medium">
          <a
            href="#overview"
            className="hover:text-[#F0AE2C] transition-colors focus-visible:outline-none"
          >
            Overview
          </a>
          <a
            href="#architecture"
            className="hover:text-[#F0AE2C] transition-colors focus-visible:outline-none"
          >
            Architecture
          </a>
          <a
            href="#labels"
            className="hover:text-[#F0AE2C] transition-colors focus-visible:outline-none"
          >
            27 Labels
          </a>
          <a
            href="#status"
            className="hover:text-[#F0AE2C] transition-colors focus-visible:outline-none"
          >
            System Status
          </a>
        </nav>

        {/* Small uppercase indicator at top right */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0B0805] border border-[rgba(191,145,51,0.25)] shadow-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C] animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest font-semibold text-[#F4EBDD]">
              SCROLL TO EXPLORE &darr;
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
