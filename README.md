# PortfolioX

PortfolioX is a backend financial portfolio management system built with a strict Layered Architecture. It cleanly separates pure domain logic from external concerns like database persistence, ensuring the system is highly testable, maintainable, and mathematically accurate.

## 🛠 Tech Stack
*   **Language:** Python 3.10+
*   **Database:** Neon Serverless PostgreSQL (Production) / SQLite (Testing)
*   **ORM:** SQLAlchemy 2.0 (Data Mapper Pattern)
*   **Migrations:** Alembic
*   **Testing:** Pytest

## 🏗 Architecture Highlights
*   **Domain-Driven:** Core business logic lives in pure Python classes (`Domain Models`).
*   **Data Mapper Pattern:** Database tables (`SQLAlchemy Models`) are completely decoupled from Domain Models.
*   **Repository Pattern:** Repositories handle the translation between Database Models and Domain Models.
*   **Financial Accuracy:** Strict usage of `decimal.Decimal` for all monetary values to prevent floating-point compounding errors.
*   **Dynamic Market Data:** Asset prices are strictly transient. `current_price` is never stored in the database to prevent stale data; it is injected dynamically at runtime.

---

## 🚀 Setup & Installation

### 1. Clone the repository and set up a Virtual Environment
```bash
git clone [https://github.com/atharva486/PortfolioX.git](https://github.com/atharva486/PortfolioX.git)
cd PortfolioX
python -m venv venv

# Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate