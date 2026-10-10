"use client";

import React, { useState, useEffect, useRef } from "react";
import { api, BatchClassifyJobResponse, BatchClassifyJobStatusResponse } from "@/lib/api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface ClassificationControlsProps {
  datasetId: string | null;
  totalRows: number;
  onClassificationStarted: (job: BatchClassifyJobResponse) => void;
  onClassificationCompleted: () => void;
  isProcessing: boolean;
  setIsProcessing: (val: boolean) => void;
}

export function ClassificationControls({
  datasetId,
  totalRows,
  onClassificationStarted,
  onClassificationCompleted,
  isProcessing,
  setIsProcessing,
}: ClassificationControlsProps) {
  const [mode, setMode] = useState<"fast" | "ai" | "hybrid">("fast");
  const [useMock, setUseMock] = useState<boolean>(true);
  const [activeJob, setActiveJob] = useState<BatchClassifyJobStatusResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPausing, setIsPausing] = useState<boolean>(false);
  const [isResuming, setIsResuming] = useState<boolean>(false);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState<boolean>(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startClassification = async () => {
    if (!datasetId) return;
    setErrorMessage(null);
    setIsProcessing(true);
    setShowCancelConfirm(false);

    try {
      const job = await api.startBatchClassify(datasetId, mode, useMock);
      setActiveJob({
        job_id: job.job_id,
        dataset_id: job.dataset_id,
        status: job.status,
        total_rows: job.total_rows,
        processed_rows: job.processed_rows,
        progress_percent: job.progress_percent,
        mode: job.mode,
        started_at: job.started_at,
      });
      onClassificationStarted(job);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start batch classification.");
      setIsProcessing(false);
    }
  };

  const handlePause = async () => {
    if (!activeJob) return;
    setIsPausing(true);
    try {
      const updated = await api.pauseBatchJob(activeJob.job_id);
      setActiveJob(updated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to pause classification.");
    } finally {
      setIsPausing(false);
    }
  };

  const handleResume = async () => {
    if (!activeJob) return;
    setIsResuming(true);
    try {
      const updated = await api.resumeBatchJob(activeJob.job_id);
      setActiveJob(updated);
      setIsProcessing(true);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to resume classification.");
    } finally {
      setIsResuming(false);
    }
  };

  const handleCancel = async () => {
    if (!activeJob) return;
    setIsCancelling(true);
    setShowCancelConfirm(false);
    try {
      const updated = await api.cancelBatchJob(activeJob.job_id);
      setActiveJob(updated);
      setIsProcessing(false);
      onClassificationCompleted();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to cancel classification.");
    } finally {
      setIsCancelling(false);
    }
  };

  // Poll status while job is processing or pausing
  useEffect(() => {
    if (!activeJob || (activeJob.status !== "PROCESSING" && activeJob.status !== "PAUSING" && activeJob.status !== "CANCELLING")) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      return;
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await api.getBatchJobStatus(activeJob.job_id);
        setActiveJob(status);

        if (status.status === "COMPLETED") {
          setIsProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          onClassificationCompleted();
        } else if (status.status === "CANCELLED") {
          setIsProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          onClassificationCompleted();
        } else if (status.status === "FAILED") {
          setIsProcessing(false);
          setErrorMessage(status.error_message || "Classification job encountered an error.");
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        }
      } catch (err: any) {
        console.warn("Batch status poll retry:", err);
      }
    }, 800);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [activeJob?.job_id, activeJob?.status, setIsProcessing, onClassificationCompleted]);

  return (
    <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6 lg:p-8 relative overflow-hidden shadow-2xl">
      {/* Background ambient subtle accent */}
      <div className="absolute top-0 left-0 w-80 h-80 bg-[#F0AE2C]/[0.02] rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[rgba(191,145,51,0.15)]">
        <div>
          <div className="inline-flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#F0AE2C]" />
            <span className="text-[10px] uppercase tracking-[0.25em] font-semibold text-[#A69A87]">
              Step 2: Tri-Mode Classification & Reasoning
            </span>
          </div>
          <h2 className="font-serif text-2xl font-bold text-[#F4EBDD] tracking-tight">
            Execute Intelligent Classification
          </h2>
          <p className="text-xs text-[#A69A87] mt-1">
            Choose between Fast Local ML (&lt;1ms/row), Gemma 4 Deep AI reasoning, or Adaptive Hybrid uncertainty routing.
          </p>
        </div>

        {/* Inference Mode Switcher */}
        <div className="flex items-center gap-1.5 bg-[#050505] p-1.5 rounded-lg border border-[rgba(191,145,51,0.2)]">
          <button
            onClick={() => setMode("fast")}
            className={`px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wider transition-all ${
              mode === "fast"
                ? "bg-[#F0AE2C] text-[#050505] shadow-md shadow-[#F0AE2C]/10"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
            id="toggle-fast-mode"
          >
            ⚡ Fast Mode (Local)
          </button>
          <button
            onClick={() => setMode("hybrid")}
            className={`px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wider transition-all ${
              mode === "hybrid"
                ? "bg-[#F0AE2C] text-[#050505] shadow-md shadow-[#F0AE2C]/10"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
            id="toggle-hybrid-mode"
          >
            ⚖️ Hybrid Mode
          </button>
          <button
            onClick={() => setMode("ai")}
            className={`px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wider transition-all ${
              mode === "ai"
                ? "bg-[#F0AE2C] text-[#050505] shadow-md shadow-[#F0AE2C]/10"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
            id="toggle-ai-mode"
          >
            🧠 AI Mode (Gemma 4)
          </button>
        </div>
      </div>

      {/* Mode Notification Banner */}
      <div className="mt-4 p-3 rounded bg-[#050505]/70 border border-white/5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-[#A69A87]">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          {mode === "fast" && (
            <span>
              <strong className="text-[#F4EBDD]">Fast Local Mode Active:</strong> Calibrated Linear SVM with Word + Char-WB TF-IDF (&lt;1ms/row, &gt;1,300 rows/s, 99.2% validation Macro-F1, zero external API dependency).
            </span>
          )}
          {mode === "hybrid" && (
            <span>
              <strong className="text-[#F4EBDD]">Hybrid Mode Active:</strong> Fast local classifier triages high-confidence items (&ge;85%) instantly; uncertain or flagged vouchers route to Gemma 4 for deep reasoning.
            </span>
          )}
          {mode === "ai" && (
            <span>
              <strong className="text-[#F4EBDD]">Gemma 4 AI Mode Active:</strong> Full chain-of-thought financial reasoning with candidate retriever and accounting guardrails via Google GenAI SDK.
            </span>
          )}
        </div>
        <Badge variant={mode === "fast" ? "gold" : mode === "hybrid" ? "neutral" : "subtle"} size="sm">
          {mode === "fast" ? "LOCAL ML (FAST)" : mode === "hybrid" ? "ADAPTIVE HYBRID" : "GEMMA 4 LLM"}
        </Badge>
      </div>

      {/* Action / Progress Area */}
      <div className="mt-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="flex items-center gap-3 flex-wrap">
          {(!activeJob || activeJob.status === "COMPLETED" || activeJob.status === "FAILED" || activeJob.status === "CANCELLED") && (
            <Button
              variant="gold"
              size="md"
              disabled={!datasetId || isProcessing}
              isLoading={isProcessing}
              onClick={startClassification}
              id="btn-run-batch-classification"
            >
              {isProcessing ? "Classifying Transactions..." : activeJob?.status === "CANCELLED" ? `Restart All ${totalRows || 0} Transactions` : `Classify All ${totalRows || 0} Transactions`}
            </Button>
          )}

          {/* Pause / Resume Controls during active processing */}
          {activeJob && (activeJob.status === "PROCESSING" || activeJob.status === "PAUSING") && (
            <Button
              variant="outline"
              size="md"
              onClick={handlePause}
              disabled={isPausing || activeJob.status === "PAUSING"}
              isLoading={isPausing}
              id="btn-pause-job"
              className="border-amber-500/40 text-amber-300 hover:border-amber-400"
            >
              <span className="flex items-center gap-2">
                <span>⏸</span>
                <span>{activeJob.status === "PAUSING" ? "Pausing at record..." : "Pause Processing"}</span>
              </span>
            </Button>
          )}

          {activeJob && activeJob.status === "PAUSED" && (
            <Button
              variant="gold"
              size="md"
              onClick={handleResume}
              disabled={isResuming}
              isLoading={isResuming}
              id="btn-resume-job"
            >
              <span className="flex items-center gap-2">
                <span>▶</span>
                <span>Resume Processing</span>
              </span>
            </Button>
          )}

          {/* Cancel button during processing or paused */}
          {activeJob && (activeJob.status === "PROCESSING" || activeJob.status === "PAUSED" || activeJob.status === "PAUSING") && (
            <Button
              variant="ghost"
              size="md"
              onClick={() => setShowCancelConfirm(true)}
              disabled={isCancelling}
              id="btn-cancel-job"
              className="text-red-400/80 hover:text-red-400 hover:bg-red-950/20"
            >
              <span className="flex items-center gap-1.5">
                <span>✕</span>
                <span>Cancel Batch</span>
              </span>
            </Button>
          )}

          {activeJob?.status === "COMPLETED" && (
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              <span>Batch Complete &bull; 100% Processed</span>
            </div>
          )}

          {activeJob?.status === "PAUSED" && (
            <Badge variant="subtle" size="sm">
              PAUSED AT ROW {activeJob.processed_rows}
            </Badge>
          )}

          {activeJob?.status === "CANCELLED" && (
            <div className="flex items-center gap-2 text-amber-400/90 text-xs font-semibold uppercase tracking-wider">
              <span>Job Cancelled &bull; {activeJob.processed_rows} of {activeJob.total_rows} Preserved</span>
            </div>
          )}
        </div>

        {/* Live Progress Bar when active, paused, or complete */}
        {activeJob && (
          <div className="w-full lg:max-w-md bg-[#050505] p-3 rounded border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[#A69A87] flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    activeJob.status === "PROCESSING"
                      ? "bg-[#F0AE2C] animate-pulse"
                      : activeJob.status === "PAUSED"
                      ? "bg-amber-400"
                      : activeJob.status === "COMPLETED"
                      ? "bg-emerald-400"
                      : "bg-red-400"
                  }`}
                />
                Status: {activeJob.status} ({activeJob.processed_rows} / {activeJob.total_rows})
              </span>
              <span className="text-[#F0AE2C] font-semibold">
                {activeJob.progress_percent}%
              </span>
            </div>

            <div className="w-full h-2 bg-[#11100E] rounded-full overflow-hidden border border-white/5">
              <div
                className={`h-full transition-all duration-300 rounded-full ${
                  activeJob.status === "PAUSED"
                    ? "bg-amber-500/70"
                    : activeJob.status === "CANCELLED"
                    ? "bg-red-500/60"
                    : "bg-gradient-to-r from-[#9D7019] via-[#F0AE2C] to-[#ffe29c]"
                }`}
                style={{ width: `${activeJob.progress_percent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Cancel Confirmation Prompt */}
      {showCancelConfirm && activeJob && (
        <div className="mt-4 p-4 rounded-lg bg-red-950/30 border border-red-500/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-red-300 uppercase tracking-wider">
              Confirm Batch Cancellation
            </h4>
            <p className="text-xs text-[#F4EBDD]/80">
              Outstanding records will stop scheduling immediately. All {activeJob.processed_rows} completed predictions will be safely retained in your dataset.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCancelConfirm(false)}
            >
              Keep Processing
            </Button>
            <Button
              variant="gold"
              size="sm"
              isLoading={isCancelling}
              onClick={handleCancel}
              className="!bg-red-600 hover:!bg-red-500 text-white"
            >
              Confirm Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="mt-4 p-3 rounded bg-red-950/40 border border-red-500/50 flex items-center gap-2 text-xs text-red-200">
          <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
