"""Execution script for Phase 11: Generating balanced Region Suitability Dataset.

Generates 3,000 balanced 16x16 image block samples (1,000 per class):
- Class 0: Smooth (Low Texture)
- Class 1: Medium Texture
- Class 2: High Texture / Complex Edges

Saves dataset directly to datasets/region_dataset.csv.
"""
import sys
from pathlib import Path

# Add python_engine to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from training.region_model.dataset_generator import RegionDatasetGenerator


def main():
    print("=" * 70)
    print("  PHASE 11: AI REGION MODEL DATASET GENERATION")
    print("=" * 70)

    dataset_dir = BASE_DIR / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    csv_dest = dataset_dir / "region_dataset.csv"

    print(f"\n[1/3] Initializing RegionDatasetGenerator (block_size=16, seed=42)...")
    generator = RegionDatasetGenerator(block_size=16, random_seed=42)

    samples_per_class = 1000
    total_target = samples_per_class * 3
    print(f"[2/3] Synthesizing {total_target} balanced blocks ({samples_per_class} per class)...")
    samples = generator.generate_balanced_dataset(samples_per_class=samples_per_class)

    print(f"[3/3] Saving feature vectors to {csv_dest}...")
    saved_path = generator.save_to_csv(samples, str(csv_dest))
    print(f" -> Successfully saved to: {saved_path}")

    # Validation and summary
    summary = generator.summarize_dataset(saved_path)
    print("\n--- DATASET VALIDATION & METRICS ---")
    print(f"Total Samples Generated: {summary['total_samples']:,}")
    print(f"Features per Sample:     {summary['feature_count']}")
    print(f"Class Distribution:      {summary['class_distribution']}")
    print(f"Zero NaNs or Infs:       {summary['is_valid']}")
    print("\nFeature Summary Statistics (Mean ± Std):")
    for feat_name, stats in summary["feature_statistics"].items():
        print(f"  • {feat_name:<22}: {stats['mean']:>8.4f} ± {stats['std']:<8.4f} (range [{stats['min']}, {stats['max']}])")

    print("\n" + "=" * 70)
    print("  PHASE 11 DATASET GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
