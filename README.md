# 🚛 FastShip API

A production-style **shipment tracking & delivery management REST API** built with FastAPI — featuring JWT authentication, role-based users (sellers & delivery partners), automatic partner assignment, event-driven shipment timelines, transactional emails, and background task processing.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-blacklist%20%2B%20broker-DC382D?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-workers-37814A?logo=celery&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-migrations-6BA81E)

---

## ✨ Features

### 🔐 Authentication & Account Security
- **OAuth2 Password Flow + JWT** access tokens (PyJWT) with expiry & unique `jti`
- **Logout via Redis token blacklist** — revoked tokens are rejected instantly
- **Password hashing** with bcrypt (passlib)
- **Email verification** on signup — signed, URL-safe, salted tokens (itsdangerous)
- **Password reset flow** — email link → HTML form page → secure POST (form data), 24h token expiry
- Two independent user roles with separate token endpoints: **Seller** & **Delivery Partner**

### 📦 Shipment Management
- Submit, read, update, and **soft-cancel** shipments (full history preserved)
- **Automatic delivery partner assignment** by serviceable zip codes (PostgreSQL `ARRAY` + `any_()`) and real-time handling capacity
- **Event-driven timeline** — shipment status is derived from its latest event, never overwritten
- **Tag system** — many-to-many with composite-PK link table, seeded reference data (express, fragile, …)
- Client **review flow without an account** — signed review link delivered on `delivered` status

### 📬 Notifications & Pages
- Transactional emails on every important status (`placed`, `out_for_delivery`, `delivered`, `cancelled`) via **fastapi-mail** + SMTP
- **Jinja2 templates** shared between emails and server-rendered pages
- Public **tracking page**, **review form**, and **password reset pages** (TemplateResponse + HTML forms)
- Non-blocking delivery with **BackgroundTasks**; **Celery + Redis** worker setup for dedicated processing (with **Flower** monitoring)

### 🗄️ Data Layer
- **SQLModel** (SQLAlchemy + Pydantic) with fully **async** engine (asyncpg)
- UUID primary keys, relationships in all flavors: one-to-one, one-to-many, many-to-many
- **Alembic** migrations (async template) with autogenerate + data seeding

---

## 🏗️ Architecture

```
Client ──► Router (HTTP layer)          FastAPI + Pydantic schemas
              │   validation, auth via dependency chain
              ▼
           Service (business layer)     BaseService → UserService → Seller/PartnerService
              │   rules, orchestration              → Shipment/Event/NotificationService
              ▼
           Models (data layer)          SQLModel + PostgreSQL (asyncpg)
              │
              ├── Redis  ── token blacklist · Celery broker
              └── SMTP   ── transactional emails (background)
```

**Auth dependency chain** — protecting an endpoint takes one parameter:

```
oauth2_scheme → decode JWT → jti blacklist check → load user from DB → SellerDep
```

---

## 📁 Project Structure

```
app/
├── main.py                  # App entry: FastAPI instance, lifespan, Scalar docs
├── config.py                # Pydantic-settings: App / Database / Security / Notification
├── utils.py                 # JWT + itsdangerous token helpers, template paths
├── core/
│   └── security.py          # OAuth2 schemes (seller & partner)
├── database/
│   ├── models.py            # SQLModel models: User → Seller/DeliveryPartner,
│   │                        # Shipment, ShipmentEvent, Review, Tag (+ link table)
│   ├── session.py           # Async engine & session dependency
│   └── redis.py             # JWT blacklist (jti)
├── api/
│   ├── router.py            # Master router
│   ├── dependencies.py      # DI hub: SessionDep, SellerDep, service deps
│   ├── routers/             # /seller · /partner · /shipment endpoints
│   └── schemas/             # Request/response Pydantic schemas
├── services/                # Business logic (base, user, seller, partner,
│   │                        # shipment, shipment_event, notification)
├── templates/               # Jinja2: emails + tracking/review/reset pages
└── worker/
    └── tasks.py             # Celery app (Redis broker)

migrations/                  # Alembic (async) — versioned schema history
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.12+**
- **PostgreSQL** (running locally or remote)
- **Redis** (on Windows: via WSL)

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/fastship-api.git
cd fastship-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root (never commit this file):

```env
# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=fastship

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your_long_random_secret
JWT_ALGORITHM=HS256

# SMTP (Gmail: create an App Password — requires 2FA)
MAIL_USERNAME=you@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=you@gmail.com
MAIL_FROM_NAME=FastShip
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Start the services

```bash
# Redis (broker + blacklist)
redis-server

# API server → http://localhost:8000
fastapi dev app/main.py

# (Optional) Celery worker + Flower monitoring
celery -A app.worker.tasks worker --loglevel=info -E
celery -A app.worker.tasks flower --basic-auth=admin:pass   # → http://localhost:5555
```

### 5. Explore the API

| Docs | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| Scalar | `http://localhost:8000/scalar` |

---

## 📡 API Overview

### Seller — `/seller`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup` | Register (sends verification email) |
| POST | `/token` | Login — returns JWT (OAuth2 password flow) |
| GET | `/verify` | Verify email via signed token |
| GET | `/forgot_password` | Send password-reset email |
| GET | `/reset_password_form` | HTML form to enter a new password |
| POST | `/reset_password` | Apply new password (form data) |
| GET | `/logout` | Blacklist current token |

### Delivery Partner — `/partner`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup` | Register (zip codes + handling capacity) |
| POST | `/token` | Login |
| POST | `/` | Update serviceable zip codes / capacity |
| GET | `/verify` | Verify email |
| GET | `/logout` | Logout |

### Shipment — `/shipment`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/` | Submit shipment (🔒 seller) — auto-assigns partner, emails client |
| GET | `/` | Get shipment by id |
| GET | `/track` | Public tracking page (HTML) |
| PATCH | `/` | Update status/location (🔒 assigned partner) — appends timeline event |
| DELETE | `/cancel` | Soft-cancel (🔒 owning seller) |
| GET/POST | `/review` | Review form + submission (signed token from email) |
| GET/DELETE | `/tag` | Add / remove a tag |

**Shipment lifecycle:**

```
placed → in_transit → out_for_delivery → delivered → review ⭐
  ✉️                       ✉️               ✉️ + review link
                └────────── cancelled ✉️ (seller only, history preserved)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| ORM / Validation | SQLModel · Pydantic v2 · pydantic-settings |
| Database | PostgreSQL + asyncpg |
| Migrations | Alembic (async template) |
| Auth | PyJWT · passlib[bcrypt] · itsdangerous |
| Cache / Queue | Redis (token blacklist · Celery broker) |
| Background jobs | FastAPI BackgroundTasks · Celery · Flower |
| Email | fastapi-mail + Jinja2 templates |
| API docs | Swagger UI · Scalar |

---

## 🗺️ Roadmap

- [ ] Move all notification delivery to Celery tasks (worker scaffold in place)
- [ ] Centralized error handling with custom exception hierarchy + auto-registered handlers
- [ ] One-review-per-shipment constraint & review token expiry
- [ ] Test suite (pytest + httpx AsyncClient)
- [ ] Dockerfile & docker-compose (API + Postgres + Redis + worker)
- [ ] CI pipeline (lint, test, migrate check)

---

## 📄 License


---

