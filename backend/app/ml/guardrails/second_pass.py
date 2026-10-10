"""Second-pass arbitration and reasoning engine for ambiguous or contradicted voucher classifications."""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.ingestion.schema import CanonicalTransaction
from app.ml.signals.models import MoneyFlowDirection, EntityRole, AccountingSignalProfile
from app.ml.signals.engine import AccountingSignalsEngine
from app.ml.signals.voucher_cards import VOUCHER_CARDS
from app.ml.signals.retriever import candidate_retriever
from app.ml.guardrails.models import (
    AccountingContradiction,
    ContradictionSeverity,
)

logger = logging.getLogger("vyom.ml.guardrails.second_pass")


class SecondPassReasoningEngine:
    """
    Arbitrates borderline, low-confidence, or contradictory classifications
    through targeted rule-based resolution and domain disambiguation.
    """

    @classmethod
    def arbitrate(
        cls,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
        primary_category: str,
        alternative_category: Optional[str],
        contradictions: List[AccountingContradiction],
        signals_profile: Union[AccountingSignalProfile, None] = None,
        gemma_classifier: Any = None,
    ) -> Tuple[str, str]:
        """
        Arbitrate between candidate categories.
        Returns: (final_category, justification_narrative)
        """
        if signals_profile is None:
            signals_profile = AccountingSignalsEngine.extract_signals(txn)

        if isinstance(txn, CanonicalTransaction):
            text = txn.compact_representation().lower()
            supplier = txn.seller_supplier
            buyer = txn.buyer_customer
            qty = txn.quantity
        else:
            raw = txn.get("raw_record") or txn
            text = str(raw).lower()
            supplier = txn.get("seller_supplier")
            buyer = txn.get("buyer_customer")
            qty = txn.get("quantity")

        # 1. Structural Contradiction Resolution
        critical_contradictions = [c for c in contradictions if c.severity == ContradictionSeverity.CRITICAL]
        if critical_contradictions:
            crit = critical_contradictions[0]
            if crit.code in ("CONTRA_EXTERNAL_COUNTERPARTY", "CONTRA_STATUTORY_TAX"):
                if signals_profile.money_flow == MoneyFlowDirection.OUTFLOW or EntityRole.VENDOR_SUPPLIER in signals_profile.detected_entity_roles:
                    return (
                        "Payment",
                        f"Second-pass re-routed from '{primary_category}' to 'Payment': Contra entry contradicted by external counterparty or statutory tax; outward vendor flow detected.",
                    )
                if signals_profile.money_flow == MoneyFlowDirection.INFLOW or EntityRole.CUSTOMER_BUYER in signals_profile.detected_entity_roles:
                    return (
                        "Receipt",
                        f"Second-pass re-routed from '{primary_category}' to 'Receipt': Contra entry contradicted by external counterparty or statutory tax; inward customer flow detected.",
                    )

            if crit.code == "SALES_OUTWARD_DISBURSEMENT":
                return (
                    "Purchase",
                    f"Second-pass re-routed from '{primary_category}' to 'Purchase': Outward procurement flow and vendor role contradict revenue billing.",
                )

            if crit.code == "PURCHASE_INWARD_COLLECTION":
                return (
                    "Sales",
                    f"Second-pass re-routed from '{primary_category}' to 'Sales': Inward customer receivable collection contradicts procurement purchase.",
                )

        # 2. Warning Resolution
        warning_contradictions = [c for c in contradictions if c.severity == ContradictionSeverity.WARNING]
        for warn in warning_contradictions:
            if warn.code == "INTERNAL_ACCOUNT_AS_PAYMENT":
                return (
                    "Contra",
                    f"Second-pass re-routed from '{primary_category}' to 'Contra': Both accounts are internal treasury accounts with zero external third-party creditor.",
                )

            if warn.code == "RETURN_WITHOUT_RETURN_SIGNALS":
                if "Purchase" in primary_category:
                    return (
                        "Purchase",
                        f"Second-pass re-routed from '{primary_category}' to 'Purchase': Return category lacked negative quantity or reversal references; forward procurement affirmed.",
                    )
                if "Sales" in primary_category:
                    return (
                        "Sales",
                        f"Second-pass re-routed from '{primary_category}' to 'Sales': Return category lacked negative quantity or reversal references; forward sales affirmed.",
                    )

            if warn.code == "ZERO_AMOUNT_COMMERCIAL_INVOICE":
                if any(k in text for k in ("delivery challan", "dc-", "dc", "quantity shipped")):
                    return (
                        "Delivery Note",
                        f"Second-pass re-routed from '{primary_category}' to 'Delivery Note': Non-valued commercial record contains delivery challan dispatch indicators.",
                    )
                if any(k in text for k in ("grn", "item received")):
                    return (
                        "Receipt Note",
                        f"Second-pass re-routed from '{primary_category}' to 'Receipt Note': Non-valued commercial record contains warehouse goods receipt indicators.",
                    )

        # 3. Disambiguation with Alternative Candidate
        if alternative_category and alternative_category != primary_category:
            primary_card = VOUCHER_CARDS.get(primary_category)
            alt_card = VOUCHER_CARDS.get(alternative_category)

            # Check if alternative category cleanly aligns with money flow while primary does not
            if primary_card and alt_card:
                if alt_card.expected_flow == signals_profile.money_flow and primary_card.expected_flow != signals_profile.money_flow:
                    return (
                        alternative_category,
                        f"Second-pass selected alternative '{alternative_category}' over '{primary_category}': Flow alignment verified with {signals_profile.money_flow.value}.",
                    )

        # 4. Affirm Primary Category with Explanatory Justification
        card = VOUCHER_CARDS.get(primary_category)
        rule = card.disambiguation_rule if card else "Standard domain rules applied."
        return (
            primary_category,
            f"Second-pass affirmed '{primary_category}': Analyzed signal profile and confirmed category alignment. Guidance: {rule}",
        )
