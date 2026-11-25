"""Runtime settings, read from environment variables (see .env.example)."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# Fuzzy matching (0-100). The deck specifies ~85% as the "confident match" cutoff.
MATCH_CUTOFF = float(os.getenv("MATCH_CUTOFF", "85"))
# Below the cutoff but above this floor, we show the closest item as a hint
# but still report "could not verify". Below the floor there is no hint.
WEAK_MATCH_FLOOR = float(os.getenv("WEAK_MATCH_FLOOR", "60"))

# A billed amount is only flagged when it is more than this fraction above the
# CGHS reference (5% by default), to avoid flagging rounding differences.
CGHS_TOLERANCE = float(os.getenv("CGHS_TOLERANCE", "0.05"))

# Which CGHS rate column to use when the request doesn't say. "nabh" is the
# higher rate, so it produces fewer flags (the cautious choice).
DEFAULT_ACCREDITATION = os.getenv("DEFAULT_ACCREDITATION", "nabh")

# NVIDIA hosted model used to improve explanations for flagged bill items.
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
