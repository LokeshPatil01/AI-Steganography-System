"""Model Training Module for AI Region Suitability Classifier (Phase 12).

Trains a Scikit-Learn Random Forest Classifier on extracted 8-dimensional spatial feature vectors:
- Class 0: Smooth / Low Texture (Preserved untouched; lowest capacity)
- Class 1: Medium Texture (Moderate embedding capacity)
- Class 2: High Texture / Complex Edges (High capacity; maximum HVS visual masking)

Saves the serialized model artifact to `models/region_model.joblib`
and metadata report to `models/region_model_metadata.json`.
"""
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from training.region_model.dataset_generator import FEATURE_NAMES, RegionDatasetGenerator

DEFAULT_DATASET_PATH = BASE_DIR / "datasets" / "region_dataset.csv"
DEFAULT_MODEL_DIR = BASE_DIR / "models"
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "region_model.joblib"
DEFAULT_METADATA_PATH = DEFAULT_MODEL_DIR / "region_model_metadata.json"


@dataclass
class TrainingMetrics:
    """Evaluation metrics for a trained region suitability model."""
    train_samples: int
    test_samples: int
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    confusion_matrix: List[List[int]]
    per_class_metrics: Dict[str, Dict[str, float]]
    feature_importances: Dict[str, float]
    hyperparameters: Dict[str, Any]
    trained_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegionModelTrainer:
    """Orchestrates loading, stratified splitting, Random Forest training, evaluation, and serialization."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = 12,
        min_samples_split: int = 4,
        min_samples_leaf: int = 2,
        random_state: int = 42,
    ):
        self.hyperparameters = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "random_state": random_state,
            "class_weight": "balanced",
            "n_jobs": -1,
        }
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            class_weight="balanced",
            n_jobs=-1,
        )
        self.is_trained: bool = False
        self.metrics: Optional[TrainingMetrics] = None
        self.feature_names: List[str] = list(FEATURE_NAMES)

    def load_and_split(
        self,
        csv_path: Optional[str] = None,
        test_size: float = 0.20,
        random_state: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Loads feature matrix X and label vector y, performing stratified train-test split."""
        path = csv_path or str(DEFAULT_DATASET_PATH)
        X, y, feats = RegionDatasetGenerator.load_from_csv(path)
        self.feature_names = feats

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
        return X_train, X_test, y_train, y_test

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> TrainingMetrics:
        """Fits the Random Forest classifier and computes validation metrics on test partition."""
        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(X_test)

        acc = float(round(float(accuracy_score(y_test, y_pred)), 4))
        macro_prec = float(round(float(precision_score(y_test, y_pred, average="macro", zero_division=0)), 4))
        macro_rec = float(round(float(recall_score(y_test, y_pred, average="macro", zero_division=0)), 4))
        macro_f1 = float(round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4))
        weighted_f1 = float(round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4))

        cm = confusion_matrix(y_test, y_pred).tolist()

        # Per-class breakdown
        per_class: Dict[str, Dict[str, float]] = {}
        class_names = ["0_Smooth", "1_Medium", "2_HighTexture"]
        for cls_idx, name in enumerate(class_names):
            prec = float(round(float(precision_score(y_test == cls_idx, y_pred == cls_idx, zero_division=0)), 4))
            rec = float(round(float(recall_score(y_test == cls_idx, y_pred == cls_idx, zero_division=0)), 4))
            f1 = float(round(float(f1_score(y_test == cls_idx, y_pred == cls_idx, zero_division=0)), 4))
            per_class[name] = {"precision": prec, "recall": rec, "f1_score": f1}

        # Feature importances
        raw_importances = self.model.feature_importances_
        sorted_pairs = sorted(
            zip(self.feature_names, raw_importances),
            key=lambda x: x[1],
            reverse=True,
        )
        feat_importances = {name: float(round(float(val), 4)) for name, val in sorted_pairs}

        self.metrics = TrainingMetrics(
            train_samples=len(y_train),
            test_samples=len(y_test),
            accuracy=acc,
            macro_precision=macro_prec,
            macro_recall=macro_rec,
            macro_f1=macro_f1,
            weighted_f1=weighted_f1,
            confusion_matrix=cm,
            per_class_metrics=per_class,
            feature_importances=feat_importances,
            hyperparameters=self.hyperparameters,
            trained_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.metrics

    def save_artifact(
        self,
        model_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Serializes the fitted model to .joblib and writes JSON metadata."""
        if not self.is_trained:
            raise RuntimeError("Cannot save model: Model has not been trained yet.")

        m_dest = Path(model_path or DEFAULT_MODEL_PATH)
        meta_dest = Path(metadata_path or DEFAULT_METADATA_PATH)

        m_dest.parent.mkdir(parents=True, exist_ok=True)
        meta_dest.parent.mkdir(parents=True, exist_ok=True)

        # 1. Save model with joblib
        joblib.dump(self.model, m_dest)

        # 2. Save metadata report
        metadata_dict = {
            "model_type": "RandomForestClassifier",
            "framework": "scikit-learn",
            "feature_names": self.feature_names,
            "classes": [0, 1, 2],
            "class_descriptions": {
                "0": "Smooth / Flat (Preserved untouched; lowest capacity)",
                "1": "Medium Texture (Moderate embedding capacity)",
                "2": "High Texture / Complex Edges (High capacity; maximum HVS masking)",
            },
            "metrics": self.metrics.to_dict() if self.metrics else {},
        }
        with open(meta_dest, mode="w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2)

        return str(m_dest.resolve()), str(meta_dest.resolve())

    @classmethod
    def load_artifact(cls, model_path: Optional[str] = None) -> RandomForestClassifier:
        """Loads a pre-trained serialized model artifact from disk."""
        m_path = Path(model_path or DEFAULT_MODEL_PATH)
        if not m_path.is_file():
            raise FileNotFoundError(f"Model artifact not found at: {m_path}")
        return joblib.load(m_path)

    @classmethod
    def train_and_export(
        cls,
        csv_path: Optional[str] = None,
        model_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
        test_size: float = 0.20,
        random_state: int = 42,
    ) -> Tuple[RandomForestClassifier, TrainingMetrics, str, str]:
        """Convenience method executing complete load -> split -> train -> evaluate -> save pipeline."""
        trainer = cls(random_state=random_state)
        X_train, X_test, y_train, y_test = trainer.load_and_split(
            csv_path=csv_path, test_size=test_size, random_state=random_state
        )
        metrics = trainer.train(X_train, y_train, X_test, y_test)
        saved_model, saved_meta = trainer.save_artifact(model_path, metadata_path)
        return trainer.model, metrics, saved_model, saved_meta


def main():
    print("=" * 70)
    print("  PHASE 12: AI REGION SUITABILITY MODEL TRAINING (RANDOM FOREST)")
    print("=" * 70)

    print(f"\n[1/4] Loading dataset from: {DEFAULT_DATASET_PATH}...")
    trainer = RegionModelTrainer(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
    )
    X_train, X_test, y_train, y_test = trainer.load_and_split(
        test_size=0.20, random_state=42
    )
    print(f" -> Train set: {X_train.shape[0]:,} samples | Test set: {X_test.shape[0]:,} samples")

    print("\n[2/4] Training Random Forest Classifier (100 trees, parallel n_jobs=-1)...")
    metrics = trainer.train(X_train, y_train, X_test, y_test)

    print("\n[3/4] Model Evaluation Results:")
    print(f"  * Overall Accuracy:    {metrics.accuracy * 100:.2f}%")
    print(f"  * Macro Precision:     {metrics.macro_precision * 100:.2f}%")
    print(f"  * Macro Recall:        {metrics.macro_recall * 100:.2f}%")
    print(f"  * Macro F1-Score:      {metrics.macro_f1 * 100:.2f}%")
    print(f"  * Weighted F1-Score:   {metrics.weighted_f1 * 100:.2f}%")

    print("\n  Per-Class Performance Breakdown:")
    for cls_name, vals in metrics.per_class_metrics.items():
        print(f"    - {cls_name:<16}: Precision={vals['precision']:.4f}, Recall={vals['recall']:.4f}, F1={vals['f1_score']:.4f}")

    print("\n  Feature Importance Ranking:")
    for feat_name, imp in metrics.feature_importances.items():
        bar = "#" * int(imp * 40)
        print(f"    * {feat_name:<22}: {imp:>6.4f} | {bar}")

    print("\n  Confusion Matrix (Row: True, Col: Pred):")
    print("        [Pred 0]  [Pred 1]  [Pred 2]")
    labels = ["True 0", "True 1", "True 2"]
    for lbl, row in zip(labels, metrics.confusion_matrix):
        print(f"  {lbl}    {row[0]:>6}    {row[1]:>6}    {row[2]:>6}")

    print("\n[4/4] Serializing model and metadata...")
    m_path, meta_path = trainer.save_artifact()
    print(f" -> Model Artifact:   {m_path}")
    print(f" -> Metadata Summary: {meta_path}")

    print("\n" + "=" * 70)
    print("  PHASE 12 MODEL TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
