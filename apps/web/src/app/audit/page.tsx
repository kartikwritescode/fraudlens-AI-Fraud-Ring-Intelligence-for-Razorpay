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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <ScrollText className="w-4 h-4 text-emerald-400" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Immutable Security Audit Trail</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
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
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono glass-card border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-800 transition-all disabled:opacity-50 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            <span>Sync Ledger</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2 p-3 rounded-xl glass-card border border-slate-800/80 shadow-md">
        <Filter className="w-3.5 h-3.5 text-slate-400 ml-1" />
        <span className="text-xs font-mono text-slate-400 font-semibold mr-1">Severity:</span>
        {["ALL", "CRITICAL", "HIGH", "INFO"].map((sev) => (
          <button
            key={sev}
            onClick={() => setFilterSeverity(sev)}
            className={`px-3 py-1 rounded-lg text-xs font-mono transition-all ${
              filterSeverity === sev
                ? "bg-slate-800 text-white border border-slate-600 shadow-sm font-bold"
                : "text-slate-400 hover:text-white hover:bg-slate-800/40 border border-transparent"
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Timeline List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 font-mono text-xs glass-card rounded-xl border border-slate-800/80">
            <RefreshCw className="w-5 h-5 animate-spin text-emerald-400 mx-auto mb-2" />
            Loading cryptographic audit records...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 font-mono text-xs glass-card rounded-xl border border-slate-800/80">
            No audit records matching criteria.
          </div>
        ) : (
          filteredLogs.map((log, idx) => {
            const Icon = getActorIcon(log.actor);
            return (
              <div
                key={idx}
                className="p-4 rounded-xl glass-card border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs hover:border-slate-700/80 transition-all shadow-md"
              >
                <div className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-center justify-center shrink-0 text-emerald-400 shadow-inner">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-bold">{log.action}</span>
                      <span className={`px-2 py-0.2 rounded-full text-[10px] font-bold border ${getSeverityBadge(log.severity)}`}>
                        {log.severity}
                      </span>
                      {log.case_id && log.case_id !== "N/A" && (
                        <span className="text-[11px] text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                          {log.case_id}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-300 text-[11px] mt-1.5 font-sans leading-relaxed">{log.details}</p>
                    <div className="text-[10px] text-slate-400 mt-2 flex items-center gap-2.5">
                      <span>Actor: <span className="text-slate-200 font-semibold">{log.actor}</span></span>
                      <span>•</span>
                      <span>Result: <span className="text-emerald-400 font-bold">{log.result}</span></span>
                    </div>
                  </div>
                </div>

                <div className="text-right text-[11px] text-slate-400 shrink-0 font-mono bg-slate-950/40 px-3 py-1.5 rounded-lg border border-slate-800/60">
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
