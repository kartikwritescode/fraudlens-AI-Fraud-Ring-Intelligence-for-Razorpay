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
  Terminal,
} from "lucide-react";

interface NavItem {
  id: string;
  href: string;
  label: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { id: "overview", href: "/", label: "Overview", icon: Activity },
  { id: "live-risk", href: "/live-risk", label: "Live Risk", icon: Radio },
  { id: "fraud-rings", href: "/fraud-rings", label: "Fraud Rings", icon: Network },
  { id: "investigations", href: "/investigations", label: "Investigations", icon: SearchCheck },
  { id: "analytics", href: "/analytics", label: "Analytics", icon: BarChart3 },
  { id: "audit", href: "/audit", label: "Audit", icon: ScrollText },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#090A0F] border-r border-[#21262D] flex flex-col justify-between h-screen sticky top-0 select-none z-30">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-[#21262D]">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:border-emerald-500/60 transition-colors">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-wide text-white">FraudLens</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  LIVE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium tracking-tight">AI Fraud-Ring Intelligence</p>
            </div>
          </Link>
          <div className="mt-3 text-[11px] text-slate-400 font-mono italic leading-tight border-l-2 border-emerald-500/50 pl-2">
            "See the fraud behind the transaction."
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Command Center
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.id}
                href={item.href}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded text-xs font-medium transition-all ${
                  isActive
                    ? "bg-[#161B22] text-white border border-[#30363D] shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-[#161B22]/50 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                  <span className={isActive ? "text-white font-semibold" : ""}>{item.label}</span>
                </div>
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Target Spec & Runtime Footnote */}
      <div className="p-4 border-t border-[#21262D] bg-[#07090e]/60 space-y-2">
        <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span className="flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            Core Stack
          </span>
          <span className="text-slate-300">FastAPI + Neo4j</span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-slate-400" />
            Engine Port
          </span>
          <span className="text-emerald-400">:8000 (Live)</span>
        </div>
      </div>
    </aside>
  );
};
