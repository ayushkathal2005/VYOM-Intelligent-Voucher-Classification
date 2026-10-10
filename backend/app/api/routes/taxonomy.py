"""Authoritative taxonomy and voucher knowledge card exploration endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException

from app.ml.signals.voucher_cards import VOUCHER_CARDS
from app.ml.taxonomy import normalize_voucher_label
from app.api.schemas import TaxonomyCardResponse

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy & Knowledge Base"])


@router.get("", response_model=List[TaxonomyCardResponse])
def get_all_taxonomy_cards():
    """Retrieve full repository of the 27 authoritative voucher knowledge cards with accounting ledgers."""
    cards = []
    for card in VOUCHER_CARDS.values():
        cards.append(
            TaxonomyCardResponse(
                category=card.category,
                description=card.description,
                expected_flow=card.expected_flow.value,
                primary_identifiers=card.primary_identifiers,
                typical_ledgers=card.typical_ledgers,
                key_signals=card.key_signals,
                negative_signals=card.negative_signals,
                common_confusion_pairs=card.common_confusion_pairs,
                disambiguation_rule=card.disambiguation_rule,
            )
        )
    return cards


@router.get("/{category}", response_model=TaxonomyCardResponse)
def get_taxonomy_card(category: str):
    """Retrieve accounting knowledge card and disambiguation rules for a specific category."""
    norm = normalize_voucher_label(category)
    if not norm or norm not in VOUCHER_CARDS:
        raise HTTPException(status_code=404, detail=f"Voucher category '{category}' not found in taxonomy.")

    card = VOUCHER_CARDS[norm]
    return TaxonomyCardResponse(
        category=card.category,
        description=card.description,
        expected_flow=card.expected_flow.value,
        primary_identifiers=card.primary_identifiers,
        typical_ledgers=card.typical_ledgers,
        key_signals=card.key_signals,
        negative_signals=card.negative_signals,
        common_confusion_pairs=card.common_confusion_pairs,
        disambiguation_rule=card.disambiguation_rule,
    )
