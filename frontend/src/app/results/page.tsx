"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { WorkspaceNav } from "@/components/dashboard/WorkspaceNav";
import { ExportToolbar } from "@/components/dashboard/ExportToolbar";
import { ReviewQueueTable } from "@/components/dashboard/ReviewQueueTable";
import { VoucherDetailModal } from "@/components/dashboard/VoucherDetailModal";
import { HumanOverrideModal } from "@/components/dashboard/HumanOverrideModal";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/Button";

export default function ResultsPage() {
  const {
    activeDataset,
    refreshTrigger,
    triggerRefresh,
    loadAnalytics,
    isClassified,
  } = useWorkspace();

  const [inspectRowId, setInspectRowId] = useState<number | null>(null);
  const [overrideRowId, setOverrideRowId] = useState<number | null>(null);

  const handleOverrideApplied = () => {
    if (activeDataset) {
      loadAnalytics(activeDataset.dataset_id);
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
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="font-serif text-2xl font-bold text-[#F4EBDD]">
                  Classification Results &amp; Audited Exports
                </h1>
                <p className="text-xs text-[#A69A87] mt-0.5">
                  Complete classified records, confidence tiers, triage decisions, and audit-ready Excel/CSV exports.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Link href="/analytics">
                  <Button variant="outline" size="sm">
                    View Analytics &rarr;
                  </Button>
                </Link>
              </div>
            </div>

            {/* Export Toolbar */}
            <ExportToolbar
              datasetId={activeDataset.dataset_id}
              filename={activeDataset.filename}
              totalRows={activeDataset.total_rows}
              isClassified={isClassified}
            />

            {/* All Predictions Table */}
            <ReviewQueueTable
              datasetId={activeDataset.dataset_id}
              onInspectVoucher={(rowId) => setInspectRowId(rowId)}
              onOverrideVoucher={(rowId) => setOverrideRowId(rowId)}
              refreshTrigger={refreshTrigger}
            />

            {/* Modals */}
            <VoucherDetailModal
              datasetId={activeDataset.dataset_id}
              rowId={inspectRowId}
              isOpen={inspectRowId !== null}
              onClose={() => setInspectRowId(null)}
              onTriggerOverride={(rowId) => {
                setInspectRowId(null);
                setOverrideRowId(rowId);
              }}
            />

            <HumanOverrideModal
              datasetId={activeDataset.dataset_id}
              rowId={overrideRowId}
              isOpen={overrideRowId !== null}
              onClose={() => setOverrideRowId(null)}
              onOverrideApplied={handleOverrideApplied}
            />
          </div>
        ) : (
          <div className="p-12 text-center bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-[#11100E] border border-[rgba(191,145,51,0.3)] flex items-center justify-center text-xl text-[#F0AE2C]">
              📑
            </div>
            <div className="space-y-1">
              <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
                No Dataset Loaded
              </h3>
              <p className="text-xs text-[#A69A87] max-w-md mx-auto">
                Upload and classify a dataset to inspect classified records, examine triage reasoning, and export audited workbooks.
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
