"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  api,
  PaginatedPredictionsResponse,
  PredictionRecordResponse,
} from "@/lib/api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

const AUTHORITATIVE_CATEGORIES = [
  "Purchase",
  "Sales",
  "Purchase Return / Debit Note",
  "Sales Return / Credit Note",
  "Payment",
  "Receipt",
  "Contra",
  "Journal",
  "Salary / Payroll",
  "Attendance",
  "Purchase Order",
  "Sales Order",
  "Receipt Note",
  "Delivery Note",
  "Rejection In",
  "Rejection Out",
  "Stock Journal",
  "Physical Stock",
  "Material In",
  "Material Out",
  "Job Work In Order",
  "Job Work Out Order",
  "Import",
  "Export",
  "Expense",
  "Advance / Prepayment",
  "Other / Miscellaneous",
];

interface ReviewQueueTableProps {
  datasetId: string | null;
  onInspectVoucher: (rowId: number) => void;
  onOverrideVoucher: (rowId: number) => void;
  refreshTrigger: number;
}

export function ReviewQueueTable({
  datasetId,
  onInspectVoucher,
  onOverrideVoucher,
  refreshTrigger,
}: ReviewQueueTableProps) {
  const [data, setData] = useState<PaginatedPredictionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filters state
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);
  const [triageFilter, setTriageFilter] = useState<string>("ALL");
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchPredictions = useCallback(async () => {
    if (!datasetId) return;
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.getPredictions(datasetId, {
        page,
        pageSize,
        triageDecision: triageFilter,
        confidenceTier: tierFilter,
        category: categoryFilter,
        search: searchQuery,
      });
      setData(res);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load prediction records.");
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, page, pageSize, triageFilter, tierFilter, categoryFilter, searchQuery]);

  // Refetch on filter changes or external refresh trigger
  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions, refreshTrigger]);

  if (!datasetId) {
    return (
      <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-10 text-center">
        <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
          Audit Review Queue Ready
        </h3>
        <p className="text-xs text-[#A69A87] mt-1 max-w-md mx-auto">
          Upload an accounting dataset and execute batch classification to activate the multi-dimensional audit triage table.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6 lg:p-8 relative overflow-hidden shadow-2xl space-y-6">
      {/* Background ambient subtle accent */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-[#F0AE2C]/[0.02] rounded-full blur-3xl pointer-events-none" />

      {/* Header & Triage Tabs */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-[rgba(191,145,51,0.15)]">
        <div>
          <div className="inline-flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#F0AE2C]" />
            <span className="text-[10px] uppercase tracking-[0.25em] font-semibold text-[#A69A87]">
              Step 3: Multi-Dimensional Audit & Review Triage
            </span>
          </div>
          <h2 className="font-serif text-2xl font-bold text-[#F4EBDD] tracking-tight">
            Voucher Classification Review Queue
          </h2>
          <p className="text-xs text-[#A69A87] mt-1">
            Filter, inspect signals, verify confidence scores, and apply authoritative human overrides.
          </p>
        </div>

        {/* Triage Status Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 bg-[#050505] p-1.5 rounded-lg border border-[rgba(191,145,51,0.2)]">
          <button
            onClick={() => {
              setTriageFilter("ALL");
              setPage(1);
            }}
            className={`px-3 py-1 rounded text-xs font-semibold uppercase tracking-wider transition-all ${
              triageFilter === "ALL"
                ? "bg-[#F0AE2C] text-[#050505]"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
          >
            All
          </button>
          <button
            onClick={() => {
              setTriageFilter("AUTO_VERIFIED");
              setPage(1);
            }}
            className={`px-3 py-1 rounded text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
              triageFilter === "AUTO_VERIFIED"
                ? "bg-emerald-500 text-black"
                : "text-emerald-400/80 hover:text-emerald-300"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Auto-Verified
          </button>
          <button
            onClick={() => {
              setTriageFilter("FLAGGED_FOR_REVIEW");
              setPage(1);
            }}
            className={`px-3 py-1 rounded text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
              triageFilter === "FLAGGED_FOR_REVIEW"
                ? "bg-amber-500 text-black"
                : "text-amber-400/80 hover:text-amber-300"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Review Queue
          </button>
          <button
            onClick={() => {
              setTriageFilter("CRITICAL_REJECTION");
              setPage(1);
            }}
            className={`px-3 py-1 rounded text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
              triageFilter === "CRITICAL_REJECTION"
                ? "bg-red-500 text-white"
                : "text-red-400/80 hover:text-red-300"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            Critical Rejection
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3 items-center">
        {/* Search */}
        <div className="lg:col-span-4 relative">
          <input
            type="text"
            placeholder="Search Doc #, Vendor, Buyer, Reasoning..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            className="w-full px-3.5 py-2 pl-9 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] placeholder-[#A69A87]/50 focus:border-[#F0AE2C] focus:outline-none"
          />
          <svg
            className="w-4 h-4 text-[#A69A87] absolute left-2.5 top-2.5 pointer-events-none"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {/* Confidence Tier Filter */}
        <div className="lg:col-span-3">
          <select
            value={tierFilter}
            onChange={(e) => {
              setTierFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
          >
            <option value="ALL">All Confidence Tiers</option>
            <option value="HIGH">HIGH (&#8805; 85%)</option>
            <option value="MEDIUM">MEDIUM (65% - 84%)</option>
            <option value="LOW">LOW (&lt; 65%)</option>
          </select>
        </div>

        {/* Category Filter */}
        <div className="lg:col-span-3">
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
          >
            <option value="ALL">All 27 Categories</option>
            {AUTHORITATIVE_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Page Size Selector */}
        <div className="lg:col-span-2 flex items-center justify-end gap-2">
          <span className="text-xs text-[#A69A87] whitespace-nowrap">Page size:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="px-2.5 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
          >
            <option value={10}>10</option>
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="overflow-x-auto rounded border border-white/5 bg-[#050505]/70">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-white/10 text-[#A69A87] font-mono text-[11px] bg-black/40">
              <th className="p-3">#</th>
              <th className="p-3">Document / Ref</th>
              <th className="p-3">Counterparty</th>
              <th className="p-3">Amount</th>
              <th className="p-3">Predicted Category</th>
              <th className="p-3">Confidence</th>
              <th className="p-3">Triage Decision</th>
              <th className="p-3">Contradictions</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {isLoading ? (
              <tr>
                <td colSpan={9} className="p-8 text-center text-[#A69A87]">
                  Loading predictions...
                </td>
              </tr>
            ) : !data || data.predictions.length === 0 ? (
              <tr>
                <td colSpan={9} className="p-8 text-center text-[#A69A87]">
                  No matching voucher records found.
                </td>
              </tr>
            ) : (
              data.predictions.map((row) => {
                const confPercent = Math.round(row.confidence * 100);

                let triageBadgeStyle = "bg-neutral-800 text-neutral-300 border-neutral-700";
                if (row.triage_decision === "AUTO_VERIFIED") {
                  triageBadgeStyle = "bg-emerald-950/60 text-emerald-400 border-emerald-500/40";
                } else if (row.triage_decision === "FLAGGED_FOR_REVIEW") {
                  triageBadgeStyle = "bg-amber-950/60 text-amber-400 border-amber-500/40";
                } else if (row.triage_decision === "CRITICAL_REJECTION") {
                  triageBadgeStyle = "bg-red-950/60 text-red-400 border-red-500/40";
                }

                let tierColor = "text-emerald-400";
                if (row.confidence_tier === "MEDIUM") tierColor = "text-amber-400";
                if (row.confidence_tier === "LOW") tierColor = "text-red-400";

                return (
                  <tr
                    key={row.row_id}
                    className="hover:bg-white/[0.02] transition-colors group cursor-pointer"
                    onClick={() => onInspectVoucher(row.row_id)}
                  >
                    {/* Row ID */}
                    <td className="p-3 font-mono text-[#F0AE2C]">
                      {row.row_id}
                    </td>

                    {/* Doc No & Date */}
                    <td className="p-3">
                      <div className="font-medium text-[#F4EBDD]">
                        {row.doc_no || <span className="text-[#A69A87]/50 font-mono">N/A</span>}
                      </div>
                      {row.invoice_date && (
                        <div className="text-[10px] text-[#A69A87] font-mono">
                          {row.invoice_date}
                        </div>
                      )}
                    </td>

                    {/* Counterparty */}
                    <td className="p-3 text-[#F4EBDD]/90 max-w-[180px] truncate">
                      {row.seller_supplier || row.buyer_customer || (
                        <span className="text-[#A69A87]/50 italic">Internal / Unspecified</span>
                      )}
                    </td>

                    {/* Amount */}
                    <td className="p-3 font-mono text-[#F4EBDD]">
                      {row.total_amount !== null && row.total_amount !== undefined
                        ? `₹ ${Number(row.total_amount).toLocaleString("en-IN", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}`
                        : "-"}
                    </td>

                    {/* Category & Override Pill */}
                    <td className="p-3">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-[#F0AE2C]">
                          {row.predicted_category}
                        </span>
                        {row.is_overridden && (
                          <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#F0AE2C]/20 border border-[#F0AE2C]/40 text-[#F0AE2C]">
                            OVERRIDDEN
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Confidence Meter */}
                    <td className="p-3">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between font-mono text-[11px]">
                          <span className={tierColor}>{confPercent}%</span>
                          <span className="text-[9px] uppercase text-[#A69A87]">
                            {row.confidence_tier}
                          </span>
                        </div>
                        <div className="w-20 h-1.5 bg-[#11100E] rounded-full overflow-hidden border border-white/5">
                          <div
                            className={`h-full rounded-full ${
                              row.confidence_tier === "HIGH"
                                ? "bg-emerald-400"
                                : row.confidence_tier === "MEDIUM"
                                ? "bg-amber-400"
                                : "bg-red-400"
                            }`}
                            style={{ width: `${confPercent}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Triage Decision */}
                    <td className="p-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border ${triageBadgeStyle}`}
                      >
                        {row.triage_decision.replace(/_/g, " ")}
                      </span>
                    </td>

                    {/* Contradictions */}
                    <td className="p-3">
                      {row.contradictions_count > 0 ? (
                        <span className="inline-flex items-center gap-1 text-red-400 text-xs font-semibold">
                          <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          <span>{row.contradictions_count} violation(s)</span>
                        </span>
                      ) : (
                        <span className="text-emerald-400/80 text-[11px]">&ndash;</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="p-3 text-right">
                      <div
                        className="inline-flex items-center gap-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => onInspectVoucher(row.row_id)}
                          className="px-2.5 py-1 text-[11px] uppercase font-semibold text-[#A69A87] hover:text-[#F4EBDD] bg-white/5 hover:bg-white/10 rounded transition-colors"
                          title="Inspect deep audit trail & signals"
                        >
                          Inspect
                        </button>
                        <button
                          onClick={() => onOverrideVoucher(row.row_id)}
                          className="px-2.5 py-1 text-[11px] uppercase font-semibold text-[#F0AE2C] hover:text-white bg-[#F0AE2C]/10 hover:bg-[#F0AE2C]/20 border border-[#F0AE2C]/30 rounded transition-colors"
                          title="Apply authoritative human auditor override"
                        >
                          Override
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {data && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-white/5">
          <span className="text-xs text-[#A69A87] font-mono">
            Showing {data.filtered_records} filtered records ({data.total_records} total in dataset) &bull; Page {data.page} of {data.total_pages}
          </span>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={data.page <= 1}
              onClick={() => setPage(data.page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={data.page >= data.total_pages}
              onClick={() => setPage(data.page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="p-3 rounded bg-red-950/40 border border-red-500/50 flex items-center gap-2 text-xs text-red-200">
          <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
