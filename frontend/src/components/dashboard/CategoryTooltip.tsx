"use client";

import React, { useState, useRef, useEffect } from "react";
import { getVoucherDefinition, VoucherCategoryDefinition } from "@/lib/voucherCategoryDefinitions";

interface CategoryTooltipProps {
  category: string;
  children?: React.ReactNode;
  className?: string;
  showBadge?: boolean;
}

export function CategoryTooltip({
  category,
  children,
  className = "",
  showBadge = false,
}: CategoryTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const def: VoucherCategoryDefinition | undefined = getVoucherDefinition(category);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Handle keyboard Escape
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setIsOpen(false);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setIsOpen((prev) => !prev);
    }
  };

  if (!def) {
    return <span className={className}>{children || category}</span>;
  }

  return (
    <div
      ref={containerRef}
      className={`relative inline-flex items-center group/tooltip ${className}`}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onFocus={() => setIsOpen(true)}
      onBlur={(e) => {
        // If focus moved outside container, close
        if (!containerRef.current?.contains(e.relatedTarget as Node)) {
          setIsOpen(false);
        }
      }}
      tabIndex={0}
      role="button"
      aria-haspopup="dialog"
      aria-expanded={isOpen}
      aria-label={`Voucher category definition: ${def.name}`}
      onKeyDown={handleKeyDown}
      onClick={() => setIsOpen((prev) => !prev)}
    >
      {/* Trigger display */}
      {children ? (
        children
      ) : showBadge ? (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0B0805] border border-[rgba(191,145,51,0.25)] text-xs font-semibold text-[#F4EBDD] hover:border-[#F0AE2C] hover:text-[#F0AE2C] transition-colors cursor-help">
          <span>{def.name}</span>
          <span className="text-[10px] text-[#F0AE2C]/70">ⓘ</span>
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 font-medium text-[#F4EBDD] hover:text-[#F0AE2C] transition-colors cursor-help border-b border-dotted border-[rgba(191,145,51,0.4)]">
          <span>{def.name}</span>
          <span className="text-[10px] text-[#F0AE2C]/70 font-mono">ⓘ</span>
        </span>
      )}

      {/* Popover Card */}
      {isOpen && (
        <div
          role="dialog"
          aria-label={def.name}
          className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2 w-80 sm:w-96 p-4 rounded-lg bg-[#0B0805] border border-[rgba(191,145,51,0.4)] shadow-2xl backdrop-blur-xl text-left pointer-events-auto animate-in fade-in zoom-in-95 duration-150"
        >
          {/* Header */}
          <div className="flex items-start justify-between gap-2 border-b border-[rgba(191,145,51,0.15)] pb-2 mb-2.5">
            <div>
              <span className="text-[10px] uppercase font-mono tracking-widest text-[#F0AE2C]">
                Voucher Category Reference
              </span>
              <h4 className="font-serif text-sm font-bold text-[#F4EBDD]">
                {def.name}
              </h4>
            </div>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-[rgba(191,145,51,0.1)] text-[#F0AE2C] border border-[rgba(191,145,51,0.2)]">
              {def.flowDirection}
            </span>
          </div>

          {/* Meaning */}
          <div className="space-y-2 text-xs leading-relaxed">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#A69A87] block mb-0.5">
                Accounting Definition:
              </span>
              <p className="text-[#F4EBDD]/90">{def.meaning}</p>
            </div>

            {/* Typical Use */}
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#A69A87] block mb-0.5">
                When Typically Used:
              </span>
              <p className="text-[#A69A87]">{def.typicalUse}</p>
            </div>

            {/* Illustrative Transaction */}
            <div className="pt-2 border-t border-[rgba(191,145,51,0.1)]">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#F0AE2C] block mb-0.5">
                Illustrative Transaction:
              </span>
              <code className="text-[11px] block p-2 rounded bg-[#050505] border border-[rgba(191,145,51,0.2)] font-mono text-[#F4EBDD]/90 break-words whitespace-pre-wrap">
                {def.exampleTransaction}
              </code>
            </div>
          </div>

          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px] border-4 border-transparent border-t-[#0B0805]" />
        </div>
      )}
    </div>
  );
}
