"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { TaxonomyModal } from "./TaxonomyModal";

const NAV_ITEMS = [
  { href: "/upload", label: "Upload Studio", id: "nav-upload" },
  { href: "/classify", label: "Classify", id: "nav-classify" },
  { href: "/analytics", label: "Analytics & Accuracy", id: "nav-analytics" },
  { href: "/review", label: "Review Queue", id: "nav-review" },
  { href: "/results", label: "Results & Export", id: "nav-results" },
  { href: "/test", label: "AI Sandbox", id: "nav-test" },
];

export function WorkspaceNav() {
  const pathname = usePathname();
  const { activeDataset, isProcessing, isClassified } = useWorkspace();
  const [isTaxonomyOpen, setIsTaxonomyOpen] = useState(false);

  return (
    <>
      <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-3 sm:p-4 mb-8 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Active Dataset Info */}
        <div className="flex items-center gap-3 flex-wrap">
          <Link
            href="/"
            className="flex items-center gap-2 group text-xs uppercase font-mono tracking-wider text-[#A69A87] hover:text-[#F0AE2C] transition-colors mr-2"
          >
            <span>&larr;</span>
            <span>Dashboard</span>
          </Link>

          <span className="hidden sm:inline-block h-3.5 w-[1px] bg-white/10" />

          {activeDataset ? (
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  isProcessing
                    ? "bg-[#F0AE2C] animate-pulse"
                    : isClassified
                    ? "bg-emerald-400"
                    : "bg-amber-400"
                }`}
              />
              <span className="font-serif text-sm font-bold text-[#F4EBDD] truncate max-w-[200px] sm:max-w-xs">
                {activeDataset.filename}
              </span>
              <Badge variant="gold" size="sm">
                {activeDataset.total_rows} rows
              </Badge>
              {isClassified && (
                <Badge variant="neutral" size="sm">
                  CLASSIFIED
                </Badge>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#A69A87]/50" />
              <span className="text-xs text-[#A69A87] font-mono">
                No active dataset loaded
              </span>
            </div>
          )}
        </div>

        {/* Center/Right: Route Tabs & 27 Cards */}
        <div className="flex items-center gap-2 flex-wrap">
          <nav className="flex items-center bg-[#050505] p-1 rounded-md border border-[rgba(191,145,51,0.2)] overflow-x-auto">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  id={item.id}
                  className={`px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                    isActive
                      ? "bg-[#F0AE2C] text-[#050505] shadow-sm"
                      : "text-[#A69A87] hover:text-[#F4EBDD]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsTaxonomyOpen(true)}
            id="btn-workspace-taxonomy"
            className="text-xs"
          >
            27 Knowledge Cards
          </Button>
        </div>
      </div>

      <TaxonomyModal
        isOpen={isTaxonomyOpen}
        onClose={() => setIsTaxonomyOpen(false)}
      />
    </>
  );
}
