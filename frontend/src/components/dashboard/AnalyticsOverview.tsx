"use client";

import React from "react";
import { DatasetAnalyticsResponse } from "@/lib/api";

interface AnalyticsOverviewProps {
  analytics: DatasetAnalyticsResponse | null;
  isLoading: boolean;
}

/**
 * Safely format a percentage KPI from authoritative percent and count values.
 * - Displays "0%" when metric is genuinely zero.
 * - Displays "N/A" when value cannot be calculated (denominator missing, 0, or invalid).
 * - Never converts an API error into zero.
 */
function formatKpiPercentage(
  percentValue: number | null | undefined,
  countValue: number | null | undefined,
  totalTransactions: number | null | undefined
): string {
  if (
    totalTransactions === undefined ||
    totalTransactions === null ||
    totalTransactions <= 0 ||
    isNaN(totalTransactions)
  ) {
    return "N/A";
  }

  if (percentValue !== undefined && percentValue !== null && !isNaN(percentValue)) {
    return percentValue === 0 ? "0%" : `${percentValue}%`;
  }

  if (countValue !== undefined && countValue !== null && !isNaN(countValue)) {
    if (countValue === 0) return "0%";
    const calc = Math.round((countValue / totalTransactions) * 1000) / 10;
    return `${calc}%`;
  }

  return "N/A";
}

/**
 * Safely format row count display.
 * - Displays "X rows" when count is a valid number (including 0).
 * - Displays "N/A rows" when count is undefined/null/NaN.
 */
function formatKpiRowCount(count: number | null | undefined, unit: string = "rows"): string {
  if (count === null || count === undefined || isNaN(count)) {
    return `N/A ${unit}`;
  }
  return `${count} ${unit}`;
}

