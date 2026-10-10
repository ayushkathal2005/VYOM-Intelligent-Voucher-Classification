import React from "react";

export function Footer() {
  return (
    <footer className="border-t border-[rgba(191,145,51,0.16)] bg-[#0B0805] py-12 text-[#A69A87] text-xs">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-1">
            <span className="font-serif text-base font-bold text-[#F4EBDD]">
              VYOM
            </span>
            <span className="font-serif text-base font-bold text-[#F0AE2C]">
              +
            </span>
            <span className="text-neutral-500 mx-2">&bull;</span>
            <span className="text-[11px] uppercase tracking-wider text-[#A69A87]">
              Intelligent Voucher Classification
            </span>
          </div>
          <p className="text-[11px] text-[#A69A87]/70">
            Powered by Gemma 4 through the official Google Gemini API &bull;
            Strict Phase-Gated Engineering
          </p>
        </div>

        <div className="flex items-center gap-6 text-[11px] uppercase tracking-widest font-medium">
          <a
            href="https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#F0AE2C] transition-colors"
          >
            Gemma 4 Docs
          </a>
          <a
            href="https://github.com/ayushkathal2005/VYOM-Intelligent-Voucher-Classification-Using-Open-Source-LLMs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#F0AE2C] transition-colors"
          >
            Repository
          </a>
          <a
            href="#overview"
            className="hover:text-[#F0AE2C] transition-colors"
          >
            Top &uarr;
          </a>
        </div>
      </div>
    </footer>
  );
}
