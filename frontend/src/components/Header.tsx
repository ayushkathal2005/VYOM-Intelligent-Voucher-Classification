"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";

export function Header() {
  const pathname = usePathname();
  const { activeDataset, isProcessing, isClassified } = useWorkspace();

  const navLinks = [
    { href: "/upload", label: "Upload" },
    { href: "/classify", label: "Classify" },
    { href: "/analytics", label: "Analytics" },
    { href: "/review", label: "Review" },
    { href: "/results", label: "Results" },
    { href: "/test", label: "Sandbox" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/90 backdrop-blur-md border-b border-[rgba(191,145,51,0.16)] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 h-20 flex items-center justify-between">
        {/* Brand at top left */}
        <div className="flex items-center gap-3 sm:gap-4">
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

          <span className="hidden lg:inline-block text-[11px] uppercase tracking-widest text-[#A69A87] font-medium">
            Financial Transaction Intelligence
          </span>
        </div>

        {/* Center navigation */}
        <nav className="hidden md:flex items-center gap-5 lg:gap-6 text-xs uppercase tracking-widest text-[#A69A87] font-medium">
          <Link
            href="/"
            className={`transition-colors focus-visible:outline-none ${
              pathname === "/"
                ? "text-[#F0AE2C] font-semibold"
                : "hover:text-[#F0AE2C]"
            }`}
          >
            Overview
          </Link>

          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`transition-colors focus-visible:outline-none flex items-center gap-1.5 ${
                  isActive
                    ? "text-[#F0AE2C] font-semibold"
                    : "hover:text-[#F0AE2C]"
                }`}
              >
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C] animate-pulse" />
                )}
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Small uppercase indicator at top right */}
        <div className="flex items-center gap-3">
          {activeDataset ? (
            <Link
              href="/classify"
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0B0805] border border-[rgba(191,145,51,0.3)] shadow-sm hover:border-[#F0AE2C] transition-colors"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isProcessing
                    ? "bg-[#F0AE2C] animate-pulse"
                    : isClassified
                    ? "bg-emerald-400"
                    : "bg-amber-400"
                }`}
              />
              <span className="text-[10px] uppercase tracking-wider font-semibold text-[#F4EBDD] truncate max-w-[120px] sm:max-w-[160px]">
                {activeDataset.filename}
              </span>
            </Link>
          ) : (
            <Link
              href="/upload"
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0B0805] border border-[rgba(191,145,51,0.25)] shadow-sm hover:border-[#F0AE2C] transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C] animate-pulse" />
              <span className="text-[10px] uppercase tracking-widest font-semibold text-[#F4EBDD]">
                LOAD WORKBOOK &rarr;
              </span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
