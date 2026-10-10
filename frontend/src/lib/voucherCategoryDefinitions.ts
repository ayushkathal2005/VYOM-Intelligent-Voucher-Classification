/**
 * Authoritative user-facing definitions for all 27 canonical voucher categories in VYOM+.
 * Each category includes:
 * - meaning: What the voucher category represents in accounting.
 * - typicalUse: When it is typically used in business operations.
 * - exampleTransaction: Short illustrative accounting transaction with Dr/Cr accounts.
 */

export interface VoucherCategoryDefinition {
  name: string;
  meaning: string;
  typicalUse: string;
  exampleTransaction: string;
  flowDirection: "Inflow" | "Outflow" | "Internal" | "Order Commitment" | "Non-Financial Movement";
}

export const VOUCHER_CATEGORY_DEFINITIONS: Record<string, VoucherCategoryDefinition> = {
  "Purchase": {
    name: "Purchase",
    meaning: "Records goods or commercial services procured from a supplier or vendor, recognizing an accounts payable liability and input tax credit.",
    typicalUse: "Used upon receiving a supplier's tax invoice for inventory, raw materials, or commercial goods.",
    exampleTransaction: "Dr. Purchases A/c $5,000, Dr. Input GST $900 | Cr. Sundry Creditor (Supplier) $5,900",
    flowDirection: "Outflow",
  },
  "Sales": {
    name: "Sales",
    meaning: "Records goods or commercial services billed to an external customer or buyer, recognizing revenue and output tax liability.",
    typicalUse: "Used when issuing a finalized commercial sales tax invoice for goods dispatched or services rendered.",
    exampleTransaction: "Dr. Sundry Debtor (Customer) $11,800 | Cr. Sales Revenue A/c $10,000, Cr. Output GST $1,800",
    flowDirection: "Inflow",
  },
  "Purchase Return / Debit Note": {
    name: "Purchase Return / Debit Note",
    meaning: "Records goods returned to a supplier or a downward cost adjustment, reducing the company's payable liability.",
    typicalUse: "Used when returning defective supplier goods or claiming price corrections against an original purchase invoice.",
    exampleTransaction: "Dr. Sundry Creditor $1,180 | Cr. Purchase Returns A/c $1,000, Cr. Input GST Reversal $180",
    flowDirection: "Inflow",
  },
  "Sales Return / Credit Note": {
    name: "Sales Return / Credit Note",
    meaning: "Records customer returns or post-sale allowances, reducing accounts receivable and output tax obligations.",
    typicalUse: "Used when acknowledging defective goods sent back by a buyer or issuing customer volume rebates.",
    exampleTransaction: "Dr. Sales Returns A/c $2,000, Dr. Output GST Reversal $360 | Cr. Sundry Debtor $2,360",
    flowDirection: "Outflow",
  },
  "Payment": {
    name: "Payment",
    meaning: "Records liquid disbursements made via bank or cash to an external vendor, supplier, or creditor settling outstanding payables.",
    typicalUse: "Used when paying supplier invoices, settling vendor balances, or remitting dues via EFT/check/cash.",
    exampleTransaction: "Dr. Sundry Creditors A/c $5,000 | Cr. HDFC Bank A/c $5,000",
    flowDirection: "Outflow",
  },
  "Receipt": {
    name: "Receipt",
    meaning: "Records liquid funds collected into company bank accounts or cash drawers from a customer or debtor settling outstanding dues.",
    typicalUse: "Used when customer payments are credited to bank accounts against past sales invoices.",
    exampleTransaction: "Dr. ICICI Bank A/c $10,000 | Cr. Sundry Debtors (Customer) $10,000",
    flowDirection: "Inflow",
  },
  "Contra": {
    name: "Contra",
    meaning: "Records internal fund transfers strictly between the business's own cash and bank accounts with zero external counterparties.",
    typicalUse: "Used for cash deposits into bank, ATM withdrawals for petty cash, or transfers between two company bank accounts.",
    exampleTransaction: "Dr. State Bank of India A/c $25,000 | Cr. Cash in Hand A/c $25,000",
    flowDirection: "Internal",
  },
  "Journal": {
    name: "Journal",
    meaning: "Records non-cash accounting adjustments, accruals, prepayments, depreciation, and closing balance transfers.",
    typicalUse: "Used during month-end closes for accruals, depreciation charges, or rectifying ledger misallocations.",
    exampleTransaction: "Dr. Depreciation Expense A/c $4,500 | Cr. Accumulated Depreciation A/c $4,500",
    flowDirection: "Internal",
  },
  "Salary / Payroll": {
    name: "Salary / Payroll",
    meaning: "Records employee payroll disbursements, salary liabilities, employer statutory contributions, and tax withholdings.",
    typicalUse: "Used for monthly wage calculation slips, executive remuneration, and payroll ledger bookings.",
    exampleTransaction: "Dr. Salaries & Wages Expense $80,000 | Cr. TDS Payable $8,000, Cr. Net Salary Payable $72,000",
    flowDirection: "Outflow",
  },
  "Attendance": {
    name: "Attendance",
    meaning: "Records employee attendance logs, shifts worked, leaves, and overtime hours before payroll processing.",
    typicalUse: "Used to record biometric muster rolls, timesheets, and contractor workdays (non-financial operational record).",
    exampleTransaction: "Operational record: 24 active workdays, 2 approved leaves logged for Employee EMP-402 (No direct ledger posting)",
    flowDirection: "Non-Financial Movement",
  },
  "Purchase Order": {
    name: "Purchase Order",
    meaning: "Records a formal commercial commitment placed with a supplier before goods delivery or invoice issuance.",
    typicalUse: "Used when issuing an approved purchase requisition to an external vendor for 100 units of raw materials.",
    exampleTransaction: "Contractual commitment memo: PO-2026-88 issued for 500 units steel @ $45/unit (Zero financial ledger impact until invoice)",
    flowDirection: "Order Commitment",
  },
  "Sales Order": {
    name: "Sales Order",
    meaning: "Records an accepted commercial order from a customer prior to product dispatch or revenue recognition.",
    typicalUse: "Used upon confirming a client's purchase request to reserve inventory and schedule manufacturing.",
    exampleTransaction: "Contractual commitment memo: SO-1049 confirmed for 200 units widget @ $80/unit (Zero revenue booked until billed)",
    flowDirection: "Order Commitment",
  },
  "Receipt Note": {
    name: "Receipt Note",
    meaning: "Records physical warehouse intake of goods received from a supplier against a Purchase Order (Goods Receipt Note / GRN).",
    typicalUse: "Used by warehouse security and storekeepers upon physical inspection and gate-entry of supplier shipments.",
    exampleTransaction: "Dr. Warehouse Stores Inventory A/c | Cr. GRN Clearing A/c (Physical verification of 100 units received)",
    flowDirection: "Non-Financial Movement",
  },
  "Delivery Note": {
    name: "Delivery Note",
    meaning: "Records physical goods dispatched and outbound transit to a customer (Delivery Challan) prior to or alongside billing.",
    typicalUse: "Used by shipping dispatchers accompanying carrier consignments delivering orders to customer sites.",
    exampleTransaction: "Dr. Goods in Transit A/c | Cr. Finished Goods Inventory A/c (Challan DC-902 dispatched with transporter)",
    flowDirection: "Non-Financial Movement",
  },
  "Rejection In": {
    name: "Rejection In",
    meaning: "Records physical receipt and quarantine logging of defective goods returned to our warehouse by a receiving organization.",
    typicalUse: "Used by warehouse QA when customers return damaged goods at the gate before financial credit note processing.",
    exampleTransaction: "Dr. Quarantine Defective Stock A/c | Cr. Goods Return Clearing A/c (50 rejected units placed in QA quarantine)",
    flowDirection: "Non-Financial Movement",
  },
  "Rejection Out": {
    name: "Rejection Out",
    meaning: "Records physical return and outward dispatch of substandard goods sent back to a supplier or subcontractor accompanied by an outward rejection gate pass.",
    typicalUse: "Used when factory receiving rejects defective supplier raw materials at inspection and loads them onto outbound trucks.",
    exampleTransaction: "Dr. Supplier Rejection Clearing A/c | Cr. Warehouse Raw Stores A/c (Gate pass RJN-OUT issued for 20 defective motors)",
    flowDirection: "Non-Financial Movement",
  },
  "Stock Journal": {
    name: "Stock Journal",
    meaning: "Records internal inventory movements, warehouse-to-warehouse transfers, kit assembly, and quantity/grade revaluation.",
    typicalUse: "Used when transferring 1,000kg of flour from Central Silo to Processing Plant #2 or converting raw material into finished bundles.",
    exampleTransaction: "Dr. Plant 2 Inventory A/c $15,000 | Cr. Central Warehouse Inventory A/c $15,000",
    flowDirection: "Non-Financial Movement",
  },
  "Physical Stock": {
    name: "Physical Stock",
    meaning: "Records physical audit stock recount quantities against book records to recognize inventory shrinkage, spoilage, or surpluses.",
    typicalUse: "Used during quarterly inventory audits when physical count reveals 98 units on shelves while book ledger shows 100 units.",
    exampleTransaction: "Dr. Inventory Shrinkage Expense A/c $240 | Cr. Stock on Hand Asset A/c $240 (Reconciles 2 missing units)",
    flowDirection: "Non-Financial Movement",
  },
  "Material In": {
    name: "Material In",
    meaning: "Tracks physical intake of raw materials or components received from a principal or subcontractor for job work processing.",
    typicalUse: "Used when a client sends 500 meters of raw fabric to our facility for subcontracted dyeing and printing.",
    exampleTransaction: "Off-balance custody ledger: 500m customer fabric logged under Job Work Material In Challan MIW-77",
    flowDirection: "Non-Financial Movement",
  },
  "Material Out": {
    name: "Material Out",
    meaning: "Tracks physical dispatch of raw materials or components sent to an external job worker or subcontractor for processing.",
    typicalUse: "Used when dispatching metal sheets from our factory to an external laser cutting contractor.",
    exampleTransaction: "Dr. Materials in Custody of Job Worker A/c | Cr. Stores Inventory A/c (Outward challan MOW-412)",
    flowDirection: "Non-Financial Movement",
  },
  "Job Work In Order": {
    name: "Job Work In Order",
    meaning: "Contractual work order received from a principal engaging our firm to perform processing operations on customer materials.",
    typicalUse: "Used when our company operates as the contracted job worker receiving a processing order and fee agreement from a client.",
    exampleTransaction: "Contractual commitment memo: JWIO-55 agreed with Principal ABC to dye 2,000 meters fabric @ $2.50/m processing charge",
    flowDirection: "Order Commitment",
  },
  "Job Work Out Order": {
    name: "Job Work Out Order",
    meaning: "Contractual subcontracting work order issued to an external contractor outsourcing processing operations on our materials.",
    typicalUse: "Used when our company acts as principal engaging an outside job worker to perform specialized electroplating on our components.",
    exampleTransaction: "Contractual commitment memo: JWOO-109 issued to Job Worker XYZ agreeing to pay $4.00/unit plating fee upon completion",
    flowDirection: "Order Commitment",
  },
  "Import": {
    name: "Import",
    meaning: "Records cross-border commercial procurement of goods from an overseas supplier, involving customs duties, CIF valuation, and foreign exchange.",
    typicalUse: "Used when purchasing overseas machinery or inventory shipped by international suppliers under Bill of Entry.",
    exampleTransaction: "Dr. Import Purchases A/c $50,000, Dr. Basic Customs Duty $5,000, Dr. IGST $9,900 | Cr. Overseas Vendor A/c $50,000, Cr. Customs Duty Payable $14,900",
    flowDirection: "Outflow",
  },
  "Export": {
    name: "Export",
    meaning: "Records cross-border commercial sales of goods or services billed to foreign buyers, with zero-rated tax, shipping bills, and foreign currency.",
    typicalUse: "Used when shipping manufactured products to international customers under Letter of Undertaking (LUT) or export invoice.",
    exampleTransaction: "Dr. Foreign Debtor A/c (USD 12,000 @ ₹83) ₹996,000 | Cr. Export Sales A/c ₹996,000 (Zero GST under LUT)",
    flowDirection: "Inflow",
  },
  "Expense": {
    name: "Expense",
    meaning: "Records operational overhead costs, administrative expenditures, and service bills necessary for daily business operations.",
    typicalUse: "Used when recording electricity bills, office rent, internet subscriptions, legal retainers, or travel reimbursements.",
    exampleTransaction: "Dr. Electricity Expense A/c $1,200, Dr. Input GST $216 | Cr. Utility Payable / Cash A/c $1,416",
    flowDirection: "Outflow",
  },
  "Advance / Prepayment": {
    name: "Advance / Prepayment",
    meaning: "Records funds disbursed or received ahead of invoice generation or service fulfillment (deferred asset or unearned liability).",
    typicalUse: "Used when receiving a 30% advance deposit from a customer before project kickoff or paying an upfront vendor retainer.",
    exampleTransaction: "Dr. Advance to Suppliers (Current Asset) $10,000 | Cr. Bank A/c $10,000",
    flowDirection: "Outflow",
  },
  "Other / Miscellaneous": {
    name: "Other / Miscellaneous",
    meaning: "Records rare, non-standard, or unclassified transactions requiring specialist auditor review or secondary clarification.",
    typicalUse: "Used as a quarantine classification for anomalous bank entries, ambiguous foreign receipts, or unidentified vouchers.",
    exampleTransaction: "Dr. Suspense Clearing A/c $850 | Cr. Bank A/c $850 (Flagged for senior auditor investigation)",
    flowDirection: "Non-Financial Movement",
  },
};

/**
 * Helper to normalize and retrieve the definition for any category string.
 */
export function getVoucherDefinition(categoryName: string): VoucherCategoryDefinition | undefined {
  if (!categoryName) return undefined;
  if (VOUCHER_CATEGORY_DEFINITIONS[categoryName]) {
    return VOUCHER_CATEGORY_DEFINITIONS[categoryName];
  }
  const clean = categoryName.trim().toLowerCase().replace(/[\s\/\-_]/g, "");
  for (const [key, val] of Object.entries(VOUCHER_CATEGORY_DEFINITIONS)) {
    if (key.toLowerCase().replace(/[\s\/\-_]/g, "") === clean) {
      return val;
    }
  }
  return undefined;
}
