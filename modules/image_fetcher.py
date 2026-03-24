import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

from modules.claude_engine import ask_claude

IMAGES_DIR = Path("data/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024   # 5 MB
MIN_DIMENSION = 200                 # px
ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}
HEADERS = {"User-Agent": "Mozilla/5.0"}


def extract_image_query(tweet_text: str) -> str:
    """Ask Claude to derive a good image search query from the tweet."""
    prompt = (
        f"Given this IB tweet, extract the most important technical concept that would benefit "
        f"from a visual diagram or chart. Return ONLY a search query (3-5 words) for finding an "
        f"educational image. Examples: \"LBO structure diagram\", \"DCF model flowchart\", "
        f"\"enterprise value bridge chart\".\n\nTweet: {tweet_text}"
    )
    query = ask_claude(prompt, timeout=60)
    # Strip any surrounding quotes Claude might add
    return query.strip().strip('"').strip("'")


def search_images(query: str, max_results: int = 5) -> list:
    if not DDGS_AVAILABLE:
        raise ImportError("duckduckgo-search is not installed. Run: pip install duckduckgo-search")
    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=max_results))
    return results


def _safe_filename(query: str) -> str:
    """Convert query string to a safe filename stem."""
    return re.sub(r"[^a-z0-9_]", "_", query.lower())[:50]


def _validate_image(path: Path) -> bool:
    """Return True if the file is a valid image meeting size and dimension requirements."""
    if path.stat().st_size > MAX_FILE_SIZE:
        return False
    if not PIL_AVAILABLE:
        return True  # Skip dimension check if Pillow not installed
    try:
        with Image.open(path) as img:
            w, h = img.size
            return w >= MIN_DIMENSION and h >= MIN_DIMENSION
    except Exception:
        return False


def download_image(url: str, dest_path: Path) -> bool:
    """Download image from URL to dest_path. Returns True on success."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        if resp.status_code != 200:
            return False
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type:
            return False
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return True
    except Exception:
        return False


def fetch_image_for_tweet(tweet_text: str) -> dict | None:
    """
    Full pipeline: extract query → search → download → validate.
    Returns dict with keys: local_path, source_url, query
    Returns None if no valid image found.
    """
    query = extract_image_query(tweet_text)
    results = search_images(query, max_results=8)

    stem = _safe_filename(query)

    for result in results:
        url = result.get("image") or result.get("url", "")
        if not url:
            continue

        ext = Path(urlparse(url).path).suffix.lower()
        if ext not in ALLOWED_EXTS:
            ext = ".jpg"

        dest = IMAGES_DIR / f"{stem}{ext}"

        if not download_image(url, dest):
            continue

        if not _validate_image(dest):
            dest.unlink(missing_ok=True)
            continue

        return {
            "local_path": str(dest),
            "source_url": url,
            "query": query,
        }

    return None
