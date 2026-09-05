"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldAlert,
  Activity,
  Network,
  SearchCheck,
  BarChart3,
  ScrollText,
  Radio,
  Server,
  Zap,
  CheckCircle2,
  Database,
  Cpu,
} from "lucide-react";

interface NavCategory {
  category: string;
  items: {
    id: string;
    href: string;
    label: string;
    icon: React.ElementType;
    badge?: string;
    badgeColor?: string;
  }[];
}

const navCategories: NavCategory[] = [
  {
    category: "Real-Time Telemetry",
    items: [
      { id: "overview", href: "/", label: "Command Center", icon: Activity },
      { id: "live-risk", href: "/live-risk", label: "Live Risk Stream", icon: Radio, badge: "STREAM", badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" },
    ],
  },
  {
    category: "Graph Intelligence",
    items: [
      { id: "fraud-rings", href: "/fraud-rings", label: "Fraud Rings", icon: Network, badge: "10 RINGS", badgeColor: "bg-rose-500/10 text-rose-400 border-rose-500/30" },
      { id: "investigations", href: "/investigations", label: "AI Investigations", icon: SearchCheck, badge: "12 CASES", badgeColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30" },
    ],
  },
  {
    category: "Forensics & Governance",
    items: [
      { id: "analytics", href: "/analytics", label: "Risk Analytics", icon: BarChart3 },
      { id: "audit", href: "/audit", label: "Audit Trail", icon: ScrollText },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside
      aria-label="Platform Navigation"
      className="w-64 bg-[#080B11] border-r border-[#1E293B]/70 flex flex-col justify-between h-screen sticky top-0 select-none z-30 shadow-2xl shrink-0 hidden md:flex"
    >
      <div>
        {/* Brand Header */}
        <div className="p-4 border-b border-[#1E293B]/70 bg-[#06080D]/50">
          <Link href="/" className="flex items-center gap-3 group focus-visible:ring-1 focus-visible:ring-emerald-400 rounded-lg">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 via-emerald-500/10 to-transparent border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-950/50 group-hover:border-emerald-400/80 transition-all">
              <ShieldAlert className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white font-sans">FraudLens</span>
                <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 tracking-wider">
                  ENTERPRISE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Razorpay AI Risk Engine</p>
            </div>
          </Link>
          <div className="mt-3 text-[10px] text-slate-400/90 font-mono italic leading-snug border-l-2 border-emerald-500/60 pl-2.5">
            "See the fraud behind the transaction."
          </div>
        </div>

        {/* Categorized Navigation */}
        <nav className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-230px)]">
          {navCategories.map((group) => (
            <div key={group.category} className="space-y-1">
              <div className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">
                {group.category}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 ${
                      isActive
                        ? "bg-gradient-to-r from-emerald-500/15 via-emerald-500/5 to-transparent text-white border-l-2 border-emerald-400 shadow-sm pl-2.5 font-semibold"
                        : "text-slate-400 hover:text-white hover:bg-slate-800/40 border-l-2 border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 transition-colors ${isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-slate-300"}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${item.badgeColor || "bg-slate-800 text-slate-300 border-slate-700"}`}>
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Target Spec & Live Runtime Footnote */}
      <div className="p-3.5 border-t border-[#1E293B]/70 bg-[#06080D]/70 space-y-2.5">
        <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Razorpay Pipeline
          </span>
          <span className="text-emerald-400 font-semibold font-mono">ACTIVE</span>
        </div>

        <div className="grid grid-cols-2 gap-1.5 pt-1 text-[10px] font-mono text-slate-400">
          <div className="p-1.5 rounded bg-slate-900/60 border border-slate-800/80 flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-cyan-400" />
            <span className="truncate">FastAPI :8000</span>
          </div>
          <div className="p-1.5 rounded bg-slate-900/60 border border-slate-800/80 flex items-center gap-1.5">
            <Database className="w-3 h-3 text-amber-400" />
            <span className="truncate">Neo4j :7687</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

