
# Architecture Decision Records (ADRs) - PortfolioX

## 1. Use of `Decimal` over `float` for Monetary Values
* **Context:** Financial applications require strict mathematical precision. Python's built-in `float` type uses base-2 floating-point arithmetic, which introduces compounding rounding errors (e.g., `0.1 + 0.2 = 0.30000000000000004`).
* **Decision:** We strictly use Python's `decimal.Decimal` for all currency amounts, prices, and balances across the application.
* **Consequence:** We avoid silent accounting errors and ensure perfectly accurate Profit & Loss (P&L) and order execution math. The slight performance cost of `Decimal` is negligible compared to the requirement for financial accuracy.

## 2. Removal of `current_price` from Core Asset Models
* **Context:** Initially, `Asset` models (Stock/Bond) stored a `current_price` attribute. However, prices are highly volatile and belong to the "Market", not the "Asset". 
* **Decision:** We removed `current_price` from the core `Asset` classes. Assets are now treated purely as descriptive metadata (symbol, name, type). Prices are now dynamically injected into the `Account` and `Portfolio` methods at runtime.
* **Consequence:** This enforces a **Single Source of Truth (SSOT)**. It completely eliminates the risk of "stale data" bugs where a user's portfolio value could be calculated using outdated prices from when the asset was originally instantiated.