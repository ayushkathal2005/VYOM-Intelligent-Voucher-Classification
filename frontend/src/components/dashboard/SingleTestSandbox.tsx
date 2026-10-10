"use client";

import React, { useState } from "react";
import { api, SingleClassifyRequest, SingleClassifyResponse } from "@/lib/api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

const PRESETS = [
  {
    name: "Clean Purchase Invoice",
    data: {
      doc_no: "INV-2026-901",
      invoice_date: "2026-03-15",
      seller_supplier: "Precision Steel Ltd",
      buyer_customer: "VYOM Manufacturing Corp",
      total_amount: 118000,
      taxable_value: 100000,
      gst: 18000,
      items_description: "Industrial steel sheets 10mm gauge for assembly",
      quantity: 50,
    },
  },
  {
    name: "Internal Bank Contra Transfer",
    data: {
      doc_no: "CONTRA-102",
      invoice_date: "2026-03-18",
      seller_supplier: "HDFC Current Account",
      buyer_customer: "SBI Escrow Account",
      total_amount: 500000,
      taxable_value: 0,
      gst: 0,
      items_description: "Inter-bank liquidity transfer from main operational account",
      quantity: 1,
    },
  },
  {
    name: "Sales Return / Credit Note",
    data: {
      doc_no: "CN-8841",
      invoice_date: "2026-03-20",
      seller_supplier: "Apex Distributors",
      buyer_customer: "Reliance Retail Hub",
      total_amount: -45000,
      taxable_value: -38135,
      gst: -6865,
      items_description: "Damaged electronics consignment returned from invoice INV-8800",
      quantity: -10,
    },
  },
  {
    name: "Procurement Purchase Order",
    data: {
      doc_no: "PO-2026-044",
      invoice_date: "2026-03-22",
      seller_supplier: "Global Microchip Fab",
      buyer_customer: "VYOM Tech Labs",
      total_amount: 850000,
      taxable_value: 720000,
      gst: 130000,
      items_description: "Procurement commitment for Q2 semiconductor controllers",
      quantity: 500,
    },
  },
  {
    name: "Contradiction Test: Contra with Vendor Tax",
    data: {
      doc_no: "TEST-CONTRA-ERR",
      invoice_date: "2026-03-25",
      seller_supplier: "Tata Consultancy Services",
      buyer_customer: "VYOM Tech Labs",
      total_amount: 59000,
      taxable_value: 50000,
      gst: 9000,
      items_description: "IT maintenance fee with statutory tax billed by external vendor",
      quantity: 1,
    },
  },
];

