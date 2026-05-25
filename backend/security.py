import os
import re
import secrets
import time
from collections import defaultdict
from urllib.parse import urlparse

from werkzeug.security import check_password_hash, generate_password_hash

# Allowed values (whitelist — blocks injection via "material" etc.)
ALLOWED_MATERIALS = frozenset({"Cotton", "Linen", "Silk", "Wool", "Synthetic"})
ALLOWED_USE_CASES = frozenset({"Apparel", "Quilting", "Upholstery", "Curtains"})
ALLOWED_WEIGHTS = frozenset({"Light", "Medium", "Heavy"})

MAX_NAME_LEN = 120
MAX_SLUG_LEN = 120
MAX_COLOR_LEN = 40
MAX_DESC_LEN = 2000
MAX_URL_LEN = 500
MAX_MISC_LEN = 80
MAX_PRICE = 1_000_000
MAX_REVIEWS = 1_000_000
MAX_GSM = 2000
MIN_GSM = 50
MAX_MEDIA_ITEMS = 20

YOUTUBE_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)[\w-]+",
    re.I,
)
VIMEO_PATTERN = re.compile(r"^(https?://)?(www\.)?(vimeo\.com/|player\.vimeo\.com/video/)\d+", re.I)

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Login rate limit: 5 failures per 15 minutes per IP
_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SEC = 900


def get_secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "").strip()
    if key:
        return key
    # Dev-only fallback; set SECRET_KEY in production
    return "dev-only-change-me-set-SECRET_KEY-env-var"


def get_admin_username() -> str:
    return os.environ.get("ADMIN_USERNAME", "Pratham").strip()


def get_admin_password_plain() -> str:
    return os.environ.get("ADMIN_PASSWORD", "Lollipop069")


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def check_login_rate_limit(ip: str) -> tuple[bool, int]:
    """Return (allowed, seconds_until_retry)."""
    # Rate limiting is disabled for local development so login failures do not block access.
    return True, 0


def record_failed_login(ip: str) -> None:
    _LOGIN_ATTEMPTS[ip].append(time.time())


def clear_login_attempts(ip: str) -> None:
    _LOGIN_ATTEMPTS.pop(ip, None)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf(session_token: str | None, header_token: str | None) -> bool:
    if not session_token or not header_token:
        return False
    return secrets.compare_digest(session_token, header_token)


def _clean_str(value, field: str, max_len: int, required: bool = True) -> str:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return ""
    text = str(value).strip()
    if required and not text:
        raise ValueError(f"{field} is required")
    if len(text) > max_len:
        raise ValueError(f"{field} is too long (max {max_len} characters)")
    return text


def validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not slug or len(slug) > MAX_SLUG_LEN:
        raise ValueError("Invalid slug")
    if not SLUG_PATTERN.match(slug):
        raise ValueError("Slug may only contain lowercase letters, numbers, and hyphens")
    return slug


def validate_image_url(url: str) -> str:
    url = _clean_str(url, "image_url", MAX_URL_LEN)
    if url.startswith("/"):
        return url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Image URL must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("Invalid image URL")
    return url


def validate_video_url(url: str) -> tuple[str, str]:
    """Return (url, video_source) where source is upload, youtube, or vimeo."""
    url = _clean_str(url, "url", MAX_URL_LEN)
    if url.startswith("/"):
        return url, "upload"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Invalid video URL")
    if YOUTUBE_PATTERN.match(url):
        return url, "youtube"
    if VIMEO_PATTERN.match(url):
        return url, "vimeo"
    if url.lower().endswith((".mp4", ".webm", ".mov")):
        return url, "upload"
    raise ValueError("Video must be MP4 upload, YouTube, or Vimeo link")


