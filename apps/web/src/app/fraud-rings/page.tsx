"use client";

import React, { useState, useEffect, useCallback } from "react";
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import {
  Network,
  ShieldAlert,
  Clock,
  Layers,
  Users,
  CreditCard,
  Smartphone,
  Globe,
  Store,
  ArrowRight,
  TrendingUp,
  AlertOctagon,
  Loader2,
} from "lucide-react";
import { fetchRings, fetchRingDetail, fetchTransactionNetwork } from "@/lib/api";
import { DiscoveredRing, GraphNode, GraphEdge } from "@/lib/types";

// Node type visual color mappings
const nodeColors: Record<string, { bg: string; border: string; text: string; icon: any }> = {
  Customer: { bg: "#0D2136", border: "#38BDF8", text: "#E0F2FE", icon: Users },
  Device: { bg: "#28133E", border: "#C084FC", text: "#F3E8FF", icon: Smartphone },
  IP: { bg: "#0A2540", border: "#22D3EE", text: "#ECFEFF", icon: Globe },
  PaymentToken: { bg: "#38230D", border: "#FBBF24", text: "#FEF3C7", icon: CreditCard },
  Merchant: { bg: "#0D2F22", border: "#34D399", text: "#ECFDF5", icon: Store },
  Transaction: { bg: "#381014", border: "#F87171", text: "#FEE2E2", icon: AlertOctagon },
};

