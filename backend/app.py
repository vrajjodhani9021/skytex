import os
import re
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.utils import secure_filename

load_dotenv(Path(__file__).parent / ".env")

try:
    from backend.database import (
        ensure_unique_slug,
        execute,
        fabric_to_api,
        get_admin_by_username,
        get_connection,
        init_db,
        save_media_with_cursor,
        uses_sqlite,
    )
    from backend.security import (
        check_login_rate_limit,
        clear_login_attempts,
        client_ip,
        generate_csrf_token,
        get_secret_key,
        record_failed_login,
        validate_csrf,
        validate_fabric_payload_with_slug,
        validate_slug_param,
        verify_password,
    )
except ImportError:
    from database import (
        ensure_unique_slug,
        execute,
        fabric_to_api,
        get_admin_by_username,
        get_connection,
        init_db,
        save_media_with_cursor,
        uses_sqlite,
    )
    from security import (
        check_login_rate_limit,
        clear_login_attempts,
        client_ip,
        generate_csrf_token,
        get_secret_key,
        record_failed_login,
        validate_csrf,
        validate_fabric_payload_with_slug,
        validate_slug_param,
        verify_password,
    )

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
UPLOAD_DIR = FRONTEND_DIR / "assets" / "uploads"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.secret_key = get_secret_key()

# Secure session cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=3600,  # 1 hour admin session
)

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://127.0.0.1:5000",
        "http://localhost:5000",
    ],
)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return jsonify({"error": "Unauthorized"}), 401
        if not validate_csrf(session.get("csrf_token"), request.headers.get("X-CSRF-Token")):
            return jsonify({"error": "Invalid or missing security token"}), 403
        return f(*args, **kwargs)

    return decorated


