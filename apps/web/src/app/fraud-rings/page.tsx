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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21262D] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <Network className="w-5 h-5 text-red-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Fraud-Ring Graph Intelligence Explorer</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
              COMMUNITY DETECTION
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Algorithmic multi-entity graph cluster discovery revealing coordinated syndicates across payments
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2 text-[10px] font-mono overflow-x-auto">
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#161B22] border border-[#30363D]">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color.border }} />
              <span className="text-slate-300">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Graph & Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left 1 Col: Ring Selector List */}
        <div className="space-y-3">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 px-1">
            Discovered Fraud Rings ({rings.length})
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-slate-500 bg-[#161B22]/40 rounded-lg border border-[#21262D]">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
              Scanning graph communities...
            </div>
          ) : rings.length === 0 ? (
            <div className="p-6 text-center text-xs font-mono text-slate-500 bg-[#161B22]/40 rounded-lg border border-[#21262D]">
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
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? "bg-[#161B22] border-emerald-500/50 shadow-md"
                        : "bg-[#090A0F] border-[#21262D] hover:border-[#30363D]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`font-mono text-xs font-bold ${isSelected ? "text-emerald-400" : "text-white"}`}>
                        {ring.ring_id}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                        {riskVal.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-1 capitalize">
                      {patternStr}
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mt-2 pt-2 border-t border-[#21262D]">
                      <span>{ring.member_count || 0} Accounts</span>
                      <span className="text-white font-semibold">₹{(amtVal / 1000).toFixed(0)}k Vol</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Center 2 Cols: React Flow Interactive Graph Canvas */}
        <div className="lg:col-span-2 rounded-lg bg-[#090A0F] border border-[#30363D] overflow-hidden flex flex-col h-[680px] relative">
          <div className="p-3 border-b border-[#21262D] bg-[#161B22]/60 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-300 font-bold flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              Graph Subgraph: {selectedRingId}
            </span>
            <span className="text-slate-400">
              {nodes.length} Nodes / {edges.length} Edges
            </span>
          </div>

          <div className="flex-1 w-full h-full relative">
            {graphLoading && (
              <div className="absolute inset-0 bg-[#090A0F]/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center text-xs font-mono text-slate-400 gap-2">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                <span>Traversing multi-entity graph neighborhood...</span>
              </div>
            )}

            {nodes.length === 0 && !graphLoading ? (
              <div className="w-full h-full flex flex-col items-center justify-center text-xs font-mono text-slate-500 p-8 text-center">
                <Network className="w-8 h-8 text-slate-600 mb-2" />
                <p>Select a fraud ring from the left to visualize its multi-entity topology.</p>
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
                <Background color="#161B22" gap={20} size={1} />
                <Controls className="!bg-[#161B22] !border-[#30363D] !text-white" />
                <MiniMap
                  nodeColor={(n: any) => {
                    const raw = n.data?.raw;
                    return raw?.type ? nodeColors[raw.type]?.border || "#38BDF8" : "#38BDF8";
                  }}
                  className="!bg-[#090A0F] !border-[#21262D]"
                />
              </ReactFlow>
            )}
          </div>
        </div>

        {/* Right 1 Col: Ring Dossier & Formation Timeline */}
        <div className="space-y-4">
          {/* Selected Node Inspector (If clicked) */}
          {selectedNode && (
            <div className="p-4 rounded-lg bg-[#161B22] border border-cyan-500/40 space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-cyan-400 font-bold">Inspected Entity</span>
                <span className="text-[10px] text-slate-400">{selectedNode.type}</span>
              </div>
              <div className="font-mono text-sm font-bold text-white truncate">{selectedNode.id}</div>
              <div className="text-xs font-mono text-slate-400">
                Risk Score:{" "}
                <span className="text-red-400 font-bold">
                  {typeof selectedNode.risk_score === "number" ? selectedNode.risk_score.toFixed(2) : "N/A"}
                </span>
              </div>
            </div>
          )}

          {/* Ring Metrics Card */}
          {selectedRing && (
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-white uppercase">{selectedRing.ring_id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                  {selectedRing.risk_band || "CRITICAL"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-[#090A0F] border border-[#21262D]">
                  <span className="text-[10px] text-slate-400">Attempted</span>
                  <div className="text-sm font-bold text-white mt-0.5">
                    ₹{(selectedRing.attempted_amount || 0).toLocaleString("en-IN")}
                  </div>
                </div>
                <div className="p-2 rounded bg-[#090A0F] border border-[#21262D]">
                  <span className="text-[10px] text-slate-400">Growth Rate</span>
                  <div className="text-sm font-bold text-amber-400 mt-0.5">
                    +{selectedRing.growth_rate || 1.0}x / 24h
                  </div>
                </div>
              </div>

              <div className="space-y-1.5 text-xs font-mono text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-400">Members:</span>
                  <span>{selectedRing.member_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Devices:</span>
                  <span>{selectedRing.device_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">IP Subnets:</span>
                  <span>{selectedRing.ip_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Tokens:</span>
                  <span>{selectedRing.payment_token_count || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* Formation Timeline */}
          {selectedRing && (
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] space-y-3">
              <div className="flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-bold text-white font-mono uppercase">Formation Timeline</span>
              </div>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {(selectedRing.timeline || []).map((evt, idx) => (
                  <div key={idx} className="p-2 rounded bg-[#090A0F] border border-[#21262D] text-xs font-mono">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-amber-400 font-bold">{evt.event_type || "EVENT"}</span>
                      <span className="text-slate-500">{evt.timestamp ? evt.timestamp.slice(11, 19) : ""}</span>
                    </div>
                    <div className="text-slate-200 mt-1 font-semibold">{evt.title || ""}</div>
                    <p className="text-[11px] text-slate-400 mt-0.5">{evt.description || ""}</p>
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
