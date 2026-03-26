from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "samples" / "generated"
DEFAULT_SAMPLE_POSTMORTEM = PROJECT_ROOT / "samples" / "postmortems" / "payment-api-latency.md"
