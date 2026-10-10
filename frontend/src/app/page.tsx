"use client";

import React from "react";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { WorkspaceView } from "@/components/dashboard/WorkspaceView";
import { ProductIntroSection } from "@/components/ProductIntroSection";
import { Footer } from "@/components/Footer";

export default function Home() {
  const handleLaunch = () => {
    const el = document.getElementById("workspace");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#F4EBDD] flex flex-col justify-between selection:bg-[#F0AE2C]/30 selection:text-[#F4EBDD]">
      {/* Fixed Luxury Header */}
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 w-full">
        {/* Dominant Reference-Matched Hero Section */}
        <HeroSection onLaunchClick={handleLaunch} />

        {/* Phase 9: Connected Interactive Workspace */}
        <WorkspaceView />

        {/* Product Introduction, Architecture & 27 Taxonomy Sections */}
        <ProductIntroSection />
      </main>

      {/* Clean Restrained Footer */}
      <Footer />
    </div>
  );
}
