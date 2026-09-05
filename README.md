# FraudLens — AI Fraud-Ring Intelligence for Razorpay

> *"See the fraud behind the transaction."*

[![Status](https://img.shields.io/badge/status-Production%20Ready-emerald)]()
[![Backend](https://img.shields.io/badge/backend-FastAPI-blue)]()
[![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-black)]()
[![Graph](https://img.shields.io/badge/graph-Neo4j%205.20-blueviolet)]()
[![Database](https://img.shields.io/badge/database-PostgreSQL%2016-336791)]()
[![ML](https://img.shields.io/badge/ml-XGBoost%20%2B%20TreeSHAP-orange)]()
[![Agent](https://img.shields.io/badge/agent-LangGraph%20Controlled%20Tools-purple)]()

## Overview

FraudLens is an AI fraud-ring intelligence command center designed for the Razorpay payment ecosystem. Rather than evaluating transactions in isolation, FraudLens detects coordinated multi-entity fraud syndicates across customers, devices, IP subnets, payment tokens, and merchants.

---

## Why FraudLens?

Traditional fraud prevention systems evaluate payments one by one:
```
Transaction ──▶ ML Fraud Score ──▶ Block / Allow
```
This fails against organized fraud rings where individual transactions are kept small or deceptively normal, but shared underlying infrastructure reveals a coordinated attack syndicate.

**FraudLens introduces network-first risk intelligence:**
```
Payment Event (Razorpay Webhook)
       │
       ▼
Feature Engineering (Retrospective Velocities & Instrument Reuse)
       │
       ▼
ML Risk Scoring (XGBoost v1 + TreeSHAP Explanation Drivers)
       │
       ▼
Graph Relationship Update (Bipartite Multi-Entity Projection)
       │
       ▼
Fraud Ring Discovery (Louvain Community Detection)
       │
       ▼
Configurable Composite Risk Calculation
       │
       ▼
High-Severity Alert Generation
       │
       ▼
Autonomous AI Investigation Agent (LangGraph 8-Node State Machine)
       │
       ▼
Deterministic Financial Impact & Expected Loss Policy Matrix
       │
       ▼
Least-Harmful Recommended Action (ALLOW, MONITOR, STEP-UP, REVIEW, HOLD)
       │
       ▼
Human Analyst Approval Checkpoint (RBAC Verified)
       │
       ▼
Cryptographic Immutable Security Audit Trail
       │
       ▼
Live Dashboard Telemetry Synchronization
```

---

## Key Capabilities

- **ML Risk Scoring**: Sub-4ms gradient boosted decision tree evaluating transaction velocities and payment rail signals.
- **Graph-Based Fraud-Ring Detection**: Real-time bipartite graph projections and Louvain community detection isolating coordinated syndicates.
- **Autonomous AI Investigation Agent**: LangGraph state machine executing 9 strictly typed, read-only tools to compile empirical case dossiers.
- **Explainable Risk Scoring**: Local TreeSHAP attributions and human-readable reason codes for every scored transaction.
- **Expected-Loss Decision Policy**: Mathematical matrix balancing fraud exposure against customer friction to select the least-harmful mitigation action.
- **Human Analyst Approval**: Role-based access control checkpoints allowing analysts to review evidence dossiers and authorize actions.
- **Immutable Audit Trail**: Cryptographically chained audit ledger recording every ingestion event, agent tool execution, and analyst decision.
- **Live Command Center**: Next.js 14 dark-first operational console with streaming telemetry, interactive React Flow graph explorer, and Recharts analytics.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Next.js 14 Enterprise Command Center                 │
│         (Overview · Live Risk · Fraud Rings · Cases · Analytics)       │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │ HTTP / REST
┌────────────────────────────────────▼───────────────────────────────────┐
│                     FastAPI Ingestion & Risk Gateway                   │
│          (HMAC SHA-256 Webhook Adapter · RBAC Auth · RFC 7807)         │
└──────┬─────────────────────────────┬────────────────────────────┬──────┘
       │                             │                            │
┌──────▼──────────────┐   ┌──────────▼──────────────┐   ┌─────────▼──────────────┐
│   ML Risk Engine    │   │   Fraud Graph Engine    │   │  AI Investigation      │
│  XGBoost v1 Engine  │   │  Bipartite Projection   │   │  LangGraph Workflow    │
│  TreeSHAP Explainer │   │  Louvain Ring Detector  │   │  9 Typed Read Tools    │
│  Velocity Features  │   │  Neo4j 5.20 Bolt Driver │   │  Expected Loss Matrix  │
└─────────────────────┘   └─────────────────────────┘   └────────────────────────┘
```

---

## Tech Stack

- **Backend Gateway**: FastAPI, Pydantic v2, Uvicorn, Python 3.11+
- **Machine Learning**: XGBoost v1, SHAP (TreeSHAP), Scikit-Learn, Pandas, NumPy
- **Graph Intelligence**: NetworkX, Neo4j 5.20 (Bolt Driver), Louvain Community Modularity
- **AI Agent Framework**: LangGraph, LangChain Core
- **Database & Storage**: PostgreSQL 16 (asyncpg), Neo4j 5.20 Community, In-Memory Fallback
- **Frontend Dashboard**: Next.js 14 (App Router), TypeScript, Tailwind CSS, React Flow, Recharts, Lucide Icons

---

## Project Structure

```
fraudlens/
├── apps/
│   ├── api/                     # FastAPI Backend Gateway & Risk Orchestrator
│   │   ├── app/
│   │   │   ├── api/v1/          # Endpoints (Webhooks, Analytics, Graph, Agent, Demo)
│   │   │   ├── core/            # Config, Security Headers, RBAC Auth, RFC 7807 Errors
│   │   │   ├── db/              # PostgreSQL (asyncpg) & Neo4j (Bolt) managers
│   │   │   └── main.py          # FastAPI application entrypoint
│   │   └── requirements.txt
│   │
│   └── web/                     # Next.js 14 Dashboard
│       ├── src/
│       │   ├── app/             # 6 Navigation Routes (/, live-risk, fraud-rings, investigations, analytics, audit)
│       │   ├── components/      # Layout, Header, Sidebar, Telemetry Cards, Demo Modal
│       │   └── lib/             # Typed API clients & data models
│       └── package.json
│
├── services/                    # Domain Service Modules
│   ├── orchestrator/            # Central pipeline coordinator & composite risk engine
│   ├── risk_engine/             # XGBoost inference & TreeSHAP explainability
│   ├── graph_engine/            # Graph builder, neighbor expander, & Louvain ring detector
│   ├── agent/                   # LangGraph investigation workflow & 9 controlled tools
│   ├── ingestion/               # Razorpay webhook adapter & normalized event models
│   ├── demo/                    # ScenarioManager for SYNDICATE ATTACK #042 & state reset
│   └── simulator/               # 50,000 synthetic transaction payment universe generator
│
├── data/                        # Indexed datasets (transactions_50k.json)
├── infra/                       # Docker Compose (PostgreSQL 16, Neo4j 5.20)
├── scripts/                     # Automated lifecycle & demo test scripts
├── tests/                       # Complete Pytest test suite (40 unit tests)
├── .env.example                 # Environment configuration template
└── README.md
```

---

## Quick Start

Follow these steps to run FraudLens locally from top to bottom.

### 1. Prerequisites
- **Python**: version 3.11 or higher
- **Node.js**: version 18 or higher (with npm)
- **Git**
- *(Optional)* **Docker & Docker Compose**: FraudLens includes a high-performance in-memory mode that runs with zero external services. To persist graph structures across container restarts, Docker can optionally be started.

### 2. Clone & Enter Project
```bash
git clone https://github.com/your-org/fraudlens.git
cd fraudlens
```

### 3. Environment Setup
Create your local environment configuration file:
```bash
cp .env.example .env
```
The default configuration works out of the box for local execution in development mode.

### 4. Install Backend Dependencies
Install all required Python packages from the repository root:
```bash
pip install -r requirements.txt
```

### 5. Start Infrastructure (Optional)
FraudLens runs immediately without Docker using embedded memory-indexed projections. If you wish to run dedicated PostgreSQL and Neo4j containers:
```bash
docker compose -f infra/docker-compose.yml up -d
```

### 6. Start Backend Intelligence Gateway
Run the FastAPI service using Uvicorn:
```bash
uvicorn app.main:app --app-dir apps/api --port 8000
```
- **Liveness Probe**: `http://localhost:8000/health`
- **Readiness Probe**: `http://localhost:8000/api/v1/health`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

### 7. Install & Start Frontend Command Center
In a new terminal, build and launch the Next.js application:
```bash
cd apps/web
npm install
npm run build
npm run start
```

### 8. Open Application
Open your browser and navigate to:
```text
http://localhost:3000
```

### 9. Verify Installation
Verify the services are active and healthy:
```bash
# Verify backend liveness
curl http://localhost:8000/health

# Verify system status
curl http://localhost:8000/api/v1/system/status

# Run the full automated test suite (40 tests)
pytest tests/unit -v
```

---

## Demo — Coordinated Syndicate Attack #042

FraudLens includes an end-to-end attack simulation engine for operational drills:

### Interactive UI Walkthrough:
1. Open `http://localhost:3000`.
2. Click **"Simulate Coordinated Attack"** in the top navigation header.
3. Observe the multi-stage progression modal:
   - **Wave 1**: 3 exploratory payments arrive in the Live Risk stream.
   - **Wave 2**: 34 coordinated payments link 37 customer accounts, 5 hardware devices, 3 IP subnets, 2 corporate card tokens, and 4 merchants (~₹8.9L volume).
   - **Graph Discovery**: Streaming Louvain community detection isolates **FRAUD RING #042** (`CRITICAL` severity).
   - **Autonomous Investigation**: The LangGraph agent queries 9 controlled tools to assess velocity bursts, shared tokens, and transaction history.
   - **Evidence Synthesis**: Synthesizes verified `FACT:` citations and separates them from inferred `HYPOTHESIS:` statements.
   - **Loss-Minimizing Policy**: Computes expected loss vs false-positive customer friction and recommends **`STEP-UP + REVIEW`**.
   - **Human Approval**: Click **"Approve Recommendation"** to commit the decision to the immutable audit trail.
4. Click **"RESET DEMO"** at any time to cleanly restore the baseline state.

### Automated Script Verification:
```bash
# Run full deterministic attack drill test
python -m scripts.test_demo_scenario

# Run end-to-end pipeline lifecycle verification
python -m scripts.verify_end_to_end_pipeline
```

---

## ML Model Performance

The FraudLens risk model is an enterprise gradient boosted decision tree (XGBoost v1) trained with temporal out-of-time splits and multi-entity rolling velocity features:

- **PR-AUC**: `0.9710`
- **ROC-AUC**: `0.9996`
- **Fraud Recall**: `96.77%`
- **Precision**: `81.08%`
- **F1 Score**: `0.8824`
- **False Positive Rate (FPR)**: `0.0009` (7 false positives out of 7,725 benign test transactions)
- **Single-Row Inference Latency**: `~3.4 ms`

---

## Core ML Signals

- **`device_velocity_1h` & `ip_velocity_1h`**: Rolling 1-hour multi-account velocity burst signals identifying hardware and network cycling.
- **`customer_order_velocity_1h` & `customer_amount_velocity_1h`**: Spend acceleration and rapid velocity deviations from account history.
- **`shared_device_count` & `shared_ip_count`**: Multi-entity bipartite infrastructure reuse across distinct customer accounts.
- **`is_upi_rail`, `is_card_rail`, `is_netbanking_rail`**: Payment instrument risk modifiers.
- **TreeSHAP Attributions**: Real-time feature impact attributions that map model output to human-actionable reason codes (e.g., `SUSPICIOUS_HIGH_AMOUNT`, `SHARED_DEVICE_HIGH_DEGREE`).

---

## Testing

Run the automated test suite covering all core modules:
```bash
pytest tests/unit -v
```

All 40 unit tests cover:
- **Transaction ML Scoring**: Feature calculations, temporal leak prevention, SHAP attributions, missing value resilience.
- **Graph Intelligence**: Louvain clustering, bipartite projection, multi-hop neighbor expansion, temporal ring timelines.
- **AI Agent & Policy Engine**: LangGraph state machine, typed tool execution, expected loss vs false-positive tradeoff matrix.
- **Razorpay Webhook Adapter**: Constant-time HMAC-SHA256 signature verification, duplicate idempotency suppression, malformed payload defense.
- **Enterprise Hardening**: Cypher/SQL injection immunity, database graceful degradation, analyst RBAC authentication.

---

## Security & Governance

- **Constant-Time HMAC-SHA256 Webhook Validation**: Cryptographically validates the `X-Razorpay-Signature` header on every incoming webhook before parsing.
- **Duplicate Event Idempotency**: In-memory sliding cache tracking event IDs to prevent replay attacks and double processing.
- **Analyst RBAC Checkpoints**: API routes modifying case states require authorized `X-Analyst-Key` or Bearer tokens.
- **Injection Defense**: Cypher query parameterization and parameterized SQL statements prevent injection vulnerabilities across graph and relational queries.
- **Cryptographically Hashed Audit Trail**: SHA-256 chained audit ledger ensuring non-repudiation of all agent actions and analyst approvals.
- **Graceful Failure Degradation**: Fallback handlers gracefully maintain system operation if external databases or services become temporarily unreachable.

---

## Architecture Specifications

| Module | Engine Core | Key Responsibilities |
|---|---|---|
| **Payment Telemetry** | FastAPI Gateway | Razorpay webhook adapter, HMAC SHA-256 validation, duplicate suppression |
| **Risk Inference** | XGBoost v1 + TreeSHAP | Sub-4ms scoring, PR-AUC 0.9710, rolling velocity feature engineering |
| **Graph Intelligence** | Neo4j 5.20 / NetworkX | Bipartite entity networks, Louvain community detection, ring topologies |
| **Autonomous Agent** | LangGraph State Machine | 8-node investigative workflow, 9 controlled tools, empirical dossiers |
| **Decision Policy** | Expected Loss Matrix | Least-harmful actions: ALLOW, MONITOR, STEP-UP 2FA, HOLD |
| **Forensic Governance**| Cryptographic Audit Ledger| Immutable audit entries, RBAC analyst authentication, drill replay |
