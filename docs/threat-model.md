# FraudLens Threat Model & Ring Topologies

## 1. Coordinated Fraud Topologies

### Scenario A: Shared Device Ring
Attackers create dozens of synthetic customer accounts but transact through a small pool of spoofed or rooted devices.
- **Graph Signal**: High customer-to-device degree centrality.
- **Risk Indicator**: 10+ accounts transacting from one device within a 24-hour window.

### Scenario B: Shared IP Velocity Attack
Distributed bots or proxies hitting multiple merchants from identical IP subnets in rapid bursts.
- **Graph Signal**: Dense bipartite graph between IP hashes and merchant endpoints.
- **Risk Indicator**: High velocity of micro-transactions followed by high-value bursts.

### Scenario C: Payment Token / Card Reuse Ring
Stolen card credentials or virtual payment tokens tested across distinct customer identities.
- **Graph Signal**: High card token fan-out across mismatched billing names and shipping destinations.

### Scenario D: Testing-and-Hit Attack
Low-value probe authorizations to verify active status, followed by rapid liquidation purchases.

## 2. Least-Harmful Mitigation Strategy
Traditional brute-force IP or account blocking causes unacceptable false-positive rates for legitimate merchants. FraudLens calculates:
$$\text{Expected Loss} = P(\text{fraud}) \times L_{\text{fraud}} + P(\text{legitimate}) \times C_{\text{false\_positive}} + C_{\text{ops}}$$
Mitigation favors Step-Up Authentication (OTP/3DS challenge) over broad account termination.
