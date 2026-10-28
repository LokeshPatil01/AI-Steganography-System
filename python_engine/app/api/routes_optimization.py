"""FastAPI routes for Multi-Objective Genetic / Pareto Optimization (Phase 20)."""
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.ai.genetic_optimizer import (
    Chromosome,
    GeneticStegoOptimizer,
    OptimizationWeights,
)
from app.image.loader import ImageLoader, ImageValidationError

router = APIRouter(prefix="/optimize", tags=["Genetic & Pareto Optimization"])


class ChromosomePayload(BaseModel):
    block_size: int = 16
    bits_high_texture: int = 3
    bits_medium: int = 2
    bits_smooth: int = 0
    decision_threshold: float = 0.35
    suitability_weight_high: float = 2.0
    suitability_weight_med: float = 1.0


class GenerationSnapshotModel(BaseModel):
    generation: int
    best_fitness: float
    avg_fitness: float
    best_psnr_db: float
    best_ssim: float
    best_p_stego: float
    best_chromosome: Dict[str, Any]


class ParetoPointModel(BaseModel):
    chromosome: Dict[str, Any]
    psnr_db: float
    ssim: float
    p_stego: float
    stealth_score: float
    capacity_ratio: float
    fitness_score: float


class OptimizationResultResponse(BaseModel):
    best_evaluation: Dict[str, Any]
    convergence_history: List[GenerationSnapshotModel]
    pareto_front: List[ParetoPointModel]
    weights_used: Dict[str, float]
    generations_run: int
    population_size: int
    execution_time_ms: int


@router.get("/presets")
def get_presets():
    """Returns available multi-objective optimization weight presets."""
    return {
        "presets": OptimizationWeights.PRESETS,
        "default": "Balanced",
        "description": "Presets weight PSNR (w1), SSIM (w2), Capacity (w3), and Anti-Steganalysis Stealth (w4).",
    }


@router.post("/genetic", response_model=OptimizationResultResponse)
async def run_genetic_optimization(
    cover_image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret message text"),
    payload_file: Optional[UploadFile] = File(None, description="Binary payload file"),
    profile: str = Form("Balanced", description="Weight profile: Balanced, Quality, Security, Capacity"),
    generations: int = Form(4, description="Evolutionary generations (3-8)"),
    population_size: int = Form(8, description="Population size (4-16)"),
    stego_key: str = Form("GeneticOptimizerKey#2026", description="Steganographic passphrase"),
):
    """Executes multi-objective genetic search to discover the Pareto-optimal embedding configuration."""
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'payload_file' (binary) must be provided.",
        )

    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await cover_image.read()
    try:
        cover_pixels, (w, h) = ImageLoader.load_image(cover_bytes)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    weights = OptimizationWeights.get_preset(profile)

    optimizer = GeneticStegoOptimizer(
        weights=weights,
        population_size=population_size,
        generations=generations,
    )

    try:
        result = optimizer.run_evolution(
            cover_pixels=cover_pixels,
            payload_bytes=payload_bytes,
            stego_key=stego_key,
        )
        return OptimizationResultResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/evaluate")
async def evaluate_custom_chromosome(
    cover_image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret message text"),
    payload_file: Optional[UploadFile] = File(None, description="Binary payload file"),
    profile: str = Form("Balanced", description="Weight profile"),
    block_size: int = Form(16, description="Block partition dimension: 8, 16, 32"),
    bits_high_texture: int = Form(3, description="Bit depth high texture: 1, 2, 3"),
    bits_medium: int = Form(2, description="Bit depth medium: 1, 2"),
    bits_smooth: int = Form(0, description="Bit depth smooth: 0, 1"),
    decision_threshold: float = Form(0.35, description="Decision threshold tau in [0.20, 0.45]"),
    suitability_weight_high: float = Form(2.0, description="Suitability weight high"),
    suitability_weight_med: float = Form(1.0, description="Suitability weight medium"),
    stego_key: str = Form("GeneticOptimizerKey#2026", description="Stego passphrase"),
):
    """Evaluates a single user-specified parameter chromosome across multi-objective radar metrics."""
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'payload_file' (binary) must be provided.",
        )

    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await cover_image.read()
    try:
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    ch = Chromosome(
        block_size=block_size,
        bits_high_texture=bits_high_texture,
        bits_medium=bits_medium,
        bits_smooth=bits_smooth,
        decision_threshold=decision_threshold,
        suitability_weight_high=suitability_weight_high,
        suitability_weight_med=suitability_weight_med,
    )

    weights = OptimizationWeights.get_preset(profile)
    optimizer = GeneticStegoOptimizer(weights=weights)

    try:
        eval_res = optimizer.evaluate_chromosome(
            chromosome=ch,
            cover_pixels=cover_pixels,
            payload_bytes=payload_bytes,
            stego_key=stego_key,
        )
        return eval_res.to_dict()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
