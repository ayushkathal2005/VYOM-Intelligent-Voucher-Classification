"use client";

import React, { useState, useEffect } from "react";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  gemini_configured: boolean;
  gemini_model: string;
}

const VOUCHER_CATEGORIES = [
  {
    family: "Commercial",
    classes: [
      "Purchase",
      "Sales",
      "Purchase Return / Debit Note",
      "Sales Return / Credit Note",
      "Purchase Order",
      "Sales Order",
    ],
  },
  {
    family: "Money Movement",
    classes: ["Payment", "Receipt", "Contra", "Advance / Prepayment"],
  },
  {
    family: "Inventory & Logistics",
    classes: [
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
    ],
  },
  {
    family: "Adjustment & Admin",
    classes: ["Journal", "Expense", "Other / Miscellaneous"],
  },
  {
    family: "Special Trade & Payroll",
    classes: ["Salary / Payroll", "Attendance", "Import", "Export"],
  },
];

const INTELLIGENCE_LAYERS = [
  {
    step: "01",
    title: "Data Understanding & Ingestion",
    desc: "Ingests XLSX and CSV transaction files without fixed column orders. Standardizes aliases, detects datatypes, and preserves original row identifiers.",
  },
  {
    step: "02",
    title: "Accounting Signal Extraction",
    desc: "Extracts fundamental financial vectors: money-flow direction, supplier vs. customer counterparty roles, return indicators, and order lifecycle states.",
  },
  {
    step: "03",
    title: "Semantic Candidate Retrieval",
    desc: "Grounds unstructured item narrations and remarks via BGE-M3 semantic retrieval against 27 comprehensive voucher knowledge cards.",
  },
  {
    step: "04",
    title: "Gemma 4 Contextual Reasoning",
    desc: "Evaluates the entire transaction picture via Gemma 4 on the official Gemini API, synthesizing accounting signals rather than matching isolated keywords.",
  },
  {
    step: "05",
    title: "Reliability & Review Guardrails",
    desc: "Validates output schemas strictly with Pydantic, evaluates confidence margins, and flags ambiguous records for second-pass review.",
  },
];