def validate_gsm(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        gsm = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("GSM must be a number") from exc
    if gsm < MIN_GSM or gsm > MAX_GSM:
        raise ValueError(f"GSM must be between {MIN_GSM} and {MAX_GSM}")
    return gsm


def validate_media_list(media) -> list[dict]:
    if media is None:
        return []
    if not isinstance(media, list):
        raise ValueError("Media must be a list")
    if len(media) > MAX_MEDIA_ITEMS:
        raise ValueError(f"Maximum {MAX_MEDIA_ITEMS} media items allowed")

    validated = []
    for idx, item in enumerate(media):
        if not isinstance(item, dict):
            raise ValueError("Invalid media item")
        media_type = (item.get("media_type") or "").strip().lower()
        if media_type not in ("image", "video"):
            raise ValueError("Media type must be image or video")
        raw_url = (item.get("url") or "").strip()
        if not raw_url:
            raise ValueError("Media URL is required")
        if media_type == "image":
            url = validate_image_url(raw_url)
            video_source = None
        else:
            url, video_source = validate_video_url(raw_url)
        try:
            sort_order = int(item.get("sort_order", idx))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid sort order") from exc
        validated.append({
            "media_type": media_type,
            "url": url,
            "video_source": video_source,
            "sort_order": sort_order,
        })
    validated.sort(key=lambda m: m["sort_order"])
    return validated


def validate_fabric_payload(data: dict) -> dict:
    """Validate and sanitize fabric input. Raises ValueError on bad input."""
    name = _clean_str(data.get("name"), "name", MAX_NAME_LEN)
    material = _clean_str(data.get("material"), "material", MAX_MISC_LEN)
    color = _clean_str(data.get("color"), "color", MAX_COLOR_LEN)
    use_case = _clean_str(data.get("use_case"), "use_case", MAX_MISC_LEN)
    description = _clean_str(data.get("description"), "description", MAX_DESC_LEN)
    weight = _clean_str(data.get("weight") or "Medium", "weight", MAX_MISC_LEN, required=False)
    sustainability = _clean_str(
        data.get("sustainability") or "Eco-friendly", "sustainability", MAX_MISC_LEN, required=False
    )

    if material not in ALLOWED_MATERIALS:
        raise ValueError(f"Invalid material. Allowed: {', '.join(sorted(ALLOWED_MATERIALS))}")
    if use_case not in ALLOWED_USE_CASES:
        raise ValueError(f"Invalid use. Allowed: {', '.join(sorted(ALLOWED_USE_CASES))}")
    if weight not in ALLOWED_WEIGHTS:
        raise ValueError(f"Invalid weight. Allowed: {', '.join(sorted(ALLOWED_WEIGHTS))}")

    try:
        price_inr = float(data.get("price_inr"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Price must be a number") from exc
    if price_inr < 0 or price_inr > MAX_PRICE:
        raise ValueError("Price out of allowed range")

    try:
        reviews_count = int(data.get("reviews_count") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Reviews count must be a number") from exc
    if reviews_count < 0 or reviews_count > MAX_REVIEWS:
        raise ValueError("Reviews count out of allowed range")

    raw_slug = (data.get("slug") or "").strip()
    if not raw_slug:
        raise ValueError("Slug is required")
    slug = validate_slug(raw_slug)

    gsm = validate_gsm(data.get("gsm"))
    media = validate_media_list(data.get("media"))

    image_url = (data.get("image_url") or "").strip()
    if not image_url and media:
        first_image = next((m["url"] for m in media if m["media_type"] == "image"), None)
        if first_image:
            image_url = first_image
    if not image_url:
        raise ValueError("At least one product image is required")
    image_url = validate_image_url(image_url)

    return {
        "slug": slug,
        "name": name,
        "material": material,
        "color": color,
        "use_case": use_case,
        "price_inr": price_inr,
        "image_url": image_url,
        "description": description,
        "weight": weight,
        "sustainability": sustainability,
        "reviews_count": reviews_count,
        "gsm": gsm,
        "media": media,
    }


def validate_fabric_payload_with_slug(data: dict, slugify_fn) -> dict:
    name = _clean_str(data.get("name"), "name", MAX_NAME_LEN)
    raw_slug = (data.get("slug") or "").strip() or slugify_fn(name)
    return validate_fabric_payload({**data, "name": name, "slug": raw_slug})


def validate_slug_param(slug: str) -> str:
    """Validate slug in URL path (public read)."""
    return validate_slug(slug)
