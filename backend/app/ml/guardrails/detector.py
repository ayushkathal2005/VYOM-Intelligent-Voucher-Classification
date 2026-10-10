"""Domain contradiction detection engine for financial voucher classifications."""

from typing import Any, Dict, List, Union
from app.ingestion.schema import CanonicalTransaction
from app.ml.signals.models import MoneyFlowDirection, EntityRole, AccountingSignalProfile
from app.ml.signals.engine import AccountingSignalsEngine
from app.ml.guardrails.models import (
    AccountingContradiction,
    ContradictionSeverity,
)


class AccountingContradictionDetector:
    """
    Evaluates accounting domain consistency between transaction facts,
    signal profiles, and proposed voucher categories.
    """

    @classmethod
    def detect_contradictions(
        cls,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
        category: str,
        signals_profile: Union[AccountingSignalProfile, None] = None,
    ) -> List[AccountingContradiction]:
        """Analyze a transaction against a candidate voucher category and return detected contradictions."""
        if signals_profile is None:
            signals_profile = AccountingSignalsEngine.extract_signals(txn)

        if isinstance(txn, CanonicalTransaction):
            text = txn.compact_representation().lower()
            total_amt = txn.total_amount
            taxable_val = txn.taxable_value
            gst_val = txn.gst
            qty = txn.quantity
            supplier = txn.seller_supplier
            buyer = txn.buyer_customer
            custom = txn.custom_populated_fields
        else:
            raw = txn.get("raw_record") or txn
            text = str(raw).lower()
            total_amt = txn.get("total_amount")
            taxable_val = txn.get("taxable_value")
            gst_val = txn.get("gst")
            qty = txn.get("quantity")
            supplier = txn.get("seller_supplier")
            buyer = txn.get("buyer_customer")
            custom = {k: v for k, v in txn.items() if k not in ("row_id", "raw_record")}

        contradictions: List[AccountingContradiction] = []

        # ---------------------------------------------------------------------
        # 1. Contra Inconsistencies (Internal Bank/Cash transfers only)
        # ---------------------------------------------------------------------
        if category == "Contra":
            # Contra CANNOT have statutory tax assessed
            if signals_profile.is_tax_applicable or (gst_val is not None and gst_val > 0):
                contradictions.append(
                    AccountingContradiction(
                        code="CONTRA_STATUTORY_TAX",
                        severity=ContradictionSeverity.CRITICAL,
                        title="Contra Account Transfer With Statutory Tax",
                        message="Contra entries are strictly internal liquidity repositioning and cannot incur statutory GST or sales tax.",
                        conflicting_fields=["gst", "taxable_val"],
                        suggested_action="Reclassify to 'Payment', 'Receipt', or 'Purchase' if third-party commercial charges apply.",
                    )
                )

            # Contra CANNOT involve external commercial vendors or customer counterparties
            has_vendor = bool(supplier and len(supplier.strip()) > 0 and not any(k in supplier.lower() for k in ("bank", "cash", "branch", "petty")))
            has_buyer = bool(buyer and len(buyer.strip()) > 0 and not any(k in buyer.lower() for k in ("bank", "cash", "branch", "petty")))
            if has_vendor or has_buyer:
                contradictions.append(
                    AccountingContradiction(
                        code="CONTRA_EXTERNAL_COUNTERPARTY",
                        severity=ContradictionSeverity.CRITICAL,
                        title="Contra Entry With External Commercial Counterparty",
                        message=f"Contra vouchers are strictly internal transfers between company accounts, but external counterparty ('{supplier or buyer}') is named.",
                        conflicting_fields=["seller_supplier", "buyer_customer"],
                        suggested_action="Reclassify to 'Payment' if paying a supplier, or 'Receipt' if collecting from a customer.",
                    )
                )

            # Contra should have dual internal accounts
            if not signals_profile.has_internal_account_pair and signals_profile.money_flow != MoneyFlowDirection.INTERNAL:
                contradictions.append(
                    AccountingContradiction(
                        code="CONTRA_MISSING_INTERNAL_PAIR",
                        severity=ContradictionSeverity.WARNING,
                        title="Contra Lacks Verified Dual Internal Account Pair",
                        message="Contra classification requires identifying both source and destination internal treasury/bank accounts.",
                        conflicting_fields=["source_account", "destination_account"],
                        suggested_action="Verify whether this transaction is an external payment or journal entry.",
                    )
                )

        # ---------------------------------------------------------------------
        # 2. Sales Direction Inversion (Customer revenue cannot be vendor outflow)
        # ---------------------------------------------------------------------
        if category in ("Sales", "Sales Order"):
            if signals_profile.money_flow == MoneyFlowDirection.OUTFLOW and EntityRole.VENDOR_SUPPLIER in signals_profile.detected_entity_roles and EntityRole.CUSTOMER_BUYER not in signals_profile.detected_entity_roles:
                # Unless it's explicitly an outbound sales order/invoice with our entity as supplier
                if not any(k in text for k in ("sal-", "so-", "delivery ref", "delivery challan")):
                    contradictions.append(
                        AccountingContradiction(
                            code="SALES_OUTWARD_DISBURSEMENT",
                            severity=ContradictionSeverity.CRITICAL,
                            title="Sales Voucher Assigned to Procurement Outflow",
                            message="Transaction exhibits vendor procurement outflow characteristics rather than customer revenue generation.",
                            conflicting_fields=["seller_supplier", "money_flow"],
                            suggested_action="Reclassify to 'Purchase' or 'Purchase Order'.",
                        )
                    )

        # ---------------------------------------------------------------------
        # 3. Purchase Direction Inversion (Supplier procurement cannot be customer collection)
        # ---------------------------------------------------------------------
        if category in ("Purchase", "Purchase Order"):
            if signals_profile.money_flow == MoneyFlowDirection.INFLOW and EntityRole.CUSTOMER_BUYER in signals_profile.detected_entity_roles and EntityRole.VENDOR_SUPPLIER not in signals_profile.detected_entity_roles:
                if not any(k in text for k in ("pur-", "po-", "grn", "supplier")):
                    contradictions.append(
                        AccountingContradiction(
                            code="PURCHASE_INWARD_COLLECTION",
                            severity=ContradictionSeverity.CRITICAL,
                            title="Purchase Voucher Assigned to Inward Customer Collection",
                            message="Transaction exhibits customer revenue or receipt characteristics rather than supplier procurement.",
                            conflicting_fields=["buyer_customer", "money_flow"],
                            suggested_action="Reclassify to 'Sales' or 'Receipt'.",
                        )
                    )

        # ---------------------------------------------------------------------
        # 4. Zero Amount Commercial Invoice
        # ---------------------------------------------------------------------
        if category in ("Purchase", "Sales", "Import", "Export"):
            has_monetary_value = (total_amt is not None and total_amt > 0) or (taxable_val is not None and taxable_val > 0)
            if not has_monetary_value and qty is not None and qty > 0:
                contradictions.append(
                    AccountingContradiction(
                        code="ZERO_AMOUNT_COMMERCIAL_INVOICE",
                        severity=ContradictionSeverity.WARNING,
                        title="Zero-Valued Commercial Tax Invoice",
                        message=f"{category} vouchers require monetary billing, but total amount and taxable value are absent or zero while physical quantity is recorded.",
                        conflicting_fields=["total_amount", "taxable_value", "quantity"],
                        suggested_action="Reclassify to logistical 'Delivery Note' or 'Receipt Note' if this is a physical delivery challan.",
                    )
                )

        # ---------------------------------------------------------------------
        # 5. Return / Rejection Consistency
        # ---------------------------------------------------------------------
        if "Return" in category or "Rejection" in category:
            is_return_flagged = (
                signals_profile.has_negative_quantity
                or (qty is not None and qty < 0)
                or any(k in text for k in ("return", "dbn", "crn", "rjn", "rejected", "reversal"))
            )
            if not is_return_flagged:
                contradictions.append(
                    AccountingContradiction(
                        code="RETURN_WITHOUT_RETURN_SIGNALS",
                        severity=ContradictionSeverity.WARNING,
                        title="Return Category Without Reversal Signals",
                        message=f"Classified as '{category}', but neither negative quantity, debit/credit note prefix, nor return keywords are present.",
                        conflicting_fields=["quantity", "doc_no"],
                        suggested_action="Verify if this is standard forward 'Purchase' or 'Sales' rather than a return.",
                    )
                )

        # ---------------------------------------------------------------------
        # 6. Payment / Receipt Internal Pair Conflict
        # ---------------------------------------------------------------------
        if category in ("Payment", "Receipt"):
            if signals_profile.has_internal_account_pair or signals_profile.money_flow == MoneyFlowDirection.INTERNAL:
                contradictions.append(
                    AccountingContradiction(
                        code="INTERNAL_ACCOUNT_AS_PAYMENT",
                        severity=ContradictionSeverity.WARNING,
                        title="Internal Transfer Classified As External Payment/Receipt",
                        message=f"Classified as '{category}', but both source and destination accounts are internal treasury accounts.",
                        conflicting_fields=["source_account", "destination_account"],
                        suggested_action="Reclassify to 'Contra'.",
                    )
                )

        # ---------------------------------------------------------------------
        # 7. Cross-Border International Trade Consistency
        # ---------------------------------------------------------------------
        if category in ("Import", "Export"):
            if not signals_profile.has_customs_or_crossborder and not any(
                k in text for k in ("originating country", "destination country", "importer", "exporter", "cif", "fob", "exp", "imp", "customs")
            ):
                contradictions.append(
                    AccountingContradiction(
                        code="CROSSBORDER_WITHOUT_FOREIGN_INDICATORS",
                        severity=ContradictionSeverity.WARNING,
                        title="Cross-Border Category Without International Trade Metadata",
                        message=f"Classified as '{category}', but no foreign country, FOB, CIF, or customs clearance metadata is detected.",
                        conflicting_fields=["doc_no", "customs_duty"],
                        suggested_action="Reclassify to domestic 'Purchase' or 'Sales' if not cross-border trade.",
                    )
                )

        # ---------------------------------------------------------------------
        # 8. Payroll Metadata Consistency
        # ---------------------------------------------------------------------
        if category == "Salary / Payroll":
            if not signals_profile.has_employee_metadata and not any(k in text for k in ("employee", "payroll", "salary", "wages")):
                contradictions.append(
                    AccountingContradiction(
                        code="PAYROLL_WITHOUT_EMPLOYEE_METADATA",
                        severity=ContradictionSeverity.WARNING,
                        title="Payroll Voucher Lacks Workforce Metadata",
                        message="Classified as 'Salary / Payroll', but no employee code, salary breakdown, or payroll period is found.",
                        conflicting_fields=["employee_code", "payroll_period"],
                        suggested_action="Verify if this is an operational 'Expense' claim or supplier 'Payment'.",
                    )
                )

        # ---------------------------------------------------------------------
        # 9. Attendance With Monetary Payment
        # ---------------------------------------------------------------------
        if category == "Attendance":
            if (total_amt is not None and total_amt > 0) or (taxable_val is not None and taxable_val > 0):
                contradictions.append(
                    AccountingContradiction(
                        code="ATTENDANCE_WITH_MONETARY_PAYMENT",
                        severity=ContradictionSeverity.WARNING,
                        title="Non-Financial Attendance Log Contains Monetary Payment",
                        message="Attendance records are non-monetary operational logs (tracking shift hours/days worked), but monetary amounts are present.",
                        conflicting_fields=["total_amount", "gross_salary"],
                        suggested_action="Reclassify to 'Salary / Payroll' if monetary compensation is being calculated.",
                    )
                )

        return contradictions
