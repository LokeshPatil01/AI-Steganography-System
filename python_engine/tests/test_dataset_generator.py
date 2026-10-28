"""Unit tests for Phase 11: AI Region Model Dataset Generator."""
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

from training.region_model.dataset_generator import (
    FEATURE_NAMES,
    LABEL_COLUMN,
    RegionDatasetGenerator,
    RegionFeatureSample,
)


@pytest.fixture
def generator():
    return RegionDatasetGenerator(block_size=16, random_seed=123)


def test_feature_names_and_schema():
    assert len(FEATURE_NAMES) == 8
    expected = [
        "entropy",
        "variance",
        "std_dev",
        "sobel_gradient_mean",
        "canny_edge_density",
        "laplacian_variance",
        "color_variance",
        "noise_residual_std",
    ]
    assert FEATURE_NAMES == expected
    assert LABEL_COLUMN == "suitability_label"


def test_synthetic_block_shapes_and_types(generator):
    for gen_fn in [
        generator.generate_smooth_block,
        generator.generate_medium_block,
        generator.generate_high_texture_block,
    ]:
        block = gen_fn()
        assert isinstance(block, np.ndarray)
        assert block.shape == (16, 16, 3)
        assert block.dtype == np.uint8
        assert np.all(block >= 0) and np.all(block <= 255)


def test_feature_extraction_properties(generator):
    smooth = generator.generate_smooth_block()
    feats = generator.extract_features(smooth)

    for name in FEATURE_NAMES:
        assert name in feats
        assert isinstance(feats[name], float)
        assert not np.isnan(feats[name])
        assert not np.isinf(feats[name])

    assert 0.0 <= feats["entropy"] <= 8.0
    assert 0.0 <= feats["canny_edge_density"] <= 1.0
    assert feats["variance"] >= 0.0
    assert feats["std_dev"] >= 0.0


def test_hvs_rule_classification(generator):
    # Pure solid block must be classified as 0 (Smooth)
    solid = np.full((16, 16, 3), 128, dtype=np.uint8)
    solid_feats = generator.extract_features(solid)
    assert generator.classify_by_hvs_rules(solid_feats) == 0

    # Sharp checkerboard block must be classified as 2 (High Texture)
    check = np.indices((16, 16)).sum(axis=0) // 2 % 2
    check_single = np.where(check[:, :, None] == 1, 230, 20).astype(np.uint8)
    check_rgb = np.repeat(check_single, 3, axis=2)
    check_feats = generator.extract_features(check_rgb)
    assert generator.classify_by_hvs_rules(check_feats) == 2


def test_sample_dataclass_methods():
    sample = RegionFeatureSample(
        entropy=2.5,
        variance=150.0,
        std_dev=12.24,
        sobel_gradient_mean=18.5,
        canny_edge_density=0.08,
        laplacian_variance=210.0,
        color_variance=450.0,
        noise_residual_std=4.2,
        suitability_label=1,
    )
    d = sample.to_dict()
    assert d["entropy"] == 2.5
    assert d["suitability_label"] == 1
    assert len(d) == 9

    fl = sample.to_feature_list()
    assert len(fl) == 8
    assert fl[0] == 2.5


def test_balanced_dataset_generation_small(generator):
    samples = generator.generate_balanced_dataset(samples_per_class=15)
    assert len(samples) == 45

    counts = {0: 0, 1: 0, 2: 0}
    for s in samples:
        counts[s.suitability_label] += 1

    assert counts == {0: 15, 1: 15, 2: 15}


def test_csv_save_and_load(generator):
    samples = generator.generate_balanced_dataset(samples_per_class=10)

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_file = os.path.join(tmp_dir, "test_dataset.csv")
        saved_path = generator.save_to_csv(samples, csv_file)
        assert os.path.isfile(saved_path)

        X, y, feats = generator.load_from_csv(saved_path)
        assert X.shape == (30, 8)
        assert y.shape == (30,)
        assert X.dtype == np.float32
        assert y.dtype == np.int64
        assert feats == FEATURE_NAMES

        # Verify balance
        unique, counts = np.unique(y, return_counts=True)
        assert list(unique) == [0, 1, 2]
        assert list(counts) == [10, 10, 10]


def test_dataset_summarize_diagnostics(generator):
    samples = generator.generate_balanced_dataset(samples_per_class=10)

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_file = os.path.join(tmp_dir, "test_summary.csv")
        generator.save_to_csv(samples, csv_file)

        summary = generator.summarize_dataset(csv_file)
        assert summary["total_samples"] == 30
        assert summary["feature_count"] == 8
        assert summary["class_distribution"] == {0: 10, 1: 10, 2: 10}
        assert summary["is_valid"] is True
        assert summary["has_nans"] is False
        assert summary["has_infs"] is False


def test_production_generated_dataset():
    """Verifies that the canonical datasets/region_dataset.csv created in Phase 11 exists and is valid."""
    dataset_path = Path(__file__).resolve().parent.parent / "datasets" / "region_dataset.csv"
    assert dataset_path.is_file(), f"Expected {dataset_path} to exist."

    X, y, feats = RegionDatasetGenerator.load_from_csv(str(dataset_path))
    assert X.shape == (3000, 8)
    assert y.shape == (3000,)
    assert not np.isnan(X).any()
    assert not np.isinf(X).any()

    unique, counts = np.unique(y, return_counts=True)
    assert list(unique) == [0, 1, 2]
    assert list(counts) == [1000, 1000, 1000]
