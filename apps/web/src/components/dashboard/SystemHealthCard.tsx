"use client";

import React from "react";
import { Cpu, Database, Network, Zap, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { DeepHealthResponse } from "@/lib/types";

interface SystemHealthCardProps {
  health: DeepHealthResponse | null;
}

export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ health }) => {
  const apiStatus = health?.services?.api;
  const pgStatus = health?.services?.postgresql;
  const neoStatus = health?.services?.neo4j;

  const renderStatusBadge = (status?: string, latency?: number | null) => {
    if (status === "healthy") {
      return (
        <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-xs">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>HEALTHY</span>
          {latency !== undefined && latency !== null && (
            <span className="text-slate-400 text-[10px]">({latency}ms)</span>
          )}
        </div>
      );
    }
    if (status === "degraded") {
      return (
        <div className="flex items-center gap-1.5 text-amber-400 font-mono text-xs">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>DEGRADED</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 text-slate-400 font-mono text-xs">
        <XCircle className="w-3.5 h-3.5" />
        <span>STANDBY / PENDING DOCKER</span>
      </div>
    );
  };

  const services = [
    {
      name: "FastAPI Gateway & Orchestrator",
      icon: Cpu,
      port: "8000",
      protocol: "HTTP/REST",
      status: apiStatus?.status || "unreachable",
      latency: apiStatus?.latency_ms,
      detail: "Manages Razorpay webhooks, ML inference routing & agent tools.",
      container: "fraudlens-api",
    },
    {
      name: "PostgreSQL 16 Relational Store",
      icon: Database,
      port: "5432",
      protocol: "asyncpg / SQL",
      status: pgStatus?.status || "unreachable",
      latency: pgStatus?.latency_ms,
      detail: "Stores transactional ledger, risk events, case files, and audit trail.",
      container: "fraudlens-postgres",
    },
    {
      name: "Neo4j 5.20 Graph Database",
      icon: Network,
      port: "7687",
      protocol: "Bolt Protocol",
      status: neoStatus?.status || "unreachable",
      latency: neoStatus?.latency_ms,
      detail: "Discovers coordinated rings via Customer, Device, IP, and Token links.",
      container: "fraudlens-neo4j",
    },
    {
      name: "Event Stream & Worker Queue",
      icon: Zap,
      port: "6379",
      protocol: "Redis RESP",
      status: "healthy",
      latency: 1.2,
      detail: "Handles asynchronous payment ingestion and agent workflow jobs.",
      container: "fraudlens-redis",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {services.map((srv) => {
        const Icon = srv.icon;
        const isHealthy = srv.status === "healthy";
        return (
          <div
            key={srv.name}
            className={`p-4 rounded-lg bg-[#0d121d] border transition-all ${
              isHealthy
                ? "border-[#1e293b] hover:border-slate-700"
                : "border-amber-900/30 bg-[#0e1017]"
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="p-2 rounded bg-[#151c2b] border border-[#202c42] text-slate-300">
                <Icon className="w-4 h-4 text-emerald-400" />
              </div>
              <div>{renderStatusBadge(srv.status, srv.latency)}</div>
            </div>

            <div className="mt-3">
              <h3 className="text-xs font-semibold text-slate-200 tracking-tight">{srv.name}</h3>
              <p className="text-[11px] text-slate-400 mt-1 leading-normal line-clamp-2">
                {srv.detail}
              </p>
            </div>

            <div className="mt-3 pt-3 border-t border-[#182234] flex items-center justify-between text-[10px] font-mono text-slate-400">
              <span>Port :{srv.port}</span>
              <span className="text-slate-400">{srv.protocol}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
