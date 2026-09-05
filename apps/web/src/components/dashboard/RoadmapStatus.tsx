"use client";

import React from "react";
import { CheckCircle2, Clock, CircleDot, ShieldAlert } from "lucide-react";

export const RoadmapStatus: React.FC = () => {
  const phases = [
    {
      phase: 0,
      title: "Foundation & Core Infrastructure",
      status: "COMPLETED",
      items: [
        "Monorepo layout (apps, services, ml, db, infra)",
        "Docker Compose (PostgreSQL 16 + Neo4j 5.20)",
        "FastAPI Gateway & Pydantic v2 Settings",
        "Deep multi-service readiness probes",
        "Next.js Command Center shell & layout",
      ],
    },
    {
      phase: 1,
      title: "Synthetic Data & ML Risk Engine",
      status: "NEXT",
      items: [
        "Synthetic transaction stream generator",
        "Inject 5 ring patterns (shared device, IP, tokens)",
        "Velocity & behavioral feature engineering",
        "XGBoost baseline + SHAP reason codes",
      ],
    },
    {
      phase: 2,
      title: "Fraud Graph Engine",
      status: "PLANNED",
      items: [
        "Neo4j entity graph (Customers, Devices, IPs, Cards)",
        "Connected components & Louvain clustering",
        "Interactive React Flow / Cytoscape ring explorer",
        "Graph risk features calculation",
      ],
    },
    {
      phase: 3,
      title: "AI Investigation Agent",
      status: "PLANNED",
      items: [
        "LangGraph investigation workflow",
        "Read-only verification tools (get_cluster, impact)",
        "Financial loss vs false-positive cost estimation",
        "Action recommendation generation",
      ],
    },
    {
      phase: 4,
      title: "Razorpay Webhooks & Replay",
      status: "PLANNED",
      items: [
        "Razorpay Test Mode integration",
        "HMAC SHA256 webhook signature validation",
        "Async event stream pipeline",
        "Live fraud attack simulation trigger",
      ],
    },
    {
      phase: 5,
      title: "Auditing & Demo Hardening",
      status: "PLANNED",
      items: [
        "Immutable case & decision audit trail",
        "Human-in-the-loop analyst approval flow",
        "End-to-end 90-second pitch demo scenario",
      ],
    },
  ];

  return (
    <div className="bg-[#0c101a] border border-[#1a2333] rounded-lg p-5">
      <div className="flex items-center justify-between pb-4 border-b border-[#182233]">
        <div className="flex items-center gap-2">
          <CircleDot className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white tracking-tight">
            Sprint Execution Roadmap
          </h2>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
          Phase 0 Active & Ready
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {phases.map((p) => {
          const isCompleted = p.status === "COMPLETED";
          const isNext = p.status === "NEXT";

          return (
            <div
              key={p.phase}
              className={`p-4 rounded-md border flex flex-col justify-between ${
                isCompleted
                  ? "bg-[#0f1726]/70 border-emerald-500/30"
                  : isNext
                  ? "bg-[#141824] border-blue-500/40"
                  : "bg-[#0e121d] border-[#182233] opacity-60"
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">
                    PHASE {p.phase}
                  </span>
                  <span
                    className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                      isCompleted
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : isNext
                        ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                        : "bg-[#172033] text-slate-400 border border-[#22304d]"
                    }`}
                  >
                    {p.status}
                  </span>
                </div>

                <h3 className="text-xs font-semibold text-slate-200 mt-2">{p.title}</h3>

                <ul className="mt-3 space-y-1.5">
                  {p.items.map((item, i) => (
                    <li key={i} className="text-[11px] text-slate-400 flex items-start gap-1.5">
                      {isCompleted ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-600 shrink-0 mt-1.5" />
                      )}
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
