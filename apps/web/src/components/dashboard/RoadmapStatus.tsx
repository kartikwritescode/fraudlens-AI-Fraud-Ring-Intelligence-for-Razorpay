"use client";

import React from "react";
import { CheckCircle2, Clock, CircleDot, ShieldAlert } from "lucide-react";

export const RoadmapStatus: React.FC = () => {
  const modules = [
    {
      id: "ingestion",
      title: "Payment Telemetry & Ingestion",
      status: "OPERATIONAL",
      items: [
        "Razorpay Test & Live Webhook Ingestion",
        "Constant-time HMAC-SHA256 signature verification",
        "Sliding idempotency cache with replay mitigation",
        "Dual-mode event streaming & simulated bursts",
      ],
    },
    {
      id: "ml_engine",
      title: "ML Risk Engine & SHAP Explainability",
      status: "OPERATIONAL",
      items: [
        "XGBoost v1: 0.971 PR-AUC, 96.8% Recall, 0.09% FPR",
        "Sub-4ms inference pipeline with TreeSHAP attributions",
        "Retrospective velocity & card instrument reuse signals",
        "Risk band classification: LOW, MEDIUM, HIGH, CRITICAL",
      ],
    },
    {
      id: "graph_engine",
      title: "Fraud Graph Intelligence",
      status: "OPERATIONAL",
      items: [
        "Bipartite entity network (Customer, Device, IP, Token)",
        "Louvain community detection for syndicate isolation",
        "Interactive React Flow cluster visualization",
        "Real-time neighbor expansion & ring timeline tracking",
      ],
    },
    {
      id: "ai_agent",
      title: "Autonomous AI Investigation Agent",
      status: "OPERATIONAL",
      items: [
        "LangGraph 8-node investigative state machine",
        "9 typed verification tools & hypothesis evaluation",
        "Deterministic financial impact & expected loss matrices",
        "Synthesized investigative dossiers with proof citations",
      ],
    },
    {
      id: "orchestrator",
      title: "Unified Pipeline Orchestrator",
      status: "OPERATIONAL",
      items: [
        "Composite scoring combining ML score & Graph ring risk",
        "Configurable policy weights & threshold automation",
        "Least-harmful actions: ALLOW, MONITOR, STEP-UP, HOLD",
        "Automated case generation for high-severity alerts",
      ],
    },
    {
      id: "governance",
      title: "Forensic Audit & Governance",
      status: "OPERATIONAL",
      items: [
        "Cryptographically hashed immutable audit ledger",
        "Human-in-the-loop analyst approval checkpoints",
        "Role-based access control (RBAC) security enforcement",
        "Instant drill simulation & reproducible state recovery",
      ],
    },
  ];

  return (
    <div className="bg-[#0c101a] border border-[#1a2333] rounded-lg p-5">
      <div className="flex items-center justify-between pb-4 border-b border-[#182233]">
        <div className="flex items-center gap-2">
          <CircleDot className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white tracking-tight">
            Enterprise Security Architecture & System Health
          </h2>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
          All Modules Active & Healthy
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modules.map((m) => (
          <div
            key={m.id}
            className="p-4 rounded-md border flex flex-col justify-between bg-[#0f1726]/70 border-emerald-500/30"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  {m.id.replace("_", " ")}
                </span>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {m.status}
                </span>
              </div>

              <h3 className="text-xs font-semibold text-slate-200 mt-2">{m.title}</h3>

              <ul className="mt-3 space-y-1.5">
                {m.items.map((item, i) => (
                  <li key={i} className="text-[11px] text-slate-400 flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
