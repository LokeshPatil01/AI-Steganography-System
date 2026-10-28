"""Configuration constants and paths for the Steganography Engine."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATASETS_DIR = BASE_DIR / "datasets"
RESULTS_DIR = BASE_DIR / "results"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Engine Constants
BLOCK_SIZE = 16
DEFAULT_SECURITY_THRESHOLD = 0.35  # Steganalyzer detectability threshold
MAX_FEEDBACK_ITERATIONS = 5
RSA_KEY_SIZE_BITS = 4096
AES_KEY_SIZE_BYTES = 32  # AES-256
GCM_NONCE_SIZE_BYTES = 12  # 96-bit recommended for GCM
GCM_TAG_SIZE_BYTES = 16  # 128-bit authentication tag