export function AnalyticsOverview({ analytics, isLoading }: AnalyticsOverviewProps) {
  if (isLoading) {
    return (
      <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-8 animate-pulse text-center">
        <p className="text-sm text-[#A69A87]">Calculating distribution analytics & audit metrics...</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="w-full bg-[#0B0805] border border-[rgba(191,145,51,0.15)] rounded-lg p-8 text-center">
        <p className="text-sm text-[#A69A87]">
          Execute batch classification to view financial distribution intelligence and triage metrics.
        </p>
      </div>
    );
  }

  const sortedCategories = Object.entries(analytics.category_distribution || {}).sort(
    (a, b) => b[1] - a[1]
  );

  const topCategoryCount = sortedCategories.length > 0 ? sortedCategories[0][1] : 1;
  const contradictionRecords = analytics.contradiction_breakdown || analytics.contradiction_counts || {};

  return (
    <div className="w-full space-y-6">
      {/* 5 Core Audit KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* KPI 1: Total Transactions */}
        <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-5 relative overflow-hidden">
          <span className="text-[10px] uppercase tracking-widest text-[#A69A87] font-semibold block">
            Total Transactions
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-serif text-3xl font-bold text-[#F4EBDD]">
              {analytics.total_transactions ?? 0}
            </span>
            <span className="text-xs text-[#A69A87] font-mono">
              ({analytics.processed_transactions ?? analytics.total_transactions ?? 0} processed)
            </span>
          </div>
          <div className="mt-3 text-[11px] text-[#A69A87] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C]" />
            <span>Ingested & Parsed</span>
          </div>
        </div>

        {/* KPI 2: Auto-Verified */}
        <div className="bg-[#0B0805] border border-emerald-500/20 rounded-lg p-5 relative overflow-hidden shadow-sm shadow-emerald-500/5">
          <span className="text-[10px] uppercase tracking-widest text-emerald-400 font-semibold block">
            Auto-Verified Rate
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-serif text-3xl font-bold text-emerald-400">
              {formatKpiPercentage(
                analytics.auto_verified_percentage,
                analytics.auto_verified_count,
                analytics.total_transactions
              )}
            </span>
            <span className="text-xs text-emerald-300/80 font-mono">
              ({formatKpiRowCount(analytics.auto_verified_count)})
            </span>
          </div>
          <div className="mt-3 text-[11px] text-emerald-400/90 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>High Confidence &bull; No Contradictions</span>
          </div>
        </div>

        {/* KPI 3: Review Queue */}
        <div className="bg-[#0B0805] border border-amber-500/20 rounded-lg p-5 relative overflow-hidden shadow-sm shadow-amber-500/5">
          <span className="text-[10px] uppercase tracking-widest text-amber-400 font-semibold block">
            Review Queue
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-serif text-3xl font-bold text-amber-400">
              {formatKpiPercentage(
                analytics.flagged_percentage ?? analytics.review_queue_percentage,
                analytics.flagged_for_review_count,
                analytics.total_transactions
              )}
            </span>
            <span className="text-xs text-amber-300/80 font-mono">
              ({formatKpiRowCount(analytics.flagged_for_review_count)})
            </span>
          </div>
          <div className="mt-3 text-[11px] text-amber-400/90 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span>Auditor Verification Needed</span>
          </div>
        </div>

        {/* KPI 4: Critical Rejections */}
        <div className="bg-[#0B0805] border border-red-500/20 rounded-lg p-5 relative overflow-hidden shadow-sm shadow-red-500/5">
          <span className="text-[10px] uppercase tracking-widest text-red-400 font-semibold block">
            Critical Rejection
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-serif text-3xl font-bold text-red-400">
              {formatKpiPercentage(
                analytics.critical_rejection_percentage,
                analytics.critical_rejection_count,
                analytics.total_transactions
              )}
            </span>
            <span className="text-xs text-red-300/80 font-mono">
              ({formatKpiRowCount(analytics.critical_rejection_count)})
            </span>
          </div>
          <div className="mt-3 text-[11px] text-red-400/90 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            <span>Contradiction Violations</span>
          </div>
        </div>

        {/* KPI 5: Mean Calibrated Confidence */}
        <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-5 relative overflow-hidden">
          <span className="text-[10px] uppercase tracking-widest text-[#F0AE2C] font-semibold block">
            Mean Calibrated Confidence
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-serif text-3xl font-bold text-[#F4EBDD]">
              {analytics.average_confidence !== undefined &&
              analytics.average_confidence !== null &&
              !isNaN(analytics.average_confidence)
                ? `${(analytics.average_confidence * 100).toFixed(1)}%`
                : "N/A"}
            </span>
            <span className="text-xs text-[#A69A87] font-mono">
              / 100.0%
            </span>
          </div>
          <div className="mt-3 text-[11px] text-[#A69A87] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F0AE2C]" />
            <span>
              {formatKpiRowCount(
                analytics.overridden_count ?? analytics.human_override_count ?? 0,
                "Overrides Applied"
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Category Frequency Breakdown & Tier/Contradiction Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Category Distribution Bars */}
        <div className="lg:col-span-7 bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6">
          <div className="flex items-center justify-between pb-4 border-b border-white/5">
            <h3 className="font-serif text-base font-semibold text-[#F4EBDD]">
              Predicted Voucher Categories ({sortedCategories.length} active)
            </h3>
            <span className="text-[11px] text-[#A69A87] font-mono uppercase">
              Distribution Count & %
            </span>
          </div>

          <div className="mt-4 space-y-2.5 max-h-72 overflow-y-auto pr-2">
            {sortedCategories.map(([category, count]) => {
              const pct = ((count / Math.max(analytics.total_transactions, 1)) * 100).toFixed(1);
              const barWidth = Math.max(5, (count / Math.max(topCategoryCount, 1)) * 100);

              return (
                <div key={category} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#F4EBDD] font-medium truncate max-w-[280px]">
                      {category}
                    </span>
                    <span className="text-[#A69A87] font-mono">
                      {count} <span className="text-[#A69A87]/60">({pct}%)</span>
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-[#11100E] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#9D7019] to-[#F0AE2C] rounded-full transition-all duration-300"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Confidence Tiers & Accounting Contradictions */}
        <div className="lg:col-span-5 space-y-6">
          {/* Confidence Tiers */}
          <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6">
            <h3 className="font-serif text-base font-semibold text-[#F4EBDD] pb-3 border-b border-white/5">
              Confidence Tier Distribution
            </h3>
            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="p-3 bg-[#11100E] rounded border border-emerald-500/20 text-center">
                <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold block">
                  HIGH (&#8805;85%)
                </span>
                <span className="font-serif text-xl font-bold text-emerald-400 block mt-1">
                  {analytics.confidence_tier_distribution?.HIGH || 0}
                </span>
              </div>

              <div className="p-3 bg-[#11100E] rounded border border-amber-500/20 text-center">
                <span className="text-[10px] uppercase tracking-wider text-amber-400 font-semibold block">
                  MED (65-84%)
                </span>
                <span className="font-serif text-xl font-bold text-amber-400 block mt-1">
                  {analytics.confidence_tier_distribution?.MEDIUM || 0}
                </span>
              </div>

              <div className="p-3 bg-[#11100E] rounded border border-red-500/20 text-center">
                <span className="text-[10px] uppercase tracking-wider text-red-400 font-semibold block">
                  LOW (&lt;65%)
                </span>
                <span className="font-serif text-xl font-bold text-red-400 block mt-1">
                  {analytics.confidence_tier_distribution?.LOW || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Contradiction Breakdown */}
          <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.2)] rounded-lg p-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <h3 className="font-serif text-base font-semibold text-[#F4EBDD]">
                Contradictions Detected
              </h3>
              <span className="text-xs font-mono text-[#F0AE2C]">
                {Object.values(contradictionRecords).reduce((a, b) => a + b, 0)} Total
              </span>
            </div>

            <div className="mt-3 space-y-2 max-h-36 overflow-y-auto pr-1">
              {Object.keys(contradictionRecords).length === 0 ? (
                <p className="text-xs text-emerald-400 py-2">
                  No structural accounting contradictions triggered.
                </p>
              ) : (
                Object.entries(contradictionRecords).map(([rule, count]) => (
                  <div
                    key={rule}
                    className="flex items-center justify-between text-xs p-2 bg-[#11100E] rounded border border-white/5"
                  >
                    <span className="text-[#A69A87] font-mono text-[11px] truncate max-w-[220px]">
                      {rule}
                    </span>
                    <span className="text-[#F0AE2C] font-semibold font-mono">
                      {count}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
