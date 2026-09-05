"use client";

import React from "react";
import { ArrowRight, BrainCircuit, Network, ShieldCheck, UserCheck, ScrollText, Binary } from "lucide-react";

export const ArchitectureOverview: React.FC = () => {
  const stages = [
    {
      step: "01",
      title: "Transaction Event",
      subtitle: "Razorpay Webhooks / Replay",
      icon: Binary,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
    },
    {
      step: "02",
      title: "ML Risk Engine",
      subtitle: "XGBoost + Velocity + SHAP",
      icon: BrainCircuit,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
    },
    {
      step: "03",
      title: "Relationship Graph",
      subtitle: "Neo4j Multi-Entity Links",
      icon: Network,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
    },
    {
      step: "04",
      title: "Ring Discovery",
      subtitle: "Louvain Community Detection",
      icon: Network,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/20",
    },
    {
      step: "05",
      title: "Investigation Agent",
      subtitle: "LangGraph Controlled Tools",
      icon: ShieldCheck,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/20",
    },
    {
      step: "06",
      title: "Human Approval",
      subtitle: "Least-Destructive Action",
      icon: UserCheck,
      color: "text-rose-400",
      bg: "bg-rose-500/10",
      border: "border-rose-500/20",
    },
    {
      step: "07",
      title: "Audit Trail",
      subtitle: "Immutable Decision Log",
      icon: ScrollText,
      color: "text-slate-300",
      bg: "bg-slate-500/10",
      border: "border-slate-500/20",
    },
  ];

  return (
    <div className="bg-[#0c101a] border border-[#1a2333] rounded-lg p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#182233] gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
            <span>Coordinated Intelligence Architecture</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Not Just a Classifier
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Network intelligence reveals ring attacks where individual transactions appear ambiguous.
          </p>
        </div>
        <div className="text-right">
          <span className="text-[11px] font-mono text-slate-400">Spec Version: Sept 2026</span>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-7 gap-3 relative">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          return (
            <div key={stage.step} className="flex flex-col relative group">
              <div
                className={`p-3 rounded-md bg-[#101624] border ${stage.border} flex flex-col justify-between h-32 transition-all hover:bg-[#131b2c]`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">{stage.step}</span>
                  <div className={`p-1.5 rounded ${stage.bg}`}>
                    <Icon className={`w-3.5 h-3.5 ${stage.color}`} />
                  </div>
                </div>

                <div className="mt-2">
                  <div className="text-xs font-semibold text-slate-200 leading-snug">
                    {stage.title}
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono mt-1 leading-tight">
                    {stage.subtitle}
                  </div>
                </div>
              </div>

              {idx < stages.length - 1 && (
                <div className="hidden md:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-slate-600">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
