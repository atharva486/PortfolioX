# Architecture Decision Records (ADRs) - PortfolioX

## ADR-001: Strict Use of Decimal over Float
* **Context:** Financial applications require strict mathematical precision. Python's built-in `float` type uses base-2 floating-point arithmetic, which introduces compounding rounding errors.
* **Decision:** We strictly use Python's `decimal.Decimal` for all currency amounts, prices, and balances across the application.
* **Consequence:** We avoid silent accounting errors and ensure perfectly accurate Profit & Loss (P&L) and order execution math.

## ADR-002: Removal of current_price from Core Asset Models
* **Context:** Initially, `Asset` models (Stock/Bond) stored a `current_price` attribute. However, prices are highly volatile and belong to the "Market", not the "Asset". 
* **Decision:** We removed `current_price` from the core `Asset` classes. Prices are now dynamically injected into the `Account` and `Portfolio` methods at runtime.
* **Consequence:** This enforces a Single Source of Truth (SSOT). It completely eliminates the risk of "stale data" bugs where a user's portfolio value could be calculated using outdated prices.

## ADR-003: Domain Mapper Placeholders for Dynamic Data
* **Context:** The `Stock` and `Bond` domain objects require fields like `current_price` to be instantiated. However, our database (`AssetModel`) only stores static facts like `symbol`.
* **Decision:** When mapping from the database to the domain in the Repository layer, we inject placeholder values (e.g., `Decimal("0.0")` for price). 
* **Consequence:** The Repository's job is just to reconstruct the object. It is the responsibility of the Service Layer to fetch live market data from an external API and update the Domain object *before* running business logic.

## ADR-004: SQLAlchemy as the Application ORM
* **Context:** We need a reliable way to interact with the database without writing raw, vulnerable SQL strings for every operation.
* **Decision:** We are using SQLAlchemy as our ORM instead of raw SQL.
* **Consequence:** SQLAlchemy uses the "Data Mapper" pattern, perfectly supporting our Layered Architecture by separating database tables from business logic. It automatically prevents SQL injection attacks and handles complex joins securely.

## ADR-005: Alembic for Database Version Control
* **Context:** Database schemas evolve over time, and manually running `ALTER TABLE` scripts across different environments is error-prone.
* **Decision:** We use Alembic to manage our database schema history.
* **Consequence:** Alembic acts like "Git for our database," generating versioned migration files. This ensures all developers and production servers run the exact same schema.

## ADR-006: SQLite for Development and Testing
* **Context:** Developers need a frictionless environment to run tests rapidly without managing external database infrastructure.
* **Decision:** We use in-memory SQLite (`sqlite:///:memory:`) for local testing.
* **Consequence:** Using an in-memory database for Pytest allows us to spin up a fresh, isolated database in milliseconds for every single test, ensuring tests never corrupt each other's data and run at maximum speed.

## ADR-007: Integration Test Database Strategy
* **Context:** Production runs on Postgres, raising the question of whether tests should run on Postgres to guarantee 1:1 parity.
* **Decision:** We are keeping our integration/repository tests running on in-memory SQLite.
* **Consequence:** While true Postgres-specific testing is more accurate, in-memory SQLite keeps our test suite running in milliseconds. We prioritize lightning-fast test feedback for developer velocity.

## ADR-008: Neon Connection Pooling & Alembic Configuration
* **Context:** Neon offers a connection pooler. Application traffic needs concurrency, but migrations need stateful isolation.
* **Decision:** 
  1. **App Traffic:** Use Neon Pooler (ON) to handle rapid user requests without exhausting connections.
  2. **Migrations:** Use Neon Direct URL (Pool OFF) with SQLAlchemy `NullPool`.
* **Consequence:** Alembic opens exactly one private, uninterrupted TCP connection to execute DDL safely, preventing dangling connections and resource leaks, while the main app remains highly scalable.

## ADR-009: Preventing Concurrent Order Race Conditions (PORTX-14)
* **The Problem (Double-Spend):** When firing concurrent orders via `asyncio.gather`, both requests read the account balance before either transaction commits. This allowed a user to buy $1,800 of stock with only a $1,000 balance (both requests succeeded, overwriting each other to result in a $100 final balance).
* **The Solution:** Added `.with_for_update()` to the SQLAlchemy query when fetching the account prior to placing an order.
* **Consequence:** This acquires a pessimistic row-level lock (`SELECT ... FOR UPDATE`) in PostgreSQL. Concurrent requests are forced to wait their turn, read the newly updated balance, and correctly fail with `InsufficientFundsError`.

## ADR-010: Database Concurrency & Deadlock Prevention (PORTX-14 & PORTX-15)

* **The Problem (Race Conditions & Deadlocks):** 
  High-frequency concurrent trading can cause two critical database failures:
  1. **Double-Spends:** Concurrent requests reading the same starting balance before either commits.
  2. **Deadlocks:** Concurrent transactions locking tables in different sequences, causing an infinite circular wait that crashes the database.

* **The Decision (Consistent Pessimistic Locking & Gateway Locks):** 
  We rely on PostgreSQL row-level pessimistic locking via SQLAlchemy's `.with_for_update()`. 
  To prevent deadlocks, we enforce a **Strict Lock Ordering Rule**:
  
  **Rule:** *Any transaction touching both the `accounts` table and the `holdings` table MUST acquire the lock on the `accounts` row first (The Gateway Lock).* 

* **Consequence:** 
  1. `.with_for_update()` forces concurrent requests to wait in line, preventing Double-Spends.
  2. Enforcing the Gateway Lock (Account first) serializes all operations for a specific user. Because no two transactions can access a user's holdings without holding the Account lock first, circular waits between holdings are mathematically impossible.


## ADR-011: Live Market Data & Async Concurrency (PORTX-16)

* **The Problem:** The app relied on hardcoded prices passed by the client. Real-time portfolio valuation requires fetching live market data for multiple holdings simultaneously. Fetching 10 assets sequentially took ~11 seconds, causing unacceptable UI latency.
* **The Decision:** We implemented a dedicated `MarketDataService` using `httpx` to fetch live prices from the Finnhub API. For portfolio valuations, we utilize `asyncio.gather()` to fetch all holding prices concurrently. 
* **Error Handling:** The service degrades gracefully. If one ticker fails, it logs the error and returns the successful prices rather than crashing the batch request. We also implemented Just-In-Time (JIT) asset creation in the database if an asset doesn't exist locally.
* **Proof of Concept (Benchmark):** 
  * Sequential Fetch (10 symbols): 10.89 seconds
  * Concurrent Fetch (10 symbols): 1.37 seconds
  * Result: **8.0x faster** using `asyncio.gather()`.