export default function FraudRingsPage() {
  const [rings, setRings] = useState<DiscoveredRing[]>([]);
  const [selectedRingId, setSelectedRingId] = useState<string>("ring_disc_001");
  const [selectedRing, setSelectedRing] = useState<DiscoveredRing | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [graphLoading, setGraphLoading] = useState(false);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Load ring list
  useEffect(() => {
    async function load() {
      try {
        const res = await fetchRings();
        const list = Array.isArray(res) ? res : (res?.rings || []);
        setRings(list);
        if (list.length > 0) {
          setSelectedRingId(list[0].ring_id);
        }
      } catch (err) {
        console.error("Failed to load rings:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // When selected ring changes, load ring details and graph nodes
  useEffect(() => {
    if (!selectedRingId) return;

    async function loadRingData() {
      setGraphLoading(true);
      try {
        const ring = await fetchRingDetail(selectedRingId);
        setSelectedRing(ring);

        // Fetch graph subgraph for the primary transaction in the ring
        const txId = ring?.transaction_ids?.[0];
        if (txId) {
          const network = await fetchTransactionNetwork(txId, 2);
          const rawNodes = network?.nodes || [];
          const rawEdges = network?.edges || [];

          // Generate circular layout
          const newNodes: Node[] = rawNodes.map((n, idx) => {
            const angle = (idx / Math.max(1, rawNodes.length)) * 2 * Math.PI;
            const radius = idx === 0 ? 0 : 220;
            const x = 360 + radius * Math.cos(angle);
            const y = 260 + radius * Math.sin(angle);
            const styling = nodeColors[n.type] || nodeColors.Customer;
            const riskVal = typeof n.risk_score === "number" ? n.risk_score : 0;

            return {
              id: n.id,
              position: { x, y },
              data: {
                label: (
                  <div
                    className="px-3 py-2 rounded font-mono text-[11px] border shadow-lg cursor-pointer transition-transform hover:scale-105"
                    style={{
                      backgroundColor: styling.bg,
                      borderColor: styling.border,
                      color: styling.text,
                    }}
                  >
                    <div className="font-bold uppercase text-[9px] opacity-75">{n.type}</div>
                    <div className="font-semibold truncate max-w-[130px]">{n.label || n.id}</div>
                    {riskVal > 0 && (
                      <div className="text-[9px] text-red-400 mt-0.5">Risk: {riskVal.toFixed(2)}</div>
                    )}
                  </div>
                ),
                raw: n,
              },
            };
          });

          const newEdges: Edge[] = rawEdges.map((e) => ({
            id: e.id || `e_${e.source}_${e.target}`,
            source: e.source,
            target: e.target,
            label: e.label || e.type || "",
            labelStyle: { fill: "#94A3B8", fontSize: 9, fontFamily: "monospace" },
            labelBgStyle: { fill: "#090A0F", fillOpacity: 0.8 },
            style: { stroke: e.is_suspicious ? "#F87171" : "#475569", strokeWidth: e.is_suspicious ? 2 : 1.5 },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: e.is_suspicious ? "#F87171" : "#475569",
            },
          }));

          setNodes(newNodes);
          setEdges(newEdges);
        } else {
          setNodes([]);
          setEdges([]);
        }
      } catch (err) {
        console.error("Failed to load ring detail or graph:", err);
        setNodes([]);
        setEdges([]);
      } finally {
        setGraphLoading(false);
      }
    }

    loadRingData();
  }, [selectedRingId, setNodes, setEdges]);

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.data?.raw || null);
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
              <Network className="w-4 h-4 text-rose-400" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Fraud-Ring Graph Intelligence Explorer</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              COMMUNITY DETECTION
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Algorithmic multi-entity graph cluster discovery revealing coordinated syndicates across payments
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2 text-[10px] font-mono overflow-x-auto py-1">
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full ring-2 ring-white/10" style={{ backgroundColor: color.border }} />
              <span className="text-slate-300 font-medium">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Graph & Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left 1 Col: Ring Selector List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
              Discovered Fraud Rings
            </span>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50">
              {rings.length} ACTIVE
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-slate-400 glass-card rounded-xl border border-slate-800/80">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
              Scanning graph communities...
            </div>
          ) : rings.length === 0 ? (
            <div className="p-6 text-center text-xs font-mono text-slate-400 glass-card rounded-xl border border-slate-800/80">
              No active rings detected.
            </div>
          ) : (
            <div className="space-y-2 max-h-[640px] overflow-y-auto pr-1">
              {rings.map((ring) => {
                const isSelected = ring.ring_id === selectedRingId;
                const riskVal = typeof ring.risk_score === "number" ? ring.risk_score : 0;
                const patternStr = (ring.pattern_type || "COORDINATED_SYNDICATE").replace(/_/g, " ");
                const amtVal = typeof ring.attempted_amount === "number" ? ring.attempted_amount : 0;

                return (
                  <button
                    key={ring.ring_id}
                    onClick={() => {
                      setSelectedRingId(ring.ring_id);
                      setSelectedNode(null);
                    }}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                      isSelected
                        ? "glass-card border-emerald-500/50 bg-emerald-500/[0.04] shadow-lg shadow-emerald-500/5"
                        : "glass-card border-slate-800/70 hover:border-slate-700/80 hover:bg-slate-800/30"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${isSelected ? "bg-emerald-400 animate-pulse" : "bg-slate-600"}`} />
                        <span className={`font-mono text-xs font-bold ${isSelected ? "text-emerald-400" : "text-white"}`}>
                          {ring.ring_id}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {riskVal.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-2 capitalize font-medium">
                      {patternStr}
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mt-2.5 pt-2.5 border-t border-slate-800/60">
                      <span className="flex items-center gap-1.5">
                        <Users className="w-3 h-3 text-slate-500" />
                        {ring.member_count || 0} Accounts
                      </span>
                      <span className="text-white font-semibold">₹{(amtVal / 1000).toFixed(0)}k Vol</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Center 2 Cols: React Flow Interactive Graph Canvas */}
        <div className="lg:col-span-2 rounded-xl glass-card border border-slate-800/80 overflow-hidden flex flex-col h-[680px] relative shadow-xl">
          <div className="p-3.5 border-b border-slate-800/60 bg-slate-900/60 flex items-center justify-between text-xs font-mono backdrop-blur-sm">
            <span className="text-slate-200 font-bold flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              Graph Subgraph: <span className="text-emerald-400">{selectedRingId}</span>
            </span>
            <div className="flex items-center gap-3 text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                {nodes.length} Nodes
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                {edges.length} Edges
              </span>
            </div>
          </div>

          <div className="flex-1 w-full h-full relative">
            {graphLoading && (
              <div className="absolute inset-0 bg-[#06080D]/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center text-xs font-mono text-slate-300 gap-2">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                <span>Traversing multi-entity graph neighborhood...</span>
              </div>
            )}

            {nodes.length === 0 && !graphLoading ? (
              <div className="w-full h-full flex flex-col items-center justify-center text-xs font-mono text-slate-400 p-8 text-center">
                <div className="w-12 h-12 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-center mb-3">
                  <Network className="w-6 h-6 text-slate-500" />
                </div>
                <p className="max-w-xs text-slate-400">Select a fraud ring from the left to visualize its multi-entity topology.</p>
              </div>
            ) : (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                fitView
              >
                <Background color="#1E293B" gap={24} size={1} />
                <Controls className="!bg-slate-900/90 !border-slate-700/60 !text-white !rounded-lg !shadow-xl" />
                <MiniMap
                  nodeColor={(n: any) => {
                    const raw = n.data?.raw;
                    return raw?.type ? nodeColors[raw.type]?.border || "#38BDF8" : "#38BDF8";
                  }}
                  className="!bg-slate-950/90 !border-slate-800/80 !rounded-lg"
                />
              </ReactFlow>
            )}
          </div>
        </div>

        {/* Right 1 Col: Ring Dossier & Formation Timeline */}
        <div className="space-y-4">
          {/* Selected Node Inspector (If clicked) */}
          {selectedNode && (
            <div className="p-4 rounded-xl glass-card border border-cyan-500/40 space-y-3 animate-in fade-in shadow-lg shadow-cyan-500/5">
              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                  <span className="text-cyan-400 font-bold">Inspected Node</span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  {selectedNode.type}
                </span>
              </div>
              <div className="font-mono text-xs font-bold text-white break-all p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                {selectedNode.id}
              </div>
              <div className="flex items-center justify-between text-xs font-mono pt-1">
                <span className="text-slate-400">Node Risk Score:</span>
                <span className="text-rose-400 font-bold px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20">
                  {typeof selectedNode.risk_score === "number" ? selectedNode.risk_score.toFixed(2) : "N/A"}
                </span>
              </div>
            </div>
          )}

          {/* Ring Metrics Card */}
          {selectedRing && (
            <div className="p-5 rounded-xl glass-card border border-slate-800/80 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">{selectedRing.ring_id}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  {selectedRing.risk_band || "CRITICAL"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Attempted</span>
                  <div className="text-sm font-bold text-white mt-1">
                    ₹{(selectedRing.attempted_amount || 0).toLocaleString("en-IN")}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Growth Rate</span>
                  <div className="text-sm font-bold text-amber-400 mt-1">
                    +{selectedRing.growth_rate || 1.0}x / 24h
                  </div>
                </div>
              </div>

              <div className="space-y-2 text-xs font-mono text-slate-300 pt-1">
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Members:</span>
                  <span className="font-bold text-white">{selectedRing.member_count || 0}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Devices:</span>
                  <span className="font-bold text-white">{selectedRing.device_count || 0}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">IP Subnets:</span>
                  <span className="font-bold text-white">{selectedRing.ip_count || 0}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Payment Tokens:</span>
                  <span className="font-bold text-white">{selectedRing.payment_token_count || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* Formation Timeline */}
          {selectedRing && (
            <div className="p-5 rounded-xl glass-card border border-slate-800/80 space-y-3.5 shadow-xl">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">Formation Timeline</span>
              </div>

              <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                {(selectedRing.timeline || []).map((evt, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs font-mono hover:border-slate-700/80 transition-colors">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-amber-400 font-bold px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">{evt.event_type || "EVENT"}</span>
                      <span className="text-slate-400">{evt.timestamp ? evt.timestamp.slice(11, 19) : ""}</span>
                    </div>
                    <div className="text-slate-200 mt-2 font-semibold">{evt.title || ""}</div>
                    <p className="text-[11px] text-slate-400 mt-1 leading-relaxed font-sans">{evt.description || ""}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
