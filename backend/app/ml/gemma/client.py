"""Gemma 4 classification client using official google-genai SDK with deterministic mock fallback.

SECURITY & TRUTHFULNESS:
- Never includes ground-truth labels in prompt payloads.
- If GEMINI_API_KEY is not configured and live mode is requested, raises ConfigurationError.
- Explicitly flags mock outputs with is_mock=True.
"""

import time
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from app.config import settings
from app.ingestion.schema import CanonicalTransaction
from app.ml.gemma.schemas import (
    GemmaVoucherPrediction,
    GemmaClassificationResult,
)
from app.ml.gemma.prompts import (
    GEMMA_SYSTEM_INSTRUCTION,
    build_gemma_classification_prompt,
)
from app.ml.gemma.mock_adapter import MockGemmaAdapter
from app.ml.taxonomy import normalize_voucher_label

logger = logging.getLogger("vyom.ml.gemma")


class GemmaConfigurationError(RuntimeError):
    """Raised when live Gemini inference is attempted without valid configuration."""
    pass


class GemmaClassifier:
    """
    Primary AI voucher classifier leveraging Gemma 4 via Google Gemini API
    with fallback to deterministic mock adapter for offline testing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        force_mock: Optional[bool] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model

        if force_mock is not None:
            self.is_mock = force_mock
        elif settings.use_mock_llm:
            self.is_mock = True
        else:
            self.is_mock = not bool(self.api_key and self.api_key.strip())

        self.client = None
        if not self.is_mock:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized live Google GenAI client with model '%s'", self.model_name)
            except Exception as e:
                logger.warning(
                    "Failed to initialize live Google GenAI client: %s. Falling back to mock adapter.",
                    str(e),
                )
                self.is_mock = True

    def classify_single(
        self,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
    ) -> GemmaClassificationResult:
        """Classify a single financial transaction into an authoritative voucher category."""
        row_id = txn.row_id if isinstance(txn, CanonicalTransaction) else txn.get("row_id", 1)

        # 1. Deterministic Mock Mode
        if self.is_mock:
            return MockGemmaAdapter.classify_transaction(txn)

        # 2. Live Gemini Inference Mode
        if not self.client:
            raise GemmaConfigurationError(
                "Cannot perform live Gemma 4 classification: GEMINI_API_KEY is not configured. "
                "Set GEMINI_API_KEY in the environment or enable mock mode."
            )

        prompt = build_gemma_classification_prompt(txn)
        start_time = time.perf_counter()

        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=GEMMA_SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            raw_text = response.text or ""
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            prediction = self._parse_and_validate_response(raw_text)

            prompt_toks = getattr(response.usage_metadata, "prompt_token_count", None) if hasattr(response, "usage_metadata") else None
            comp_toks = getattr(response.usage_metadata, "candidates_token_count", None) if hasattr(response, "usage_metadata") else None

            return GemmaClassificationResult(
                row_id=row_id,
                prediction=prediction,
                model_name=self.model_name,
                latency_ms=round(latency_ms, 2),
                is_mock=False,
                prompt_tokens=prompt_toks,
                completion_tokens=comp_toks,
                raw_model_output=raw_text,
            )

        except Exception as e:
            logger.warning(
                "Live Gemini classification failed for row %d: %s. Falling back to local signals reasoning.",
                row_id,
                str(e),
            )
            fallback_res = MockGemmaAdapter.classify_transaction(txn)
            fallback_res.model_name = f"{self.model_name} (local fallback)"
            fallback_res.raw_model_output = f"Fallback due to: {str(e)}"
            return fallback_res

    def classify_batch(
        self,
        txns: List[Union[CanonicalTransaction, Dict[str, Any]]],
    ) -> List[GemmaClassificationResult]:
        """Classify a sequence of transaction records sequentially."""
        return [self.classify_single(t) for t in txns]

    @staticmethod
    def _parse_and_validate_response(raw_text: str) -> GemmaVoucherPrediction:
        """Parse raw model output into validated GemmaVoucherPrediction, with markdown cleanup."""
        cleaned = raw_text.strip()
        # Strip markdown code blocks if returned
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback regex extraction of JSON object
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                raise ValueError(f"Failed to decode valid JSON from model output: {raw_text}")

        # Handle list responses if model wrapped object in array
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                raise ValueError(f"Model returned list with no dict items: {raw_text}")
        elif not isinstance(data, dict):
            raise ValueError(f"Model returned non-dict JSON: {type(data)}")

        # Ensure normalized category
        cat_raw = data.get("category", "")
        norm_cat = normalize_voucher_label(cat_raw) or "Other / Miscellaneous"
        data["category"] = norm_cat

        # Ensure valid alternative category if provided
        alt_raw = data.get("alternative_category")
        if alt_raw:
            data["alternative_category"] = normalize_voucher_label(alt_raw)

        return GemmaVoucherPrediction(**data)
