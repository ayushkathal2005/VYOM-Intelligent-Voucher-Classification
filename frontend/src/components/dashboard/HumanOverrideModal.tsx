"use client";

import React, { useState } from "react";
import { api, HumanOverrideResponse } from "@/lib/api";
import { Button } from "../ui/Button";

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

interface HumanOverrideModalProps {
  datasetId: string;
  rowId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onOverrideApplied: (response: HumanOverrideResponse) => void;
}

export function HumanOverrideModal({
  datasetId,
  rowId,
  isOpen,
  onClose,
  onOverrideApplied,
}: HumanOverrideModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("Payment");
  const [overrideReason, setOverrideReason] = useState<string>("");
  const [reviewerId, setReviewerId] = useState<string>("senior-auditor-1");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || rowId === null) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideReason.trim()) {
      setError("Please provide an audit justification reason for overriding this classification.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await api.overridePrediction(datasetId, rowId, {
        overridden_category: selectedCategory,
        override_reason: overrideReason.trim(),
        reviewer_id: reviewerId.trim() || "auditor-1",
      });
      onOverrideApplied(result);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to submit human override.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
      <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.3)] rounded-lg w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#050505]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-[#11100E] border border-[#F0AE2C]/30 flex items-center justify-center text-[#F0AE2C]">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <div>
              <h3 className="font-serif text-base font-bold text-[#F4EBDD]">
                Apply Authoritative Human Override
              </h3>
              <p className="text-xs text-[#A69A87] font-mono">
                Overriding Transaction Row #{rowId}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-[#A69A87] hover:text-[#F4EBDD] p-1.5 rounded hover:bg-white/5 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Target Category Select */}
          <div className="space-y-1.5">
            <label className="text-xs uppercase tracking-wider font-semibold text-[#A69A87]">
              Select Correct Accounting Category (27 Authoritative Classes)
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#11100E] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
              id="select-override-category"
            >
              {AUTHORITATIVE_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Audit Reviewer ID */}
          <div className="space-y-1.5">
            <label className="text-xs uppercase tracking-wider font-semibold text-[#A69A87]">
              Reviewer / Auditor Identifier
            </label>
            <input
              type="text"
              value={reviewerId}
              onChange={(e) => setReviewerId(e.target.value)}
              placeholder="e.g. senior-auditor-1"
              className="w-full px-3.5 py-2.5 bg-[#11100E] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
              id="input-reviewer-id"
            />
          </div>

          {/* Justification Reason */}
          <div className="space-y-1.5">
            <label className="text-xs uppercase tracking-wider font-semibold text-[#A69A87]">
              Override Justification Reason (Required for Audit Trail)
            </label>
            <textarea
              rows={3}
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="e.g. Counterparty is an external supplier with tax invoice details; reclassified from Contra to Payment."
              className="w-full px-3.5 py-2.5 bg-[#11100E] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] placeholder-[#A69A87]/50 focus:border-[#F0AE2C] focus:outline-none resize-none"
              id="textarea-override-reason"
            />
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded bg-red-950/40 border border-red-500/50 text-red-200 text-xs">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              size="sm"
              isLoading={isSubmitting}
              id="btn-confirm-override"
            >
              Confirm Override &amp; Verify
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
