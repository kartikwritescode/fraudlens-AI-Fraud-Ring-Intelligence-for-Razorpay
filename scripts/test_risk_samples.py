import json
from ml.features.engineer import extract_features_dataset
from services.risk_engine.inference import RiskScorer

scorer = RiskScorer.get_instance()

with open("data/transactions_50k.json", "r", encoding="utf-8") as f:
    data = json.load(f)

txs = data["transactions"]
df_feat, labels, sorted_txs = extract_features_dataset(txs[:10000])

fraud_indices = [i for i, t in enumerate(sorted_txs) if t["is_fraud"]]
print(f"Sample fraud count in first 10,000 txs: {len(fraud_indices)}")

for idx in fraud_indices[:6]:
    tx = sorted_txs[idx]
    feat = df_feat.iloc[idx].to_dict()
    res = scorer.assess_transaction(tx, custom_features=feat)
    print(f"\n[{tx['fraud_type']}] ID={tx['transaction_id']}")
    print(f"  Risk Score: {res.risk_score:.4f} ({res.risk_band})")
    print(f"  Top Reasons: {res.reason_codes}")

# Also test a legitimate one
legit_idx = 42
tx_l = sorted_txs[legit_idx]
feat_l = df_feat.iloc[legit_idx].to_dict()
res_l = scorer.assess_transaction(tx_l, custom_features=feat_l)
print(f"\n[LEGITIMATE] ID={tx_l['transaction_id']}")
print(f"  Risk Score: {res_l.risk_score:.4f} ({res_l.risk_band})")
print(f"  Top Reasons: {res_l.reason_codes}")
