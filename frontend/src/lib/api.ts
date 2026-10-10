/**
 * VYOM+ API Client & TypeScript Interfaces
 * Authoritative interface definitions matching backend/app/api/schemas.py
 */

export interface DatasetUploadResponse {
  dataset_id: string;
  filename: string;
  total_rows: number;
  columns_detected: string[];
  canonical_fields_mapped: Record<string, string>;
  unmapped_columns: string[];
  warnings: string[];
  created_at: string;
}

export interface DatasetSummaryResponse {
  dataset_id: string;
  filename: string;
  total_rows: number;
  processed_rows: number;
  is_classified: boolean;
  status: string;
  created_at: string;
}

export interface PreviewRecord {
  row_id: number;
  data: Record<string, any>;
}

export interface PaginatedPreviewResponse {
  dataset_id: string;
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  columns: string[];
  rows: PreviewRecord[];
}

export interface SingleClassifyRequest {
  row_id?: number;
  doc_no?: string;
  invoice_date?: string;
  seller_supplier?: string;
  buyer_customer?: string;
  total_amount?: number;
  taxable_value?: number;
  gst?: number;
  quantity?: number;
  items_description?: string;
  custom_populated_fields?: Record<string, any>;
  use_mock?: boolean;
}

export interface ExtractedSignals {
  money_flow: {
    direction: string;
    flow_type: string;
    is_inward: boolean;
    is_outward: boolean;
    is_internal_contra: boolean;
    is_order_commitment: boolean;
    is_non_financial_movement: boolean;
    confidence: number;
  };
  entity_roles: {
    seller_role: string;
    buyer_role: string;
    is_internal_account_pair: boolean;
    is_crossborder: boolean;
    is_tax_authority_counterparty: boolean;
  };
  tax_returns: {
    has_statutory_tax: boolean;
    tax_rate_percent?: number | null;
    is_return_reversal: boolean;
    has_negative_quantity: boolean;
  };
  trade_crossborder: {
    is_import: boolean;
    is_export: boolean;
  };
  composite_signature: string;
}

export interface ContradictionDetail {
  rule_id: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  rule_name: string;
  description: string;
  suggested_action: string;
}

export interface GemmaPredictionPayload {
  category: string;
  confidence: number;
  reasoning: string;
  detected_signals: string[];
  alternative_category?: string | null;
  alternative_confidence?: number | null;
  raw_response?: string | null;
  is_mock: boolean;
}

export interface GuardrailEvaluationPayload {
  predicted_category: string;
  raw_confidence: number;
  calibrated_confidence: number;
  confidence_tier: "HIGH" | "MEDIUM" | "LOW";
  triage_decision: "AUTO_VERIFIED" | "FLAGGED_FOR_REVIEW" | "CRITICAL_REJECTION";
  contradictions: ContradictionDetail[];
  penalties_applied: number;
  second_pass_applied: boolean;
  original_category?: string | null;
  re_routed: boolean;
  audit_notes: string[];
}

export interface SingleClassifyResponse {
  result: {
    prediction: GemmaPredictionPayload;
    latency_ms: number;
    model_name: string;
    timestamp: string;
  };
  evaluation: GuardrailEvaluationPayload;
}

export interface BatchClassifyJobResponse {
  job_id: string;
  dataset_id: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  total_rows: number;
  processed_rows: number;
  progress_percent: number;
  started_at: string;
}

