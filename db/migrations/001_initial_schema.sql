-- ==============================================================================
-- FraudLens Database Schema - 001_initial_schema.sql
-- ==============================================================================

-- 1. Merchants Table
CREATE TABLE IF NOT EXISTS merchants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(64) PRIMARY KEY,
    country VARCHAR(8) DEFAULT 'IND',
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Fraud Rings Table
CREATE TABLE IF NOT EXISTS rings (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128),
    pattern_type VARCHAR(64),
    risk_score NUMERIC(5, 4) NOT NULL DEFAULT 0.0000,
    risk_band VARCHAR(16) NOT NULL DEFAULT 'LOW',
    member_count INTEGER NOT NULL DEFAULT 0,
    attempted_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    estimated_loss NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(32) NOT NULL DEFAULT 'DISCOVERED', -- DISCOVERED, INVESTIGATING, MITIGATED, RESOLVED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(64) PRIMARY KEY,
    razorpay_payment_id VARCHAR(64),
    order_id VARCHAR(64),
    merchant_id VARCHAR(64) REFERENCES merchants(id),
    customer_id VARCHAR(64) REFERENCES customers(id),
    ring_id VARCHAR(64) REFERENCES rings(id),
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    status VARCHAR(32) NOT NULL DEFAULT 'authorized', -- authorized, captured, failed, blocked
    payment_method VARCHAR(32) NOT NULL DEFAULT 'card', -- card, upi, netbanking, wallet
    device_id VARCHAR(64),
    ip_hash VARCHAR(64),
    email_hash VARCHAR(64),
    phone_hash VARCHAR(64),
    payment_token_hash VARCHAR(64),
    billing_country VARCHAR(8) DEFAULT 'IND',
    shipping_country VARCHAR(8) DEFAULT 'IND',
    risk_score NUMERIC(5, 4) DEFAULT 0.0000,
    risk_band VARCHAR(16) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH, CRITICAL
    is_fraud BOOLEAN DEFAULT FALSE,
    fraud_type VARCHAR(64),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tx_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_tx_merchant ON transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_tx_device ON transactions(device_id);
CREATE INDEX IF NOT EXISTS idx_tx_ip ON transactions(ip_hash);
CREATE INDEX IF NOT EXISTS idx_tx_token ON transactions(payment_token_hash);
CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tx_risk_score ON transactions(risk_score DESC);

-- 5. Risk Events Table (ML + Graph Scoring History)
CREATE TABLE IF NOT EXISTS risk_events (
    id VARCHAR(64) PRIMARY KEY,
    transaction_id VARCHAR(64) REFERENCES transactions(id),
    model_version VARCHAR(32) NOT NULL,
    score NUMERIC(5, 4) NOT NULL,
    ml_score NUMERIC(5, 4) NOT NULL,
    velocity_score NUMERIC(5, 4) NOT NULL,
    behavioral_anomaly NUMERIC(5, 4) NOT NULL,
    graph_score NUMERIC(5, 4) NOT NULL,
    reason_codes_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_events_tx ON risk_events(transaction_id);

-- 6. Investigation Cases Table
CREATE TABLE IF NOT EXISTS cases (
    id VARCHAR(64) PRIMARY KEY,
    ring_id VARCHAR(64) REFERENCES rings(id),
    transaction_id VARCHAR(64) REFERENCES transactions(id),
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN', -- OPEN, INVESTIGATING, AWAITING_APPROVAL, APPROVED, REJECTED, CLOSED
    agent_summary TEXT,
    recommendation VARCHAR(64), -- ALLOW, MONITOR, STEP_UP_AUTH, HOLD_MERCHANT, BLOCK_RING
    confidence NUMERIC(5, 4) DEFAULT 0.0000,
    evidence_json JSONB DEFAULT '{}'::jsonb,
    financial_impact_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_ring ON cases(ring_id);

-- 7. Audit Logs Table (Immutable Decision Trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    case_id VARCHAR(64) REFERENCES cases(id),
    actor_type VARCHAR(32) NOT NULL, -- AGENT, HUMAN_ANALYST, SYSTEM_RULE
    actor_id VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL, -- CASE_CREATED, HYPOTHESIS_TESTED, RECOMMENDATION_GENERATED, APPROVED, REJECTED
    input_hash VARCHAR(64),
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    rationale TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_logs(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
