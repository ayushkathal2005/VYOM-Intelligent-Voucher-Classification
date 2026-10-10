"""Authoritative 27 Voucher Knowledge Cards defining domain semantics, ledger behaviors, and disambiguation checklists."""

from typing import Dict, List
from pydantic import BaseModel, Field

from app.ml.signals.models import MoneyFlowDirection
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS


class VoucherKnowledgeCard(BaseModel):
    """Encapsulated accounting intelligence card for a single voucher category."""

    category: str = Field(..., description="Authoritative category label")
    description: str = Field(..., description="Formal accounting definition and scope")
    expected_flow: MoneyFlowDirection = Field(..., description="Primary money-flow direction")
    primary_identifiers: List[str] = Field(..., description="Typical column names or document codes")
    typical_ledgers: List[str] = Field(..., description="Associated debit/credit ledgers")
    key_signals: List[str] = Field(..., description="Strong positive indicators")
    negative_signals: List[str] = Field(..., description="Features that rule out this category")
    common_confusion_pairs: List[str] = Field(..., description="Commonly confused categories")
    disambiguation_rule: str = Field(..., description="Direct guidance on distinguishing from confused categories")


VOUCHER_CARDS: Dict[str, VoucherKnowledgeCard] = {
    # 1. Purchase
    "Purchase": VoucherKnowledgeCard(
        category="Purchase",
        description="Accounting recording of goods or services procured from a vendor/supplier, establishing accounts payable and input tax credit.",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Document Number", "Vendor Name", "Base Amount", "Tax Amount", "PO Ref"],
        typical_ledgers=["Purchase Account (Dr)", "Input GST (Dr)", "Sundry Creditors (Cr)"],
        key_signals=["Vendor/supplier counterparty", "Input tax credit (CGST/SGST/IGST)", "PO reference linkage"],
        negative_signals=["Customer debtor", "Delivery challan outbound", "Promised delivery date only"],
        common_confusion_pairs=["Purchase Order", "Sales", "Receipt Note"],
        disambiguation_rule="Distinguish from Purchase Order by presence of finalized tax amounts and financial payable liability; distinguish from Sales by vendor supplier role rather than customer buyer.",
    ),

    # 2. Sales
    "Sales": VoucherKnowledgeCard(
        category="Sales",
        description="Accounting recording of goods or services billed to a customer/buyer, recognizing revenue and output tax liability.",
        expected_flow=MoneyFlowDirection.INFLOW,
        primary_identifiers=["Document Number", "Customer", "Company", "Base Amount", "Delivery Ref"],
        typical_ledgers=["Sundry Debtors (Dr)", "Sales Revenue (Cr)", "Output GST (Cr)"],
        key_signals=["Customer buyer counterparty", "Output tax liability", "Delivery note reference linkage"],
        negative_signals=["Vendor supplier role", "PO reference inward", "Debit note document"],
        common_confusion_pairs=["Sales Order", "Purchase", "Delivery Note"],
        disambiguation_rule="Distinguish from Sales Order by finalized tax billing and receivable creation; distinguish from Delivery Note by presence of monetary billing and tax breakdown.",
    ),

    # 3. Purchase Return / Debit Note
    "Purchase Return / Debit Note": VoucherKnowledgeCard(
        category="Purchase Return / Debit Note",
        description="Document issued to a supplier adjusting payable liability downward due to rejected, damaged, or returned goods.",
        expected_flow=MoneyFlowDirection.INFLOW,
        primary_identifiers=["Document Number", "DBN", "Debit Note", "Original Doc Ref", "PUR-", "Units Returned", "Reason for Return"],
        typical_ledgers=["Sundry Creditors (Dr)", "Purchase Returns (Cr)", "Input GST Reversal (Cr)"],
        key_signals=["Negative units returned", "Debit note prefix (DBN)", "Original purchase invoice reference"],
        negative_signals=["Credit note prefix (CRN)", "Customer buyer counterparty"],
        common_confusion_pairs=["Sales Return / Credit Note", "Rejection Out", "Purchase"],
        disambiguation_rule="Distinguish from Sales Return by vendor/creditor recipient and DBN prefix; distinguish from Rejection Out by financial ledger adjustment rather than physical gate pass.",
    ),

    # 4. Sales Return / Credit Note
    "Sales Return / Credit Note": VoucherKnowledgeCard(
        category="Sales Return / Credit Note",
        description="Document issued to a customer acknowledging returned goods and reducing their outstanding accounts receivable.",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Document Number", "CRN", "Credit Note", "Original Invoice Ref", "SAL-", "Units Returned", "Reason for Return"],
        typical_ledgers=["Sales Returns (Dr)", "Output GST Reversal (Dr)", "Sundry Debtors (Cr)"],
        key_signals=["Credit note prefix (CRN)", "Customer return acknowledgment", "Original sales invoice reference"],
        negative_signals=["Debit note prefix (DBN)", "Vendor supplier role"],
        common_confusion_pairs=["Purchase Return / Debit Note", "Rejection In", "Sales"],
        disambiguation_rule="Distinguish from Purchase Return by customer debtor recipient and CRN prefix; distinguish from Rejection In by financial credit adjustment.",
    ),

    # 5. Payment
    "Payment": VoucherKnowledgeCard(
        category="Payment",
        description="Disbursement of liquid funds (bank or cash) to an external supplier, vendor, or creditor settling outstanding payables.",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Payment ID", "Payer Organization", "Payee Organization", "Payment Amount", "Against Invoice"],
        typical_ledgers=["Sundry Creditors (Dr)", "Bank / Cash Account (Cr)"],
        key_signals=["Disbursement to third-party payee", "Settlement against invoice reference", "Payment type / method"],
        negative_signals=["Internal destination bank account", "Receiving organization inward flow"],
        common_confusion_pairs=["Contra", "Receipt", "Expense"],
        disambiguation_rule="Distinguish from Contra by presence of external commercial third-party payee (Contra is strictly internal bank-to-bank).",
    ),

    # 6. Receipt
    "Receipt": VoucherKnowledgeCard(
        category="Receipt",
        description="Collection of liquid funds into the company bank or cash account from a customer or debtor settling outstanding receivables.",
        expected_flow=MoneyFlowDirection.INFLOW,
        primary_identifiers=["Receipt ID", "Receiving Organization", "Paying Organization", "Received Amount", "Against Invoice"],
        typical_ledgers=["Bank / Cash Account (Dr)", "Sundry Debtors (Cr)"],
        key_signals=["Inward monetary collection", "Settlement from paying organization", "Bank deposit details"],
        negative_signals=["Vendor disbursement outflow", "Internal account transfer"],
        common_confusion_pairs=["Payment", "Sales", "Contra"],
        disambiguation_rule="Distinguish from Payment by inward cash/bank flow; distinguish from Sales by liquidation of receivables rather than product revenue billing.",
    ),

    # 7. Contra
    "Contra": VoucherKnowledgeCard(
        category="Contra",
        description="Internal fund repositioning strictly between two internal accounts of the same organization (e.g. Bank to Cash, Bank A to Bank B).",
        expected_flow=MoneyFlowDirection.INTERNAL,
        primary_identifiers=["Contra ID", "Source Account", "Destination Account", "Transfer Amount", "Bank IFSC Code"],
        typical_ledgers=["Destination Bank/Cash (Dr)", "Source Bank/Cash (Cr)"],
        key_signals=["Source Account AND Destination Account present", "Zero external third-party creditor/debtor", "Internal fund repositioning purpose"],
        negative_signals=["Third-party vendor payee", "Customer payer", "GST or tax breakdown"],
        common_confusion_pairs=["Payment", "Receipt", "Journal"],
        disambiguation_rule="Distinguish from Payment and Receipt by lack of any external party; both sending and receiving sides are internal liquid asset accounts.",
    ),

    # 8. Journal
    "Journal": VoucherKnowledgeCard(
        category="Journal",
        description="Non-cash adjusting accounting entry allocating debits and credits for accruals, prepayments, depreciation, or transfers.",
        expected_flow=MoneyFlowDirection.ADJUSTMENT,
        primary_identifiers=["Journal ID", "Debit Side", "Credit Side", "Amount", "Journal Type", "Narration"],
        typical_ledgers=["Expense/Asset Ledger (Dr)", "Liability/Provision Ledger (Cr)"],
        key_signals=["Explicit Debit Side and Credit Side ledgers", "Adjusting entry narration", "Non-cash transaction type"],
        negative_signals=["Physical bank disbursement", "Shipping bill / delivery challan"],
        common_confusion_pairs=["Contra", "Expense", "Stock Journal"],
        disambiguation_rule="Distinguish from Contra by non-cash nominal/real ledger entries rather than bank/cash accounts; distinguish from Stock Journal by general financial accounts rather than item quantities.",
    ),

    # 9. Salary / Payroll
    "Salary / Payroll": VoucherKnowledgeCard(
        category="Salary / Payroll",
        description="Monthly employee compensation processing capturing gross earnings, statutory deductions, and net payable wages.",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Employee Code", "Employee Full Name", "Payroll Period", "Gross Salary", "Net Payable"],
        typical_ledgers=["Salaries & Wages Expense (Dr)", "Provident Fund / Tax Payable (Cr)", "Bank / Net Payable (Cr)"],
        key_signals=["Employee Code and Full Name", "Payroll period format (Month-YYYY)", "Statutory deductions (Professional Tax, Income Tax)"],
        negative_signals=["Vendor invoice", "Item product description", "Customer customer billing"],
        common_confusion_pairs=["Attendance", "Expense", "Payment"],
        disambiguation_rule="Distinguish from Attendance by monetary compensation amounts and tax deductions; distinguish from Expense by payroll period and employee salary codes.",
    ),

    # 10. Attendance
    "Attendance": VoucherKnowledgeCard(
        category="Attendance",
        description="Non-monetary operational record tracking employee daily shift presence, hours worked, overtime, and leave allocations.",
        expected_flow=MoneyFlowDirection.ATTENDANCE_LOG,
        primary_identifiers=["Employee Code", "Days Worked", "Overtime Hours", "Biometric Log", "Attendance ID"],
        typical_ledgers=["None (Operational Non-Financial Ledger)"],
        key_signals=["Days worked, shift count, overtime hours", "Biometric verification", "Absence and leave tracking"],
        negative_signals=["Gross salary amount", "Net payable wages", "Bank disbursement UTR"],
        common_confusion_pairs=["Salary / Payroll"],
        disambiguation_rule="Distinguish from Salary / Payroll by absence of monetary gross/net payment calculations; purely tracks hours and working days.",
    ),

    # 11. Purchase Order
    "Purchase Order": VoucherKnowledgeCard(
        category="Purchase Order",
        description="Commercial procurement commitment issued to a supplier requesting goods at agreed rates before delivery or invoicing.",
        expected_flow=MoneyFlowDirection.ORDER_COMMITMENT,
        primary_identifiers=["PO Number", "Supplier", "Ordering Company", "Quantity Required", "Promised Delivery", "Terms"],
        typical_ledgers=["None (Commitment memo, no general ledger posting)"],
        key_signals=["PO Number prefix", "Promised delivery date", "Quantity required and unit rate terms"],
        negative_signals=["Tax invoice document", "GRN quality status", "Payment UTR receipt"],
        common_confusion_pairs=["Purchase", "Sales Order", "Receipt Note"],
        disambiguation_rule="Distinguish from Purchase by absence of finalized financial liabilities and tax posting; distinguish from Sales Order by supplier vendor destination.",
    ),

    # 12. Sales Order
    "Sales Order": VoucherKnowledgeCard(
        category="Sales Order",
        description="Commercial sales order confirmation received from a customer committing to buy products under specified terms.",
        expected_flow=MoneyFlowDirection.ORDER_COMMITMENT,
        primary_identifiers=["SO Number", "Customer", "Selling Company", "Quantity Ordered", "Payment Terms"],
        typical_ledgers=["None (Commitment memo, no general ledger posting)"],
        key_signals=["SO Number prefix", "Quantity ordered", "Selling company acknowledging customer demand"],
        negative_signals=["Tax invoice billed", "Delivery challan dispatched"],
        common_confusion_pairs=["Sales", "Purchase Order", "Delivery Note"],
        disambiguation_rule="Distinguish from Sales by order booking stage before goods dispatch; distinguish from Purchase Order by customer demand acknowledgment.",
    ),

    # 13. Receipt Note
    "Receipt Note": VoucherKnowledgeCard(
        category="Receipt Note",
        description="Warehouse inward document (GRN) acknowledging physical delivery of ordered goods from a supplier following quality check.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["GRN Number", "Receiving Company", "Item Received", "Quantity Received", "Quality Status", "Storage Location"],
        typical_ledgers=["Inventory Asset (Dr)", "Goods Receipt Clearing (Cr)"],
        key_signals=["GRN Number identifier", "Quality status passed/inspected", "Storage facility location"],
        negative_signals=["Outward dispatch challan", "Commercial billing invoice"],
        common_confusion_pairs=["Purchase", "Material In", "Delivery Note"],
        disambiguation_rule="Distinguish from Purchase by focus on physical intake verification (GRN, Inspected By, Quality Status) without tax ledger posting; distinguish from Material In by standard supplier procurement rather than job work.",
    ),

    # 14. Delivery Note
    "Delivery Note": VoucherKnowledgeCard(
        category="Delivery Note",
        description="Warehouse outward dispatch challan accompanying goods shipped to a customer via transport carrier.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Delivery Challan No", "Dispatch Date", "Item Dispatched", "Quantity Shipped", "Courier/Transport"],
        typical_ledgers=["Goods in Transit (Dr)", "Finished Goods Inventory (Cr)"],
        key_signals=["Delivery Challan No prefix", "Quantity shipped and carrier details", "Delivery address"],
        negative_signals=["Inward goods GRN", "Tax invoice billing"],
        common_confusion_pairs=["Sales", "Material Out", "Receipt Note"],
        disambiguation_rule="Distinguish from Sales by logistical transport document without financial tax ledger entry; distinguish from Material Out by customer fulfillment rather than job work.",
    ),

    # 15. Rejection In
    "Rejection In": VoucherKnowledgeCard(
        category="Rejection In",
        description="Physical receipt and logging of defective goods returned to our warehouse by a receiving organization.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Rejection Note No", "Item Rejected", "Quantity Rejected", "Rejection Reason", "GRN Reference"],
        typical_ledgers=["Rejection Clearing (Dr)", "Quarantine Inventory (Cr)"],
        key_signals=["Inward rejection note logged against GRN", "Item rejected with stated defect reason", "Approved By inspection"],
        negative_signals=["Outward delivery note reference", "Vendor supplier return"],
        common_confusion_pairs=["Rejection Out", "Sales Return / Credit Note"],
        disambiguation_rule="Distinguish from Rejection Out by inward warehouse logging against GRN; distinguish from Sales Return by physical gate receipt rather than financial credit note.",
    ),

    # 16. Rejection Out
    "Rejection Out": VoucherKnowledgeCard(
        category="Rejection Out",
        description="Physical return of substandard goods sent back to a customer or supplier accompanied by a rejection gate pass.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Rejection Note No (RJN-OUT)", "Customer", "Item Rejected", "DN Reference", "Authorized By"],
        typical_ledgers=["Quarantine Inventory (Dr)", "Goods Dispatched (Cr)"],
        key_signals=["Rejection Out document (RJN-OUT)", "Delivery note reference linkage", "Authorized outward return"],
        negative_signals=["Inward GRN receipt"],
        common_confusion_pairs=["Rejection In", "Purchase Return / Debit Note"],
        disambiguation_rule="Distinguish from Rejection In by outward dispatch direction and DN reference; distinguish from Purchase Return by physical goods movement rather than debit note accounting.",
    ),

    # 17. Stock Journal
    "Stock Journal": VoucherKnowledgeCard(
        category="Stock Journal",
        description="Internal inventory entry recording transfers between storage facilities, reclassification, or quantity revaluation.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Stock Adj ID", "Item Name", "Adjustment Qty", "Storage Facility", "Adjustment Date", "Reason"],
        typical_ledgers=["Inventory Variance (Dr/Cr)", "Stock Asset Account (Cr/Dr)"],
        key_signals=["Stock Adj ID identifier", "Storage facility transfer", "Adjustment quantity and unit cost"],
        negative_signals=["Physical audit count discrepancy", "External customer dispatch"],
        common_confusion_pairs=["Physical Stock", "Journal"],
        disambiguation_rule="Distinguish from Physical Stock by deliberate ledger adjustment and facility transfer rather than audit recount; distinguish from Journal by stock item quantities.",
    ),

    # 18. Physical Stock
    "Physical Stock": VoucherKnowledgeCard(
        category="Physical Stock",
        description="Inventory audit entry recording physical stock recount quantities against book records to recognize shrinkage or discrepancy.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Stock Count ID", "Book Quantity", "Counted Quantity", "Discrepancy", "Variance Status"],
        typical_ledgers=["Inventory Shrinkage Expense (Dr)", "Stock Asset (Cr)"],
        key_signals=["Stock Count ID identifier", "Book quantity vs counted quantity comparison", "Discrepancy and variance status"],
        negative_signals=["Inter-warehouse transfer reason", "Sales order commitment"],
        common_confusion_pairs=["Stock Journal"],
        disambiguation_rule="Distinguish from Stock Journal by presence of dual Book Quantity and Counted Quantity comparison detecting physical count discrepancy.",
    ),

    # 19. Material In
    "Material In": VoucherKnowledgeCard(
        category="Material In",
        description="Movement tracking intake of raw materials or components received from a principal or subcontractor for job work processing.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Inward Job Work No (MIW-)", "Material Description", "Storage", "Subcontractor", "Reference PO"],
        typical_ledgers=["Customer Material in Custody (Off-balance tracking)"],
        key_signals=["Inward job work number (MIW)", "Subcontractor party", "Reference PO job work linkage"],
        negative_signals=["Standard commercial supplier purchase", "Outward finished dispatch"],
        common_confusion_pairs=["Receipt Note", "Material Out", "Job Work In Order"],
        disambiguation_rule="Distinguish from Receipt Note by job work material processing purpose; distinguish from Job Work In Order by actual material movement rather than contract booking.",
    ),

    # 20. Material Out
    "Material Out": VoucherKnowledgeCard(
        category="Material Out",
        description="Movement tracking dispatch of materials or processed components sent to a job work contractor.",
        expected_flow=MoneyFlowDirection.NON_FINANCIAL_MOVEMENT,
        primary_identifiers=["Outward Job Work No (MOW-)", "Material Description", "Contractor", "Reference PO"],
        typical_ledgers=["Material at Job Worker (Asset Dr)"],
        key_signals=["Outward job work number (MOW)", "Contractor party", "Subcontracting processing job purpose"],
        negative_signals=["Finished goods customer delivery challan"],
        common_confusion_pairs=["Delivery Note", "Material In", "Job Work Out Order"],
        disambiguation_rule="Distinguish from Delivery Note by dispatch to contractor for processing rather than customer sale; distinguish from Job Work Out Order by physical dispatch movement.",
    ),

    # 21. Job Work In Order
    "Job Work In Order": VoucherKnowledgeCard(
        category="Job Work In Order",
        description="Contractual work order received from a principal engaging our firm to perform processing operations on customer materials.",
        expected_flow=MoneyFlowDirection.ORDER_COMMITMENT,
        primary_identifiers=["JWIO Ref", "Processor", "Principal", "Processing Rate", "Terms", "Order Date"],
        typical_ledgers=["None (Operational commitment memo)"],
        key_signals=["JWIO reference prefix", "Principal party entity", "Processing rate per unit fee"],
        negative_signals=["Service charge payable to subcontractor", "Inward material intake challan"],
        common_confusion_pairs=["Job Work Out Order", "Material In"],
        disambiguation_rule="Distinguish from Job Work Out Order by role as processor receiving order from principal; distinguish from Material In by contract booking rather than physical material receipt.",
    ),

    # 22. Job Work Out Order
    "Job Work Out Order": VoucherKnowledgeCard(
        category="Job Work Out Order",
        description="Contractual subcontracting work order issued to an external contractor outsourcing processing operations on our materials.",
        expected_flow=MoneyFlowDirection.ORDER_COMMITMENT,
        primary_identifiers=["JWOO Ref", "Processor", "Principal", "Service Charge", "Agreement Terms"],
        typical_ledgers=["None (Operational commitment memo)"],
        key_signals=["JWOO reference prefix", "Service charge payable", "Outsourced agreement terms"],
        negative_signals=["Processing rate receivable from principal"],
        common_confusion_pairs=["Job Work In Order", "Material Out"],
        disambiguation_rule="Distinguish from Job Work In Order by our role as principal outsourcing to external processor; distinguish from Material Out by contractual terms rather than dispatch.",
    ),

    # 23. Import
    "Import": VoucherKnowledgeCard(
        category="Import",
        description="Cross-border commercial procurement of goods from a foreign supplier subject to customs duty, CIF valuation, and foreign exchange.",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Import Bill No", "Originating Country", "Importer", "Cost Insurance Freight", "Customs Duty", "Import GST"],
        typical_ledgers=["Import Purchases (Dr)", "Customs Duty Expense (Dr)", "Foreign Supplier Creditor (Cr)"],
        key_signals=["Import Bill No identifier", "Foreign originating country", "Cost Insurance Freight (CIF) valuation and Customs Duty"],
        negative_signals=["Domestic GST only", "Export shipping bill"],
        common_confusion_pairs=["Purchase", "Export"],
        disambiguation_rule="Distinguish from Purchase by foreign originating country, import bill number, and statutory customs duty clearance.",
    ),

    # 24. Export
    "Export": VoucherKnowledgeCard(
        category="Export",
        description="Cross-border commercial supply of goods to an international buyer governed by FOB valuation, shipping bills, and export incentives.",
        expected_flow=MoneyFlowDirection.INFLOW,
        primary_identifiers=["Export Invoice No", "Destination Country", "Exporter", "Free on Board Value", "Freight Charges", "Export Incentive"],
        typical_ledgers=["Foreign Customer Debtor (Dr)", "Export Sales Revenue (Cr)", "Export Incentive Receivable (Dr)"],
        key_signals=["Export Invoice No identifier", "Foreign destination country", "Free on Board (FOB) valuation and export incentive"],
        negative_signals=["Domestic CGST/SGST", "Import customs duty"],
        common_confusion_pairs=["Sales", "Import"],
        disambiguation_rule="Distinguish from Sales by international destination country, export invoice number, and FOB terms.",
    ),

    # 25. Expense
    "Expense": VoucherKnowledgeCard(
        category="Expense",
        description="Operational expenditure claim or petty disbursement incurred for business operations (travel, office supplies, utilities).",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Expense Claim No", "Claim Date", "Expense Type", "Amount Claimed", "Department", "Status", "Approved By"],
        typical_ledgers=["Operating Expense Ledger (Dr)", "Cash / Accounts Payable (Cr)"],
        key_signals=["Expense Claim No identifier", "Amount claimed and expense type", "Departmental approval"],
        negative_signals=["Inventory goods procured for resale", "Gross salary wage payroll"],
        common_confusion_pairs=["Payment", "Purchase", "Salary / Payroll"],
        disambiguation_rule="Distinguish from Purchase by operational/administrative expense rather than stock-in-trade procurement; distinguish from Payment by expense approval claim rather than supplier settlement.",
    ),

    # 26. Advance / Prepayment
    "Advance / Prepayment": VoucherKnowledgeCard(
        category="Advance / Prepayment",
        description="Monetary consideration paid to a supplier or received from a customer prior to the delivery of goods or finalized tax invoice.",
        expected_flow=MoneyFlowDirection.OUTFLOW,
        primary_identifiers=["Advance ID", "Party Name", "Advance Amount", "Purpose", "Proforma Invoice Ref"],
        typical_ledgers=["Advance to Suppliers (Dr) OR Customer Advance Liability (Cr)", "Bank Account (Cr/Dr)"],
        key_signals=["Advance consideration payment", "Proforma invoice linkage", "Pre-delivery booking"],
        negative_signals=["Final tax invoice with full GST output", "Completed goods delivery challan"],
        common_confusion_pairs=["Payment", "Receipt", "Purchase"],
        disambiguation_rule="Distinguish from Payment/Receipt by prepayment status before commercial tax invoice issuance.",
    ),

    # 27. Other / Miscellaneous
    "Other / Miscellaneous": VoucherKnowledgeCard(
        category="Other / Miscellaneous",
        description="Residual non-standard transactions that do not strictly meet the specific criteria of the standard 26 categories.",
        expected_flow=MoneyFlowDirection.UNKNOWN,
        primary_identifiers=["Voucher ID", "Transaction Date", "Amount", "Narration"],
        typical_ledgers=["Suspense / Miscellaneous Account"],
        key_signals=["Non-standard narration", "Scrap sale or petty round-off", "Uncategorized ledger posting"],
        negative_signals=["Clear PO/SO reference", "Clear tax breakdown and standard invoice"],
        common_confusion_pairs=["Journal", "Expense"],
        disambiguation_rule="Only assigned when transaction lacks sufficient distinguishing signals to confidently classify into the specific 26 categories.",
    ),
}
