import json
from services.simulator.models import PaymentUniverse
from services.graph_engine.graph_builder import build_graph_from_universe

print("Loading data/transactions_50k.json...")
with open("data/transactions_50k.json", "r", encoding="utf-8") as f:
    universe_dict = json.load(f)

universe = PaymentUniverse(**universe_dict)
graph = build_graph_from_universe(universe)

stats = universe.stats
node_counts = graph.get_node_counts()
rel_counts = graph.get_relationship_counts()

print("\n========================================================")
print("             FRAUDLENS PHASE 1 ACTUAL STATISTICS         ")
print("========================================================")
print(f"transactions:        {stats['total_transactions']:,}")
print(f"customers:           {stats['total_customers']:,}")
print(f"merchants:           {stats['total_merchants']:,}")
print(f"fraud transactions:  {stats['fraud_transactions']:,} ({stats['fraud_rate_percentage']}%)")
print(f"fraud rings:         {stats['total_fraud_rings']}")
print(f"Neo4j nodes:         {node_counts['TotalNodes']:,}")
print(f"Neo4j relationships: {rel_counts['TotalRelationships']:,}")

print("\n--- Neo4j Nodes by Label ---")
for k, v in node_counts.items():
    if k != "TotalNodes":
        print(f"  {k:15}: {v:,}")

print("\n--- Neo4j Relationships by Type ---")
for k, v in rel_counts.items():
    if k != "TotalRelationships":
        print(f"  {k:30}: {v:,}")

print("\n--- Ground-Truth Injected Fraud Rings ---")
for r in stats["rings_detail"]:
    print(f"  [{r['ring_id']}] {r['pattern']:30} | Members: {r['members']:2d} | Txs: {r['tx_count']:2d} | Rs. {r['attempted_inr']:,.2f}")

print("========================================================\n")
