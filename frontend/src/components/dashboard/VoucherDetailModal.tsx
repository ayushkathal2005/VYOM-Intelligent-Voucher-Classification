"use client";

import React, { useState, useEffect } from "react";
import { api, PredictionDetailResponse } from "@/lib/api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface VoucherDetailModalProps {
  datasetId: string;
  rowId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onTriggerOverride: (rowId: number) => void;
}

export function VoucherDetailModal({
  datasetId,
  rowId,
  isOpen,
  onClose,
  onTriggerOverride,
}: VoucherDetailModalProps) {
  const [detail, setDetail] = useState<PredictionDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || rowId === null) {
      setDetail(null);
      return;
    }

    const loadDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getPredictionDetail(datasetId, rowId);
        setDetail(data);
      } catch (err: any) {
        setError(err.message || "Failed to load voucher detail.");
      } finally {
        setIsLoading(false);
      }
    };

    loadDetail();
  }, [isOpen, rowId, datasetId]);

  if (!isOpen || rowId === null) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.3)] rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-white/10 flex items-center justify-between bg-[#050505]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md bg-[#11100E] border border-[#F0AE2C]/30 flex items-center justify-center text-[#F0AE2C]">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
                  Voucher #{rowId} &bull; {detail?.doc_no || "No Document Number"}
                </h3>
                {detail?.is_overridden && (
                  <Badge variant="gold" size="sm">OVERRIDDEN</Badge>
                )}
              </div>
              <p className="text-xs text-[#A69A87] font-mono mt-0.5">
                Deep Accounting Signals & LLM Guardrails Inspection
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="text-[#A69A87] hover:text-[#F4EBDD] p-1.5 rounded hover:bg-white/5 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {isLoading ? (
            <div className="p-12 text-center text-[#A69A87]">
              Loading comprehensive voucher audit trail...
            </div>
          ) : error ? (
            <div className="p-4 rounded bg-red-950/40 border border-red-500/50 text-red-200 text-xs">
              {error}
            </div>
          ) : !detail ? (
            <div className="text-center text-[#A69A87]">No detail available.</div>
          ) : (
            <>
              {/* Classification Summary Bar */}
              <div className="p-4 rounded-lg bg-[#050505] border border-[rgba(191,145,51,0.25)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    Authoritative Category Classification
                  </span>
                  <div className="text-xl font-serif font-bold text-[#F0AE2C] mt-1 flex items-center gap-2">
                    <span>{detail.predicted_category}</span>
                    {detail.is_overridden && (
                      <span className="text-xs font-sans text-amber-300 font-normal">
                        (Overridden by auditor)
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                      Calibrated Confidence
                    </span>
                    <span className="font-mono text-base font-bold text-[#F4EBDD]">
                      {Math.round(detail.confidence * 100)}% ({detail.confidence_tier})
                    </span>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                      Triage Decision
                    </span>
                    <span
                      className={`inline-block text-[11px] uppercase font-bold px-2 py-0.5 rounded ${
                        detail.triage_decision === "AUTO_VERIFIED"
                          ? "text-emerald-400 bg-emerald-950/60"
                          : detail.triage_decision === "FLAGGED_FOR_REVIEW"
                          ? "text-amber-400 bg-amber-950/60"
                          : "text-red-400 bg-red-950/60"
                      }`}
                    >
                      {detail.triage_decision.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>
              </div>

              {/* Transaction Metadata & Financial Details */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-[#11100E] rounded border border-white/5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] block">Date</span>
                  <span className="font-mono text-xs text-[#F4EBDD] font-semibold mt-1 block">
                    {detail.invoice_date || "-"}
                  </span>
                </div>
                <div className="p-3 bg-[#11100E] rounded border border-white/5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] block">Seller / Supplier</span>
                  <span className="text-xs text-[#F4EBDD] font-medium mt-1 block truncate" title={detail.seller_supplier || ""}>
                    {detail.seller_supplier || "-"}
                  </span>
                </div>
                <div className="p-3 bg-[#11100E] rounded border border-white/5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] block">Buyer / Customer</span>
                  <span className="text-xs text-[#F4EBDD] font-medium mt-1 block truncate" title={detail.buyer_customer || ""}>
                    {detail.buyer_customer || "-"}
                  </span>
                </div>
                <div className="p-3 bg-[#11100E] rounded border border-white/5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] block">Total Amount</span>
                  <span className="font-mono text-xs text-[#F0AE2C] font-bold mt-1 block">
                    {detail.total_amount !== null && detail.total_amount !== undefined
                      ? `₹ ${Number(detail.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                      : "-"}
                  </span>
                </div>
              </div>

              {/* Line Items Description */}
              {detail.item_descriptions && detail.item_descriptions.length > 0 && (
                <div className="p-3.5 bg-[#11100E] rounded border border-white/5 space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    Items & Narration Description
                  </span>
                  <p className="text-xs text-[#F4EBDD]/90 font-mono leading-relaxed">
                    {detail.item_descriptions.join("; ")}
                  </p>
                </div>
              )}

              {/* Contradictions Detected Banner (if any) */}
              {detail.contradictions && detail.contradictions.length > 0 && (
                <div className="p-4 rounded bg-red-950/40 border border-red-500/50 space-y-2">
                  <div className="flex items-center gap-2 text-red-400 font-semibold text-xs uppercase tracking-wider">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>{detail.contradictions.length} Accounting Contradiction Violations Triggered</span>
                  </div>

                  <div className="space-y-2 mt-2">
                    {detail.contradictions.map((c, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-black/40 border border-red-500/30 text-xs">
                        <div className="flex items-center justify-between font-mono">
                          <span className="text-red-300 font-bold">{c.rule_name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/60 text-red-200">
                            {c.severity}
                          </span>
                        </div>
                        <p className="text-red-200/90 mt-1">{c.description}</p>
                        <p className="text-red-400/80 mt-1 italic">Suggested Action: {c.suggested_action}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Signals Observed */}
              {detail.detected_signals && detail.detected_signals.length > 0 && (
                <div className="p-3.5 bg-[#11100E] rounded border border-white/5 space-y-2">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    Accounting Signals Extracted
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.detected_signals.map((sig, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F0AE2C]/10 border border-[#F0AE2C]/30 text-[#F0AE2C]"
                      >
                        {sig}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Reasoning Chain */}
              <div className="p-3.5 bg-[#11100E] rounded border border-white/5 space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                  Model Reasoning & Grounding
                </span>
                <p className="text-xs text-[#F4EBDD] leading-relaxed whitespace-pre-wrap">
                  {detail.reasoning}
                </p>
              </div>

              {/* Auditor Override History (if overridden) */}
              {detail.is_overridden && (
                <div className="p-3.5 rounded bg-[#F0AE2C]/5 border border-[#F0AE2C]/30 space-y-1 text-xs">
                  <span className="text-[10px] uppercase tracking-wider text-[#F0AE2C] font-semibold block">
                    Auditor Reviewer Override Record
                  </span>
                  <div className="flex items-center justify-between text-[#F4EBDD]">
                    <span>Overridden Category: <strong className="text-[#F0AE2C]">{detail.overridden_category}</strong></span>
                    <span className="text-[#A69A87] font-mono">By: {detail.reviewer_id}</span>
                  </div>
                  <p className="text-[#A69A87] mt-1">Reason: &ldquo;{detail.override_reason}&rdquo;</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/10 flex items-center justify-between bg-[#050505]">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
          >
            Close
          </Button>

          <Button
            variant="gold"
            size="sm"
            onClick={() => onTriggerOverride(rowId)}
            id="btn-override-from-modal"
          >
            Override Classification
          </Button>
        </div>
      </div>
    </div>
  );
}
