"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  ShieldAlert,
  Bot,
  Activity,
  X,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
} from "lucide-react";
import { fetchTransactionFeed, triggerAgentInvestigation } from "@/lib/api";
import { TransactionFeedItem } from "@/lib/types";

export default function LiveRiskPage() {
  const [feed, setFeed] = useState<TransactionFeedItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [riskBand, setRiskBand] = useState("ALL");
  const [search, setSearch] = useState("");
  const [inspectTx, setInspectTx] = useState<TransactionFeedItem | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [investigationResult, setInvestigationResult] = useState<any>(null);

  const loadFeed = async () => {
    setLoading(true);
    try {
      const data = await fetchTransactionFeed(riskBand, search || undefined, 60, 0);
      setFeed(data.items);
      setTotal(data.total);
      try {
        localStorage.setItem("fraudlens_live_feed", JSON.stringify(data));
      } catch (e) {}
    } catch (err) {
      console.error("Failed to load feed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    try {
      const cached = localStorage.getItem("fraudlens_live_feed");
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed.items && parsed.items.length > 0) {
          setFeed(parsed.items);
          setTotal(parsed.total);
        }
      }
    } catch (e) {}
  }, []);

  useEffect(() => {
    loadFeed();
  }, [riskBand]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadFeed();
  };

  const handleStartInvestigation = async (txId: string) => {
    setInvestigating(true);
    try {
      const res = await triggerAgentInvestigation(txId);
      setInvestigationResult(res);
    } catch (err) {
      console.error("Investigation failed:", err);
    } finally {
      setInvestigating(false);
    }
  };

  const getSeverityBadge = (band: string) => {
    switch (band) {
      case "CRITICAL":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "HIGH":
        return "bg-orange-500/10 text-orange-400 border-orange-500/20";
      case "MEDIUM":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21262D] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <Radio className="w-5 h-5 text-red-400 animate-pulse" />
            <h1 className="text-xl font-bold tracking-tight text-white">Live Transaction Risk Stream</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              {total} TRANSACTIONS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time transaction authorization scoring powered by XGBoost & TreeSHAP explainability
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadFeed}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono bg-[#161B22] border border-[#30363D] text-slate-300 hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            <span>Refresh Feed</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-lg bg-[#161B22] border border-[#30363D]">
        {/* Band Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
          <span className="text-xs text-slate-400 font-mono flex items-center gap-1 mr-1">
            <Filter className="w-3.5 h-3.5" /> Severity:
          </span>
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((band) => (
            <button
              key={band}
              onClick={() => setRiskBand(band)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                riskBand === band
                  ? "bg-[#21262D] text-white border border-slate-500 shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-[#21262D]/50 border border-transparent"
              }`}
            >
              {band}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search tx, customer, merchant..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#090A0F] border border-[#30363D] rounded pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 font-mono focus:outline-none focus:border-slate-500"
          />
        </form>
      </div>

      {/* Main Data Table */}
      <div className="rounded-lg bg-[#161B22] border border-[#30363D] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-[#090A0F]/60 border-b border-[#21262D] text-slate-400 font-mono">
                <th className="py-3 px-4 font-medium">Transaction ID</th>
                <th className="py-3 px-4 font-medium">Merchant</th>
                <th className="py-3 px-4 font-medium">Customer ID</th>
                <th className="py-3 px-4 font-medium">Amount</th>
                <th className="py-3 px-4 font-medium">Score</th>
                <th className="py-3 px-4 font-medium">Risk Band</th>
                <th className="py-3 px-4 font-medium">Primary Reason</th>
                <th className="py-3 px-4 font-medium">Ring Link</th>
                <th className="py-3 px-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262D]">
              {feed.length === 0 && loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 font-mono">
                    Streaming live transactions from risk engine...
                  </td>
                </tr>
              ) : feed.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 font-mono">
                    No transactions matching selected criteria.
                  </td>
                </tr>
              ) : (
                feed.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    onClick={() => {
                      setInspectTx(tx);
                      setInvestigationResult(null);
                    }}
                    className="hover:bg-[#21262D]/50 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-white">{tx.transaction_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{tx.merchant_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{tx.customer_id}</td>
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      ₹{tx.amount.toLocaleString("en-IN")}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold">
                      <span
                        className={
                          tx.risk_score >= 0.7
                            ? "text-red-400"
                            : tx.risk_score >= 0.4
                            ? "text-amber-400"
                            : "text-emerald-400"
                        }
                      >
                        {tx.risk_score.toFixed(3)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getSeverityBadge(
                          tx.risk_band
                        )}`}
                      >
                        {tx.risk_band}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs truncate" title={tx.primary_reason}>
                      {tx.primary_reason}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-cyan-400">
                      {tx.ring_id || "—"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectTx(tx);
                          setInvestigationResult(null);
                        }}
                        className="px-2.5 py-1 rounded text-[11px] font-mono bg-[#21262D] hover:bg-[#30363D] text-slate-200 transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over Inspection Drawer / Modal */}
      {inspectTx && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl h-full bg-[#161B22] border-l border-[#30363D] flex flex-col p-6 overflow-y-auto space-y-6">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-[#21262D] pb-4">
              <div className="flex items-center gap-3">
                <ShieldAlert className="w-5 h-5 text-red-400" />
                <div>
                  <h2 className="text-base font-bold text-white font-mono">{inspectTx.transaction_id}</h2>
                  <p className="text-xs text-slate-400">Transaction Authorization Audit</p>
                </div>
              </div>
              <button
                onClick={() => setInspectTx(null)}
                className="p-1.5 rounded hover:bg-[#21262D] text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Core Summary Cards */}
            <div className="grid grid-cols-3 gap-3 font-mono">
              <div className="p-3 rounded bg-[#090A0F] border border-[#21262D]">
                <div className="text-[10px] text-slate-400">Amount</div>
                <div className="text-base font-bold text-white mt-1">₹{inspectTx.amount.toLocaleString("en-IN")}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{inspectTx.payment_method.toUpperCase()}</div>
              </div>
              <div className="p-3 rounded bg-[#090A0F] border border-[#21262D]">
                <div className="text-[10px] text-slate-400">ML Risk Score</div>
                <div className="text-base font-bold text-red-400 mt-1">{inspectTx.risk_score.toFixed(4)}</div>
                <div className="text-[10px] text-red-400/80 mt-0.5">BAND: {inspectTx.risk_band}</div>
              </div>
              <div className="p-3 rounded bg-[#090A0F] border border-[#21262D]">
                <div className="text-[10px] text-slate-400">Fraud Ring Link</div>
                <div className="text-base font-bold text-cyan-400 mt-1">{inspectTx.ring_id || "None"}</div>
                <div className="text-[10px] text-cyan-400/80 mt-0.5">Graph Coordinated</div>
              </div>
            </div>

            {/* SHAP Reason Codes */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                ML Model Interpretability (TreeSHAP)
              </h3>
              <div className="p-3 rounded bg-[#090A0F] border border-[#21262D] space-y-2 text-xs font-mono">
                <div className="flex items-center gap-2 text-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                  <span>{inspectTx.primary_reason}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span>Retrospective rolling customer velocity spike detected (5m & 1h window)</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                  <span>Device fingerprint mismatch against historical customer baseline</span>
                </div>
              </div>
            </div>

            {/* Entity Links */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                Infrastructure & Entities
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D]">
                  <span className="text-slate-400">Customer ID:</span>
                  <div className="text-white mt-0.5">{inspectTx.customer_id}</div>
                </div>
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D]">
                  <span className="text-slate-400">Merchant ID:</span>
                  <div className="text-white mt-0.5">{inspectTx.merchant_id}</div>
                </div>
              </div>
            </div>

            {/* Trigger Agent Investigation Action */}
            <div className="p-4 rounded-lg bg-[#090A0F] border border-[#30363D] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-white font-mono">AI Investigation Agent</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  LangGraph
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Execute controlled autonomous evidence synthesis, 2-hop graph expansion, and financial loss comparison.
              </p>

              <button
                onClick={() => handleStartInvestigation(inspectTx.transaction_id)}
                disabled={investigating}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm disabled:opacity-50 font-mono"
              >
                {investigating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Investigating via 9 Controlled Tools...</span>
                  </>
                ) : (
                  <>
                    <Bot className="w-4 h-4" />
                    <span>Launch Autonomous AI Investigation</span>
                  </>
                )}
              </button>

              {/* Result Dossier Snippet */}
              {investigationResult && (
                <div className="mt-4 p-4 rounded bg-[#161B22] border border-emerald-500/40 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" /> Case Created: {investigationResult.case_id}
                    </span>
                    <a
                      href={`/investigations?case=${investigationResult.case_id}`}
                      className="text-[11px] font-mono text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      <span>Open Dossier</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="text-xs text-slate-300 font-mono">
                    <span className="text-slate-400">Recommendation:</span>{" "}
                    <span className="text-red-400 font-bold">
                      {investigationResult.report?.recommended_action || "HOLD"}
                    </span>{" "}
                    (Confidence: {(investigationResult.report?.confidence * 100).toFixed(0)}%)
                  </div>
                  <p className="text-xs text-slate-400 italic">
                    "{investigationResult.report?.executive_summary}"
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
