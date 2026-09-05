"""
Model Training & Out-of-Time Evaluation Pipeline for FraudLens
Trains XGBoost with class-imbalance weighting and TreeSHAP explainability.
Strictly evaluates on chronological out-of-time test set.
"""

import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import shap

from ml.features.engineer import extract_features_dataset, FEATURE_NAMES

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def evaluate_at_review_budget(
    y_true: np.ndarray, y_probs: np.ndarray, budget_pct: float
) -> float:
    """Computes recall when analysts review top budget_pct% highest scored transactions."""
    k = max(1, int(len(y_probs) * budget_pct))
    top_k_indices = np.argsort(y_probs)[::-1][:k]
    fraud_captured = np.sum(y_true[top_k_indices] == 1)
    total_fraud = np.sum(y_true == 1)
    return float(fraud_captured / total_fraud) if total_fraud > 0 else 0.0


def train_and_evaluate(
    data_path: str = "data/transactions_50k.json",
    artifact_output: str = "ml/artifacts/risk_model_v1.joblib",
    early_stopping_rounds: int = 15,
):
    print(f"[*] Loading transactions from {data_path}...")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    transactions = data.get("transactions", [])
    print(f"[OK] Loaded {len(transactions):,} transactions.")

    print("[*] Extracting rolling behavioral features (no target leakage)...")
    X, y, sorted_txs = extract_features_dataset(transactions)
    print(f"[OK] Features engineered: {X.shape[0]:,} rows x {X.shape[1]} features.")

    # Chronological Split: 70% Train, 15% Validation, 15% Test
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

    print(f"\n[*] Chronological Split Summary:")
    print(f"    Train: {len(X_train):,} ({y_train.sum()} fraud, {y_train.mean()*100:.2f}%)")
    print(f"    Val:   {len(X_val):,} ({y_val.sum()} fraud, {y_val.mean()*100:.2f}%)")
    print(f"    Test:  {len(X_test):,} ({y_test.sum()} fraud, {y_test.mean()*100:.2f}%) [OUT-OF-TIME]")

    # Calculate class imbalance scale_pos_weight
    neg_count = (y_train == 0).sum()
    pos_count = max(1, (y_train == 1).sum())
    scale_weight = float(neg_count / pos_count)
    print(f"[*] Imbalance scale_pos_weight: {scale_weight:.2f}")

    print("\n[*] Training XGBoost Classifier...")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_weight,
        eval_metric=["aucpr", "logloss"],
        early_stopping_rounds=early_stopping_rounds,
        random_state=42,
        tree_method="hist",
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    print(f"[OK] XGBoost trained successfully (Best iteration: {model.best_iteration}).")

    print("\n[*] Initializing TreeSHAP Explainer...")
    explainer = shap.TreeExplainer(model)
    print("[OK] TreeSHAP explainer ready.")

    print("\n[*] Evaluating on Out-Of-Time Test Set...")
    test_probs = model.predict_proba(X_test)[:, 1]
    # Decision threshold tuned on validation or standard 0.50
    test_preds = (test_probs >= 0.50).astype(int)

    pr_auc = float(average_precision_score(y_test, test_probs))
    roc_auc = float(roc_auc_score(y_test, test_probs))
    precision = float(precision_score(y_test, test_preds, zero_division=0))
    recall = float(recall_score(y_test, test_preds, zero_division=0))
    f1 = float(f1_score(y_test, test_preds, zero_division=0))

    cm = confusion_matrix(y_test, test_preds)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    recall_at_1pct = evaluate_at_review_budget(y_test.to_numpy(), test_probs, 0.01)
    recall_at_2pct = evaluate_at_review_budget(y_test.to_numpy(), test_probs, 0.02)
    recall_at_5pct = evaluate_at_review_budget(y_test.to_numpy(), test_probs, 0.05)

    metrics = {
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "recall_at_1pct_review": round(recall_at_1pct, 4),
        "recall_at_2pct_review": round(recall_at_2pct, 4),
        "recall_at_5pct_review": round(recall_at_5pct, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "test_sample_count": len(y_test),
        "test_fraud_count": int(y_test.sum()),
    }

    print("========================================================")
    print("       MEASURED OUT-OF-TIME MODEL EVALUATION METRICS    ")
    print("========================================================")
    print(f"PR-AUC (Precision-Recall AUC): {metrics['pr_auc']:.4f}")
    print(f"ROC-AUC:                       {metrics['roc_auc']:.4f}")
    print(f"Precision (@0.50 threshold):   {metrics['precision']:.4f}")
    print(f"Recall (@0.50 threshold):      {metrics['recall']:.4f}")
    print(f"F1 Score:                      {metrics['f1']:.4f}")
    print(f"False Positive Rate (FPR):     {metrics['fpr']:.4f}")
    print(f"Recall @ 1% Review Budget:     {metrics['recall_at_1pct_review']*100:.1f}%")
    print(f"Recall @ 2% Review Budget:     {metrics['recall_at_2pct_review']*100:.1f}%")
    print(f"Recall @ 5% Review Budget:     {metrics['recall_at_5pct_review']*100:.1f}%")
    print(f"Confusion Matrix:              TP={tp} | FP={fp} | TN={tn} | FN={fn}")
    print("========================================================\n")

    # Feature importances
    importances = model.feature_importances_
    feat_imp = sorted(zip(FEATURE_NAMES, importances), key=lambda x: x[1], reverse=True)
    print("Top Feature Importances:")
    for feat, imp in feat_imp[:8]:
        print(f"  - {feat:30}: {imp*100:.2f}%")

    # Persist Artifact
    artifact = {
        "model": model,
        "explainer": explainer,
        "feature_names": FEATURE_NAMES,
        "metrics": metrics,
        "model_version": "v1.0.0-xgb",
        "thresholds": {
            "low": 0.39,
            "medium": 0.69,
            "high": 0.89,
        },
    }

    out_file = Path(artifact_output)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, out_file)
    print(f"\n[OK] Model artifact successfully saved to: {out_file}")

    return artifact


def main():
    parser = argparse.ArgumentParser(description="Train FraudLens Transaction ML Risk Model")
    parser.add_argument("--data", type=str, default="data/transactions_50k.json", help="Path to input transactions JSON")
    parser.add_argument("--output", type=str, default="ml/artifacts/risk_model_v1.joblib", help="Output artifact path")
    args = parser.parse_args()

    train_and_evaluate(data_path=args.data, artifact_output=args.output)


if __name__ == "__main__":
    main()
