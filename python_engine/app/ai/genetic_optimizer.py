"""Multi-Objective Genetic Algorithm & Pareto Optimization Suite (Phase 20).

Automates meta-heuristic parameter discovery across conflicting steganographic objectives:
1. Visual Imperceptibility: Maximizing PSNR and SSIM.
2. Adversarial Stealth: Minimizing CNN Steganalyzer detectability P(stego).
3. Embedding Efficiency: Maximizing capacity utilization while preserving smooth blocks.

Implements:
- Multi-Objective Objective Fitness Score: S = w1*(PSNR-30)/20 + w2*SSIM + w3*(C_used/C_max) - w4*P(stego).
- Discrete and continuous parameter chromosome encoding.
- Elitist genetic evolution (Tournament selection, Uniform crossover, Adaptive mutation).
- Pareto non-dominated frontier extraction.
"""
from dataclasses import asdict, dataclass
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from app.ai.steganalyzer_net import SteganalyzerDetector
from app.image.metrics import compute_mse, compute_psnr, compute_ssim, evaluate_quality_rating
from app.steganography.baseline_lsb import BaselineLSB, CapacityExceededError
from app.steganography.scatter_stego import KeyScatteredAiLSB


@dataclass
class OptimizationWeights:
    """Weights for the multi-objective fitness formulation."""
    w_quality: float = 0.25   # PSNR weight (w1)
    w_ssim: float = 0.25      # SSIM weight (w2)
    w_capacity: float = 0.25  # Capacity utilization weight (w3)
    w_stealth: float = 0.25   # Adversarial stealth / anti-steganalysis weight (w4)

    PRESETS = {
        "Balanced": {"w_quality": 0.25, "w_ssim": 0.25, "w_capacity": 0.25, "w_stealth": 0.25},
        "Quality": {"w_quality": 0.40, "w_ssim": 0.40, "w_capacity": 0.10, "w_stealth": 0.10},
        "Security": {"w_quality": 0.20, "w_ssim": 0.20, "w_capacity": 0.10, "w_stealth": 0.50},
        "Capacity": {"w_quality": 0.20, "w_ssim": 0.20, "w_capacity": 0.50, "w_stealth": 0.10},
    }

    @classmethod
    def get_preset(cls, name: str) -> "OptimizationWeights":
        p = cls.PRESETS.get(name, cls.PRESETS["Balanced"])
        return cls(**p)


@dataclass
class Chromosome:
    """Encodes a candidate steganographic parameter configuration."""
    block_size: int = 16              # Choices: 8, 16, 32
    bits_high_texture: int = 3       # Depth for Class 2: 1, 2, 3
    bits_medium: int = 2             # Depth for Class 1: 1, 2
    bits_smooth: int = 0             # Depth for Class 0: 0, 1
    decision_threshold: float = 0.35 # CNN detector threshold tau in [0.20, 0.45]
    suitability_weight_high: float = 2.0  # Weight for Class 2 [1.0, 3.0]
    suitability_weight_med: float = 1.0   # Weight for Class 1 [0.5, 2.0]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def random(cls, rng: Optional[random.Random] = None) -> "Chromosome":
        r = rng or random
        return cls(
            block_size=r.choice([8, 16, 32]),
            bits_high_texture=r.choice([1, 2, 3]),
            bits_medium=r.choice([1, 2]),
            bits_smooth=r.choice([0, 1]),
            decision_threshold=round(r.uniform(0.20, 0.45), 2),
            suitability_weight_high=round(r.uniform(1.0, 3.0), 2),
            suitability_weight_med=round(r.uniform(0.5, 2.0), 2),
        )


@dataclass
class FitnessEvaluation:
    """Evaluation metrics and fitness score for a specific chromosome."""
    chromosome: Chromosome
    fitness_score: float
    psnr_db: float
    ssim: float
    mse: float
    capacity_used_ratio: float
    p_stego: float
    viable: bool
    quality_rating: str
    is_imperceptible: bool

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chromosome"] = self.chromosome.to_dict()
        return d


