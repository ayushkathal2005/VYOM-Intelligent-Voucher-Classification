"use client";

import React, { useState, useRef } from "react";
import { api, DatasetUploadResponse, PaginatedPreviewResponse } from "@/lib/api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface UploadStudioProps {
  onDatasetLoaded: (dataset: DatasetUploadResponse) => void;
  activeDataset: DatasetUploadResponse | null;
}

export function UploadStudio({ onDatasetLoaded, activeDataset }: UploadStudioProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<PaginatedPreviewResponse | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [isDetectedColsExpanded, setIsDetectedColsExpanded] = useState(false);
  const [isCanonicalMappedExpanded, setIsCanonicalMappedExpanded] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    const validExtensions = [".xlsx", ".xls", ".csv"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setUploadError("Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV (.csv) workbook.");
      return;
    }

    setUploadError(null);
    setIsUploading(true);

    try {
      const result = await api.uploadDataset(file);
      setIsDetectedColsExpanded(false);
      setIsCanonicalMappedExpanded(false);
      onDatasetLoaded(result);
    } catch (err: any) {
      setUploadError(err.message || "Failed to parse and upload transaction dataset.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleLoadCuratedDemo = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsUploading(true);
    setUploadError(null);
    try {
      const resp = await fetch("/demo_voucher_sample.xlsx");
      if (!resp.ok) throw new Error("Could not fetch demo dataset.");
      const blob = await resp.blob();
      const demoFile = new File([blob], "demo_voucher_sample.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      await handleFile(demoFile);
    } catch (err: any) {
      setUploadError(err.message || "Failed to load demo dataset.");
      setIsUploading(false);
    }
  };

  const loadPreview = async (page: number = 1) => {
    if (!activeDataset) return;
    setIsPreviewLoading(true);
    try {
      const data = await api.getDatasetPreview(activeDataset.dataset_id, page, 10);
      setPreviewData(data);
      setShowPreviewModal(true);
    } catch (err: any) {
      setUploadError(err.message || "Failed to load dataset preview.");
    } finally {
      setIsPreviewLoading(false);
    }
  };

  return (
    <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6 lg:p-8 relative overflow-hidden shadow-2xl">
      {/* Background ambient subtle accent */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-[#F0AE2C]/[0.02] rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[rgba(191,145,51,0.15)]">
        <div>
          <div className="inline-flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#F0AE2C]" />
            <span className="text-[10px] uppercase tracking-[0.25em] font-semibold text-[#A69A87]">
              Step 1: Dataset Ingestion & Schema Discovery
            </span>
          </div>
          <h2 className="font-serif text-2xl font-bold text-[#F4EBDD] tracking-tight">
            Accounting Workbook Ingestion
          </h2>
          <p className="text-xs text-[#A69A87] mt-1">
            Upload commercial invoices, purchase orders, or payment journals in .xlsx or .csv format with zero leakage.
          </p>
        </div>

        {activeDataset && (
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadPreview(1)}
              isLoading={isPreviewLoading}
              id="btn-preview-dataset"
            >
              Inspect Raw Rows ({activeDataset.total_rows})
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              id="btn-upload-new-file"
            >
              Upload Different File
            </Button>
          </div>
        )}
      </div>

      {/* Upload Zone */}
      {!activeDataset ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`mt-6 border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 ${
            isDragging
              ? "border-[#F0AE2C] bg-[#F0AE2C]/[0.05] scale-[1.005]"
              : "border-[rgba(191,145,51,0.25)] hover:border-[#F0AE2C]/60 bg-[#050505]/60 hover:bg-[#11100E]"
          }`}
          id="dropzone-upload"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFile(e.target.files[0]);
              }
            }}
            accept=".xlsx,.xls,.csv"
            className="hidden"
            id="file-upload-input"
          />

          <div className="w-14 h-14 rounded-full bg-[#11100E] border border-[rgba(191,145,51,0.3)] flex items-center justify-center mb-4 text-[#F0AE2C] shadow-inner">
            {isUploading ? (
              <svg className="animate-spin h-6 w-6 text-[#F0AE2C]" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            )}
          </div>

          <h3 className="font-serif text-lg font-medium text-[#F4EBDD]">
            {isUploading ? "Parsing & Discovering Schema..." : "Drop your accounting workbook here"}
          </h3>
          <p className="text-xs text-[#A69A87] mt-1.5 max-w-sm">
            Drag and drop or click to browse. Supports Excel (.xlsx) and CSV (.csv) transaction records.
          </p>

          <div className="flex items-center gap-2 mt-4">
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-black/40 border border-white/10 text-[#A69A87]">
              .XLSX
            </span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-black/40 border border-white/10 text-[#A69A87]">
              .CSV
            </span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-black/40 border border-white/10 text-[#A69A87]">
              AUTO-SCHEMA
            </span>
          </div>

          {/* Quick Demo Dataset Loader */}
          <div className="mt-5 pt-4 border-t border-white/5 flex items-center justify-center gap-3">
            <span className="text-[11px] text-[#A69A87]">Presenter Quick Demo:</span>
            <button
              type="button"
              onClick={handleLoadCuratedDemo}
              disabled={isUploading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[11px] font-semibold text-[#F0AE2C] bg-[#11100E] border border-[rgba(191,145,51,0.35)] hover:border-[#F0AE2C] hover:bg-[#1a1814] transition-all cursor-pointer shadow-sm"
              id="btn-load-demo-dataset"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C] animate-pulse" />
              <span>Load Curated Demo Dataset (25 Vouchers)</span>
            </button>
          </div>
        </div>
      ) : (
        /* Active Dataset Schema Discovery Card */
        <div className="mt-6 space-y-6">
          <div className="bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded-lg p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-[#11100E] border border-[#F0AE2C]/30 flex items-center justify-center text-[#F0AE2C]">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-serif text-base font-semibold text-[#F4EBDD]">
                      {activeDataset.filename}
                    </h3>
                    <Badge variant="gold" size="sm">ACTIVE DATASET</Badge>
                  </div>
                  <p className="text-xs text-[#A69A87] font-mono mt-0.5">
                    ID: {activeDataset.dataset_id} &bull; {activeDataset.total_rows} Transactions
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs text-[#F0AE2C] hover:underline"
                >
                  Upload New
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      handleFile(e.target.files[0]);
                    }
                  }}
                  accept=".xlsx,.xls,.csv"
                  className="hidden"
                />
              </div>
            </div>

            {/* Schema Mapping Intelligence */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-2 items-start">
              {/* 1. Detected Columns */}
              <div className="p-3 bg-[#11100E] rounded border border-white/5 flex flex-col justify-between">
                <button
                  type="button"
                  onClick={() => setIsDetectedColsExpanded((prev) => !prev)}
                  className="w-full flex items-center justify-between text-left group cursor-pointer focus:outline-none focus-visible:ring-1 focus-visible:ring-[#F0AE2C]/50 rounded py-0.5"
                  aria-expanded={isDetectedColsExpanded}
                  aria-controls="detected-columns-content"
                  id="btn-toggle-detected-columns"
                >
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold group-hover:text-[#F0AE2C] transition-colors">
                      Detected Columns
                    </span>
                    <span className="text-[10px] font-mono text-[#F0AE2C]/90 bg-[#F0AE2C]/10 px-1.5 py-0.5 rounded border border-[#F0AE2C]/20">
                      {activeDataset.columns_detected.length} columns detected
                    </span>
                  </div>
                  <span className="text-[#A69A87] group-hover:text-[#F0AE2C] transition-colors p-0.5 shrink-0 ml-1">
                    <svg
                      className={`w-3.5 h-3.5 transition-transform duration-200 ${
                        isDetectedColsExpanded ? "rotate-180 text-[#F0AE2C]" : "rotate-0"
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </button>

                {!isDetectedColsExpanded ? (
                  <div className="mt-2 space-y-1.5">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {activeDataset.columns_detected.slice(0, 4).map((col) => (
                        <span
                          key={col}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-[rgba(191,145,51,0.2)] text-[#F4EBDD] max-w-[130px] truncate"
                          title={col}
                        >
                          {col}
                        </span>
                      ))}
                      {activeDataset.columns_detected.length > 4 && (
                        <button
                          type="button"
                          onClick={() => setIsDetectedColsExpanded(true)}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#161410] border border-[rgba(191,145,51,0.3)] text-[#F0AE2C] hover:border-[#F0AE2C] hover:bg-[#1f1b14] transition-colors cursor-pointer"
                          title="Click to expand all columns"
                        >
                          +{activeDataset.columns_detected.length - 4} more ▼
                        </button>
                      )}
                    </div>
                    <p className="text-[10px] text-[#A69A87]/80 font-mono">
                      {activeDataset.columns_detected.length} columns detected &bull; Click header to inspect
                    </p>
                  </div>
                ) : (
                  <div
                    id="detected-columns-content"
                    className="mt-2.5 max-h-56 overflow-y-auto pr-1 space-y-2 border-t border-white/5 pt-2"
                  >
                    <div className="flex flex-wrap gap-1.5">
                      {activeDataset.columns_detected.map((col) => (
                        <span
                          key={col}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-[rgba(191,145,51,0.2)] text-[#F4EBDD] break-all"
                          title={col}
                        >
                          {col}
                        </span>
                      ))}
                    </div>
                    <div className="sticky bottom-0 pt-1 flex justify-end bg-gradient-to-t from-[#11100E] via-[#11100E]/90 to-transparent">
                      <button
                        type="button"
                        onClick={() => setIsDetectedColsExpanded(false)}
                        className="text-[10px] font-mono text-[#A69A87] hover:text-[#F0AE2C] transition-colors py-0.5"
                      >
                        ▲ Collapse list
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* 2. Canonical Fields Mapped */}
              <div className="p-3 bg-[#11100E] rounded border border-white/5 flex flex-col justify-between">
                <button
                  type="button"
                  onClick={() => setIsCanonicalMappedExpanded((prev) => !prev)}
                  className="w-full flex items-center justify-between text-left group cursor-pointer focus:outline-none focus-visible:ring-1 focus-visible:ring-[#F0AE2C]/50 rounded py-0.5"
                  aria-expanded={isCanonicalMappedExpanded}
                  aria-controls="canonical-mappings-content"
                  id="btn-toggle-canonical-mappings"
                >
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold group-hover:text-[#F0AE2C] transition-colors">
                      Canonical Fields Mapped
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400/90 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      {Object.keys(activeDataset.canonical_fields_mapped).length} canonical mappings
                    </span>
                  </div>
                  <span className="text-[#A69A87] group-hover:text-[#F0AE2C] transition-colors p-0.5 shrink-0 ml-1">
                    <svg
                      className={`w-3.5 h-3.5 transition-transform duration-200 ${
                        isCanonicalMappedExpanded ? "rotate-180 text-[#F0AE2C]" : "rotate-0"
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </button>

                {!isCanonicalMappedExpanded ? (
                  <div className="mt-2 space-y-1.5">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {Object.entries(activeDataset.canonical_fields_mapped)
                        .slice(0, 3)
                        .map(([canonical, original]) => (
                          <span
                            key={canonical}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F0AE2C]/10 border border-[#F0AE2C]/30 text-[#F0AE2C] max-w-[170px] truncate"
                            title={`Mapped from: ${original}`}
                          >
                            {canonical} &larr; {original}
                          </span>
                        ))}
                      {Object.keys(activeDataset.canonical_fields_mapped).length > 3 && (
                        <button
                          type="button"
                          onClick={() => setIsCanonicalMappedExpanded(true)}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#161410] border border-[rgba(191,145,51,0.3)] text-[#F0AE2C] hover:border-[#F0AE2C] hover:bg-[#1f1b14] transition-colors cursor-pointer"
                          title="Click to expand all mappings"
                        >
                          +{Object.keys(activeDataset.canonical_fields_mapped).length - 3} more ▼
                        </button>
                      )}
                    </div>
                    <p className="text-[10px] text-[#A69A87]/80 font-mono">
                      {Object.keys(activeDataset.canonical_fields_mapped).length} canonical mappings &bull; Click header to inspect
                    </p>
                  </div>
                ) : (
                  <div
                    id="canonical-mappings-content"
                    className="mt-2.5 max-h-56 overflow-y-auto pr-1 space-y-2 border-t border-white/5 pt-2"
                  >
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(activeDataset.canonical_fields_mapped).map(([canonical, original]) => (
                        <span
                          key={canonical}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F0AE2C]/10 border border-[#F0AE2C]/30 text-[#F0AE2C] break-all"
                          title={`Mapped from: ${original}`}
                        >
                          {canonical} &larr; {original}
                        </span>
                      ))}
                    </div>
                    <div className="sticky bottom-0 pt-1 flex justify-end bg-gradient-to-t from-[#11100E] via-[#11100E]/90 to-transparent">
                      <button
                        type="button"
                        onClick={() => setIsCanonicalMappedExpanded(false)}
                        className="text-[10px] font-mono text-[#A69A87] hover:text-[#F0AE2C] transition-colors py-0.5"
                      >
                        ▲ Collapse list
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* 3. Schema Integrity & Warnings */}
              <div className="p-3 bg-[#11100E] rounded border border-white/5 flex flex-col justify-start">
                <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block py-0.5">
                  Schema Integrity & Warnings
                </span>
                {activeDataset.warnings.length === 0 ? (
                  <div className="flex items-center gap-1.5 mt-2 text-emerald-400 text-xs">
                    <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Clean schema. Zero target leakage.</span>
                  </div>
                ) : (
                  <div className="space-y-1 mt-2">
                    {activeDataset.warnings.map((w, idx) => (
                      <div key={idx} className="text-[11px] text-amber-300/90 flex items-start gap-1">
                        <span className="text-amber-400 font-bold">&bull;</span>
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Error Banner */}
      {uploadError && (
        <div className="mt-4 p-3 rounded bg-red-950/40 border border-red-500/50 flex items-center gap-2 text-xs text-red-200">
          <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{uploadError}</span>
        </div>
      )}

      {/* Raw Tabular Preview Modal */}
      {showPreviewModal && previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.3)] rounded-lg w-full max-w-5xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 sm:p-6 border-b border-white/10 flex items-center justify-between">
              <div>
                <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
                  Raw Tabular Records Preview
                </h3>
                <p className="text-xs text-[#A69A87] font-mono mt-0.5">
                  Page {previewData.page} of {previewData.total_pages} &bull; {previewData.total_records} Total Rows
                </p>
              </div>
              <button
                onClick={() => setShowPreviewModal(false)}
                className="text-[#A69A87] hover:text-[#F4EBDD] p-1.5 rounded hover:bg-white/5 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Table Area */}
            <div className="overflow-x-auto overflow-y-auto flex-1 p-4">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-[#A69A87] font-mono text-[11px]">
                    <th className="p-2.5"># Row</th>
                    {previewData.columns.map((c) => (
                      <th key={c} className="p-2.5 whitespace-nowrap">{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {previewData.rows.map((r) => (
                    <tr key={r.row_id} className="hover:bg-white/[0.02]">
                      <td className="p-2.5 font-mono text-[#F0AE2C]">{r.row_id}</td>
                      {previewData.columns.map((c) => (
                        <td key={c} className="p-2.5 whitespace-nowrap text-[#F4EBDD]/90 font-mono text-[11px]">
                          {r.data[c] !== null && r.data[c] !== undefined ? String(r.data[c]) : "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Modal Footer Controls */}
            <div className="p-4 border-t border-white/10 flex items-center justify-between bg-[#050505]">
              <span className="text-xs text-[#A69A87]">
                Showing rows {(previewData.page - 1) * previewData.page_size + 1} &ndash;{" "}
                {Math.min(previewData.page * previewData.page_size, previewData.total_records)}
              </span>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={previewData.page <= 1}
                  onClick={() => loadPreview(previewData.page - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={previewData.page >= previewData.total_pages}
                  onClick={() => loadPreview(previewData.page + 1)}
                >
                  Next
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowPreviewModal(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
