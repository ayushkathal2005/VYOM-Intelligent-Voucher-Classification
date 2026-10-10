"use client";

import React from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { WorkspaceNav } from "@/components/dashboard/WorkspaceNav";
import { ClassificationControls } from "@/components/dashboard/ClassificationControls";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/Button";

export default function ClassifyPage() {
  const {
    activeDataset,
    isProcessing,
    setIsProcessing,
    setIsClassified,
    loadAnalytics,
    triggerRefresh,
    isClassified,
  } = useWorkspace();

  const handleClassificationStarted = () => {
    setIsProcessing(true);
  };

  const handleClassificationCompleted = async () => {
    setIsProcessing(false);
    setIsClassified(true);
    if (activeDataset) {
      await loadAnalytics(activeDataset.dataset_id);
    }
    triggerRefresh();
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#F4EBDD] flex flex-col justify-between selection:bg-[#F0AE2C]/30 selection:text-[#F4EBDD]">
      <Header />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-16 space-y-6">
        <WorkspaceNav />

        {activeDataset ? (
          <div className="space-y-6">
            <ClassificationControls
              datasetId={activeDataset.dataset_id}
              totalRows={activeDataset.total_rows}
              onClassificationStarted={handleClassificationStarted}
              onClassificationCompleted={handleClassificationCompleted}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
            />

            {isClassified && (
              <div className="p-4 rounded-lg bg-[#0B0805] border border-emerald-500/25 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
                <div className="space-y-0.5">
                  <span className="text-xs font-serif font-bold text-emerald-400">
                    Classification Processing Complete
                  </span>
                  <p className="text-xs text-[#A69A87]">
                    Transactions classified and guardrail-verified. View distribution analytics or inspect individual predictions.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <Link href="/analytics">
                    <Button variant="outline" size="sm">
                      View Analytics &rarr;
                    </Button>
                  </Link>
                  <Link href="/results">
                    <Button variant="gold" size="sm">
                      Inspect Results &rarr;
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-12 text-center bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-[#11100E] border border-[rgba(191,145,51,0.3)] flex items-center justify-center text-xl text-[#F0AE2C]">
              📁
            </div>
            <div className="space-y-1">
              <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
                No Dataset Loaded
              </h3>
              <p className="text-xs text-[#A69A87] max-w-md mx-auto">
                Please upload an Excel or CSV transaction workbook in the Upload Studio before configuring classification.
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
