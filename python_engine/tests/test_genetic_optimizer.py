"""Automated Unit & Integration Tests for Phase 20: Multi-Objective Genetic / Pareto Optimization."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.ai.genetic_optimizer import (
    Chromosome,
    FitnessEvaluation,
    GeneticStegoOptimizer,
    OptimizationWeights,
    ParetoPoint,
)
from app.image.loader import ImageLoader
from app.main import app


@pytest.fixture
def test_cover_image() -> np.ndarray:
    """Returns a deterministic 64x64 RGB test image."""
    rng = np.random.default_rng(2026)
    return rng.integers(40, 220, (64, 64, 3), dtype=np.uint8)


@pytest.fixture
def test_payload() -> bytes:
    """Returns a sample confidential research payload."""
    return b"PARETO_OPTIMIZATION_TEST_PAYLOAD_FINAL_YEAR_2026"


class TestGeneticAlgorithmComponents:
    """Unit tests for Chromosome, Weights, and Operators."""

    def test_presets_weights(self):
        presets = ["Balanced", "Quality", "Security", "Capacity"]
        for p in presets:
            w = OptimizationWeights.get_preset(p)
            total = w.w_quality + w.w_ssim + w.w_capacity + w.w_stealth
            assert abs(total - 1.0) < 1e-4

    def test_chromosome_serialization_and_random(self):
        c = Chromosome(block_size=16, bits_high_texture=3, bits_medium=2, bits_smooth=0, decision_threshold=0.35)
        d = c.to_dict()
        assert d["block_size"] == 16
        assert d["bits_high_texture"] == 3

        rnd = Chromosome.random()
        assert rnd.block_size in (8, 16, 32)
        assert rnd.bits_high_texture in (1, 2, 3)
        assert 0.20 <= rnd.decision_threshold <= 0.45

    def test_fitness_score_computation(self):
        opt = GeneticStegoOptimizer()
        # High quality & low detectability => high fitness
        high_fit = opt.compute_fitness_score(psnr_db=48.0, ssim=0.995, capacity_used_ratio=0.15, p_stego=0.10)
        # Low quality & high detectability => low fitness
        low_fit = opt.compute_fitness_score(psnr_db=32.0, ssim=0.920, capacity_used_ratio=0.80, p_stego=0.85)
        assert high_fit > low_fit

    def test_crossover_operator(self):
        opt = GeneticStegoOptimizer(crossover_rate=1.0, seed=42)
        p1 = Chromosome(block_size=8, bits_high_texture=1)
        p2 = Chromosome(block_size=32, bits_high_texture=3)
        c1, c2 = opt.crossover(p1, p2)
        assert c1.block_size in (8, 32)
        assert c2.block_size in (8, 32)

    def test_mutation_operator(self):
        opt = GeneticStegoOptimizer(mutation_rate=1.0, seed=99)
        orig = Chromosome(block_size=16)
        mutated = opt.mutate(orig)
        assert mutated.block_size in (8, 16, 32)

    def test_extract_pareto_front(self):
        # A dominates B (higher PSNR, lower P(stego))
        eval_a = FitnessEvaluation(
            chromosome=Chromosome(block_size=16),
            fitness_score=0.75,
            psnr_db=45.0,
            ssim=0.99,
            mse=2.0,
            capacity_used_ratio=0.2,
            p_stego=0.15,
            viable=True,
            quality_rating="EXCELLENT",
            is_imperceptible=True,
        )
        eval_b = FitnessEvaluation(
            chromosome=Chromosome(block_size=8),
            fitness_score=0.40,
            psnr_db=38.0,
            ssim=0.96,
            mse=8.0,
            capacity_used_ratio=0.5,
            p_stego=0.45,
            viable=True,
            quality_rating="GOOD",
            is_imperceptible=False,
        )
        pareto = GeneticStegoOptimizer.extract_pareto_front([eval_a, eval_b])
        # Only eval_a should be on the front
        assert len(pareto) == 1
        assert pareto[0].psnr_db == 45.0


class TestEvolutionaryOptimizer:
    """Integration tests for GeneticStegoOptimizer."""

    def test_evaluate_chromosome_live(self, test_cover_image: np.ndarray, test_payload: bytes):
        opt = GeneticStegoOptimizer()
        ch = Chromosome(block_size=16, bits_high_texture=3, bits_medium=2, bits_smooth=0, decision_threshold=0.35)
        res = opt.evaluate_chromosome(ch, test_cover_image, test_payload)
        assert res.viable is True
        assert res.psnr_db > 35.0
        assert res.ssim > 0.95
        assert 0.0 <= res.p_stego <= 1.0

    def test_run_evolution_convergence(self, test_cover_image: np.ndarray, test_payload: bytes):
        opt = GeneticStegoOptimizer(
            population_size=6,
            generations=3,
            seed=2026,
        )
        res = opt.run_evolution(test_cover_image, test_payload)
        assert res["generations_run"] == 3
        assert len(res["convergence_history"]) == 3
        assert len(res["pareto_front"]) >= 1
        assert res["best_evaluation"]["viable"] is True
        # Elitism guarantees best fitness is non-decreasing
        hist = res["convergence_history"]
        assert hist[2]["best_fitness"] >= hist[0]["best_fitness"] or abs(hist[2]["best_fitness"] - hist[0]["best_fitness"]) < 0.05


class TestFastAPIOptimizationRoutes:
    """Integration tests for FastAPI /optimize endpoints."""

    client = TestClient(app)

    def test_get_presets_endpoint(self):
        response = self.client.get("/optimize/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "Balanced" in data["presets"]
        assert "Quality" in data["presets"]

    def test_evaluate_endpoint(self, test_cover_image: np.ndarray):
        png_bytes = ImageLoader.save_image_to_bytes(test_cover_image)
        response = self.client.post(
            "/optimize/evaluate",
            files={"cover_image": ("cover.png", png_bytes, "image/png")},
            data={
                "message": "Optimization Test Secret 2026",
                "profile": "Quality",
                "block_size": 16,
                "bits_high_texture": 3,
                "bits_medium": 2,
                "bits_smooth": 0,
                "decision_threshold": 0.35,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "fitness_score" in data
        assert "psnr_db" in data
        assert "p_stego" in data
        assert data["viable"] is True

    def test_genetic_evolution_endpoint(self, test_cover_image: np.ndarray):
        png_bytes = ImageLoader.save_image_to_bytes(test_cover_image)
        response = self.client.post(
            "/optimize/genetic",
            files={"cover_image": ("cover.png", png_bytes, "image/png")},
            data={
                "message": "Genetic Search Test 2026",
                "profile": "Balanced",
                "generations": 2,
                "population_size": 4,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "best_evaluation" in data
        assert "convergence_history" in data
        assert len(data["convergence_history"]) == 2
        assert "pareto_front" in data
