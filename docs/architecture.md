# FraudLens Architecture Specification

## 1. Executive Summary
FraudLens is a network-first fraud ring intelligence platform built for Razorpay. It solves the blind spot of traditional transaction classifiers: organized fraud rings that coordinate attacks across shared devices, payment tokens, IP hashes, and merchant endpoints.

## 2. Ingestion & Event Gateway
- **Ingestion Mode 1**: Razorpay Test Mode webhooks (`payment.authorized`, `payment.captured`, `payment.failed`).
- **Ingestion Mode 2**: High-throughput synthetic stream replay for stress testing and demo reliability.
- **HMAC Verification**: SHA256 signature verification over incoming payloads.

## 3. Machine Learning Risk Engine
- **Baseline Model**: XGBoost / LightGBM tabular classifier trained on temporal transaction splits.
- **Ensemble Score**:
  $$\text{Risk} = 0.55 \times \text{ML\_Probability} + 0.20 \times \text{Velocity} + 0.15 \times \text{Anomaly} + 0.10 \times \text{Graph\_Risk}$$
- **Local Explanations**: TreeSHAP reason codes showing top risk drivers.

## 4. Neo4j Fraud Graph
- **Nodes**: `Customer`, `Transaction`, `Merchant`, `Device`, `IP`, `PaymentToken`.
- **Edges**: `MADE`, `FOR`, `USES`, `FROM`.
- **Clustering**: Louvain community detection and connected components to isolate suspicious clusters.

## 5. Agentic Investigation Workflow
- **Framework**: LangGraph.
- **Guardrails**: Agent is equipped with read-only verification tools. It cannot unilaterally block transactions or manipulate databases.
- **Financial Impact Engine**: Calculates Expected Loss across Allow, Step-Up Authentication, and Ring Quarantine actions.
- **Human in the Loop**: Consequential actions require explicit analyst review and signature.
- **Audit Log**: Every tool call, rationale, and analyst decision is permanently recorded in PostgreSQL.
