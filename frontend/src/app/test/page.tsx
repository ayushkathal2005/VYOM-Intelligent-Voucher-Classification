"use client";

import React from "react";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { WorkspaceNav } from "@/components/dashboard/WorkspaceNav";
import { SingleTestSandbox } from "@/components/dashboard/SingleTestSandbox";

export default function TestSandboxPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-[#F4EBDD] flex flex-col justify-between selection:bg-[#F0AE2C]/30 selection:text-[#F4EBDD]">
      <Header />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-16 space-y-6">
        <WorkspaceNav />

        <div className="space-y-6">
          <div className="pb-2">
            <h1 className="font-serif text-2xl font-bold text-[#F4EBDD]">
              Real-Time AI Voucher Sandbox
            </h1>
            <p className="text-xs text-[#A69A87] mt-0.5">
              Interactive single-transaction classification across Fast Local ML, Adaptive Hybrid, and Gemma 4 AI modes.
            </p>
          </div>

          <SingleTestSandbox />
        </div>
      </main>

      <Footer />
    </div>
  );
}
