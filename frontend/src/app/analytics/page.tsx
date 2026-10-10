"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { WorkspaceNav } from "@/components/dashboard/WorkspaceNav";
import { AnalyticsOverview } from "@/components/dashboard/AnalyticsOverview";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/Button";

export default function AnalyticsPage() {
  const {
    activeDataset,
    analytics,
    isAnalyticsLoading,
    loadAnalytics,
  } = useWorkspace();

  useEffect(() => {
    if (activeDataset && !analytics) {
      loadAnalytics(activeDataset.dataset_id);
    }
  }, [activeDataset, analytics, loadAnalytics]);

  return (
    <div className="min-h-screen bg-[#050505] text-[#F4EBDD] flex flex-col justify-between selection:bg-[#F0AE2C]/30 selection:text-[#F4EBDD]">
      <Header />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-16 space-y-6">
        <WorkspaceNav />

        {activeDataset ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-serif text-2xl font-bold text-[#F4EBDD]">
                  Classification Analytics &amp; Integrity
                </h1>
                <p className="text-xs text-[#A69A87] mt-0.5">
                  Multi-class distribution, honest accuracy reporting, and rule-based contradiction detection.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Link href="/review">
                  <Button variant="outline" size="sm">
                    Open Review Queue &rarr;
                  </Button>
                </Link>
                <Link href="/results">
                  <Button variant="gold" size="sm">
                    View All Results &rarr;
                  </Button>
                </Link>
              </div>
            </div>

            <AnalyticsOverview
              analytics={analytics}
              isLoading={isAnalyticsLoading}
            />
          </div>
        ) : (
          <div className="p-12 text-center bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-[#11100E] border border-[rgba(191,145,51,0.3)] flex items-center justify-center text-xl text-[#F0AE2C]">
              📊
            </div>
            <div className="space-y-1">
              <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
                No Dataset Loaded
              </h3>
              <p className="text-xs text-[#A69A87] max-w-md mx-auto">
                Upload and classify a dataset to view distribution metrics, calibrated confidence levels, and contradiction analysis.
              </p>
            </div>
            <Link href="/upload">
              <Button variant="gold" size="md">
                Go to Upload Studio &rarr;
              </Button>
            </Link>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