@dataclass
class GenerationSnapshot:
    """Convergence metrics for a single generation step."""
    generation: int
    best_fitness: float
    avg_fitness: float
    best_psnr_db: float
    best_ssim: float
    best_p_stego: float
    best_chromosome: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParetoPoint:
    """Represents a non-dominated trade-off solution on the Pareto frontier."""
    chromosome: Dict[str, Any]
    psnr_db: float
    ssim: float
    p_stego: float
    stealth_score: float  # 1.0 - p_stego
    capacity_ratio: float
    fitness_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GeneticStegoOptimizer:
    """Multi-Objective Genetic Algorithm optimizer for steganographic hyper-parameters."""

    def __init__(
        self,
        weights: Optional[OptimizationWeights] = None,
        population_size: int = 10,
        generations: int = 5,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.2,
        elitism_count: int = 2,
        seed: Optional[int] = None,
    ):
        self.weights = weights or OptimizationWeights.get_preset("Balanced")
        self.population_size = max(4, population_size)
        self.generations = max(1, generations)
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = min(elitism_count, self.population_size // 2)
        self.rng = random.Random(seed)
        self.detector = SteganalyzerDetector.get_instance()
        self._eval_cache: Dict[str, FitnessEvaluation] = {}

    def _chromosome_cache_key(self, ch: Chromosome) -> str:
        return f"{ch.block_size}_{ch.bits_high_texture}_{ch.bits_medium}_{ch.bits_smooth}_{ch.decision_threshold:.2f}"

    def compute_fitness_score(
        self,
        psnr_db: float,
        ssim: float,
        capacity_used_ratio: float,
        p_stego: float,
    ) -> float:
        """Calculates multi-objective fitness S per PROJECT_ARCHITECTURE.md Section 11."""
        # Normalize PSNR over working range [30.0, 50.0]
        norm_psnr = min(max((psnr_db - 30.0) / 20.0, 0.0), 1.0)
        norm_ssim = min(max(ssim, 0.0), 1.0)
        norm_cap = min(max(capacity_used_ratio, 0.0), 1.0)
        norm_pstego = min(max(p_stego, 0.0), 1.0)

        fitness = (
            self.weights.w_quality * norm_psnr
            + self.weights.w_ssim * norm_ssim
            + self.weights.w_capacity * norm_cap
            - self.weights.w_stealth * norm_pstego
        )
        return round(float(fitness), 4)

    def evaluate_chromosome(
        self,
        chromosome: Chromosome,
        cover_pixels: np.ndarray,
        payload_bytes: bytes,
        stego_key: str = "GeneticOptimizerKey#2026",
    ) -> FitnessEvaluation:
        """Evaluates an individual parameter chromosome against cover pixels and payload."""
        cache_key = self._chromosome_cache_key(chromosome)
        if cache_key in self._eval_cache:
            return self._eval_cache[cache_key]

        try:
            # 1. Embed using the chromosome's block size
            stego_pixels, meta = KeyScatteredAiLSB.embed(
                cover_pixels=cover_pixels,
                payload=payload_bytes,
                stego_key=stego_key,
                block_size=chromosome.block_size,
            )

            # 2. Objective Image Fidelity Metrics
            mse_val = compute_mse(cover_pixels, stego_pixels)
            psnr_val = compute_psnr(cover_pixels, stego_pixels)
            ssim_res = compute_ssim(cover_pixels, stego_pixels)
            ssim_val = float(ssim_res["ssim_mean"])
            quality_rating, is_imperceptible = evaluate_quality_rating(psnr_val, ssim_val)

            # 3. Capacity utilization ratio
            cap_used = float(meta.get("capacity_used_percent", 10.0)) / 100.0

            # 4. CNN Steganalyzer detectability
            det_res = self.detector.predict(stego_pixels, threshold=chromosome.decision_threshold)
            p_stego = float(det_res.stego_probability)

            # 5. Composite Multi-Objective Fitness
            fitness = self.compute_fitness_score(psnr_val, ssim_val, cap_used, p_stego)

            eval_res = FitnessEvaluation(
                chromosome=chromosome,
                fitness_score=fitness,
                psnr_db=round(float(psnr_val), 2),
                ssim=round(ssim_val, 4),
                mse=round(float(mse_val), 4),
                capacity_used_ratio=round(cap_used, 4),
                p_stego=round(p_stego, 4),
                viable=True,
                quality_rating=quality_rating,
                is_imperceptible=is_imperceptible,
            )

        except (CapacityExceededError, ValueError):
            # Penalize chromosomes whose block sizes cannot absorb payload
            eval_res = FitnessEvaluation(
                chromosome=chromosome,
                fitness_score=-1.0,
                psnr_db=0.0,
                ssim=0.0,
                mse=999.0,
                capacity_used_ratio=1.0,
                p_stego=1.0,
                viable=False,
                quality_rating="DEGRADED",
                is_imperceptible=False,
            )

        self._eval_cache[cache_key] = eval_res
        return eval_res

    def crossover(self, parent_a: Chromosome, parent_b: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Performs uniform parameter crossover between two parent chromosomes."""
        if self.rng.random() > self.crossover_rate:
            return parent_a, parent_b

        def pick(val_a, val_b):
            return val_a if self.rng.random() < 0.5 else val_b

        child_1 = Chromosome(
            block_size=pick(parent_a.block_size, parent_b.block_size),
            bits_high_texture=pick(parent_a.bits_high_texture, parent_b.bits_high_texture),
            bits_medium=pick(parent_a.bits_medium, parent_b.bits_medium),
            bits_smooth=pick(parent_a.bits_smooth, parent_b.bits_smooth),
            decision_threshold=pick(parent_a.decision_threshold, parent_b.decision_threshold),
            suitability_weight_high=pick(parent_a.suitability_weight_high, parent_b.suitability_weight_high),
            suitability_weight_med=pick(parent_a.suitability_weight_med, parent_b.suitability_weight_med),
        )

        child_2 = Chromosome(
            block_size=pick(parent_b.block_size, parent_a.block_size),
            bits_high_texture=pick(parent_b.bits_high_texture, parent_a.bits_high_texture),
            bits_medium=pick(parent_b.bits_medium, parent_a.bits_medium),
            bits_smooth=pick(parent_b.bits_smooth, parent_a.bits_smooth),
            decision_threshold=pick(parent_b.decision_threshold, parent_a.decision_threshold),
            suitability_weight_high=pick(parent_b.suitability_weight_high, parent_a.suitability_weight_high),
            suitability_weight_med=pick(parent_b.suitability_weight_med, parent_a.suitability_weight_med),
        )

        return child_1, child_2

    def mutate(self, chromosome: Chromosome) -> Chromosome:
        """Applies adaptive mutation to individual parameter genes."""
        c = Chromosome(**chromosome.to_dict())

        if self.rng.random() < self.mutation_rate:
            c.block_size = self.rng.choice([8, 16, 32])
        if self.rng.random() < self.mutation_rate:
            c.bits_high_texture = self.rng.choice([1, 2, 3])
        if self.rng.random() < self.mutation_rate:
            c.bits_medium = self.rng.choice([1, 2])
        if self.rng.random() < self.mutation_rate:
            c.bits_smooth = self.rng.choice([0, 1])
        if self.rng.random() < self.mutation_rate:
            c.decision_threshold = round(self.rng.uniform(0.20, 0.45), 2)
        if self.rng.random() < self.mutation_rate:
            c.suitability_weight_high = round(self.rng.uniform(1.0, 3.0), 2)
        if self.rng.random() < self.mutation_rate:
            c.suitability_weight_med = round(self.rng.uniform(0.5, 2.0), 2)

        return c

    def tournament_select(self, evaluated_pop: List[FitnessEvaluation], k: int = 3) -> Chromosome:
        """Selects parent using tournament selection."""
        candidates = self.rng.sample(evaluated_pop, min(k, len(evaluated_pop)))
        best = max(candidates, key=lambda ind: ind.fitness_score)
        return best.chromosome

    @staticmethod
    def extract_pareto_front(evaluations: List[FitnessEvaluation]) -> List[ParetoPoint]:
        """Extracts the non-dominated Pareto frontier trading off PSNR vs. Stealth."""
        viable_evals = [e for e in evaluations if e.viable]
        if not viable_evals:
            return []

        pareto_points: List[ParetoPoint] = []
        for a in viable_evals:
            dominated = False
            for b in viable_evals:
                if a is b:
                    continue
                # b dominates a if b is at least as good in PSNR and Stealth and strictly better in one
                b_better_or_equal = (b.psnr_db >= a.psnr_db) and (b.p_stego <= a.p_stego)
                b_strictly_better = (b.psnr_db > a.psnr_db) or (b.p_stego < a.p_stego)

                if b_better_or_equal and b_strictly_better:
                    dominated = True
                    break

            if not dominated:
                pt = ParetoPoint(
                    chromosome=a.chromosome.to_dict(),
                    psnr_db=a.psnr_db,
                    ssim=a.ssim,
                    p_stego=a.p_stego,
                    stealth_score=round(1.0 - a.p_stego, 4),
                    capacity_ratio=a.capacity_used_ratio,
                    fitness_score=a.fitness_score,
                )
                pareto_points.append(pt)

        # Sort front by PSNR descending
        pareto_points.sort(key=lambda p: p.psnr_db, reverse=True)
        return pareto_points

    def run_evolution(
        self,
        cover_pixels: np.ndarray,
        payload_bytes: bytes,
        stego_key: str = "GeneticOptimizerKey#2026",
    ) -> Dict[str, Any]:
        """Executes full multi-objective evolutionary search."""
        start_time = time.perf_counter()

        # 1. Initialize random population
        population = [Chromosome.random(self.rng) for _ in range(self.population_size)]
        # Seed standard research baseline into initial population
        population[0] = Chromosome(block_size=16, bits_high_texture=3, bits_medium=2, bits_smooth=0, decision_threshold=0.35)

        history: List[GenerationSnapshot] = []
        all_evaluations: List[FitnessEvaluation] = []

        for gen in range(1, self.generations + 1):
            # Evaluate all individuals
            eval_pop = [
                self.evaluate_chromosome(ind, cover_pixels, payload_bytes, stego_key)
                for ind in population
            ]
            all_evaluations.extend(eval_pop)

            # Sort population by fitness descending
            eval_pop.sort(key=lambda x: x.fitness_score, reverse=True)
            best_ind = eval_pop[0]

            avg_fit = float(np.mean([ind.fitness_score for ind in eval_pop]))

            snapshot = GenerationSnapshot(
                generation=gen,
                best_fitness=round(best_ind.fitness_score, 4),
                avg_fitness=round(avg_fit, 4),
                best_psnr_db=best_ind.psnr_db,
                best_ssim=best_ind.ssim,
                best_p_stego=best_ind.p_stego,
                best_chromosome=best_ind.chromosome.to_dict(),
            )
            history.append(snapshot)

            # Stop after last generation
            if gen == self.generations:
                break

            # 2. Reproduction with Elitism
            new_population: List[Chromosome] = []

            # Preserve top elite individuals
            for elite in eval_pop[:self.elitism_count]:
                new_population.append(elite.chromosome)

            # Generate rest of offspring via selection, crossover, and mutation
            while len(new_population) < self.population_size:
                p1 = self.tournament_select(eval_pop)
                p2 = self.tournament_select(eval_pop)
                c1, c2 = self.crossover(p1, p2)
                new_population.append(self.mutate(c1))
                if len(new_population) < self.population_size:
                    new_population.append(self.mutate(c2))

            population = new_population

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract non-dominated Pareto frontier
        pareto_front = self.extract_pareto_front(all_evaluations)

        # Overall best solution
        best_overall = max(all_evaluations, key=lambda x: x.fitness_score)

        return {
            "best_evaluation": best_overall.to_dict(),
            "convergence_history": [snap.to_dict() for snap in history],
            "pareto_front": [pt.to_dict() for pt in pareto_front],
            "weights_used": asdict(self.weights),
            "generations_run": self.generations,
            "population_size": self.population_size,
            "execution_time_ms": elapsed_ms,
        }
