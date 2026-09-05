import httpx
import json

client = httpx.Client(base_url="http://localhost:8000", timeout=10.0)

print("========================================================")
print("          LIVE FRAUD GRAPH INTELLIGENCE API             ")
print("========================================================")

# 1. List Rings
res_rings = client.get("/rings")
assert res_rings.status_code == 200, f"Error {res_rings.status_code}: {res_rings.text}"
rings = res_rings.json()
print(f"\n[GET /rings] Discovered {len(rings)} Active Fraud Rings:")
for r in rings:
    print(f"  [{r['ring_id']}] Score: {r['risk_score']:.2f} ({r['risk_band']}) | Type: {r['pattern_type']} | Members: {r['member_count']} | Txs: {r['transaction_count']} | Vol: Rs. {r['attempted_amount']:,.2f}")

# 2. Get Ring Detail & Formation Timeline
first_ring_id = rings[0]["ring_id"]
res_detail = client.get(f"/rings/{first_ring_id}")
assert res_detail.status_code == 200
detail = res_detail.json()
print(f"\n[GET /rings/{first_ring_id}] Ring Profile & Timeline:")
print(f"  Explanation: {detail['explanation']}")
print(f"  Timeline Events ({len(detail['timeline'])}):")
for ev in detail["timeline"][:5]:
    print(f"    - [{ev['timestamp']}] {ev['event_type']}: {ev['title']} ({ev['severity']})")

# 3. Transaction Network Neighborhood (Interactive Graph Subgraph)
sample_tx = detail["transaction_ids"][0]
res_net = client.get(f"/transactions/{sample_tx}/network?hops=2")
assert res_net.status_code == 200
net = res_net.json()
print(f"\n[GET /transactions/{sample_tx}/network] Interactive Subgraph:")
print(f"  Center: {net['center_id']} (Type: {net['center_type']})")
print(f"  Node Count: {net['node_count']} | Edge Count: {net['edge_count']}")
print(f"  Cluster ID: {net['cluster_id']} | Cluster Risk: {net['cluster_risk_score']}")
print(f"  Sample Nodes: {[n['label'] + ' (' + n['type'] + ')' for n in net['nodes'][:5]]}")
print(f"  Sample Edges: {[e['type'] for e in net['edges'][:5]]}")

# 4. Entity Neighbors Expansion
sample_entity = detail["customer_ids"][0]
res_ent = client.get(f"/entities/{sample_entity}/neighbors")
assert res_ent.status_code == 200
ent = res_ent.json()
print(f"\n[GET /entities/{sample_entity}/neighbors] Entity Expansion:")
print(f"  Center: {ent['center_id']} (Type: {ent['center_type']}) | Connected Nodes: {ent['node_count']}")
print("========================================================\n")
