"""FastAPI entry point for AI Steganography Engine."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.routes_adaptive import router as adaptive_router
from app.api.routes_ai import router as ai_router
from app.api.routes_ai_stego import router as ai_stego_router
from app.api.routes_analysis import router as analysis_router
from app.api.routes_detect import router as detect_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_optimization import router as optimization_router
from app.api.routes_pipeline import router as pipeline_router
from app.api.routes_robustness import router as robustness_router
from app.api.routes_scatter import router as scatter_router
from app.api.routes_stego import router as stego_router

app = FastAPI(
    title="AI-Based Adaptive Steganography Engine",
    description="Research-oriented Steganography & AI Engine for automated key generation and adaptive embedding",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(stego_router)
app.include_router(adaptive_router)
app.include_router(ai_stego_router)
app.include_router(scatter_router)
app.include_router(feedback_router)
app.include_router(detect_router)
app.include_router(pipeline_router)
app.include_router(ai_router)
app.include_router(analysis_router)
app.include_router(metrics_router)
app.include_router(robustness_router)
app.include_router(optimization_router)

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    components: dict

@app.get("/", tags=["General"])
def root():
    return {
        "message": "AI-Based Adaptive Steganography Engine is running",
        "docs_url": "/docs",
        "health_check": "/health",
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    return HealthResponse(
        status="healthy",
        service="python_engine",
        version="1.0.0",
        components={
            "cryptography": "available",
            "image_processing": "available",
            "opencv": "available",
            "fastapi": "running",
            "steganography": "baseline_lsb_available",
            "adaptive_steganography": "rule_based_available",
            "ai_adaptive_steganography": "available",
            "prng_scatter_steganography": "available",
            "ai_region_classifier": "available",
            "cnn_steganalyzer": "available",
            "feedback_optimizer": "available",
            "feature_extraction": "available",
            "quality_metrics": "available",
            "robustness_profiler": "available",
            "genetic_optimizer": "available",
        },
    )
