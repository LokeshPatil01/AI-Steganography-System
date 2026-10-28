"""Unit tests for Phase 12: AI Region Suitability Model Training & Evaluation."""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from training.region_model.dataset_generator import FEATURE_NAMES
from training.region_model.evaluate import evaluate_model
from training.region_model.train import (
    DEFAULT_DATASET_PATH,
    DEFAULT_METADATA_PATH,
    DEFAULT_MODEL_PATH,
    RegionModelTrainer,
    TrainingMetrics,
)


@pytest.fixture
def trainer():
    return RegionModelTrainer(
        n_estimators=20,  # Fast lightweight model for unit tests
        max_depth=8,
        random_state=42,
    )


def test_trainer_initialization(trainer):
    assert trainer.is_trained is False
    assert trainer.metrics is None
    assert trainer.hyperparameters["n_estimators"] == 20
    assert trainer.hyperparameters["max_depth"] == 8
    assert trainer.feature_names == FEATURE_NAMES


def test_load_and_split(trainer):
    assert DEFAULT_DATASET_PATH.is_file(), "Dataset CSV must exist from Phase 11."
    X_train, X_test, y_train, y_test = trainer.load_and_split(
        test_size=0.20, random_state=42
    )

    assert X_train.shape[1] == 8
    assert X_test.shape[1] == 8
    assert len(y_train) == 2400
    assert len(y_test) == 600

    # Verify stratified balance in test set (200 of each class)
    unique, counts = np.unique(y_test, return_counts=True)
    assert list(unique) == [0, 1, 2]
    assert list(counts) == [200, 200, 200]


def test_train_pipeline_accuracy(trainer):
    X_train, X_test, y_train, y_test = trainer.load_and_split(
        test_size=0.20, random_state=42
    )
    metrics = trainer.train(X_train, y_train, X_test, y_test)

    assert trainer.is_trained is True
    assert isinstance(metrics, TrainingMetrics)
    assert metrics.accuracy >= 0.95
    assert metrics.macro_f1 >= 0.95
    assert metrics.macro_precision >= 0.95
    assert metrics.macro_recall >= 0.95

    # Check confusion matrix shape (3x3)
    assert len(metrics.confusion_matrix) == 3
    assert all(len(row) == 3 for row in metrics.confusion_matrix)


def test_feature_importances(trainer):
    X_train, X_test, y_train, y_test = trainer.load_and_split(
        test_size=0.20, random_state=42
    )
    metrics = trainer.train(X_train, y_train, X_test, y_test)

    assert len(metrics.feature_importances) == 8
    sum_importances = sum(metrics.feature_importances.values())
    assert abs(sum_importances - 1.0) < 0.01

    for name in FEATURE_NAMES:
        assert name in metrics.feature_importances
        assert metrics.feature_importances[name] >= 0.0


def test_save_and_load_artifact(trainer):
    X_train, X_test, y_train, y_test = trainer.load_and_split(
        test_size=0.20, random_state=42
    )
    trainer.train(X_train, y_train, X_test, y_test)

    with tempfile.TemporaryDirectory() as tmp_dir:
        m_file = os.path.join(tmp_dir, "test_model.joblib")
        meta_file = os.path.join(tmp_dir, "test_meta.json")

        saved_m, saved_meta = trainer.save_artifact(m_file, meta_file)
        assert os.path.isfile(saved_m)
        assert os.path.isfile(saved_meta)

        # Verify metadata JSON validity
        with open(saved_meta, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["model_type"] == "RandomForestClassifier"
            assert data["classes"] == [0, 1, 2]
            assert "metrics" in data

        # Load model and verify predictions match
        loaded_model = RegionModelTrainer.load_artifact(saved_m)
        preds_orig = trainer.model.predict(X_test[:10])
        preds_loaded = loaded_model.predict(X_test[:10])
        np.testing.assert_array_equal(preds_orig, preds_loaded)


def test_evaluate_model_function():
    assert DEFAULT_MODEL_PATH.is_file(), "Production model must exist."
    res = evaluate_model(str(DEFAULT_MODEL_PATH), str(DEFAULT_DATASET_PATH))

    assert res["total_evaluated"] == 3000
    assert res["accuracy"] >= 0.95
    assert res["roc_auc_ovr"] >= 0.95
    assert res["macro_f1"] >= 0.95
    assert "confusion_matrix" in res


def test_production_model_artifact_integrity():
    """Verifies that the canonical models/region_model.joblib is valid and functional."""
    assert DEFAULT_MODEL_PATH.is_file()
    assert DEFAULT_METADATA_PATH.is_file()

    model = RegionModelTrainer.load_artifact(str(DEFAULT_MODEL_PATH))
    assert isinstance(model, RandomForestClassifier)
    assert model.n_features_in_ == 8

    # Test single dummy block feature vector
    dummy_input = np.array([[3.2, 120.0, 10.95, 22.4, 0.06, 180.0, 360.0, 3.8]], dtype=np.float32)
    pred_class = model.predict(dummy_input)[0]
    pred_probs = model.predict_proba(dummy_input)[0]

    assert pred_class in [0, 1, 2]
    assert len(pred_probs) == 3
    assert abs(np.sum(pred_probs) - 1.0) < 1e-5
