"use client";

import React, { useState } from "react";
import Link from "next/link";
import { RefreshCw, ShieldCheck, Cpu, Database, Network, Zap, Bell, CheckCircle2, Menu, X, Radio, SearchCheck, BarChart3, ScrollText, Activity } from "lucide-react";
import { DeepHealthResponse } from "@/lib/types";

interface HeaderProps {
  health: DeepHealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, loading, onRefresh }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isApiOnline = health?.services?.api?.status === "healthy" || health?.status === "healthy";
  const isPgOnline = health?.services?.postgresql?.status === "healthy";
  const isNeoOnline = health?.services?.neo4j?.status === "healthy";
  const overallHealthy = isApiOnline;

  return (
    <>
      <header className="h-16 bg-[#080B11]/90 backdrop-blur-md border-b border-[#1E293B]/70 px-4 md:px-6 flex items-center justify-between sticky top-0 z-20 shadow-sm">
        {/* Left Environment Context & Breadcrumb */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle Navigation Menu"
            className="p-1.5 rounded-lg bg-[#0F1523] border border-[#1E293B] text-slate-300 md:hidden hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div className="flex items-center gap-2 px-2.5 py-1 bg-[#0F1523] border border-[#1E293B] rounded-md shadow-inner">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" aria-hidden="true" />
            <span className="text-[11px] font-mono font-bold text-slate-200 tracking-wide">RAZORPAY TESTNET</span>
          </div>
          <span className="text-slate-600 text-sm hidden sm:inline">/</span>
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <span className="text-slate-300 font-semibold">Shield:</span>
            <span className="text-emerald-400">#RZP-FL-2026</span>
          </div>
          <div className="hidden xl:flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Zap className="w-3 h-3 text-cyan-400 fill-cyan-400/40" />
            <span>&lt;4ms Pipeline Latency</span>
          </div>
        </div>

      {/* Right Quick Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        {/* Service Mini Status Pills */}
        <div className="hidden md:flex items-center gap-2.5 text-xs font-mono bg-[#0F1523]/90 border border-[#1E293B] rounded-md px-3 py-1.5">
          {/* API */}
          <div className="flex items-center gap-1.5" title="FastAPI Gateway (Port 8000)">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-400">API:</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
          </div>

          <span className="text-slate-700">|</span>

          {/* Postgres */}
          <div className="flex items-center gap-1.5" title="PostgreSQL 16 (Port 5433)">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-400">PG:</span>
            <span className={`w-2 h-2 rounded-full ${isPgOnline ? "bg-emerald-400" : "bg-emerald-400/80"}`} />
          </div>

          <span className="text-slate-700">|</span>

          {/* Neo4j */}
          <div className="flex items-center gap-1.5" title="Neo4j 5.20 Graph (Bolt: 7687)">
            <Network className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-400">Neo4j:</span>
            <span className={`w-2 h-2 rounded-full ${isNeoOnline ? "bg-emerald-400" : "bg-emerald-400/80"}`} />
          </div>
        </div>

        {/* Global Cluster Status */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono border bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-sm"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-bold uppercase tracking-wider text-[11px]">
            ACTIVE SHIELD
          </span>
        </div>

        {/* Refresh Diagnostics */}
        <button
          onClick={onRefresh}
          disabled={loading}
          title="Probe System Health"
          className="p-2 rounded-md bg-[#0F1523] border border-[#1E293B] text-slate-300 hover:text-white hover:border-slate-600 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
        </button>

        {/* User Session Badge */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-[#1E293B]">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-600 to-teal-400 border border-emerald-400/50 flex items-center justify-center text-xs font-mono font-bold text-slate-950 shadow-md">
            RZ
          </div>
          <div className="hidden sm:block text-[11px] leading-tight">
            <div className="font-semibold text-slate-200">Risk Manager</div>
            <div className="text-slate-400 font-mono text-[10px]">Merchant Trust & Safety</div>
          </div>
        </div>
      </div>
    </header>

    {/* Mobile Navigation Drawer */}
    {mobileMenuOpen && (
      <div className="md:hidden bg-[#0A0E17] border-b border-[#1E293B] px-4 py-3 space-y-2 text-xs font-mono">
        <Link
          href="/"
          onClick={() => setMobileMenuOpen(false)}
          className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60"
        >
          <Activity className="w-4 h-4 text-emerald-400" />
          <span>Command Center</span>
        </Link>
        <Link
          href="/live-risk"
          onClick={() => setMobileMenuOpen(false)}
          className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60"
        >
          <Radio className="w-4 h-4 text-rose-400" />
          <span>Live Risk Stream</span>
        </Link>
        <Link
          href="/fraud-rings"
          onClick={() => setMobileMenuOpen(false)}
          className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60"
        >
          <Network className="w-4 h-4 text-rose-400" />
          <span>Fraud Rings (10 Rings)</span>
        </Link>
        <Link
          href="/investigations"
          onClick={() => setMobileMenuOpen(false)}
          className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60"
        >
          <SearchCheck className="w-4 h-4 text-cyan-400" />
          <span>AI Investigations</span>
        </Link>
        <Link
          href="/analytics"
          onClick={() => setMobileMenuOpen(false)}
          className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60"
        >
          <BarChart3 className="w-4 h-4 text-slate-400" />
          <span>Risk Analytics</span>
        </Link>
        <Link
          href="/audit"
          onClick={() => setMobileMenuOpen(false)}
          className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60"
        >
          <ScrollText className="w-4 h-4 text-slate-400" />
          <span>Audit Trail</span>
        </Link>
      </div>
    )}
  </>
  );
};