export function SingleTestSandbox() {
  const [formData, setFormData] = useState<SingleClassifyRequest>({
    ...PRESETS[0].data,
    use_mock: true,
  });
  const [result, setResult] = useState<SingleClassifyResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setFormData({
      ...preset.data,
      use_mock: formData.use_mock ?? true,
    });
    setResult(null);
    setError(null);
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await api.classifySingle(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to classify transaction.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6 lg:p-8 relative overflow-hidden shadow-2xl space-y-6">
      {/* Background ambient subtle accent */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-[#F0AE2C]/[0.02] rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[rgba(191,145,51,0.15)]">
        <div>
          <div className="inline-flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#F0AE2C]" />
            <span className="text-[10px] uppercase tracking-[0.25em] font-semibold text-[#A69A87]">
              Interactive AI Sandbox
            </span>
          </div>
          <h2 className="font-serif text-2xl font-bold text-[#F4EBDD] tracking-tight">
            Single Transaction Real-Time Classifier
          </h2>
          <p className="text-xs text-[#A69A87] mt-1">
            Test any transaction on demand. Evaluate signal extraction, candidate retrieval rankings, and guardrail arbitration in real-time.
          </p>
        </div>

        {/* Inference Mode Switcher */}
        <div className="flex items-center gap-1 bg-[#050505] p-1 rounded border border-[rgba(191,145,51,0.2)]">
          <button
            type="button"
            onClick={() => setFormData((prev) => ({ ...prev, mode: "fast" }))}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold uppercase tracking-wider transition-all ${
              (formData.mode ?? "fast") === "fast"
                ? "bg-[#F0AE2C] text-[#050505]"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
          >
            ⚡ Fast
          </button>
          <button
            type="button"
            onClick={() => setFormData((prev) => ({ ...prev, mode: "hybrid" }))}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold uppercase tracking-wider transition-all ${
              formData.mode === "hybrid"
                ? "bg-[#F0AE2C] text-[#050505]"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
          >
            ⚖️ Hybrid
          </button>
          <button
            type="button"
            onClick={() => setFormData((prev) => ({ ...prev, mode: "ai" }))}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold uppercase tracking-wider transition-all ${
              formData.mode === "ai"
                ? "bg-[#F0AE2C] text-[#050505]"
                : "text-[#A69A87] hover:text-[#F4EBDD]"
            }`}
          >
            🧠 AI (Gemma 4)
          </button>
        </div>
      </div>

      {/* Quick Test Presets */}
      <div className="space-y-2">
        <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
          Quick Demonstration Presets (Click to load):
        </span>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.name}
              type="button"
              onClick={() => applyPreset(preset)}
              className="px-3 py-1.5 rounded text-xs font-mono bg-[#11100E] border border-[rgba(191,145,51,0.2)] text-[#F4EBDD] hover:border-[#F0AE2C] hover:text-[#F0AE2C] transition-all"
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      {/* Form & Output Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Form Column */}
        <form onSubmit={handleRun} className="lg:col-span-7 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                Document / Invoice #
              </label>
              <input
                type="text"
                value={formData.doc_no || ""}
                onChange={(e) => setFormData({ ...formData, doc_no: e.target.value })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] font-mono focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                Invoice Date
              </label>
              <input
                type="date"
                value={formData.invoice_date || ""}
                onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] font-mono focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                Seller / Supplier
              </label>
              <input
                type="text"
                value={formData.seller_supplier || ""}
                onChange={(e) => setFormData({ ...formData, seller_supplier: e.target.value })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                Buyer / Customer
              </label>
              <input
                type="text"
                value={formData.buyer_customer || ""}
                onChange={(e) => setFormData({ ...formData, buyer_customer: e.target.value })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                Total Amount (₹)
              </label>
              <input
                type="number"
                step="any"
                value={formData.total_amount ?? ""}
                onChange={(e) => setFormData({ ...formData, total_amount: e.target.value ? Number(e.target.value) : undefined })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] font-mono focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                Taxable Value (₹)
              </label>
              <input
                type="number"
                step="any"
                value={formData.taxable_value ?? ""}
                onChange={(e) => setFormData({ ...formData, taxable_value: e.target.value ? Number(e.target.value) : undefined })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] font-mono focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
                GST (₹)
              </label>
              <input
                type="number"
                step="any"
                value={formData.gst ?? ""}
                onChange={(e) => setFormData({ ...formData, gst: e.target.value ? Number(e.target.value) : undefined })}
                className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] font-mono focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] uppercase tracking-wider text-[#A69A87] font-semibold">
              Items Description & Narration
            </label>
            <textarea
              rows={2}
              value={formData.items_description || ""}
              onChange={(e) => setFormData({ ...formData, items_description: e.target.value })}
              className="w-full px-3 py-2 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded text-xs text-[#F4EBDD] focus:border-[#F0AE2C] focus:outline-none resize-none"
            />
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              variant="gold"
              size="md"
              isLoading={isLoading}
              id="btn-sandbox-classify"
            >
              Classify Transaction Now
            </Button>
          </div>
        </form>

        {/* Output Column */}
        <div className="lg:col-span-5 bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded-lg p-5 min-h-[380px] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <h3 className="font-serif text-sm font-semibold text-[#F4EBDD]">
                Real-Time Inference Output
              </h3>
              {result && (
                <span className="text-[10px] text-[#A69A87] font-mono">
                  {result.result.latency_ms} ms &bull; {result.result.model_name}
                </span>
              )}
            </div>

            {error && (
              <div className="mt-4 p-3 rounded bg-red-950/40 border border-red-500/50 text-red-200 text-xs">
                {error}
              </div>
            )}

            {!result && !error && (
              <div className="p-12 text-center text-[#A69A87] text-xs">
                Select a preset or enter transaction details to test real-time classification.
              </div>
            )}

            {result && (
              <div className="mt-4 space-y-4">
                {/* Predicted Category Card */}
                <div className="p-4 rounded bg-[#11100E] border border-[#F0AE2C]/30 space-y-1">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    Predicted Voucher Category
                  </span>
                  <div className="text-xl font-serif font-bold text-[#F0AE2C]">
                    {result.result.prediction.category}
                  </div>
                  <div className="flex items-center gap-3 pt-2 text-xs font-mono">
                    <span className="text-[#F4EBDD]">
                      Confidence: <strong>{Math.round(result.evaluation.calibrated_confidence * 100)}%</strong>
                    </span>
                    <span className="text-[#A69A87]">
                      Tier: <strong>{result.evaluation.confidence_tier}</strong>
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        result.evaluation.triage_decision === "AUTO_VERIFIED"
                          ? "bg-emerald-950 text-emerald-400"
                          : result.evaluation.triage_decision === "FLAGGED_FOR_REVIEW"
                          ? "bg-amber-950 text-amber-400"
                          : "bg-red-950 text-red-400"
                      }`}
                    >
                      {result.evaluation.triage_decision.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>

                {/* Contradictions (if any) */}
                {result.evaluation.contradictions.length > 0 && (
                  <div className="p-3 rounded bg-red-950/40 border border-red-500/50 space-y-1 text-xs">
                    <span className="text-red-400 font-bold block uppercase tracking-wider text-[10px]">
                      {result.evaluation.contradictions.length} Contradiction Violations
                    </span>
                    {result.evaluation.contradictions.map((c, i) => (
                      <div key={i} className="text-red-200 text-[11px]">
                        &bull; <strong>{c.rule_name}</strong>: {c.description}
                      </div>
                    ))}
                  </div>
                )}

                {/* Reasoning */}
                <div className="p-3 rounded bg-[#11100E] border border-white/5 space-y-1 text-xs">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    AI Reasoning
                  </span>
                  <p className="text-[#F4EBDD] leading-relaxed">
                    {result.result.prediction.reasoning}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
