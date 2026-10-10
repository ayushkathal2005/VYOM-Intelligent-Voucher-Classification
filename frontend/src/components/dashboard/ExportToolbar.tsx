"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "../ui/Button";

interface ExportToolbarProps {
  datasetId: string | null;
  filename?: string;
  totalRows?: number;
  isClassified?: boolean;
}

export function ExportToolbar({
  datasetId,
  filename,
  totalRows,
  isClassified,
}: ExportToolbarProps) {
  const [isExporting, setIsExporting] = useState<boolean>(false);

  if (!datasetId || !isClassified) return null;

  const handleDownload = (format: "xlsx" | "csv") => {
    setIsExporting(true);
    const downloadUrl = api.getExportUrl(datasetId, format);
    // Create an invisible link and trigger download
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", `VYOM_Audited_${filename || "dataset"}.${format}`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => setIsExporting(false), 1500);
  };

  return (
    <div className="w-full bg-[#050505] border border-[rgba(191,145,51,0.25)] rounded-lg p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-md bg-[#11100E] border border-[#F0AE2C]/30 flex items-center justify-center text-[#F0AE2C]">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h3 className="font-serif text-sm font-semibold text-[#F4EBDD]">
            Export Audited Dataset
          </h3>
          <p className="text-xs text-[#A69A87] font-mono">
            {totalRows} records &bull; Preserves raw columns + appends 8 <code className="text-[#F0AE2C]">VYOM_*</code> audit trail headers.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant="gold"
          size="sm"
          onClick={() => handleDownload("xlsx")}
          isLoading={isExporting}
          id="btn-export-xlsx"
        >
          Download Audited Excel (.xlsx)
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDownload("csv")}
          isLoading={isExporting}
          id="btn-export-csv"
        >
          Download CSV (.csv)
        </Button>
      </div>
    </div>
  );
}
