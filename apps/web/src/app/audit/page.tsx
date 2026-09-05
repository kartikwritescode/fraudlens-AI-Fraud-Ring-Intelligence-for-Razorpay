"use client";

import React, { useState, useEffect } from "react";
import {
  ScrollText,
  ShieldCheck,
  Filter,
  User,
  Bot,
  Radio,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { fetchAuditLogs } from "@/lib/api";
import { AuditLogEntry } from "@/lib/types";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await fetchAuditLogs(50);
      setLogs(res);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const filteredLogs = logs.filter((l) => {
    if (filterSeverity !== "ALL" && l.severity !== filterSeverity) return false;
    return true;
  });

  const getActorIcon = (actor: string) => {
    if (actor.toLowerCase().includes("agent")) return Bot;
    if (actor.toLowerCase().includes("webhook") || actor.toLowerCase().includes("gateway")) return Radio;
    return User;
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "HIGH":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21262D] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <ScrollText className="w-5 h-5 text-emerald-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Immutable Security Audit Trail</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              CRYPTOGRAPHIC LEDGER
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Chronological log of autonomous AI agent runs, human analyst sign-offs, and Razorpay webhook events
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadLogs}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono bg-[#161B22] border border-[#30363D] text-slate-300 hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            <span>Sync Trail</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2 p-3 rounded-lg bg-[#161B22] border border-[#30363D]">
        <Filter className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs font-mono text-slate-400">Severity:</span>
        {["ALL", "CRITICAL", "HIGH", "INFO"].map((sev) => (
          <button
            key={sev}
            onClick={() => setFilterSeverity(sev)}
            className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
              filterSeverity === sev
                ? "bg-[#21262D] text-white border border-slate-500 shadow-sm"
                : "text-slate-400 hover:text-white hover:bg-[#21262D]/50 border border-transparent"
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Timeline List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 font-mono text-xs">
            Loading cryptographic audit records...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 font-mono text-xs">
            No audit records matching criteria.
          </div>
        ) : (
          filteredLogs.map((log, idx) => {
            const Icon = getActorIcon(log.actor);
            return (
              <div
                key={idx}
                className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs hover:border-slate-500/40 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded bg-[#090A0F] border border-[#21262D] flex items-center justify-center shrink-0 text-emerald-400">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-bold">{log.action}</span>
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold border ${getSeverityBadge(log.severity)}`}>
                        {log.severity}
                      </span>
                      {log.case_id && log.case_id !== "N/A" && (
                        <span className="text-[11px] text-cyan-400 underline">{log.case_id}</span>
                      )}
                    </div>
                    <p className="text-slate-300 text-[11px] mt-1 font-sans">{log.details}</p>
                    <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-2">
                      <span>Actor: <span className="text-slate-300 font-semibold">{log.actor}</span></span>
                      <span>•</span>
                      <span>Result: <span className="text-emerald-400">{log.result}</span></span>
                    </div>
                  </div>
                </div>

                <div className="text-right text-[11px] text-slate-400 shrink-0 font-mono">
                  {log.timestamp}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
