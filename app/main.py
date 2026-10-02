from fastapi import FastAPI

from app.api.routes.accounts import router as account_router
from app.api.routes.ai import router as ai_router
from app.api.routes.health import router as health_router
from app.api.routes.market import router as market_router
from app.api.routes.orders import router as order_router
from app.api.routes.portfolio import router as portfolio_router

app = FastAPI(
    title="PortfolioX",
    description="Layered portfolio-trading backend with a framework-free domain core.",
    version="0.1.0",
)

# Operational endpoints first so /health never conflicts with a domain route.
app.include_router(health_router)
app.include_router(account_router)
app.include_router(order_router)
app.include_router(market_router)
app.include_router(portfolio_router)
app.include_router(ai_router)

# if __name__ == "__main__":
#     backend()
