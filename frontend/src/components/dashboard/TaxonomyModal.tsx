"use client";

import React, { useState, useEffect } from "react";
import { api, TaxonomyListResponse, TaxonomyCardResponse } from "@/lib/api";
import { getVoucherDefinition } from "@/lib/voucherCategoryDefinitions";
import { Button } from "../ui/Button";

interface TaxonomyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function TaxonomyModal({ isOpen, onClose }: TaxonomyModalProps) {
  const [data, setData] = useState<TaxonomyListResponse | null>(null);
  const [selectedCard, setSelectedCard] = useState<TaxonomyCardResponse | null>(null);
  const [search, setSearch] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    const loadTaxonomy = async () => {
      setIsLoading(true);
      try {
        const res = await api.getTaxonomy();
        setData(res);
        if (res.knowledge_cards.length > 0) {
          setSelectedCard(res.knowledge_cards[0]);
        }
      } catch {
        // error handling
      } finally {
        setIsLoading(false);
      }
    };
    loadTaxonomy();
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredCards = (data?.knowledge_cards || []).filter((c) =>
    c.category_name.toLowerCase().includes(search.toLowerCase()) ||
    c.expected_flow.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
      <div className="bg-[#0B0805] border border-[rgba(191,145,51,0.3)] rounded-lg w-full max-w-5xl max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#050505]">
          <div>
            <h3 className="font-serif text-lg font-bold text-[#F4EBDD]">
              Authoritative Taxonomy &amp; Knowledge Cards (27 Classes)
            </h3>
            <p className="text-xs text-[#A69A87] font-mono mt-0.5">
              Authoritative accounting profiles, expected flows, debit/credit ledgers, and disambiguation rules.
            </p>
          </div>

          <button
            onClick={onClose}
            className="text-[#A69A87] hover:text-[#F4EBDD] p-1.5 rounded hover:bg-white/5 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content Split: Left List, Right Card Detail */}
        <div className="grid grid-cols-1 md:grid-cols-12 flex-1 overflow-hidden">
          {/* Left Cards List */}
          <div className="md:col-span-4 border-r border-white/10 flex flex-col bg-[#050505]/50 overflow-hidden">
            <div className="p-3 border-b border-white/5">
              <input
                type="text"
                placeholder="Filter voucher cards..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3 py-1.5 bg-[#11100E] border border-[rgba(191,145,51,0.2)] rounded text-xs text-[#F4EBDD] placeholder-[#A69A87]/50 focus:border-[#F0AE2C] focus:outline-none"
              />
            </div>

            <div className="overflow-y-auto flex-1 divide-y divide-white/5">
              {isLoading ? (
                <div className="p-8 text-center text-xs text-[#A69A87]">
                  Loading knowledge cards...
                </div>
              ) : (
                filteredCards.map((card) => (
                  <button
                    key={card.card_id}
                    onClick={() => setSelectedCard(card)}
                    className={`w-full text-left p-3.5 transition-colors flex items-center justify-between text-xs ${
                      selectedCard?.card_id === card.card_id
                        ? "bg-[#F0AE2C]/10 border-l-2 border-[#F0AE2C] text-[#F0AE2C] font-semibold"
                        : "text-[#A69A87] hover:bg-white/[0.02] hover:text-[#F4EBDD]"
                    }`}
                  >
                    <span className="truncate max-w-[200px]">{card.category_name}</span>
                    <span className="text-[10px] font-mono text-[#A69A87]/70 uppercase">
                      {card.primary_prefixes[0] || ""}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Right Selected Card Detail */}
          <div className="md:col-span-8 p-6 overflow-y-auto space-y-5 bg-[#0B0805]">
            {selectedCard ? (
              <>
                <div className="pb-4 border-b border-white/5">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#F0AE2C]">
                    CARD ID: {selectedCard.card_id}
                  </span>
                  <h4 className="font-serif text-2xl font-bold text-[#F4EBDD] mt-1">
                    {selectedCard.category_name}
                  </h4>
                  <p className="text-xs text-[#A69A87] mt-1 font-mono">
                    Flow: {selectedCard.expected_flow}
                  </p>
                </div>

                {/* Authoritative User-Facing Category Definition */}
                {(() => {
                  const def = getVoucherDefinition(selectedCard.category_name);
                  if (!def) return null;
                  return (
                    <div className="p-4 bg-[#11100E] rounded border border-[rgba(191,145,51,0.25)] space-y-3">
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-[#F0AE2C] font-semibold block">
                          What It Means
                        </span>
                        <p className="text-xs text-[#F4EBDD] mt-0.5 leading-relaxed">
                          {def.meaning}
                        </p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                          When Typically Used
                        </span>
                        <p className="text-xs text-[#A69A87] mt-0.5 leading-relaxed">
                          {def.typicalUse}
                        </p>
                      </div>
                      <div className="pt-2 border-t border-white/5">
                        <span className="text-[10px] uppercase tracking-wider text-[#F0AE2C] font-semibold block mb-1">
                          Illustrative Accounting Transaction
                        </span>
                        <code className="text-[11px] block p-2 rounded bg-black/60 border border-white/10 font-mono text-[#F4EBDD] break-words whitespace-pre-wrap">
                          {def.exampleTransaction}
                        </code>
                      </div>
                    </div>
                  );
                })()}

                {/* Ledgers */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-[#11100E] rounded border border-white/5">
                    <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold block">
                      Typical Debit Ledger
                    </span>
                    <span className="text-xs text-[#F4EBDD] font-mono mt-1 block">
                      {selectedCard.typical_debit_ledger}
                    </span>
                  </div>
                  <div className="p-3 bg-[#11100E] rounded border border-white/5">
                    <span className="text-[10px] uppercase tracking-wider text-amber-400 font-semibold block">
                      Typical Credit Ledger
                    </span>
                    <span className="text-xs text-[#F4EBDD] font-mono mt-1 block">
                      {selectedCard.typical_credit_ledger}
                    </span>
                  </div>
                </div>

                {/* ERP Prefixes & Documents */}
                <div className="p-3.5 bg-[#11100E] rounded border border-white/5 space-y-2">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    ERP Identifiers &amp; Documents
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCard.primary_prefixes.map((p) => (
                      <span
                        key={p}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F0AE2C]/10 border border-[#F0AE2C]/30 text-[#F0AE2C]"
                      >
                        Prefix: {p}
                      </span>
                    ))}
                    {selectedCard.typical_documents.map((d) => (
                      <span
                        key={d}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/50 border border-white/10 text-[#A69A87]"
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Key Signals */}
                <div className="p-3.5 bg-[#11100E] rounded border border-white/5 space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    Positive Detection Signals
                  </span>
                  <div className="space-y-1">
                    {selectedCard.key_signals.map((sig, i) => (
                      <div key={i} className="text-xs text-[#F4EBDD] flex items-start gap-1.5">
                        <span className="text-[#F0AE2C]">&bull;</span>
                        <span>{sig}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Disambiguation Rules */}
                <div className="p-3.5 bg-[#11100E] rounded border border-white/5 space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A69A87] font-semibold block">
                    Disambiguation &amp; Borderline Rules
                  </span>
                  <div className="space-y-1">
                    {selectedCard.disambiguation_rules.map((rule, i) => (
                      <div key={i} className="text-xs text-amber-200/90 flex items-start gap-1.5">
                        <span className="text-amber-400 font-bold">&rarr;</span>
                        <span>{rule}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="p-12 text-center text-[#A69A87] text-xs">
                Select a knowledge card to view details.
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 flex items-center justify-end bg-[#050505]">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close Explorer
          </Button>
        </div>
      </div>
    </div>
  );
}
