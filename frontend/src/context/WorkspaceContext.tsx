"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import {
  api,
  DatasetUploadResponse,
  DatasetAnalyticsResponse,
  BatchClassifyJobStatusResponse,
} from "@/lib/api";

interface WorkspaceContextType {
  activeDataset: DatasetUploadResponse | null;
  activeDatasetId: string | null;
  activeJob: BatchClassifyJobStatusResponse | null;
  activeJobId: string | null;
  analytics: DatasetAnalyticsResponse | null;
  isAnalyticsLoading: boolean;
  isProcessing: boolean;
  isClassified: boolean;
  refreshTrigger: number;
  setActiveDataset: (dataset: DatasetUploadResponse | null) => void;
  setActiveDatasetId: (id: string | null) => void;
  setActiveJob: (job: BatchClassifyJobStatusResponse | null) => void;
  loadAnalytics: (datasetId?: string) => Promise<void>;
  triggerRefresh: () => void;
  setIsProcessing: (val: boolean) => void;
  setIsClassified: (val: boolean) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [activeDataset, setActiveDatasetState] = useState<DatasetUploadResponse | null>(null);
  const [activeDatasetId, setActiveDatasetIdState] = useState<string | null>(null);
  const [activeJob, setActiveJobState] = useState<BatchClassifyJobStatusResponse | null>(null);
  const [activeJobId, setActiveJobIdState] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<DatasetAnalyticsResponse | null>(null);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isClassified, setIsClassified] = useState<boolean>(false);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Restore active dataset and job ID from localStorage on mount
  useEffect(() => {
    try {
      const savedDatasetId = localStorage.getItem("vyom_active_dataset_id");
      const savedJobId = localStorage.getItem("vyom_active_job_id");
      const savedDatasetMeta = localStorage.getItem("vyom_active_dataset_meta");

      if (savedDatasetMeta) {
        try {
          const parsed = JSON.parse(savedDatasetMeta);
          setActiveDatasetState(parsed);
          setActiveDatasetIdState(parsed.dataset_id);
        } catch {
          // ignore parsing error
        }
      } else if (savedDatasetId) {
        setActiveDatasetIdState(savedDatasetId);
      }

      if (savedJobId) {
        setActiveJobIdState(savedJobId);
      }
    } catch {
      // localStorage may not be available in SSR or strict privacy mode
    }
  }, []);

  const setActiveDataset = useCallback((dataset: DatasetUploadResponse | null) => {
    setActiveDatasetState(dataset);
    if (dataset) {
      setActiveDatasetIdState(dataset.dataset_id);
      try {
        localStorage.setItem("vyom_active_dataset_id", dataset.dataset_id);
        localStorage.setItem("vyom_active_dataset_meta", JSON.stringify(dataset));
      } catch {
        // ignore
      }
    } else {
      setActiveDatasetIdState(null);
      try {
        localStorage.removeItem("vyom_active_dataset_id");
        localStorage.removeItem("vyom_active_dataset_meta");
        localStorage.removeItem("vyom_active_job_id");
      } catch {
        // ignore
      }
    }
  }, []);

  const setActiveDatasetId = useCallback((id: string | null) => {
    setActiveDatasetIdState(id);
    if (id) {
      try {
        localStorage.setItem("vyom_active_dataset_id", id);
      } catch {
        // ignore
      }
    } else {
      try {
        localStorage.removeItem("vyom_active_dataset_id");
      } catch {
        // ignore
      }
    }
  }, []);

  const setActiveJob = useCallback((job: BatchClassifyJobStatusResponse | null) => {
    setActiveJobState(job);
    if (job) {
      setActiveJobIdState(job.job_id);
      try {
        localStorage.setItem("vyom_active_job_id", job.job_id);
      } catch {
        // ignore
      }
    } else {
      setActiveJobIdState(null);
      try {
        localStorage.removeItem("vyom_active_job_id");
      } catch {
        // ignore
      }
    }
  }, []);

  const loadAnalytics = useCallback(
    async (datasetId?: string) => {
      const targetId = datasetId || activeDatasetId || activeDataset?.dataset_id;
      if (!targetId) return;

      setIsAnalyticsLoading(true);
      try {
        const data = await api.getDatasetAnalytics(targetId);
        setAnalytics(data);
        if (data.processed_transactions > 0) {
          setIsClassified(true);
        }
      } catch {
        // analytics may not be ready if dataset not classified
      } finally {
        setIsAnalyticsLoading(false);
      }
    },
    [activeDatasetId, activeDataset]
  );

  const triggerRefresh = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  // Sync active dataset details if only ID was loaded
  useEffect(() => {
    if (activeDatasetId && !activeDataset) {
      api.listDatasets().then((list) => {
        const match = list.find((d) => d.dataset_id === activeDatasetId);
        if (match) {
          const minimalUpload: DatasetUploadResponse = {
            dataset_id: match.dataset_id,
            filename: match.filename,
            total_rows: match.total_rows,
            columns_detected: [],
            canonical_fields_mapped: {},
            unmapped_columns: [],
            warnings: [],
            created_at: match.created_at,
          };
          setActiveDatasetState(minimalUpload);
          if (match.is_classified) {
            setIsClassified(true);
          }
        }
      }).catch(() => {});
    }
  }, [activeDatasetId, activeDataset]);

  // Load analytics if dataset is classified or job is completed
  useEffect(() => {
    if (activeDatasetId) {
      loadAnalytics(activeDatasetId);
    }
  }, [activeDatasetId, loadAnalytics, refreshTrigger]);

  return (
    <WorkspaceContext.Provider
      value={{
        activeDataset,
        activeDatasetId,
        activeJob,
        activeJobId,
        analytics,
        isAnalyticsLoading,
        isProcessing,
        isClassified,
        refreshTrigger,
        setActiveDataset,
        setActiveDatasetId,
        setActiveJob,
        loadAnalytics,
        triggerRefresh,
        setIsProcessing,
        setIsClassified,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