def is_allowed_image_filename(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return bool(filename and suffix in ALLOWED_IMAGE_EXTENSIONS)


def is_allowed_video_filename(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return bool(filename and suffix in ALLOWED_VIDEO_EXTENSIONS)


def _save_uploaded_file(upload_file, allowed_suffixes: set[str], subfolder: str = "") -> str:
    suffix = Path(upload_file.filename).suffix.lower()
    if suffix not in allowed_suffixes:
        raise ValueError("Unsupported file type")
    safe_name = secure_filename(upload_file.filename)
    dest_dir = UPLOAD_DIR / subfolder if subfolder else UPLOAD_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dest_dir / safe_name
    count = 1
    while destination.exists():
        destination = dest_dir / f"{Path(safe_name).stem}-{count}{suffix}"
        count += 1
    upload_file.save(destination)
    rel = f"/assets/uploads/{subfolder + '/' if subfolder else ''}{destination.name}"
    return request.host_url.rstrip("/") + rel


@app.post("/api/admin/upload-image")
@admin_required
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file uploaded"}), 400

    image = request.files["image"]
    if image.filename == "":
        return jsonify({"error": "No image file selected"}), 400
    if not is_allowed_image_filename(image.filename):
        return jsonify({"error": "Unsupported image file type"}), 400
    if not image.mimetype.startswith("image/"):
        return jsonify({"error": "Uploaded file is not an image"}), 400

    image_url = _save_uploaded_file(image, ALLOWED_IMAGE_EXTENSIONS)
    return jsonify({"ok": True, "image_url": image_url, "url": image_url, "media_type": "image"})


@app.post("/api/admin/upload-media")
@admin_required
def upload_media():
    upload = request.files.get("file") or request.files.get("image") or request.files.get("video")
    if not upload or upload.filename == "":
        return jsonify({"error": "No file selected"}), 400

    suffix = Path(upload.filename).suffix.lower()
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        if not upload.mimetype.startswith("image/"):
            return jsonify({"error": "Uploaded file is not an image"}), 400
        url = _save_uploaded_file(upload, ALLOWED_IMAGE_EXTENSIONS)
        return jsonify({"ok": True, "url": url, "media_type": "image", "video_source": None})
    if suffix in ALLOWED_VIDEO_EXTENSIONS:
        url = _save_uploaded_file(upload, ALLOWED_VIDEO_EXTENSIONS, "videos")
        return jsonify({"ok": True, "url": url, "media_type": "video", "video_source": "upload"})
    return jsonify({"error": "Unsupported file type"}), 400


@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.get("/api/fabrics")
def list_fabrics():
    q = request.args.get("q", "").strip().lower()[:100]
    material = request.args.get("material", "").strip()[:40]
    color = request.args.get("color", "").strip()[:40]
    use_case = request.args.get("use", "").strip()[:40]

    conn = get_connection()
    cur = conn.cursor()
    execute(cur, "SELECT * FROM fabrics ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    fabrics = [fabric_to_api(r) for r in rows]

    if material:
        fabrics = [f for f in fabrics if f["material"].lower() == material.lower()]
    if color:
        fabrics = [f for f in fabrics if f["color"].lower() == color.lower()]
    if use_case:
        fabrics = [f for f in fabrics if f["use_case"].lower() == use_case.lower()]
    if q:
        fabrics = [
            f
            for f in fabrics
            if q in f["name"].lower()
            or q in f["material"].lower()
            or q in f["description"].lower()
        ]

    return jsonify(fabrics)


@app.get("/api/fabrics/<slug>")
def get_fabric(slug):
    try:
        safe_slug = validate_slug_param(slug)
    except ValueError:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_connection()
    cur = conn.cursor()
    execute(cur, "SELECT * FROM fabrics WHERE slug = %s", (safe_slug,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({"error": "Fabric not found"}), 404
    return jsonify(fabric_to_api(row))


@app.post("/api/admin/login")
def admin_login():
    ip = client_ip(request)
    allowed, wait_sec = check_login_rate_limit(ip)
    if not allowed:
        return jsonify({"error": f"Too many attempts. Try again in {wait_sec} seconds."}), 429

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()[:80]
    password = data.get("password") or ""

    if not username or not password or len(password) > 200:
        record_failed_login(ip)
        return jsonify({"error": "Invalid username or password"}), 401

    admin = get_admin_by_username(username)
    if not admin or not verify_password(password, admin["password_hash"]):
        record_failed_login(ip)
        return jsonify({"error": "Invalid username or password"}), 401

    clear_login_attempts(ip)
    session.clear()
    session.permanent = True
    session["admin"] = True
    session["username"] = username
    session["csrf_token"] = generate_csrf_token()

    return jsonify({"ok": True, "username": username, "csrf_token": session["csrf_token"]})


@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/admin/me")
def admin_me():
    if session.get("admin"):
        return jsonify({
            "authenticated": True,
            "username": session.get("username"),
            "csrf_token": session.get("csrf_token"),
        })
    return jsonify({"authenticated": False})


@app.post("/api/fabrics")
@admin_required
def create_fabric():
    data = request.get_json(silent=True) or {}
    try:
        payload = validate_fabric_payload_with_slug(data, slugify)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    conn = get_connection()
    cur = conn.cursor()
    payload["slug"] = ensure_unique_slug(cur, payload["slug"])
    insert_params = (
        payload["slug"],
        payload["name"],
        payload["material"],
        payload["color"],
        payload["use_case"],
        payload["price_inr"],
        payload["image_url"],
        payload["description"],
        payload["weight"],
        payload["sustainability"],
        payload["reviews_count"],
        payload["gsm"],
    )
    try:
        if uses_sqlite():
            execute(
                cur,
                """
                INSERT INTO fabrics (
                    slug, name, material, color, use_case, price_inr,
                    image_url, description, weight, sustainability, reviews_count, gsm
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                insert_params,
            )
            new_id = cur.lastrowid
        else:
            execute(
                cur,
                """
                INSERT INTO fabrics (
                    slug, name, material, color, use_case, price_inr,
                    image_url, description, weight, sustainability, reviews_count, gsm
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                insert_params,
            )
            new_id = cur.fetchone()["id"]
        media = payload["media"] or [
            {
                "media_type": "image",
                "url": payload["image_url"],
                "video_source": None,
                "sort_order": 0,
            }
        ]
        save_media_with_cursor(cur, new_id, media)
        conn.commit()
        execute(cur, "SELECT * FROM fabrics WHERE id = %s", (new_id,))
        row = cur.fetchone()
    except Exception as exc:
        conn.rollback()
        cur.close()
        conn.close()
        if os.environ.get("FLASK_DEBUG", "0") == "1":
            return jsonify({"error": f"Could not save fabric: {exc}"}), 400
        return jsonify({"error": "Could not save fabric. Please check all fields and try again."}), 400
    cur.close()
    conn.close()
    return jsonify(fabric_to_api(row)), 201


@app.put("/api/fabrics/<int:fabric_id>")
@admin_required
def update_fabric(fabric_id):
    if fabric_id < 1 or fabric_id > 2_147_483_647:
        return jsonify({"error": "Invalid request"}), 400

    data = request.get_json(silent=True) or {}
    conn = get_connection()
    cur = conn.cursor()
    execute(cur, "SELECT * FROM fabrics WHERE id = %s", (fabric_id,))
    existing = cur.fetchone()
    if not existing:
        cur.close()
        conn.close()
        return jsonify({"error": "Fabric not found"}), 404

    existing_keys = existing.keys() if hasattr(existing, "keys") else []
    existing_gsm = existing["gsm"] if "gsm" in existing_keys else None

    merged = {
        "name": data.get("name", existing["name"]),
        "slug": data.get("slug", existing["slug"]),
        "material": data.get("material", existing["material"]),
        "color": data.get("color", existing["color"]),
        "use_case": data.get("use_case", existing["use_case"]),
        "price_inr": data.get("price_inr", existing["price_inr"]),
        "image_url": data.get("image_url", existing["image_url"]),
        "description": data.get("description", existing["description"]),
        "weight": data.get("weight", existing["weight"]),
        "sustainability": data.get("sustainability", existing["sustainability"]),
        "reviews_count": data.get("reviews_count", existing["reviews_count"]),
        "gsm": data.get("gsm", existing_gsm),
        "media": data.get("media"),
    }
    if merged["media"] is None:
        merged["media"] = [
            {
                "media_type": m["media_type"],
                "url": m["url"],
                "video_source": m.get("video_source"),
                "sort_order": m["sort_order"],
            }
            for m in fabric_to_api(existing)["media"]
        ]

    try:
        payload = validate_fabric_payload_with_slug(merged, slugify)
    except ValueError as exc:
        cur.close()
        conn.close()
        return jsonify({"error": str(exc)}), 400

    try:
        payload["slug"] = ensure_unique_slug(cur, payload["slug"], exclude_id=fabric_id)
        execute(
            cur,
            """
            UPDATE fabrics SET
                slug = %s, name = %s, material = %s, color = %s, use_case = %s,
                price_inr = %s, image_url = %s, description = %s, weight = %s,
                sustainability = %s, reviews_count = %s, gsm = %s
            WHERE id = %s
            """,
            (
                payload["slug"],
                payload["name"],
                payload["material"],
                payload["color"],
                payload["use_case"],
                payload["price_inr"],
                payload["image_url"],
                payload["description"],
                payload["weight"],
                payload["sustainability"],
                payload["reviews_count"],
                payload["gsm"],
                fabric_id,
            ),
        )
        media = payload["media"] or [
            {
                "media_type": "image",
                "url": payload["image_url"],
                "video_source": None,
                "sort_order": 0,
            }
        ]
        save_media_with_cursor(cur, fabric_id, media)
        conn.commit()
        execute(cur, "SELECT * FROM fabrics WHERE id = %s", (fabric_id,))
        row = cur.fetchone()
    except Exception as exc:
        conn.rollback()
        cur.close()
        conn.close()
        if os.environ.get("FLASK_DEBUG", "0") == "1":
            return jsonify({"error": f"Could not update fabric: {exc}"}), 400
        return jsonify({"error": "Could not update fabric. Please check all fields and try again."}), 400
    cur.close()
    conn.close()
    return jsonify(fabric_to_api(row))


@app.delete("/api/fabrics/<int:fabric_id>")
@admin_required
def delete_fabric(fabric_id):
    if fabric_id < 1:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_connection()
    cur = conn.cursor()
    execute(cur, "SELECT id FROM fabrics WHERE id = %s", (fabric_id,))
    existing = cur.fetchone()
    if not existing:
        cur.close()
        conn.close()
        return jsonify({"error": "Fabric not found"}), 404
    execute(cur, "DELETE FROM fabrics WHERE id = %s", (fabric_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
