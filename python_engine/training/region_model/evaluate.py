"""Evaluation and Validation Script for AI Region Suitability Model (Phase 12).

Computes comprehensive diagnostic metrics on a trained model:
- Accuracy, Precision, Recall, F1-Scores
- Multiclass One-vs-Rest ROC-AUC
- Confusion Matrix
- Per-class Error Distributions
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from training.region_model.dataset_generator import FEATURE_NAMES, RegionDatasetGenerator
from training.region_model.train import DEFAULT_DATASET_PATH, DEFAULT_MODEL_PATH, RegionModelTrainer


def evaluate_model(
    model_path: str = str(DEFAULT_MODEL_PATH),
    dataset_path: str = str(DEFAULT_DATASET_PATH),
) -> Dict[str, Any]:
    """Loads trained model and evaluates on specified dataset, computing ROC-AUC and metrics."""
    model = RegionModelTrainer.load_artifact(model_path)
    X, y, feats = RegionDatasetGenerator.load_from_csv(dataset_path)

    y_pred = model.predict(X)
    y_probs = model.predict_proba(X)

    acc = float(accuracy_score(y, y_pred))
    macro_f1 = float(f1_score(y, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y, y_pred, average="weighted", zero_division=0))
    macro_prec = float(precision_score(y, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y, y_pred, average="macro", zero_division=0))

    # Multiclass ROC-AUC One-vs-Rest
    try:
        roc_auc = float(roc_auc_score(y, y_probs, multi_class="ovr", average="macro"))
    except Exception:
        roc_auc = 0.0

    cm = confusion_matrix(y, y_pred).tolist()
    clf_report = classification_report(y, y_pred, output_dict=True, zero_division=0)

    return {
        "model_path": model_path,
        "dataset_path": dataset_path,
        "total_evaluated": len(y),
        "accuracy": float(round(acc, 4)),
        "roc_auc_ovr": float(round(roc_auc, 4)),
        "macro_f1": float(round(macro_f1, 4)),
        "weighted_f1": float(round(weighted_f1, 4)),
        "macro_precision": float(round(macro_prec, 4)),
        "macro_recall": float(round(macro_rec, 4)),
        "confusion_matrix": cm,
        "classification_report": clf_report,
    }


def main():
    print("=" * 70)
    print("  PHASE 12: AI REGION MODEL COMPREHENSIVE EVALUATION")
    print("=" * 70)

    res = evaluate_model()
    print(f"\nEvaluated Samples:    {res['total_evaluated']:,}")
    print(f"Overall Accuracy:     {res['accuracy'] * 100:.2f}%")
    print(f"Multiclass ROC-AUC:   {res['roc_auc_ovr']:.4f}")
    print(f"Macro F1-Score:       {res['macro_f1'] * 100:.2f}%")
    print(f"Weighted F1-Score:    {res['weighted_f1'] * 100:.2f}%")

    print("\nConfusion Matrix:")
    labels = ["True 0", "True 1", "True 2"]
    for lbl, row in zip(labels, res["confusion_matrix"]):
        print(f"  {lbl}  -> Pred 0: {row[0]:>5} | Pred 1: {row[1]:>5} | Pred 2: {row[2]:>5}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
