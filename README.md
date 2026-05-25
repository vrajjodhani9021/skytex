# Sky Tex — Fabric Website

A fabric shop inspired by [Ivory Weave Emporium](https://ivory-weave-emporium.lovable.app/), built with **HTML/CSS** frontend and a **Python Flask** API backend. All prices are in **Indian Rupees (₹)**.

## Quick start

1. **Environment**

```bash
cd backend
copy .env.example .env
```

   By default `.env` uses **SQLite** (`sqlite:///fabrics.db`) so you can run locally without PostgreSQL. For production, set `DATABASE_URL` to your PostgreSQL URL instead.

2. **Install Python dependencies**

```bash
cd backend
pip install -r requirements.txt
```

3. **Run the server** (creates tables and seeds 12 sample fabrics on first run)

```bash
python app.py
```

4. **Open in browser**

- Home: http://127.0.0.1:5000/
- Shop: http://127.0.0.1:5000/shop.html
- Admin: http://127.0.0.1:5000/admin.html

## Admin panel

| Field    | Value        |
|----------|--------------|
| Username | `Pratham`    |
| Password | `Lollipop069` |

From the admin page you can:

- Add new fabrics (name, material, color, price in ₹, image URL, etc.)
- Edit existing fabrics
- Delete fabrics

Changes appear immediately on the shop and product pages.

## Project structure

```
Fabric_webite/
├── backend/
│   ├── app.py           # Flask API + static file server
│   ├── database.py      # SQLite + seed data
│   └── requirements.txt
└── frontend/
    ├── css/styles.css
    ├── js/              # API calls (shop, product, admin)
    ├── index.html
    ├── shop.html
    ├── product.html
    ├── collections.html
    ├── swatches.html
    ├── about.html
    ├── contact.html
    └── admin.html
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/fabrics` | List fabrics (`?material=Linen&color=&use=`) |
| GET | `/api/fabrics/<slug>` | Single fabric |
| POST | `/api/admin/login` | Admin login |
| POST | `/api/fabrics` | Create fabric (admin) |
| PUT | `/api/fabrics/<id>` | Update fabric (admin) |
| DELETE | `/api/fabrics/<id>` | Delete fabric (admin) |

Database: **PostgreSQL** via `DATABASE_URL` in `backend/.env` (tables and seed data created on first run).

## Security

This project includes protections against common attacks:

| Protection | What it does |
|------------|----------------|
| **Parameterized SQL** | All queries use bound parameters — SQL injection cannot run |
| **Password hashing** | Admin password stored as PBKDF2 hash, not plain text |
| **Login rate limit** | 5 failed attempts per IP, then 15-minute lockout |
| **CSRF tokens** | Add/edit/delete require a token from login |
| **Input validation** | Whitelist materials/uses, length limits, safe URLs & slugs |
| **Secure sessions** | HttpOnly cookies, 1-hour timeout |
| **No error leaks** | Database errors are not exposed to attackers |

### Before going live

1. Copy `backend/.env.example` to `backend/.env`
2. Set `DATABASE_URL`, a strong `SECRET_KEY`, and new `ADMIN_PASSWORD`
3. Set `FLASK_DEBUG=0`
4. Run `python migrate_admin.py` to ensure tables exist

**Note:** The admin *page* URL is still visible (`/admin.html`), but nobody can add or delete fabrics without logging in. Only the API enforces this — the HTML form alone cannot bypass the server.
