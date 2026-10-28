"""Evaluation and Benchmarking Script for CNN Steganalyzer Model (Phase 16).

Computes rigorous steganalysis detection benchmarks on independent test distributions:
- Overall Accuracy, Precision, Recall, F1-Score, and ROC-AUC.
- Detailed Confusion Matrix (TP, FP, TN, FN).
- Method-specific detectability breakdown comparing:
  1. Traditional Sequential LSB
  2. Rule-Based Content-Adaptive LSB
  3. PRNG Key-Scattered AI Adaptive LSB
- Verifies that AI-guided scattering drastically suppresses P(stego) compared to naive LSB.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch.utils.data import DataLoader

from training.steganalyzer.dataset_builder import SteganalysisDataBuilder, SteganalysisDataset
from training.steganalyzer.model_architecture import SteganalyzerCNN


def load_trained_steganalyzer(
    model_path: str = "models/steganalyzer.pth",
    device: Optional[str] = None,
) -> Tuple[SteganalyzerCNN, Dict]:
    """Loads a serialized SteganalyzerCNN checkpoint into evaluation mode."""
    if device is None:
        device_obj = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device_obj = torch.device(device)

    checkpoint = torch.load(model_path, map_location=device_obj)
    model = SteganalyzerCNN().to(device_obj)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


def evaluate_steganalyzer(
    model_path: str = "models/steganalyzer.pth",
    num_test_covers: int = 60,
    patch_size: int = 64,
    random_seed: int = 999,
) -> Dict:
    """Evaluates the trained steganalyzer on a fresh test distribution."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint = load_trained_steganalyzer(model_path, device=str(device))

    # Synthesize test dataset with fresh random seed
    builder = SteganalysisDataBuilder(patch_size=patch_size, random_seed=random_seed)
    datasets = builder.build_dataset(num_cover_images=num_test_covers)
    test_ds = datasets["test"]
    loader = DataLoader(test_ds, batch_size=16, shuffle=False)

    preds: List[float] = []
    targets: List[float] = []

    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(device)
            probs = model.predict_proba(imgs).cpu().numpy().flatten()
            preds.extend(probs)
            targets.extend(labels.numpy().flatten())

    binary_preds = [p >= 0.5 for p in preds]
    cm = confusion_matrix(targets, binary_preds)
    tn, fp, fn, tp = cm.ravel()

    acc = float(accuracy_score(targets, binary_preds))
    prec = float(precision_score(targets, binary_preds, zero_division=0))
    rec = float(recall_score(targets, binary_preds, zero_division=0))
    f1 = float(f1_score(targets, binary_preds, zero_division=0))
    try:
        auc = float(roc_auc_score(targets, preds))
    except Exception:
        auc = 0.5

    # Method-level breakdown
    method_groups: Dict[str, List[float]] = {}
    for idx, method in enumerate(test_ds.methods):
        if method not in method_groups:
            method_groups[method] = []
        method_groups[method].append(float(preds[idx]))

    method_breakdown: Dict[str, Dict] = {}
    for method, scores in method_groups.items():
        detected_count = sum(1 for s in scores if s >= 0.5)
        method_breakdown[method] = {
            "samples": len(scores),
            "mean_p_stego": round(float(np.mean(scores)), 4),
            "median_p_stego": round(float(np.median(scores)), 4),
            "detected_count": detected_count,
            "detection_rate_pct": round((detected_count / len(scores)) * 100, 2),
        }

    report = {
        "test_samples": len(test_ds),
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "method_breakdown": method_breakdown,
    }
    return report


if __name__ == "__main__":
    report = evaluate_steganalyzer()
    print(json.dumps(report, indent=2))
