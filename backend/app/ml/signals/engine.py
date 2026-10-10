"""Accounting Signals Engine extracting liquidity flow, entity roles, document linkages, and domain signals."""

from typing import Any, Dict, List, Union

from app.ingestion.schema import CanonicalTransaction
from app.ml.baseline import extract_text_representation
from app.ml.signals.models import (
    MoneyFlowDirection,
    EntityRole,
    AccountingSignalProfile,
)


class AccountingSignalsEngine:
    """Extracts domain-level accounting indicators, entity roles, and liquidity flow profiles."""

    @classmethod
    def extract_signals(
        cls,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
    ) -> AccountingSignalProfile:
        """Analyze a transaction and produce an audit-grade AccountingSignalProfile."""
        if isinstance(txn, CanonicalTransaction):
            row_id = txn.row_id
            text = txn.compact_representation().lower()
            raw = txn.raw_record
            qty = txn.quantity
            gst = txn.gst
            taxable = txn.taxable_value
            total = txn.total_amount
            custom = txn.custom_populated_fields
        else:
            row_id = txn.get("row_id", 1)
            text = extract_text_representation(txn).lower()
            raw = txn.get("raw_record") or txn
            qty = txn.get("quantity")
            gst = txn.get("gst")
            taxable = txn.get("taxable_value")
            total = txn.get("total_amount")
            custom = {k: v for k, v in txn.items() if k not in ("row_id", "raw_record")}

        primary_signals: List[str] = []
        risk_flags: List[str] = []

        # 1. Money Flow Derivation
        money_flow = cls._derive_money_flow(text, custom, primary_signals)

        # 2. Entity Role Derivation
        roles = cls._derive_entity_roles(text, primary_signals)

        # 3. Tax Signals
        has_tax = bool((gst and gst > 0) or any(k in text for k in ("gst", "tax", "customs duty", "taxable_val")))
        if has_tax:
            primary_signals.append("statutory tax assessment applicable")
        if total is not None:
            try:
                if float(total) > 0:
                    primary_signals.append("monetary transaction value established")
            except (ValueError, TypeError):
                pass

        # 4. Quantity Semantics
        has_negative_qty = False
        try:
            if qty is not None and float(qty) < 0:
                has_negative_qty = True
                primary_signals.append("negative quantity return detected")
        except (ValueError, TypeError):
            pass

        if "units returned" in text:
            primary_signals.append("goods return context indicated")

        # 5. Document Linkages
        has_order_ref = bool(
            any(k in text for k in ("order_ref:", "po number", "so number", "po ref", "so ref", "jwio", "jwoo"))
        )
        if has_order_ref:
            primary_signals.append("commercial order reference linked")

        has_dispatch_ref = bool(
            any(k in text for k in ("delivery challan", "delivery_ref", "grn", "dispatch date", "quantity shipped", "item received"))
        )
        if has_dispatch_ref:
            primary_signals.append("logistics dispatch/receipt reference linked")

        has_internal_pair = bool(
            any(k in text for k in ("source account", "destination account", "contra id", "bank ifsc")) or
            ("source" in text and "destination" in text and "account" in text)
        )
        if has_internal_pair:
            primary_signals.append("internal dual bank/cash account pair detected")

        has_crossborder = bool(
            any(k in text for k in ("import bill", "export invoice", "customs duty", "cif", "fob", "originating country", "destination country"))
        )
        if has_crossborder:
            primary_signals.append("cross-border foreign trade indicators detected")

        has_employee_meta = bool(
            any(k in text for k in ("employee code", "payroll period", "gross salary", "days worked", "attendance"))
        )
        if has_employee_meta:
            primary_signals.append("workforce compensation or attendance metadata present")

        # Risk flag evaluation
        if money_flow == MoneyFlowDirection.UNKNOWN:
            risk_flags.append("ambiguous money flow direction")
        if not roles or EntityRole.UNKNOWN in roles:
            risk_flags.append("unclear counterparty entity role")
        if total is None and taxable is None and money_flow not in (
            MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
            MoneyFlowDirection.ORDER_COMMITMENT,
            MoneyFlowDirection.ATTENDANCE_LOG,
        ):
            risk_flags.append("monetary transaction lacks explicit total amount")

        return AccountingSignalProfile(
            row_id=row_id,
            money_flow=money_flow,
            detected_entity_roles=roles,
            is_tax_applicable=has_tax,
            has_negative_quantity=has_negative_qty,
            has_order_reference=has_order_ref,
            has_dispatch_reference=has_dispatch_ref,
            has_internal_account_pair=has_internal_pair,
            has_customs_or_crossborder=has_crossborder,
            has_employee_metadata=has_employee_meta,
            primary_signals=primary_signals,
            risk_flags=risk_flags,
        )

    @classmethod
    def _derive_money_flow(cls, text: str, custom: Dict[str, Any], signals: List[str]) -> MoneyFlowDirection:
        text_lower = text.lower()

        # 1. Attendance & Shift Tracking
        if any(k in text_lower for k in ("attendance", "biometric", "days worked", "overtime", "timesheet")):
            signals.append("non-monetary shift attendance tracking")
            return MoneyFlowDirection.ATTENDANCE_LOG

        # 2. Contra / Internal Account Liquidity Transfers
        if any(k in text_lower for k in ("source account", "destination account", "contra id", "bank ifsc", "cnt-")) or (
            "source" in text_lower and "destination" in text_lower and "account" in text_lower
        ):
            signals.append("internal account liquidity transfer")
            return MoneyFlowDirection.INTERNAL

        # 3. Journal Dual-Ledger Adjustments
        if any(k in text_lower for k in ("debit side", "credit side", "journal id", "journal type", "adjusting entry", "jv-")):
            signals.append("dual nominal ledger adjustment")
            return MoneyFlowDirection.ADJUSTMENT

        # 4. Warehouse & Physical Inventory Movements
        if any(k in text_lower for k in (
            "rejection note", "rjn-in", "rjn-out", "grn", "delivery challan", "dc-", "doc_no: dc",
            "item received", "item dispatched", "stock count", "stk-cnt", "stock adj", "stk-adj",
            "inward job work", "outward job work", "material in", "material out", "mat-in", "mat-out"
        )):
            if not any(k in text_lower for k in ("taxable_val:", "tax: 6", "tax: 7", "tax: 8", "tax: 9", "base amount")):
                signals.append("physical warehouse or material inventory movement")
                return MoneyFlowDirection.NON_FINANCIAL_MOVEMENT

        # 5. Cross-Border International Trade
        if any(k in text_lower for k in ("export invoice", "destination country", "free on board", "fob", "units exported")) or "doc_no: exp" in text_lower:
            signals.append("export international trade receivable flow")
            return MoneyFlowDirection.INFLOW

        if any(k in text_lower for k in ("import bill", "originating country", "customs duty", "cif", "units imported")) or "doc_no: imp" in text_lower:
            signals.append("import international trade payable flow")
            return MoneyFlowDirection.OUTFLOW

        # 6. Commercial Pre-Fulfillment Order Commitments
        if any(k in text_lower for k in ("po number", "so number", "quantity required", "quantity ordered", "jwio", "jwoo", "promised delivery")):
            if not any(k in text_lower for k in ("grn", "delivery challan", "doc_no: pur-", "doc_no: sal-", "taxable_val:")):
                signals.append("pre-fulfillment commercial order commitment")
                return MoneyFlowDirection.ORDER_COMMITMENT

        # 7. Inward Revenue & Collections (Sales, Receipts)
        if any(k in text_lower for k in ("doc_no: sal-", "receipt id", "rcpt-", "rct-", "rec-", "paying organization", "received amount")):
            signals.append("inward liquidity collection or sales receivable flow")
            return MoneyFlowDirection.INFLOW

        # 8. Outward Disbursements & Procurements (Purchase, Payments, Expenses, Payroll)
        if any(k in text_lower for k in ("doc_no: pur-", "doc_no: pmt-", "pmt-", "payment id", "pay-", "payee organization", "amount claimed", "expense claim", "gross salary", "net payable")):
            signals.append("outward liquidity or procurement payable flow")
            return MoneyFlowDirection.OUTFLOW

        # 9. Generic Counterparty Fallback
        if any(k in text_lower for k in ("customer", "buyer")):
            signals.append("inward liquidity collection or sales receivable flow")
            return MoneyFlowDirection.INFLOW

        if any(k in text_lower for k in ("supplier", "vendor")):
            signals.append("outward liquidity or procurement payable flow")
            return MoneyFlowDirection.OUTFLOW

        return MoneyFlowDirection.UNKNOWN

    @classmethod
    def _derive_entity_roles(cls, text: str, signals: List[str]) -> List[EntityRole]:
        roles: List[EntityRole] = []

        if any(k in text for k in ("supplier", "vendor", "seller", "payee organization")):
            roles.append(EntityRole.VENDOR_SUPPLIER)
            signals.append("party identified as vendor/supplier or payment payee")

        if any(k in text for k in ("customer", "buyer", "client", "debtor", "paying organization")):
            roles.append(EntityRole.CUSTOMER_BUYER)
            signals.append("party identified as customer/buyer or paying organization")

        if any(k in text for k in ("employee", "staff", "payroll", "gross salary")):
            roles.append(EntityRole.EMPLOYEE)
            signals.append("party identified as internal employee")

        if any(k in text for k in ("source account", "destination account", "bank ifsc", "contra id")):
            roles.append(EntityRole.INTERNAL_ACCOUNT)
            signals.append("party identified as internal treasury account")

        if any(k in text for k in ("contractor", "subcontractor", "job work", "processor", "principal")):
            roles.append(EntityRole.CONTRACTOR_JOBWORKER)
            signals.append("party identified as external contractor/processor")

        if any(k in text for k in ("originating country", "destination country", "importer", "exporter", "port code")):
            roles.append(EntityRole.OVERSEAS_COUNTERPARTY)
            signals.append("party identified as overseas trade counterparty")

        if any(k in text for k in ("customs duty", "professional tax", "income tax deduction", "gst")):
            roles.append(EntityRole.TAX_AUTHORITY)

        if not roles:
            roles.append(EntityRole.UNKNOWN)

        return roles