export interface BatchClassifyJobStatusResponse {
  job_id: string;
  dataset_id: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  total_rows: number;
  processed_rows: number;
  progress_percent: number;
  started_at: string;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface PredictionRecordResponse {
  row_id: number;
  doc_no?: string | null;
  invoice_date?: string | null;
  seller_supplier?: string | null;
  buyer_customer?: string | null;
  total_amount?: number | null;
  predicted_category: string;
  confidence: number;
  confidence_tier: "HIGH" | "MEDIUM" | "LOW";
  triage_decision: "AUTO_VERIFIED" | "FLAGGED_FOR_REVIEW" | "CRITICAL_REJECTION";
  contradictions_count: number;
  is_overridden: boolean;
  overridden_category?: string | null;
  reasoning: string;
}

export interface PaginatedPredictionsResponse {
  dataset_id: string;
  page: number;
  page_size: number;
  total_records: number;
  filtered_records: number;
  total_pages: number;
  predictions: PredictionRecordResponse[];
}

export interface PredictionDetailResponse {
  row_id: number;
  doc_no?: string | null;
  invoice_date?: string | null;
  seller_supplier?: string | null;
  buyer_customer?: string | null;
  total_amount?: number | null;
  taxable_value?: number | null;
  gst?: number | null;
  quantity?: number | null;
  item_descriptions: string[];
  predicted_category: string;
  confidence: number;
  confidence_tier: "HIGH" | "MEDIUM" | "LOW";
  triage_decision: "AUTO_VERIFIED" | "FLAGGED_FOR_REVIEW" | "CRITICAL_REJECTION";
  reasoning: string;
  detected_signals: string[];
  contradictions: ContradictionDetail[];
  alternative_category?: string | null;
  alternative_confidence?: number | null;
  is_overridden: boolean;
  overridden_category?: string | null;
  override_reason?: string | null;
  reviewer_id?: string | null;
  override_timestamp?: string | null;
  custom_fields: Record<string, any>;
}

export interface HumanOverrideRequest {
  overridden_category: string;
  override_reason: string;
  reviewer_id?: string;
}

export interface HumanOverrideResponse {
  row_id: number;
  status: string;
  previous_category: string;
  new_category: string;
  override_reason: string;
  reviewer_id: string;
  timestamp: string;
}

export interface DatasetAnalyticsResponse {
  dataset_id: string;
  total_transactions: number;
  processed_transactions: number;
  auto_verified_count: number;
  flagged_for_review_count: number;
  critical_rejection_count: number;
  overridden_count: number;
  human_override_count?: number;
  average_confidence: number;
  average_latency_ms?: number;
  auto_verified_percentage: number | null;
  flagged_percentage: number | null;
  critical_rejection_percentage: number | null;
  review_queue_percentage?: number | null;
  category_distribution: Record<string, number>;
  confidence_tier_distribution: Record<string, number>;
  triage_decision_distribution?: Record<string, number>;
  triage_distribution?: Record<string, number>;
  contradiction_breakdown?: Record<string, number>;
  contradiction_counts?: Record<string, number>;
}

export interface TaxonomyCardResponse {
  card_id: string;
  category_name: string;
  expected_flow: string;
  typical_debit_ledger: string;
  typical_credit_ledger: string;
  typical_documents: string[];
  primary_prefixes: string[];
  key_signals: string[];
  negative_signals: string[];
  confusion_pairs: string[];
  disambiguation_rules: string[];
}

export interface TaxonomyListResponse {
  total_categories: number;
  categories: string[];
  knowledge_cards: TaxonomyCardResponse[];
}

// Default base URL fallback
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.port === "3000"
    ? "http://127.0.0.1:8000"
    : "http://127.0.0.1:8000");

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson && errorJson.detail) {
        errorDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Datasets
  async uploadDataset(file: File): Promise<DatasetUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/v1/datasets/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<DatasetUploadResponse>(res);
  },

  async listDatasets(): Promise<DatasetSummaryResponse[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/datasets`);
    return handleResponse<DatasetSummaryResponse[]>(res);
  },

  async getDatasetPreview(
    datasetId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedPreviewResponse> {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/datasets/${datasetId}/preview?page=${page}&page_size=${pageSize}`
    );
    return handleResponse<PaginatedPreviewResponse>(res);
  },

  // Classification
  async classifySingle(payload: SingleClassifyRequest): Promise<SingleClassifyResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/classify/single`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<SingleClassifyResponse>(res);
  },

  async startBatchClassify(
    datasetId: string,
    useMock: boolean = true
  ): Promise<BatchClassifyJobResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/classify/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, use_mock: useMock }),
    });
    return handleResponse<BatchClassifyJobResponse>(res);
  },

  async getBatchJobStatus(jobId: string): Promise<BatchClassifyJobStatusResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/classify/jobs/${jobId}`);
    return handleResponse<BatchClassifyJobStatusResponse>(res);
  },

  // Predictions & Review Queue
  async getPredictions(
    datasetId: string,
    params: {
      page?: number;
      pageSize?: number;
      triageDecision?: string;
      confidenceTier?: string;
      category?: string;
      search?: string;
    } = {}
  ): Promise<PaginatedPredictionsResponse> {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.pageSize) query.set("page_size", String(params.pageSize));
    if (params.triageDecision && params.triageDecision !== "ALL")
      query.set("triage_decision", params.triageDecision);
    if (params.confidenceTier && params.confidenceTier !== "ALL")
      query.set("confidence_tier", params.confidenceTier);
    if (params.category && params.category !== "ALL")
      query.set("category", params.category);
    if (params.search && params.search.trim())
      query.set("search", params.search.trim());

    const res = await fetch(
      `${API_BASE_URL}/api/v1/datasets/${datasetId}/predictions?${query.toString()}`
    );
    return handleResponse<PaginatedPredictionsResponse>(res);
  },

  async getPredictionDetail(
    datasetId: string,
    rowId: number
  ): Promise<PredictionDetailResponse> {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/datasets/${datasetId}/predictions/${rowId}`
    );
    return handleResponse<PredictionDetailResponse>(res);
  },

  async overridePrediction(
    datasetId: string,
    rowId: number,
    payload: HumanOverrideRequest
  ): Promise<HumanOverrideResponse> {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/datasets/${datasetId}/predictions/${rowId}/override`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    return handleResponse<HumanOverrideResponse>(res);
  },

  // Analytics
  async getDatasetAnalytics(datasetId: string): Promise<DatasetAnalyticsResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/datasets/${datasetId}/analytics`);
    return handleResponse<DatasetAnalyticsResponse>(res);
  },

  // Export Download URL generator
  getExportUrl(datasetId: string, format: "xlsx" | "csv" = "xlsx"): string {
    return `${API_BASE_URL}/api/v1/datasets/${datasetId}/export?format=${format}`;
  },

  // Taxonomy & Cards
  async getTaxonomy(): Promise<TaxonomyListResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/taxonomy`);
    return handleResponse<TaxonomyListResponse>(res);
  },

  async getTaxonomyCard(cardId: string): Promise<TaxonomyCardResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/taxonomy/${cardId}`);
    return handleResponse<TaxonomyCardResponse>(res);
  },

  // System Health
  async getSystemHealth(): Promise<{ status: string; timestamp: string }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<{ status: string; timestamp: string }>(res);
  },
};
