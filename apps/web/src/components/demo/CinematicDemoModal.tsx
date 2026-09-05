"use client";

import React, { useState } from "react";
import {
  Zap,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Bot,
  UserCheck,
  ArrowRight,
  X,
  Lock,
  Layers,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { startDemoScenario, resetDemoScenario, recordCaseDecision } from "@/lib/api";

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRefreshData: () => Promise<void>;
}

export const CinematicDemoModal: React.FC<DemoModalProps> = ({
  isOpen,
  onClose,
  onRefreshData,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isRunning, setIsRunning] = useState(false);
  const [scenarioData, setScenarioData] = useState<any>(null);
  const [decisionRecorded, setDecisionRecorded] = useState(false);

  if (!isOpen) return null;

  const handleStartCoordinatedAttack = async () => {
    setIsRunning(true);
    setCurrentStep(2);

    try {
      // Step 2 -> Step 3 -> Step 4 -> Step 5 -> Step 6 -> Step 7: Call actual backend pipeline
      const data = await startDemoScenario();
      setScenarioData(data);

      // Simulate natural progression across the pipeline steps
      setTimeout(() => setCurrentStep(3), 600);   // Txs arrive
      setTimeout(() => setCurrentStep(4), 1200);  // ML scores rise
      setTimeout(() => setCurrentStep(5), 1800);  // Graph relationships appear
      setTimeout(() => setCurrentStep(7), 2400);  // New fraud ring detected
      setTimeout(() => setCurrentStep(8), 3200);  // Agent starts
      setTimeout(() => {
        setCurrentStep(9);
        setIsRunning(false);
      }, 4200);                                  // Report appears

      await onRefreshData();
    } catch (err) {
      console.error("Scenario execution failed:", err);
      setIsRunning(false);
    }
  };

  const handleApproveAction = async () => {
    if (!scenarioData?.case_id) return;
    try {
      await recordCaseDecision(
        scenarioData.case_id,
        "STEP_UP",
        "Lead Risk Analyst approved STEP-UP 2FA challenge and expedited review for Ring #042."
      );
      setDecisionRecorded(true);
      setCurrentStep(12);
      await onRefreshData();
    } catch (err) {
      console.error("Decision approval failed:", err);
    }
  };

  const handleResetDemo = async () => {
    try {
      await resetDemoScenario();
      setScenarioData(null);
      setCurrentStep(1);
      setDecisionRecorded(false);
      await onRefreshData();
    } catch (err) {
      console.error("Reset failed:", err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in">
      <div className="w-full max-w-3xl bg-[#161B22] border-2 border-red-500/80 rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-[#21262D] bg-[#090A0F] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-red-500/10 border border-red-500/40 flex items-center justify-center text-red-400">
              <Zap className="w-4 h-4 fill-red-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white font-mono">
                  DEMO SCENARIO: FRAUD RING #042
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                  REAL PIPELINE EXECUTION
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Deterministic coordinated attack: 37 customers, 5 devices, 2 tokens, 4 merchants (~₹8.4L)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleResetDemo}
              className="flex items-center gap-1.5 px-3 py-1 rounded text-xs font-mono bg-[#21262D] hover:bg-[#30363D] text-slate-300 hover:text-white border border-[#30363D] transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>RESET DEMO</span>
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-[#21262D] text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Step 1: Initial State / Launch */}
          {currentStep === 1 && (
            <div className="text-center py-8 space-y-4">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">System Baseline is Calm</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 font-mono">
                  Ready to simulate the multi-wave attack. Wave 1 sends 3 exploratory transactions, followed by Wave 2 connecting 37 puppet accounts to stolen corporate card tokens.
                </p>
              </div>
              <button
                onClick={handleStartCoordinatedAttack}
                className="px-6 py-3 rounded-lg font-mono text-xs font-bold bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-950/60 transition-all flex items-center gap-2 mx-auto border border-red-500"
              >
                <Zap className="w-4 h-4 fill-white" />
                <span>Simulate Coordinated Attack</span>
              </button>
            </div>
          )}

          {/* Steps 2-8: Execution In Progress */}
          {currentStep >= 2 && currentStep < 9 && (
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-between text-xs font-mono border-b border-[#21262D] pb-3">
                <span className="text-amber-400 font-bold animate-pulse flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Executing FraudLens Live Pipeline...
                </span>
                <span className="text-slate-400">Stage {currentStep} of 13</span>
              </div>

              <div className="space-y-2.5 font-mono text-xs">
                <div className={`flex items-center gap-3 p-2.5 rounded ${currentStep >= 3 ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20" : "bg-[#090A0F] text-slate-500"}`}>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>[Step 3] Transactions arrive in Live Risk stream (Wave 1: 3 exploratory payments)</span>
                </div>
                <div className={`flex items-center gap-3 p-2.5 rounded ${currentStep >= 4 ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20" : "bg-[#090A0F] text-slate-500"}`}>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>[Step 4] XGBoost ML Risk Engine calculates elevated anomaly score (Score: 0.99)</span>
                </div>
                <div className={`flex items-center gap-3 p-2.5 rounded ${currentStep >= 5 ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20" : "bg-[#090A0F] text-slate-500"}`}>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>[Step 5] Neo4j graph relationships emerge: 37 customers, 5 devices, 2 card tokens</span>
                </div>
                <div className={`flex items-center gap-3 p-2.5 rounded ${currentStep >= 7 ? "bg-red-500/10 text-red-300 border border-red-500/20 font-bold" : "bg-[#090A0F] text-slate-500"}`}>
                  <AlertTriangle className="w-4 h-4" />
                  <span>[Step 6-7] NEW FRAUD RING DETECTED: FRAUD RING #042 (CRITICAL)</span>
                </div>
                <div className={`flex items-center gap-3 p-2.5 rounded ${currentStep >= 8 ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-bold" : "bg-[#090A0F] text-slate-500"}`}>
                  <Bot className="w-4 h-4" />
                  <span>[Step 8] LangGraph AI Agent investigating 9 controlled tools...</span>
                </div>
              </div>
            </div>
          )}

          {/* Step 9-13: Investigation Report & Human Approval */}
          {currentStep >= 9 && scenarioData && (
            <div className="space-y-5 animate-in fade-in font-mono">
              {/* Ring Detected Alert Banner */}
              <div className="p-4 rounded-lg bg-red-950/40 border-2 border-red-500 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ShieldAlert className="w-6 h-6 text-red-400" />
                  <div>
                    <h3 className="text-sm font-bold text-white">NEW FRAUD RING DETECTED</h3>
                    <div className="text-xs text-red-400 font-bold mt-0.5">
                      {scenarioData.ring_id} — Risk: {scenarioData.risk_band}
                    </div>
                  </div>
                </div>
                <div className="text-right text-xs">
                  <div className="text-slate-400">Attempted Volume</div>
                  <div className="text-base font-bold text-white">
                    ₹{scenarioData.attempted_volume_inr.toLocaleString("en-IN")}
                  </div>
                </div>
              </div>

              {/* Topology Metric Grid */}
              <div className="grid grid-cols-5 gap-2 text-xs">
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D] text-center">
                  <div className="text-[10px] text-slate-400">Customers</div>
                  <div className="text-sm font-bold text-white mt-0.5">{scenarioData.customers}</div>
                </div>
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D] text-center">
                  <div className="text-[10px] text-slate-400">Devices</div>
                  <div className="text-sm font-bold text-white mt-0.5">{scenarioData.devices}</div>
                </div>
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D] text-center">
                  <div className="text-[10px] text-slate-400">IP Subnets</div>
                  <div className="text-sm font-bold text-white mt-0.5">{scenarioData.ips}</div>
                </div>
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D] text-center">
                  <div className="text-[10px] text-slate-400">Tokens</div>
                  <div className="text-sm font-bold text-cyan-400 mt-0.5">{scenarioData.payment_tokens}</div>
                </div>
                <div className="p-2.5 rounded bg-[#090A0F] border border-[#21262D] text-center">
                  <div className="text-[10px] text-slate-400">Merchants</div>
                  <div className="text-sm font-bold text-white mt-0.5">{scenarioData.merchants}</div>
                </div>
              </div>

              {/* Agent Tool Call Audit Sequence */}
              <div className="p-3.5 rounded bg-[#090A0F] border border-[#21262D] space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Bot className="w-3.5 h-3.5 text-emerald-400" />
                  Agent Controlled Tool Trace
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>✓ Retrieved transaction</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>✓ Analyzed customer history</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>✓ Expanded fraud graph</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>✓ Detected suspicious cluster</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>✓ Calculated financial impact</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>✓ Compared mitigation policies</span>
                  </div>
                </div>
              </div>

              {/* Recommendation & Human Sign-off Checkpoint */}
              <div className="p-4 rounded-lg bg-[#090A0F] border border-amber-500/40 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-slate-400 text-xs">Agent Recommendation:</span>
                    <div className="text-sm font-bold text-red-400">
                      STEP-UP + REVIEW (Confidence: {(scenarioData.confidence * 100).toFixed(0)}%)
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 text-xs">Case Dossier:</span>
                    <div className="text-sm font-bold text-emerald-400">{scenarioData.case_id}</div>
                  </div>
                </div>

                {!decisionRecorded ? (
                  <div className="pt-2 border-t border-[#21262D]">
                    <button
                      onClick={handleApproveAction}
                      className="w-full py-2.5 rounded font-bold text-xs bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md flex items-center justify-center gap-2"
                    >
                      <UserCheck className="w-4 h-4" />
                      <span>Approve Recommendation (Step-Up Challenge & Hold)</span>
                    </button>
                  </div>
                ) : (
                  <div className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" /> Decision Recorded & Logged in Audit Trail
                    </span>
                    <span className="text-slate-400 text-[10px]">STATUS: RESOLVED</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#21262D] bg-[#090A0F] flex items-center justify-between font-mono text-xs">
          <span className="text-slate-400">
            FraudLens Autonomous Hackathon Engine
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-[#21262D] hover:bg-[#30363D] text-white transition-colors"
          >
            Close & View Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
