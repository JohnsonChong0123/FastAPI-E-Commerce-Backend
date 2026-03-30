# 🛒 FastAPI E-Commerce Backend

> ⚠️ **Work in Progress** — Actively under development.

A **production-style e-commerce backend** built with **FastAPI**, following **RESTful API design** and **Clean Architecture** principles.

This project serves as the backend counterpart to my mobile client:

👉 **Flutter App:** https://github.com/JohnsonChong0123/Flutter-E-Commerce-App

---

## 🎯 Project Purpose

This project demonstrates **modern backend engineering practices** used in real-world applications:

* ⚡ **FastAPI** — high-performance async web framework with automatic OpenAPI documentation
* 🧠 **Clean Architecture** — separation of concerns between routes, services, models, and schemas
* 🔐 **JWT Authentication** — secure access token & refresh token flow
* 🗄 **Database Migrations** — Alembic for version-controlled schema updates
* 🧪 **Testing** — pytest with coverage for core business logic
* 🔗 **External API Integration** — eBay product search via HTTP client

---

## ✨ Features

| Feature                   | Status      |
| ------------------------- | ----------- |
| User Registration & Login | ✅ Completed |
| JWT Access Token          | ✅ Completed |
| JWT Refresh Token         | ✅ Completed |
| Product Listing API       | ✅ Completed |
| Product Detail API        | ✅ Completed |
| eBay Product Integration  | ✅ Completed |
| Wishlist Management       | ✅ Completed |
| Shopping Cart             | ✅ Completed |
| Order Management          | 📋 Planned  |

---

## 🧱 Architecture

The project follows **Clean Architecture** principles:

```
Client → Routes → Services → Models → Database
```

### Layers

| Layer    | Responsibility                  |
| -------- | ------------------------------- |
| routes   | API endpoints (FastAPI routers) |
| services | business logic                  |
| schemas  | request / response validation   |
| models   | SQLAlchemy ORM entities         |
| core     | security, config, dependencies  |
| tests    | unit & integration tests        |

Benefits:

* scalable structure 📈
* testable business logic 🧪
* easy to maintain 🔧
* framework-independent domain logic 🧠

---

## 🔧 Tech Stack

| Category          | Package                             |
| ----------------- | ----------------------------------- |
| Web Framework     | fastapi                             |
| ORM               | sqlalchemy                          |
| Database          | postgresql                          |
| Migration Tool    | alembic                             |
| Authentication    | python-jose (JWT), passlib (bcrypt) |
| Validation        | pydantic                            |
| HTTP Client       | httpx                               |
| Testing           | pytest                              |
| Config Management | pydantic-settings                   |

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10+
* PostgreSQL (recommended)
* pip or uv

Install uv (optional but fast):

```
pip install uv
```

---

### 2. Clone Repository

```
git clone https://github.com/JohnsonChong0123/FastAPI-E-Commerce-Backend.git

cd FastAPI-E-Commerce-Backend
```

---

### 3. Create Virtual Environment

Mac / Linux:

```
python -m venv venv
source venv/bin/activate
```

Windows:

```
python -m venv venv
venv\Scripts\activate
```

---

### 4. Install Dependencies

pip:

```
pip install -r requirements.txt
```

or uv:

```
uv sync
```

---

### 5. Setup Environment Variables

Copy example env file:

```
cp .env.example .env
```

---

### 6. Run Database Migration

```
alembic upgrade head
```

---

### 7. Start Development Server

```
uvicorn main:app --reload --port 8000
```

API will be available at:

```
http://localhost:8000
```

Interactive API docs:

```
http://localhost:8000/docs
```

---

## 🔑 Environment Variables

```env
DATABASE_URL=your_database_url
TEST_DATABASE_URL=your_test_database_url
TOKEN_SECRET_KEY=your_token_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
```
---

## 🧪 Testing

Run all tests:

```
pytest
```

Run with coverage:

```
pytest --cov=. --cov-report=html
```

Open coverage report:

```
htmlcov/index.html
```

---

## 📁 Project Structure

```
.
├── alembic/              # database migrations
├── core/                 # config, security, dependencies
├── exceptions/           # custom exception handlers
├── models/               # SQLAlchemy ORM models
├── routes/               # FastAPI routers
├── schemas/              # Pydantic schemas
├── services/             # business logic layer
├── tests/                # unit & integration tests
├── main.py               # app entry point
└── database.py           # database session
```

---

## 📝 Note

This project is part of my portfolio to practice **real-world backend engineering skills** and demonstrate understanding of:

* API design
* authentication flows
* database modeling
* testing strategy
* scalable architecture

Feel free to explore the code and provide feedback 🙌
