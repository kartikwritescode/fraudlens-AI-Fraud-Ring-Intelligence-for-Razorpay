// ==============================================================================
// FraudLens Neo4j Graph Schema & Constraints
// ==============================================================================

// Uniqueness Constraints
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT ip_hash_unique IF NOT EXISTS FOR (i:IP) REQUIRE i.ip_hash IS UNIQUE;
CREATE CONSTRAINT token_hash_unique IF NOT EXISTS FOR (p:PaymentToken) REQUIRE p.token_hash IS UNIQUE;
CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS FOR (m:Merchant) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT ring_id_unique IF NOT EXISTS FOR (r:Ring) REQUIRE r.id IS UNIQUE;

// Indexes for Fast Query Traversal
CREATE INDEX customer_risk_index IF NOT EXISTS FOR (c:Customer) ON (c.risk_score);
CREATE INDEX transaction_time_index IF NOT EXISTS FOR (t:Transaction) ON (t.timestamp);
CREATE INDEX ring_risk_index IF NOT EXISTS FOR (r:Ring) ON (r.risk_score);
