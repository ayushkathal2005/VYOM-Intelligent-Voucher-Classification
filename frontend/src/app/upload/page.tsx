"use client";

import React from "react";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { WorkspaceNav } from "@/components/dashboard/WorkspaceNav";
import { UploadStudio } from "@/components/dashboard/UploadStudio";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

export default function UploadPage() {
  const { activeDataset, setActiveDataset } = useWorkspace();

  return (
    <div className="min-h-screen bg-[#050505] text-[#F4EBDD] flex flex-col justify-between selection:bg-[#F0AE2C]/30 selection:text-[#F4EBDD]">
      <Header />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-16 space-y-6">
        <WorkspaceNav />

        <div className="space-y-6">
          <UploadStudio
            onDatasetLoaded={(ds) => setActiveDataset(ds)}
            activeDataset={activeDataset}
          />

          {activeDataset && (
            <div className="p-4 rounded-lg bg-[#0B0805] border border-[rgba(191,145,51,0.25)] flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
              <div className="space-y-0.5">
                <span className="text-xs font-serif font-bold text-[#F4EBDD]">
                  Dataset Ready for Classification
                </span>
                <p className="text-xs text-[#A69A87]">
                  {activeDataset.filename} loaded with {activeDataset.total_rows} rows. Proceed to configure classification mode.
                </p>
              </div>

              <Link href="/classify">
                <Button variant="gold" size="md">
                  Continue to Classify &rarr;
                </Button>
              </Link>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
