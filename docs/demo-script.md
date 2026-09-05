# FraudLens Enterprise Incident Response & Detection Walkthrough

## Narrative Arc: "From Transaction Ambiguity to Coordinated Ring Discovery"

- **00:00 - 00:15**: *The Hook*
  - "Traditional fraud systems evaluate payments one by one. But organized fraudsters do not attack one transaction at a time—they operate coordinated rings."
  - Show the clean Command Center overview.

- **00:15 - 00:30**: *The Attack Ingestion*
  - 3 suspicious transactions arrive via Razorpay Test Webhooks.
  - Individually, each transaction scores medium risk (0.68, 0.62, 0.71). A traditional rule engine allows them.

- **00:30 - 00:50**: *The Graph Breakthrough*
  - Open Fraud Ring Explorer.
  - Neo4j graph reveals the three transactions share a device hash and IP cluster with 34 other synthetic accounts.
  - Network risk jumps to CRITICAL (0.94).

- **00:50 - 01:10**: *The AI Investigation Agent*
  - Launch Agent Investigation.
  - The LangGraph agent systematically queries tools: fetches customer history, checks ring topology, and calculates ₹8.7L in attempted exposure.

- **01:10 - 01:25**: *Financial Recommendation & Approval*
  - Agent computes expected loss and recommends targeted step-up authentication instead of indiscriminate blocking.
  - Analyst reviews evidence and clicks "Approve Recommendation".

- **01:25 - 01:30**: *Audit & Close*
  - Show immutable audit record generated with timestamp and hash.
  - "FraudLens: See the fraud behind the transaction."
