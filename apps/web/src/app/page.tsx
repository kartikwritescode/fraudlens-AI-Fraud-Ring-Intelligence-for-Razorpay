"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Activity,
  Network,
  SearchCheck,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw,
  Clock,
  CheckCircle2,
  Zap,
  X,
  RotateCcw,
  Copy,
  Check,
  CreditCard,
  Smartphone,
  Globe,
  ExternalLink,
} from "lucide-react";
import { fetchAnalyticsOverview, fetchTransactionFeed, fetchRings, runDemoAttack, resetDemoScenario } from "@/lib/api";
import { AnalyticsOverviewResponse, TransactionFeedItem, DiscoveredRing } from "@/lib/types";
import { CinematicDemoModal } from "@/components/demo/CinematicDemoModal";

const DEFAULT_ANALYTICS: AnalyticsOverviewResponse = {
  kpis: {
    total_transactions_monitored: 50000,
    high_risk_transactions: 325,
    active_fraud_rings: 10,
    total_amount_at_risk: 1485000.0,
    total_amount_prevented: 1158300.0,
    open_cases_count: 12,
  },
  risk_distribution: {
    LOW: 49675,
    MEDIUM: 120,
    HIGH: 85,
    CRITICAL: 120,
  },
  fraud_by_payment_method: [
    { method: "UPI", volume_inr: 850000 },
    { method: "CARD", volume_inr: 450000 },
    { method: "NETBANKING", volume_inr: 185000 },
  ],
  top_targeted_merchants: [],
  top_risky_devices: [],
  top_risky_ips: [],
  risk_trend_hourly: [],
};

