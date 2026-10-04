"""Where local data lives. Everything under data/ except label and id files stays out of git."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data" / "public"  # downloaded and derived public data
MANUAL = ROOT / "data" / "manual"  # our pool and labels
MODELS = ROOT / "checkpoints"

MEDIQ_POSTS = PUBLIC / "mediq_posts.csv"
PATIENT_COMMENTS = PUBLIC / "patient_comments.csv"
POOL_IDS = MANUAL / "pool.ids.csv"  # committed: which posts we label, and who labels them
POOL = MANUAL / "pool.csv"  # local only: the same posts with their text
DRAFT_LABELS = MANUAL / "draft.labels.csv"  # first-pass labels shown in the labelling tool
