"""Training Pipeline for Deep Learning Steganalyzer CNN (Phase 16).

Trains the lightweight PyTorch CNN with Spatial Rich Model (SRM) preprocessing:
- Generates balanced Cover vs. Stego dataset (Baseline LSB, Adaptive LSB, PRNG Key-Scattered AI).
- Minimizes binary cross-entropy loss using Adam optimizer.
- Employs validation monitoring and early stopping.
- Evaluates on independent test set: Accuracy, Precision, Recall, F1, ROC-AUC.
- Serializes trained weights to models/steganalyzer.pth and metadata to models/steganalyzer_metadata.json.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from training.steganalyzer.dataset_builder import SteganalysisDataBuilder, SteganalysisDataset
from training.steganalyzer.model_architecture import SteganalyzerCNN, count_parameters


class SteganalyzerTrainer:
    """Orchestrates end-to-end dataset synthesis, CNN training, and evaluation."""

    def __init__(
        self,
        patch_size: int = 64,
        batch_size: int = 16,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        epochs: int = 20,
        patience: int = 5,
        device: Optional[str] = None,
        random_seed: int = 42,
    ):
        self.patch_size = patch_size
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.epochs = epochs
        self.patience = patience
        self.random_seed = random_seed

        torch.manual_seed(random_seed)
        np.random.seed(random_seed)

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

    def train(
        self,
        num_cover_images: int = 200,
        output_model_path: str = "models/steganalyzer.pth",
        output_metadata_path: str = "models/steganalyzer_metadata.json",
        verbose: bool = True,
    ) -> Dict:
        """Executes full training pipeline and returns final metrics."""
        start_time = time.time()
        if verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Synthesizing dataset with {num_cover_images} cover scenes...")

        # 1. Build dataset
        builder = SteganalysisDataBuilder(
            patch_size=self.patch_size,
            random_seed=self.random_seed,
        )
        datasets = builder.build_dataset(num_cover_images=num_cover_images)

        train_loader = DataLoader(
            datasets["train"],
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0,
        )
        val_loader = DataLoader(
            datasets["val"],
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0,
        )
        test_loader = DataLoader(
            datasets["test"],
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0,
        )

        if verbose:
            print(f"Dataset ready: Train={len(datasets['train'])}, Val={len(datasets['val'])}, Test={len(datasets['test'])}")

        # 2. Instantiate Model
        model = SteganalyzerCNN().to(self.device)
        param_counts = count_parameters(model)
        if verbose:
            print(f"Model initialized: {param_counts['total']} parameters ({param_counts['trainable']} trainable, {param_counts['fixed_srm']} fixed SRM)")

        # 3. Setup Criterion, Optimizer, Scheduler
        criterion = nn.BCEWithLogitsLoss()
        optimizer = torch.optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=2
        )

        # 4. Training Loop with Early Stopping
        best_val_loss = float("inf")
        best_model_state = None
        no_improve_epochs = 0
        history: List[Dict] = []

        for epoch in range(1, self.epochs + 1):
            model.train()
            train_loss = 0.0
            train_preds: List[float] = []
            train_targets: List[float] = []

            for imgs, labels in train_loader:
                imgs = imgs.to(self.device)
                labels = labels.to(self.device)

                optimizer.zero_grad()
                logits = model(imgs)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()

                train_loss += loss.item() * len(labels)
                probs = torch.sigmoid(logits).detach().cpu().numpy().flatten()
                train_preds.extend(probs)
                train_targets.extend(labels.cpu().numpy().flatten())

            train_loss /= len(datasets["train"])
            train_acc = accuracy_score(train_targets, [p >= 0.5 for p in train_preds])

            # Validation step
            model.eval()
            val_loss = 0.0
            val_preds: List[float] = []
            val_targets: List[float] = []

            with torch.no_grad():
                for imgs, labels in val_loader:
                    imgs = imgs.to(self.device)
                    labels = labels.to(self.device)

                    logits = model(imgs)
                    loss = criterion(logits, labels)

                    val_loss += loss.item() * len(labels)
                    probs = torch.sigmoid(logits).cpu().numpy().flatten()
                    val_preds.extend(probs)
                    val_targets.extend(labels.cpu().numpy().flatten())

            val_loss /= len(datasets["val"])
            val_acc = accuracy_score(val_targets, [p >= 0.5 for p in val_preds])
            try:
                val_auc = float(roc_auc_score(val_targets, val_preds))
            except Exception:
                val_auc = 0.5

            scheduler.step(val_loss)

            epoch_stat = {
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "train_accuracy": round(train_acc, 4),
                "val_loss": round(val_loss, 4),
                "val_accuracy": round(val_acc, 4),
                "val_auc": round(val_auc, 4),
            }
            history.append(epoch_stat)

            if verbose:
                print(
                    f"Epoch {epoch:02d}/{self.epochs:02d} | "
                    f"Train Loss: {train_loss:.4f}, Acc: {train_acc*100:.1f}% | "
                    f"Val Loss: {val_loss:.4f}, Acc: {val_acc*100:.1f}%, AUC: {val_auc:.3f}"
                )

            # Checkpoint tracking
            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                best_model_state = model.state_dict().copy()
                no_improve_epochs = 0
            else:
                no_improve_epochs += 1
                if no_improve_epochs >= self.patience:
                    if verbose:
                        print(f"Early stopping triggered after {epoch} epochs (patience={self.patience}).")
                    break

        # 5. Load best model state and evaluate on Test set
        if best_model_state is not None:
            model.load_state_dict(best_model_state)

        model.eval()
        test_loss = 0.0
        test_preds: List[float] = []
        test_targets: List[float] = []

        with torch.no_grad():
            for imgs, labels in test_loader:
                imgs = imgs.to(self.device)
                labels = labels.to(self.device)

                logits = model(imgs)
                loss = criterion(logits, labels)

                test_loss += loss.item() * len(labels)
                probs = torch.sigmoid(logits).cpu().numpy().flatten()
                test_preds.extend(probs)
                test_targets.extend(labels.cpu().numpy().flatten())

        test_loss /= len(datasets["test"])
        binary_preds = [p >= 0.5 for p in test_preds]
        test_acc = float(accuracy_score(test_targets, binary_preds))
        test_prec = float(precision_score(test_targets, binary_preds, zero_division=0))
        test_rec = float(recall_score(test_targets, binary_preds, zero_division=0))
        test_f1 = float(f1_score(test_targets, binary_preds, zero_division=0))
        try:
            test_auc = float(roc_auc_score(test_targets, test_preds))
        except Exception:
            test_auc = 0.5

        # Breakdown by method on test set
        method_stats: Dict[str, Dict] = {}
        for sample_idx, method in enumerate(datasets["test"].methods):
            if method not in method_stats:
                method_stats[method] = {"scores": [], "count": 0}
            method_stats[method]["scores"].append(float(test_preds[sample_idx]))
            method_stats[method]["count"] += 1

        method_summary = {}
        for m, data in method_stats.items():
            method_summary[m] = {
                "count": data["count"],
                "mean_p_stego": round(float(np.mean(data["scores"])), 4),
                "detection_rate_pct": round(float(np.mean([s >= 0.5 for s in data["scores"]])) * 100, 1),
            }

        elapsed_time = round(time.time() - start_time, 2)

        test_results = {
            "test_accuracy": round(test_acc, 4),
            "test_precision": round(test_prec, 4),
            "test_recall": round(test_rec, 4),
            "test_f1": round(test_f1, 4),
            "test_auc": round(test_auc, 4),
            "test_loss": round(test_loss, 4),
            "method_breakdown": method_summary,
            "training_duration_seconds": elapsed_time,
        }

        if verbose:
            print("\n" + "=" * 60)
            print("FINAL TEST EVALUATION RESULTS:")
            print(f"Accuracy:  {test_acc * 100:.2f}%")
            print(f"Precision: {test_prec:.4f}")
            print(f"Recall:    {test_rec:.4f}")
            print(f"F1-Score:  {test_f1:.4f}")
            print(f"ROC-AUC:   {test_auc:.4f}")
            print("=" * 60)
            print("P(stego) by Steganographic Method:")
            for m, s in method_summary.items():
                print(f"  {m:15s}: Mean P(stego) = {s['mean_p_stego']:.4f} (Detected: {s['detection_rate_pct']}%)")
            print("=" * 60)

        # 6. Save model checkpoint and metadata
        out_model = Path(output_model_path)
        out_model.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "architecture": "SteganalyzerCNN",
                "parameters": param_counts,
                "test_results": test_results,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            out_model,
        )

        metadata = {
            "model_name": "SteganalyzerCNN",
            "model_type": "Spatial Rich Model (SRM) Convolutional Steganalyzer",
            "framework": "PyTorch",
            "torch_version": torch.__version__,
            "srm_kernels": ["KV 5x5", "Laplacian 5x5", "Horizontal Edge 5x5"],
            "truncation_threshold": 3.0,
            "security_decision_threshold": 0.35,
            "parameters": param_counts,
            "training_samples": len(datasets["train"]),
            "validation_samples": len(datasets["val"]),
            "test_samples": len(datasets["test"]),
            "best_epoch": len(history) - no_improve_epochs,
            "test_metrics": test_results,
            "training_history": history,
            "saved_model_path": str(out_model),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

        out_meta = Path(output_metadata_path)
        out_meta.parent.mkdir(parents=True, exist_ok=True)
        with open(out_meta, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata


if __name__ == "__main__":
    trainer = SteganalyzerTrainer(
        patch_size=64,
        batch_size=16,
        learning_rate=1e-3,
        epochs=15,
        patience=4,
    )
    res = trainer.train(num_cover_images=120)
    print("\nMetadata saved successfully.")
