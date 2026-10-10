"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  api,
  DatasetUploadResponse,
  DatasetAnalyticsResponse,
  BatchClassifyJobResponse,
  HumanOverrideResponse,
} from "@/lib/api";
import { UploadStudio } from "./UploadStudio";
import { ClassificationControls } from "./ClassificationControls";
import { AnalyticsOverview } from "./AnalyticsOverview";
import { ReviewQueueTable } from "./ReviewQueueTable";
import { VoucherDetailModal } from "./VoucherDetailModal";
import { HumanOverrideModal } from "./HumanOverrideModal";
import { SingleTestSandbox } from "./SingleTestSandbox";
import { ExportToolbar } from "./ExportToolbar";
import { TaxonomyModal } from "./TaxonomyModal";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

export function WorkspaceView() {
  const [activeTab, setActiveTab] = useState<"WORKSPACE" | "SANDBOX">("WORKSPACE");
  const [activeDataset, setActiveDataset] = useState<DatasetUploadResponse | null>(null);
  const [analytics, setAnalytics] = useState<DatasetAnalyticsResponse | null>(null);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isClassified, setIsClassified] = useState<boolean>(false);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Modals state
  const [inspectRowId, setInspectRowId] = useState<number | null>(null);
  const [overrideRowId, setOverrideRowId] = useState<number | null>(null);
  const [isTaxonomyOpen, setIsTaxonomyOpen] = useState<boolean>(false);

  // Load analytics whenever dataset is classified or refreshed
  const loadAnalytics = useCallback(async (datasetId: string) => {
    setIsAnalyticsLoading(true);
    try {
      const data = await api.getDatasetAnalytics(datasetId);
      setAnalytics(data);
      if (data.processed_transactions > 0) {
        setIsClassified(true);
      }
    } catch {
      // analytics may be pending prior to classification
    } finally {
      setIsAnalyticsLoading(false);
    }
  }, []);

  const handleDatasetLoaded = (dataset: DatasetUploadResponse) => {
    setActiveDataset(dataset);
    setIsClassified(false);
    setAnalytics(null);
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleClassificationStarted = (_job: BatchClassifyJobResponse) => {
    setIsProcessing(true);
  };

  const handleClassificationCompleted = async () => {
    setIsProcessing(false);
    setIsClassified(true);
    if (activeDataset) {
      await loadAnalytics(activeDataset.dataset_id);
      setRefreshTrigger((prev) => prev + 1);
    }
  };

  const handleOverrideApplied = (_response: HumanOverrideResponse) => {
    if (activeDataset) {
      loadAnalytics(activeDataset.dataset_id);
    }
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <section id="workspace" className="w-full py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Workspace Control Bar */}
      <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F0AE2C] animate-pulse" />
            <span className="font-serif text-lg font-bold text-[#F4EBDD]">
              VYOM+ Intelligent Workspace
            </span>
          </div>

          {activeDataset ? (
            <Badge variant="gold" size="sm">
              {activeDataset.filename} ({activeDataset.total_rows} rows)
            </Badge>
          ) : (
            <Badge variant="neutral" size="sm">
              No Dataset Loaded
            </Badge>
          )}
        </div>

        {/* View Switchers & Taxonomy Explorer Button */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center bg-[#050505] p-1 rounded-md border border-[rgba(191,145,51,0.2)]">
            <button
              onClick={() => setActiveTab("WORKSPACE")}
              className={`px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "WORKSPACE"
                  ? "bg-[#F0AE2C] text-[#050505]"
                  : "text-[#A69A87] hover:text-[#F4EBDD]"
              }`}
              id="tab-batch-workspace"
            >
              Batch Workbook Pipeline
            </button>
            <button
              onClick={() => setActiveTab("SANDBOX")}
              className={`px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "SANDBOX"
                  ? "bg-[#F0AE2C] text-[#050505]"
                  : "text-[#A69A87] hover:text-[#F4EBDD]"
              }`}
              id="tab-single-sandbox"
            >
              Real-Time AI Sandbox
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsTaxonomyOpen(true)}
            id="btn-explore-taxonomy"
          >
            27 Knowledge Cards
          </Button>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === "WORKSPACE" ? (
        <div className="space-y-8">
          {/* Step 1: Upload Studio */}
          <UploadStudio
            onDatasetLoaded={handleDatasetLoaded}
            activeDataset={activeDataset}
          />

          {/* Step 2: Classification Controls */}
          {activeDataset && (
            <ClassificationControls
              datasetId={activeDataset.dataset_id}
              totalRows={activeDataset.total_rows}
              onClassificationStarted={handleClassificationStarted}
              onClassificationCompleted={handleClassificationCompleted}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
            />
          )}

          {/* Export Toolbar (shown when classified) */}
          {activeDataset && isClassified && (
            <ExportToolbar
              datasetId={activeDataset.dataset_id}
              filename={activeDataset.filename}
              totalRows={activeDataset.total_rows}
              isClassified={isClassified}
            />
          )}

          {/* Step 3: Analytics Overview */}
          {activeDataset && (
            <AnalyticsOverview
              analytics={analytics}
              isLoading={isAnalyticsLoading}
            />
          )}

          {/* Step 4: Review Queue & Predictions Table */}
          {activeDataset && (
            <ReviewQueueTable
              datasetId={activeDataset.dataset_id}
              onInspectVoucher={(rowId) => setInspectRowId(rowId)}
              onOverrideVoucher={(rowId) => setOverrideRowId(rowId)}
              refreshTrigger={refreshTrigger}
            />
          )}
        </div>
      ) : (
        /* Real-Time AI Sandbox View */
        <SingleTestSandbox />
      )}

      {/* Modals */}
      {activeDataset && (
        <>
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
        </>
      )}

      <TaxonomyModal
        isOpen={isTaxonomyOpen}
        onClose={() => setIsTaxonomyOpen(false)}
      />
    </section>
  );
}