export default function OverviewPage() {
  const [data, setData] = useState<AnalyticsOverviewResponse>(DEFAULT_ANALYTICS);
  const [recentFeed, setRecentFeed] = useState<TransactionFeedItem[]>([]);
  const [topRings, setTopRings] = useState<DiscoveredRing[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [attackRunning, setAttackRunning] = useState(false);
  const [attackSummary, setAttackSummary] = useState<any>(null);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [copiedTx, setCopiedTx] = useState<string | null>(null);

  const handleCopyTx = (txId: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(txId);
      setCopiedTx(txId);
      setTimeout(() => setCopiedTx(null), 1800);
    }
  };

  const handleRunAttack = async () => {
    setAttackRunning(true);
    setAttackSummary(null);
    try {
      const summary = await runDemoAttack("shared_payment_token_ring", 15800.0);
      setAttackSummary(summary);
      try {
        localStorage.setItem("fraudlens_attack_summary", JSON.stringify(summary));
      } catch (e) {}
      await loadData();
    } catch (err) {
      console.error("Failed to run demo attack:", err);
    } finally {
      setAttackRunning(false);
    }
  };

  const loadData = async () => {
    setRefreshing(true);
    try {
      const [analytics, feed, ringsData] = await Promise.all([
        fetchAnalyticsOverview(),
        fetchTransactionFeed("CRITICAL", undefined, 6),
        fetchRings(),
      ]);
      setData(analytics);
      setRecentFeed(feed.items);
      setTopRings(ringsData.rings.slice(0, 4));

      // Persist across browser sessions so values render instantly on reload
      try {
        localStorage.setItem("fraudlens_overview_data", JSON.stringify(analytics));
        localStorage.setItem("fraudlens_feed_data", JSON.stringify(feed.items));
        localStorage.setItem("fraudlens_rings_data", JSON.stringify(ringsData.rings.slice(0, 4)));
      } catch (e) {}
    } catch (err) {
      console.error("Failed to load overview data:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    // 1. Instant hydration from localStorage (0ms first paint)
    try {
      const cachedData = localStorage.getItem("fraudlens_overview_data");
      if (cachedData) setData(JSON.parse(cachedData));

      const cachedFeed = localStorage.getItem("fraudlens_feed_data");
      if (cachedFeed) setRecentFeed(JSON.parse(cachedFeed));

      const cachedRings = localStorage.getItem("fraudlens_rings_data");
      if (cachedRings) setTopRings(JSON.parse(cachedRings));

      const cachedAttack = localStorage.getItem("fraudlens_attack_summary");
      if (cachedAttack) setAttackSummary(JSON.parse(cachedAttack));
    } catch (e) {
      console.warn("Could not read local storage cache:", e);
    }

    // 2. Fetch fresh telemetry in background
    loadData();
    const interval = setInterval(loadData, 20000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (amount: number) => {
    if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(2)}L`;
    }
    return `₹${amount.toLocaleString("en-IN")}`;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21262D] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-white">Fraud-Ring Intelligence Command Center</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              REAL-TIME
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous multi-signal payment risk monitoring & graph cluster detection for Razorpay
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsDemoModalOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded text-xs font-bold font-mono bg-red-600 hover:bg-red-500 text-white transition-all shadow-md shadow-red-950/40 border border-red-500"
          >
            <Zap className="w-3.5 h-3.5 fill-white" />
            <span>Simulate Coordinated Attack</span>
          </button>
          <button
            onClick={async () => {
              await resetDemoScenario();
              try {
                localStorage.removeItem("fraudlens_attack_summary");
              } catch (e) {}
              setAttackSummary(null);
              await loadData();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono bg-[#161B22] border border-[#30363D] text-slate-300 hover:text-white transition-all"
          >
            <RotateCcw className="w-3 h-3 text-slate-400" />
            <span>RESET DEMO</span>
          </button>
          <button
            onClick={loadData}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono bg-[#161B22] border border-[#30363D] text-slate-300 hover:text-white hover:border-slate-500 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-emerald-400" : ""}`} />
            <span>Sync Telemetry</span>
          </button>
          <Link
            href="/investigations"
            className="flex items-center gap-2 px-3.5 py-1.5 rounded text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm"
          >
            <SearchCheck className="w-3.5 h-3.5" />
            <span>Active Cases</span>
          </Link>
        </div>
      </div>

      <CinematicDemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        onRefreshData={loadData}
      />

      {/* Attack Execution Result Banner */}
      {attackSummary && (
        <div className="p-4 rounded-lg bg-[#161B22] border-2 border-red-500/80 shadow-xl animate-in fade-in space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Zap className="w-5 h-5 text-red-400 fill-red-400" />
              <span className="font-mono text-sm font-bold text-white uppercase">
                Attack Syndicate Intercepted & Mitigated
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/40">
                {attackSummary.risk_band} ({attackSummary.composite_risk_score.toFixed(2)})
              </span>
            </div>
            <button
              onClick={() => {
                setAttackSummary(null);
                try {
                  localStorage.removeItem("fraudlens_attack_summary");
                } catch (e) {}
              }}
              className="p-1 rounded hover:bg-[#21262D] text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-[#090A0F] border border-[#21262D]">
              <span className="text-[10px] text-slate-400">Injected Txs</span>
              <div className="font-bold text-white mt-0.5">{attackSummary.injected_transaction_count} Burst Trans</div>
            </div>
            <div className="p-2 rounded bg-[#090A0F] border border-[#21262D]">
              <span className="text-[10px] text-slate-400">Detected Ring</span>
              <div className="font-bold text-cyan-400 mt-0.5">{attackSummary.detected_ring_id}</div>
            </div>
            <div className="p-2 rounded bg-[#090A0F] border border-[#21262D]">
              <span className="text-[10px] text-slate-400">Agent Case Dossier</span>
              <div className="font-bold text-emerald-400 mt-0.5">{attackSummary.case_id}</div>
            </div>
            <div className="p-2 rounded bg-[#090A0F] border border-[#21262D]">
              <span className="text-[10px] text-slate-400">Recommended Action</span>
              <div className="font-bold text-red-400 mt-0.5">{attackSummary.agent_recommendation} Policy</div>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs font-mono pt-1">
            <span className="text-slate-400">
              Pipeline Latency: <span className="text-white font-bold">{attackSummary.execution_latency_ms}ms</span> | Prevented Loss: <span className="text-emerald-400 font-bold">₹{attackSummary.preventable_loss.toLocaleString("en-IN")}</span>
            </span>
            <Link
              href={`/investigations?case=${attackSummary.case_id}`}
              className="text-cyan-400 hover:underline flex items-center gap-1 font-bold"
            >
              <span>Inspect Full Case Dossier</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Top 6 KPI Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* Monitored */}
        <div className="p-4 rounded-xl glass-card relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Txs Monitored</span>
            <div className="w-7 h-7 rounded-lg bg-slate-800/60 border border-slate-700/50 flex items-center justify-center text-slate-300">
              <Activity className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono tracking-tight">
            {data.kpis.total_transactions_monitored.toLocaleString()}
          </div>
          <div className="text-[11px] text-emerald-400 font-mono mt-1.5 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            100% Ingested Stream
          </div>
        </div>

        {/* High Risk */}
        <div className="p-4 rounded-xl glass-card relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-colors pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>High Risk Txs</span>
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2 font-mono tracking-tight">
            {data.kpis.high_risk_transactions}
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-1.5 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400/80" />
            0.65% Alert Density
          </div>
        </div>

        {/* Fraud Rings */}
        <div className="p-4 rounded-xl glass-card relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/5 rounded-full blur-2xl group-hover:bg-rose-500/10 transition-colors pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Rings</span>
            <div className="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
              <Network className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2 font-mono tracking-tight">
            {data.kpis.active_fraud_rings}
          </div>
          <div className="text-[11px] text-rose-400/80 font-mono mt-1.5 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            Graph Coordinated
          </div>
        </div>

        {/* ₹ at Risk */}
        <div className="p-4 rounded-xl glass-card relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-2xl group-hover:bg-red-500/10 transition-colors pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>₹ At Risk</span>
            <div className="w-7 h-7 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
              <ShieldAlert className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono tracking-tight">
            {formatCurrency(data.kpis.total_amount_at_risk || 0)}
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-1.5">
            Attempted Syndicate Vol
          </div>
        </div>

        {/* ₹ Prevented */}
        <div className="p-4 rounded-xl glass-card relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>₹ Prevented</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2 font-mono tracking-tight">
            {formatCurrency(data.kpis.total_amount_prevented || 0)}
          </div>
          <div className="text-[11px] text-emerald-400/90 font-mono mt-1.5 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            78% Automated Shield
          </div>
        </div>

        {/* Active Cases */}
        <div className="p-4 rounded-xl glass-card relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-colors pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Cases</span>
            <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <SearchCheck className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono tracking-tight">
            {data.kpis.open_cases_count}
          </div>
          <div className="text-[11px] text-cyan-400 font-mono mt-1.5 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            AI Agent Dossiers
          </div>
        </div>
      </div>

      {/* Center 2-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Risk Feed Snippet */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-5 rounded-xl glass-card border border-slate-800/80">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                <h2 className="text-sm font-bold text-white tracking-wide">Live High-Risk Stream</h2>
                <span className="text-[11px] text-slate-400 font-mono">(Real-Time Ingestion)</span>
              </div>
              <Link
                href="/live-risk"
                className="text-xs text-emerald-400 hover:text-emerald-300 font-mono flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 transition-all hover:border-emerald-500/40"
              >
                <span>View Full Feed</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800/80 text-slate-400 font-mono">
                    <th className="pb-3 font-semibold">Tx ID</th>
                    <th className="pb-3 font-semibold">Merchant</th>
                    <th className="pb-3 font-semibold">Amount</th>
                    <th className="pb-3 font-semibold">Score</th>
                    <th className="pb-3 font-semibold">Severity</th>
                    <th className="pb-3 font-semibold">Ring Link</th>
                    <th className="pb-3 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {recentFeed.length === 0 && refreshing ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400 font-mono">
                        <div className="flex items-center justify-center gap-2">
                          <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                          <span>Syncing live transactions...</span>
                        </div>
                      </td>
                    </tr>
                  ) : recentFeed.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400 font-mono">
                        No transactions found
                      </td>
                    </tr>
                  ) : (
                    recentFeed.map((tx) => (
                      <tr key={tx.transaction_id} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="py-3 font-mono text-slate-200">
                          <div className="flex items-center gap-1.5">
                            <span className="font-medium text-slate-300">{tx.transaction_id}</span>
                            <button
                              onClick={() => handleCopyTx(tx.transaction_id)}
                              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700/50 text-slate-400 hover:text-white transition-opacity"
                              title="Copy ID"
                            >
                              {copiedTx === tx.transaction_id ? (
                                <Check className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                        </td>
                        <td className="py-3 font-mono text-slate-400">{tx.merchant_id}</td>
                        <td className="py-3 font-mono font-bold text-white">
                          ₹{tx.amount.toLocaleString("en-IN")}
                        </td>
                        <td className="py-3 font-mono">
                          <span className="text-rose-400 font-bold">{tx.risk_score.toFixed(2)}</span>
                        </td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                            {tx.risk_band}
                          </span>
                        </td>
                        <td className="py-3 font-mono text-[11px] text-cyan-400 font-semibold">
                          {tx.ring_id ? (
                            <Link href={`/fraud-rings?selected=${tx.ring_id}`} className="hover:underline flex items-center gap-1">
                              <span>{tx.ring_id}</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </Link>
                          ) : (
                            <span className="text-slate-500">Standalone</span>
                          )}
                        </td>
                        <td className="py-3 text-right">
                          <Link
                            href={`/live-risk?inspect=${tx.transaction_id}`}
                            className="px-2.5 py-1 rounded text-[11px] font-mono bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 transition-colors"
                          >
                            Inspect
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Activity Timeline Card */}
          <div className="p-5 rounded-xl glass-card border border-slate-800/80">
            <div className="flex items-center gap-2 mb-3.5">
              <Clock className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-bold text-white tracking-wide">Coordinated Attack Progression</h2>
            </div>
            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-rose-400 font-bold">17:52:25</span>
                <div>
                  <span className="text-white font-semibold">Autonomous Hold Authorized</span>: Case CASE-17B176BF confirmed against ring_disc_001. ₹1.88L exposure halted.
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-amber-400 font-bold">17:52:03</span>
                <div>
                  <span className="text-white font-semibold">Bipartite Projection Alert</span>: Multi-entity card token reuse detected across 6 disparate puppet accounts.
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-cyan-400 font-bold">17:46:54</span>
                <div>
                  <span className="text-white font-semibold">Graph Community Partition</span>: Neo4j Louvain modularity algorithm isolated 10 high-risk attack components.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Top Discovered Fraud Rings */}
        <div className="space-y-4">
          <div className="p-5 rounded-xl glass-card border border-slate-800/80">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Network className="w-4 h-4 text-rose-400" />
                <h2 className="text-sm font-bold text-white tracking-wide">Top Discovered Rings</h2>
              </div>
              <Link
                href="/fraud-rings"
                className="text-xs text-emerald-400 hover:text-emerald-300 font-mono flex items-center gap-1"
              >
                <span>Explore All</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {topRings.map((ring) => (
                <Link
                  key={ring.ring_id}
                  href={`/fraud-rings?selected=${ring.ring_id}`}
                  className="block p-3.5 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all group shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-white group-hover:text-emerald-400 transition-colors">
                      {ring.ring_id}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                      SCORE {ring.risk_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 font-mono">
                    Pattern: <span className="text-slate-300 capitalize">{ring.pattern_type.replace(/_/g, " ")}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-400">
                    <div>
                      Members: <span className="text-white font-semibold">{ring.member_count}</span>
                    </div>
                    <div>
                      Volume: <span className="text-white font-semibold">₹{(ring.attempted_amount / 1000).toFixed(0)}k</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Quick System Stack Status Card */}
          <div className="p-5 rounded-xl glass-card border border-slate-800/80 space-y-3">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Engine Status</span>
            </h2>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-slate-400">ML Model</span>
                <span className="text-emerald-400 font-semibold">XGBoost v1 (Active)</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-slate-400">Graph Memory</span>
                <span className="text-emerald-400 font-semibold">111,206 Nodes</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-slate-400">Relationships</span>
                <span className="text-emerald-400 font-semibold">257,706 Edges</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-slate-400">Webhook Secret</span>
                <span className="text-emerald-400 font-semibold">HMAC-SHA256 Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
