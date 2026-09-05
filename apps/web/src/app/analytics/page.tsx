"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  TrendingUp,
  CreditCard,
  Store,
  Smartphone,
  Globe,
  DollarSign,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { fetchAnalyticsOverview } from "@/lib/api";
import { AnalyticsOverviewResponse } from "@/lib/types";

const BAND_COLORS: Record<string, string> = {
  LOW: "#10B981",
  MEDIUM: "#F59E0B",
  HIGH: "#F97316",
  CRITICAL: "#EF4444",
};

const PIE_COLORS = ["#38BDF8", "#818CF8", "#C084FC", "#34D399"];

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetchAnalyticsOverview();
        setData(res);
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const riskDistData = data
    ? Object.entries(data.risk_distribution).map(([band, count]) => ({
        band,
        count,
        fill: BAND_COLORS[band] || "#94A3B8",
      }))
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21262D] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Risk & Fraud Analytics Intelligence</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              50,000 TRANSACTIONS EVALUATED
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Global network telemetry, temporal density trends, and merchant vulnerability metrics
          </p>
        </div>
      </div>

      {/* Top 3 Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Detected Attack Value</span>
            <DollarSign className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">
            ₹{data ? (data.kpis.total_amount_at_risk / 100000).toFixed(2) : "0"} Lakhs
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Across 10 algorithmically discovered fraud rings</p>
        </div>

        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Prevented Loss Exposure</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2 font-mono">
            ₹{data ? (data.kpis.total_amount_prevented / 100000).toFixed(2) : "0"} Lakhs
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Autonomous hold and step-up policy mitigation</p>
        </div>

        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Global Fraud Incident Density</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2 font-mono">0.65%</div>
          <p className="text-[11px] text-slate-400 mt-1">325 confirmed anomalies out of 50,000 volume</p>
        </div>
      </div>

      {/* 2-Column Chart Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: 24h Trend */}
        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D] space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              24-Hour Transaction & Fraud Burst Volume
            </span>
            <span className="text-[10px] font-mono text-slate-400">Hourly Distribution</span>
          </div>

          <div className="h-64 w-full">
            {data && (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.risk_trend_hourly}>
                  <defs>
                    <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#38BDF8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="hour" stroke="#64748B" fontSize={10} fontVariant="mono" />
                  <YAxis stroke="#64748B" fontSize={10} fontVariant="mono" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#090A0F", borderColor: "#30363D", fontSize: 11 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="transactions"
                    stroke="#38BDF8"
                    fillOpacity={1}
                    fill="url(#volGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Chart 2: Risk Severity Distribution */}
        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D] space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-red-400" />
              Model Calibrated Risk Band Hierarchy
            </span>
            <span className="text-[10px] font-mono text-slate-400">XGBoost Bands</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistData}>
                <XAxis dataKey="band" stroke="#64748B" fontSize={10} fontVariant="mono" />
                <YAxis stroke="#64748B" fontSize={10} fontVariant="mono" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#090A0F", borderColor: "#30363D", fontSize: 11 }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {riskDistData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Fraud by Payment Method */}
        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D] space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-cyan-400" />
              Fraud Value by Payment Instrument
            </span>
            <span className="text-[10px] font-mono text-slate-400">Instrument Volume</span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            {data && data.fraud_by_payment_method.length > 0 && (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.fraud_by_payment_method}
                    dataKey="volume_inr"
                    nameKey="method"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ method, name, value, volume_inr }: any) =>
                      `${method || name}: ₹${((value || volume_inr || 0) / 1000).toFixed(0)}k`
                    }
                  >
                    {data.fraud_by_payment_method.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "#090A0F", borderColor: "#30363D", fontSize: 11 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Chart 4: Top Targeted Merchants */}
        <div className="p-5 rounded-lg bg-[#161B22] border border-[#30363D] space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Store className="w-4 h-4 text-amber-400" />
              Top Targeted Merchant Midpoints
            </span>
            <span className="text-[10px] font-mono text-slate-400">Incident Frequency</span>
          </div>

          <div className="space-y-3 font-mono text-xs pt-2">
            {data?.top_targeted_merchants.map((m, idx) => (
              <div key={m.merchant_id} className="space-y-1">
                <div className="flex justify-between text-slate-300">
                  <span>{m.merchant_id}</span>
                  <span className="text-red-400 font-bold">{m.fraud_count} Attacks</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[#090A0F]">
                  <div
                    className="h-full rounded-full bg-red-400"
                    style={{ width: `${Math.min(100, m.fraud_count * 3)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
