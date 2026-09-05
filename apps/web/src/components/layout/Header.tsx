"use client";

import React from "react";
import { RefreshCw, ShieldCheck, Cpu, Database, Network } from "lucide-react";
import { DeepHealthResponse } from "@/lib/types";

interface HeaderProps {
  health: DeepHealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, loading, onRefresh }) => {
  const isApiOnline = health?.services?.api?.status === "healthy";
  const isPgOnline = health?.services?.postgresql?.status === "healthy";
  const isNeoOnline = health?.services?.neo4j?.status === "healthy";

  const overallHealthy = health?.status === "healthy";

  return (
    <header className="h-16 bg-[#0a0d15] border-b border-[#1a2333] px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left Environment Context */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-2.5 py-1 bg-[#121826] border border-[#1e293b] rounded">
          <span className="w-2 h-2 rounded-full bg-blue-400" />
          <span className="text-[11px] font-mono font-medium text-slate-300">RAZORPAY TESTNET</span>
        </div>
        <span className="text-slate-600 text-sm">/</span>
        <span className="text-xs font-mono text-slate-400">Risk Manager Session: #ADM-FL-2026</span>
      </div>

      {/* Right Quick Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        {/* Service Mini Status Pills */}
        <div className="flex items-center gap-2 text-xs font-mono bg-[#0f1422] border border-[#1a2333] rounded px-3 py-1.5">
          {/* API */}
          <div className="flex items-center gap-1.5" title="FastAPI Gateway">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-400">API:</span>
            <span
              className={`w-2 h-2 rounded-full ${
                isApiOnline ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
          </div>

          <span className="text-slate-700">|</span>

          {/* Postgres */}
          <div className="flex items-center gap-1.5" title="PostgreSQL 16">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-400">PG:</span>
            <span
              className={`w-2 h-2 rounded-full ${
                isPgOnline ? "bg-emerald-400" : "bg-slate-600"
              }`}
            />
          </div>

          <span className="text-slate-700">|</span>

          {/* Neo4j */}
          <div className="flex items-center gap-1.5" title="Neo4j 5.20 Graph">
            <Network className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-400">Neo4j:</span>
            <span
              className={`w-2 h-2 rounded-full ${
                isNeoOnline ? "bg-emerald-400" : "bg-slate-600"
              }`}
            />
          </div>
        </div>

        {/* Global Cluster Status */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono border ${
            overallHealthy
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : isApiOnline
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
              : "bg-red-500/10 border-red-500/30 text-red-400"
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              overallHealthy
                ? "bg-emerald-400 animate-pulse"
                : isApiOnline
                ? "bg-amber-400"
                : "bg-red-400"
            }`}
          />
          <span className="font-semibold uppercase tracking-wider text-[11px]">
            {overallHealthy ? "OPERATIONAL" : isApiOnline ? "DEGRADED (STANDBY)" : "OFFLINE"}
          </span>
        </div>

        {/* Refresh Diagnostics */}
        <button
          onClick={onRefresh}
          disabled={loading}
          title="Probe System Health"
          className="p-2 rounded bg-[#141b2a] border border-[#1e293b] text-slate-300 hover:text-white hover:bg-[#1a2337] transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
        </button>

        {/* User Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#1a2333]">
          <div className="w-7 h-7 rounded bg-emerald-950/80 border border-emerald-700/50 flex items-center justify-center text-xs font-mono font-bold text-emerald-300">
            RZ
          </div>
          <div className="text-[11px]">
            <div className="font-semibold text-slate-200">Risk Analyst</div>
            <div className="text-slate-400 font-mono text-[10px]">Razorpay Team</div>
          </div>
        </div>
      </div>
    </header>
  );
};
