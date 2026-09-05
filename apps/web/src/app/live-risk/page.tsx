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
  Copy,
  Check,
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
  const [copiedTx, setCopiedTx] = useState<string | null>(null);

  const handleCopyTx = (txId: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(txId);
      setCopiedTx(txId);
      setTimeout(() => setCopiedTx(null), 1800);
    }
  };

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
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-700/80 text-slate-300 hover:text-white hover:border-slate-500 transition-all disabled:opacity-50 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            <span>Refresh Feed</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3.5 rounded-xl glass-card border border-slate-800/80">
        {/* Band Filters */}
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
          <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mr-1 font-semibold">
            <Filter className="w-3.5 h-3.5 text-slate-400" /> Filter:
          </span>
          {[
            { id: "ALL", label: "ALL", color: "bg-slate-800 text-white border-slate-600" },
            { id: "CRITICAL", label: "CRITICAL", color: "bg-rose-500/20 text-rose-400 border-rose-500/50 shadow-rose-950/30" },
            { id: "HIGH", label: "HIGH", color: "bg-orange-500/20 text-orange-400 border-orange-500/50" },
            { id: "MEDIUM", label: "MEDIUM", color: "bg-amber-500/20 text-amber-400 border-amber-500/50" },
            { id: "LOW", label: "LOW", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" },
          ].map((band) => (
            <button
              key={band.id}
              onClick={() => setRiskBand(band.id)}
              className={`px-3 py-1 rounded-md text-xs font-mono font-bold transition-all border ${
                riskBand === band.id
                  ? `${band.color} shadow-sm scale-105`
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50 border-transparent"
              }`}
            >
              {band.label}
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
            className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-9 pr-8 py-1.5 text-xs text-slate-200 placeholder-slate-500 font-mono focus:outline-none focus:border-emerald-500/60 transition-colors"
          />
          {search && (
            <button
              type="button"
              onClick={() => {
                setSearch("");
                loadFeed();
              }}
              className="absolute right-2.5 top-2.5 text-slate-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </form>
      </div>

      {/* Main Data Table */}
      <div className="rounded-xl glass-card border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs table-fixed">
            <thead>
              <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                <th className="py-3 px-3 w-[15%] font-semibold">Transaction</th>
                <th className="py-3 px-3 w-[12%] font-semibold">Merchant</th>
                <th className="py-3 px-3 w-[12%] font-semibold">Customer</th>
                <th className="py-3 px-3 w-[11%] font-semibold">Amount</th>
                <th className="py-3 px-3 w-[8%] font-semibold">Score</th>
                <th className="py-3 px-3 w-[10%] font-semibold">Risk Band</th>
                <th className="py-3 px-3 w-[18%] font-semibold">Primary Reason</th>
                <th className="py-3 px-3 w-[8%] font-semibold">Ring</th>
                <th className="py-3 px-3 w-[6%] font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {feed.length === 0 && loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 font-mono">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                      <span>Streaming live transactions from risk engine...</span>
                    </div>
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
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-2.5 px-3 font-mono text-slate-200">
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="font-semibold text-slate-200 truncate" title={tx.transaction_id}>
                          {tx.transaction_id}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyTx(tx.transaction_id);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700/60 text-slate-400 hover:text-white transition-opacity shrink-0"
                          title="Copy Transaction ID"
                        >
                          {copiedTx === tx.transaction_id ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400 truncate" title={tx.merchant_id}>
                      {tx.merchant_id}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400 truncate" title={tx.customer_id}>
                      {tx.customer_id}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-white whitespace-nowrap">
                      ₹{tx.amount.toLocaleString("en-IN")}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold">
                      <span
                        className={
                          tx.risk_score >= 0.7
                            ? "text-rose-400"
                            : tx.risk_score >= 0.4
                            ? "text-amber-400"
                            : "text-emerald-400"
                        }
                      >
                        {tx.risk_score.toFixed(3)}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border whitespace-nowrap ${getSeverityBadge(
                          tx.risk_band
                        )}`}
                      >
                        {tx.risk_band}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 truncate font-sans text-[11px]" title={tx.primary_reason}>
                      {tx.primary_reason}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-cyan-400 font-semibold truncate" title={tx.ring_id || "—"}>
                      {tx.ring_id || "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectTx(tx);
                          setInvestigationResult(null);
                        }}
                        className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-slate-800/80 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 transition-all hover:border-slate-500 shadow-sm"
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
        <div className="fixed inset-0 z-50 flex justify-end bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl h-full bg-[#0B0F19] border-l border-slate-800 shadow-2xl flex flex-col p-6 overflow-y-auto space-y-6">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-white font-mono">{inspectTx.transaction_id}</h2>
                    <button
                      onClick={() => handleCopyTx(inspectTx.transaction_id)}
                      className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
                      title="Copy ID"
                    >
                      {copiedTx === inspectTx.transaction_id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-slate-400 font-mono">Real-Time Risk Scoring Telemetry</p>
                </div>
              </div>
              <button
                onClick={() => setInspectTx(null)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Core Summary Cards */}
            <div className="grid grid-cols-3 gap-3 font-mono">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Amount</div>
                <div className="text-lg font-bold text-white mt-1">₹{inspectTx.amount.toLocaleString("en-IN")}</div>
                <div className="text-[10px] text-emerald-400 mt-0.5 font-semibold">{inspectTx.payment_method.toUpperCase()}</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">ML Risk Score</div>
                <div className="text-lg font-bold text-rose-400 mt-1">{inspectTx.risk_score.toFixed(4)}</div>
                <div className="text-[10px] text-rose-400 font-semibold mt-0.5">BAND: {inspectTx.risk_band}</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Fraud Ring Link</div>
                <div className="text-lg font-bold text-cyan-400 mt-1">{inspectTx.ring_id || "Standalone"}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Multi-Hop Cluster</div>
              </div>
            </div>

            {/* SHAP Reason Codes */}
            <div className="space-y-2.5">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                ML Model Interpretability (TreeSHAP)
              </h3>
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3 text-xs font-mono">
                <div className="flex items-start gap-2.5 text-slate-100">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 flex-shrink-0" />
                  <span className="font-semibold">{inspectTx.primary_reason}</span>
                </div>
                <div className="flex items-start gap-2.5 text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                  <span>Abnormal customer velocity pattern across short retrospective evaluation window</span>
                </div>
                <div className="flex items-start gap-2.5 text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 mt-1.5 flex-shrink-0" />
                  <span>Hardware fingerprint mismatch against customer historical baseline</span>
                </div>
              </div>
            </div>

            {/* Entity Links */}
            <div className="space-y-2.5">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                Infrastructure & Entities
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold">Customer ID</span>
                    <div className="text-white font-semibold mt-0.5">{inspectTx.customer_id}</div>
                  </div>
                  <button
                    onClick={() => handleCopyTx(inspectTx.customer_id)}
                    className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-white"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold">Merchant ID</span>
                    <div className="text-white font-semibold mt-0.5">{inspectTx.merchant_id}</div>
                  </div>
                  <button
                    onClick={() => handleCopyTx(inspectTx.merchant_id)}
                    className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-white"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Trigger Agent Investigation Action */}
            <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3.5 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <Bot className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-white font-mono">Autonomous Risk Investigator</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
                  LANGGRAPH AGENT
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Dispatch the autonomous AI agent to execute multi-hop graph expansion, extract observable evidence facts, and generate a human-actionable dossier.
              </p>

              <button
                onClick={() => handleStartInvestigation(inspectTx.transaction_id)}
                disabled={investigating}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-950/40 disabled:opacity-50 font-mono"
              >
                {investigating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Synthesizing Evidence Across 9 Tools...</span>
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
                <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-emerald-500/40 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" /> Case Created: {investigationResult.case_id}
                    </span>
                    <a
                      href={`/investigations?case=${investigationResult.case_id}`}
                      className="text-[11px] font-mono text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
                    >
                      <span>Open Dossier</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="text-xs text-slate-300 font-mono">
                    <span className="text-slate-400">Recommendation:</span>{" "}
                    <span className="text-rose-400 font-bold">
                      {investigationResult.report?.recommended_action || "HOLD"}
                    </span>{" "}
                    <span className="text-slate-400">
                      (Confidence: {((investigationResult.report?.confidence || 0.95) * 100).toFixed(0)}%)
                    </span>
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
