# Architecture Decision Records (ADRs) - PortfolioX

## 1. Use of `Decimal` over `float` for Monetary Values
* **Context:** Financial applications require strict mathematical precision. Python's built-in `float` type uses base-2 floating-point arithmetic, which introduces compounding rounding errors (e.g., `0.1 + 0.2 = 0.30000000000000004`).
* **Decision:** We strictly use Python's `decimal.Decimal` for all currency amounts, prices, and balances across the application.
* **Consequence:** We avoid silent accounting errors and ensure perfectly accurate Profit & Loss (P&L) and order execution math. The slight performance cost of `Decimal` is negligible compared to the requirement for financial accuracy.

## 2. Removal of `current_price` from Core Asset Models
* **Context:** Initially, `Asset` models (Stock/Bond) stored a `current_price` attribute. However, prices are highly volatile and belong to the "Market", not the "Asset". 
* **Decision:** We removed `current_price` from the core `Asset` classes. Assets are now treated purely as descriptive metadata (symbol, name, type). Prices are now dynamically injected into the `Account` and `Portfolio` methods at runtime.
* **Consequence:** This enforces a **Single Source of Truth (SSOT)**. It completely eliminates the risk of "stale data" bugs where a user's portfolio value could be calculated using outdated prices from when the asset was originally instantiated.

### 3. Domain Mapper Placeholders for Dynamic Data (PORTX-9b)
* **The Problem:** The `Stock` and `Bond` domain objects require fields like `current_price`, `sector`, and `coupon_rate` to be instantiated. However, our database (`AssetModel`) only stores static facts like `symbol` and `company_name`.
* **The Decision:** When mapping from the database to the domain in `AccountRepository._to_domain()`, we inject placeholder values (e.g., `Decimal("0.0")` for price, `"Unknown"` for sector). 
* **The Reasoning:** A database should never store highly volatile data like live stock prices; if we save Apple's price as $150, it is wrong 3 seconds later. The Repository's job is just to reconstruct the object. It is the responsibility of the Service Layer to fetch live market data from an external API and update the Domain object *before* running business logic like `place_order()`.

### 4. Why we chose SQLAlchemy as the ORM
* **The Decision:** We are using SQLAlchemy instead of writing raw SQL queries.
* **The Reasoning:** SQLAlchemy uses the "Data Mapper" pattern, which perfectly supports our Layered Architecture. It allows us to keep our database tables (`Models`) completely separate from our business logic (`Domain`). Furthermore, it automatically prevents SQL injection attacks, handles complex table joins securely, and allows us to swap database engines (e.g., moving from SQLite to PostgreSQL) without rewriting our queries.

### 5. Why we chose Alembic for Database Version Control
* **The Decision:** We use Alembic to manage our database schema history.
* **The Reasoning:** Alembic acts like "Git for our database." Instead of manually running `CREATE TABLE` or `ALTER TABLE` scripts, Alembic generates versioned migration files. This ensures that every developer on the team, and eventually the production server, is running the exact same database schema. If a deployment breaks, we can easily run an Alembic downgrade to safely roll back the database without losing user data.

### 6. Why we use SQLite for Development and Testing
* **The Decision:** We are using SQLite (specifically `sqlite:///:memory:` for tests) during the development stage.
* **The Reasoning:** SQLite requires zero configuration—no Docker containers, no dedicated database servers, and no complex credentials. This removes friction during early development. More importantly, using an in-memory SQLite database for Pytest allows us to spin up a fresh, isolated database in milliseconds for every single test, ensuring tests never corrupt each other's data and run incredibly fast.
