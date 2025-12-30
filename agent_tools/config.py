"""
Configuration module for agent_tools.
Contains all configuration constants, environment variables, and logging setup.
"""
import os
import logging
import sys
from dotenv import load_dotenv
from PIL import ImageFile

# Configure PIL to handle truncated images gracefully
# This prevents OSError when images are slightly corrupted but still usable
# Set this early so it applies to all image loading throughout the application
ImageFile.LOAD_TRUNCATED_IMAGES = True

load_dotenv()

# ---------- Logging Configuration ----------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "agent.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configure root logger
logger = logging.getLogger("agent_tools")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Prevent duplicate handlers
if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional, if LOG_FILE is set)
    if LOG_FILE and LOG_FILE.lower() != "none":
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # File gets all logs
            file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Use console handler if available, otherwise print (logger might not have handlers yet)
            if console_handler:
                logger.warning(f"Could not create log file '{LOG_FILE}': {e}. Logging to console only.")
            else:
                # Fallback if no handlers configured yet
                sys.stderr.write(f"WARNING: Could not create log file '{LOG_FILE}': {e}. Logging to console only.\n")

# Prevent propagation to root logger
logger.propagate = False

# ---------- Folder Paths ----------
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"  # default main output (served at /output/…)
PREVIEW_FOLDER = "output_preview"  # local folder for UI thumbnails

# ---------- Model Configuration ----------
REASONING_MODEL = "gemini-3-pro-preview"
IMAGE_MODEL = "gemini-3-pro-image-preview"

# ---------- Input Validation Configuration ----------
MAX_STRING_LENGTH = 10000  # Maximum length for text inputs
MAX_PROMPT_LENGTH = 5000    # Maximum length for prompts
MAX_LOCATION_LENGTH = 200   # Maximum length for location strings
MAX_FILENAME_LENGTH = 255   # Maximum filename length

# Valid enum values
VALID_LIGHTING_MODES = {"morning", "noon", "sunset", "night"}
VALID_RESOLUTIONS = {"1K", "2K", "4K"}
VALID_STRENGTHS = {"subtle", "medium", "strong"}
VALID_COLOR_TEMPS = {"cool", "neutral", "warm"}
VALID_CONTRASTS = {"soft", "balanced", "punchy"}
VALID_WEATHER = {"clear", "overcast", "rain", "snow"}
VALID_SEASONS = {"none", "summer", "winter"}
VALID_CAMERA_DIRS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW", None}
VALID_CLOUD_TYPES = {"na", "n/a", "none", "cirriform", "stratiform", "cumuliform"}

# ---------- Retry Configuration ----------
RETRY_MAX_ATTEMPTS = int(os.getenv("API_RETRY_MAX_ATTEMPTS", "3"))
RETRY_INITIAL_DELAY = float(os.getenv("API_RETRY_INITIAL_DELAY", "1.0"))
RETRY_BACKOFF_FACTOR = float(os.getenv("API_RETRY_BACKOFF_FACTOR", "2.0"))
RETRY_MAX_DELAY = float(os.getenv("API_RETRY_MAX_DELAY", "60.0"))
RETRY_JITTER = True  # Add randomness to prevent thundering herd

# ---------- Session Memory Configuration ----------
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
SESSION_MAX_SIZE = int(os.getenv("SESSION_MAX_SIZE", "1000"))
SESSION_CLEANUP_INTERVAL = int(os.getenv("SESSION_CLEANUP_INTERVAL", "300"))

# ---------- Critic Configuration ----------
CRITIC_FAIL_SAFE = os.getenv("CRITIC_FAIL_SAFE", "false").lower() == "true"  # Default: fail-secure

# ---------- Performance Configuration ----------
# Maximum number of parallel workers for batch rendering
# Higher values = faster batches but more API calls simultaneously
# Adjust based on your API rate limits (default: 8, previously: 5)
MAX_RENDER_WORKERS = int(os.getenv("MAX_RENDER_WORKERS", "8"))

# Image size for agent analysis (agents don't need full resolution)
# Smaller images = faster API calls and lower costs
# Full resolution is still used for final render
ANALYSIS_IMAGE_SIZE = (1024, 1024)  # Max dimensions for analysis

# ---------- Styles Configuration ----------
STYLES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.json")

# ---------- Projects Configuration ----------
# Project-specific input and output paths
projects = {
    "cowboys": {
        "input_path": "data/raw/Cowboys",
        "output_path": "data/processed/Cowboys"
    },
    "dallas_fs": {
        "input_path": "data/raw/ProjectBeta",
        "output_path": "data/processed/DallasFS"
    }
}