export function ProductIntroSection() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/health", {
        headers: { Accept: "application/json" },
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data: HealthStatus = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Backend unreachable";
      setError(message);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isCurrent = true;
    const initialCheck = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/health", {
          headers: { Accept: "application/json" },
        });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data: HealthStatus = await res.json();
        if (isCurrent) {
          setHealth(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (isCurrent) {
          const message = err instanceof Error ? err.message : "Backend unreachable";
          setError(message);
          setHealth(null);
        }
      }
    };

    initialCheck();

    return () => {
      isCurrent = false;
    };
  }, []);

  return (
    <div className="space-y-28 py-20">
      {/* Section 1: Overview & Pipeline */}
      <section id="overview" className="max-w-7xl mx-auto px-6 sm:px-8">
        <div className="border border-[rgba(191,145,51,0.16)] bg-[#0B0805] rounded-xl p-8 sm:p-12 relative overflow-hidden">
          <div className="max-w-3xl space-y-6">
            <Badge variant="gold">System Workflow</Badge>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#F4EBDD] leading-tight">
              An AI-First Financial Classification Pipeline
            </h2>
            <p className="text-base text-[#A69A87] leading-relaxed">
              In modern enterprise workflows, transaction records are received
              as structured spreadsheets missing explicit voucher categories.
              VYOM+ replaces error-prone keyword heuristics with a multi-layered
              reasoning architecture designed for financial auditability and
              zero hallucinations.
            </p>
          </div>

          {/* Workflow Steps */}
          <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: "1. Upload & Inspect",
                desc: "Drop .xlsx or .csv files with automatic column schema mapping.",
              },
              {
                title: "2. Signal Extraction",
                desc: "Identify counterparty roles, money flow, and document stages.",
              },
              {
                title: "3. Gemma 4 Reasoning",
                desc: "Synthesize full context using Gemma 4 via the official Gemini API.",
              },
              {
                title: "4. Verify & Export",
                desc: "Inspect confidence, resolve low-margin cases, and export validated data.",
              },
            ].map((card, idx) => (
              <div
                key={idx}
                className="p-5 rounded-lg bg-[#11100E] border border-[rgba(191,145,51,0.15)] flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <span className="text-xs font-mono font-semibold text-[#F0AE2C]">
                    STEP {idx + 1}
                  </span>
                  <h3 className="font-serif text-lg font-semibold text-[#F4EBDD]">
                    {card.title}
                  </h3>
                  <p className="text-xs text-[#A69A87] leading-relaxed">
                    {card.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 2: Architecture Layers */}
      <section id="architecture" className="max-w-7xl mx-auto px-6 sm:px-8">
        <div className="space-y-8">
          <div className="max-w-2xl space-y-3">
            <Badge variant="subtle">Deep Architecture</Badge>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#F4EBDD]">
              Five Intelligence Layers
            </h2>
            <p className="text-sm text-[#A69A87]">
              Every transaction record is evaluated systematically across five
              deterministic and cognitive layers before emitting a final
              prediction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {INTELLIGENCE_LAYERS.map((layer) => (
              <div
                key={layer.step}
                className="p-6 rounded-lg bg-[#0B0805] border border-[rgba(191,145,51,0.16)] flex flex-col justify-between hover:border-[#F0AE2C]/40 transition-colors"
              >
                <div className="space-y-4">
                  <span className="text-2xl font-serif font-bold text-[#F0AE2C]">
                    {layer.step}
                  </span>
                  <h3 className="text-sm font-semibold text-[#F4EBDD] tracking-wide">
                    {layer.title}
                  </h3>
                  <p className="text-xs text-[#A69A87] leading-relaxed">
                    {layer.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 3: 27 Authoritative Voucher Categories */}
      <section id="labels" className="max-w-7xl mx-auto px-6 sm:px-8">
        <div className="border border-[rgba(191,145,51,0.16)] bg-[#0B0805] rounded-xl p-8 sm:p-12 space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="space-y-2 max-w-2xl">
              <Badge variant="gold">Domain Taxonomy</Badge>
              <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#F4EBDD]">
                27 Authoritative Voucher Categories
              </h2>
              <p className="text-sm text-[#A69A87]">
                The classifier is strictly constrained to the 27 official accounting
                voucher categories. Categories are organized into five commercial
                families for zero-ambiguity reasoning.
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs font-mono uppercase text-[#A69A87]">
                Total Classes
              </span>
              <span className="block font-serif text-3xl font-bold text-[#F0AE2C]">
                27
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-4">
            {VOUCHER_CATEGORIES.map((fam) => (
              <div
                key={fam.family}
                className="p-6 rounded-lg bg-[#11100E] border border-[rgba(191,145,51,0.15)] space-y-4"
              >
                <div className="flex items-center justify-between border-b border-[rgba(191,145,51,0.15)] pb-3">
                  <h3 className="font-serif text-base font-semibold text-[#F4EBDD]">
                    {fam.family}
                  </h3>
                  <span className="text-[11px] font-mono text-[#A69A87]">
                    {fam.classes.length} classes
                  </span>
                </div>
                <ul className="space-y-2">
                  {fam.classes.map((cls) => (
                    <li
                      key={cls}
                      className="text-xs text-[#A69A87] flex items-center gap-2"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C]/60" />
                      <span className="hover:text-[#F4EBDD] transition-colors">
                        {cls}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 4: Live System Status & Connection */}
      <section id="status" className="max-w-7xl mx-auto px-6 sm:px-8">
        <div className="p-8 rounded-xl bg-[#0B0805] border border-[rgba(191,145,51,0.2)] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  health ? "bg-emerald-400" : "bg-amber-400 animate-pulse"
                }`}
              />
              <span className="text-xs uppercase tracking-widest font-semibold text-[#F4EBDD]">
                Backend Health Status
              </span>
            </div>
            <p className="text-xs text-[#A69A87] leading-relaxed">
              FastAPI backend running locally at{" "}
              <code className="text-[#F4EBDD] font-mono">http://127.0.0.1:8000</code>
              . When Gemini API key is configured, live Gemma 4 inference is
              unlocked.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            {health ? (
              <div className="px-4 py-2 rounded bg-[#11100E] border border-[rgba(191,145,51,0.2)] text-left">
                <span className="block text-[10px] uppercase font-mono text-[#A69A87]">
                  Backend API: {health.status} ({health.app} v{health.version})
                </span>
                <span className="block text-xs font-mono text-[#F0AE2C]">
                  Model: {health.gemini_model} &bull; Key:{" "}
                  {health.gemini_configured ? "Configured" : "Mock Ready"}
                </span>
              </div>
            ) : error ? (
              <div className="px-4 py-2 rounded bg-red-950/30 border border-red-500/30 text-left">
                <span className="block text-xs text-red-400 font-mono">
                  {error}
                </span>
                <span className="text-[10px] text-red-300/70">
                  Run: uvicorn app.main:app
                </span>
              </div>
            ) : null}

            <Button
              variant="outline"
              size="sm"
              onClick={fetchHealth}
              isLoading={loading}
              id="btn-refresh-health"
            >
              Recheck Health
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
