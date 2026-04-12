"""Billing Service - Manages subscription plans, subscriptions, and payments."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.database import Base, get_engine
from sqlalchemy import inspect, text
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
import services.billing_service.models  # noqa: F401
from services.billing_service.routes import router as billing_router

app = FastAPI(title="Alfit Billing Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("billing-service"))
app.include_router(billing_router, prefix="/api/v1", tags=["Billing"])


@app.on_event("startup")
def create_tables() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if not inspector.has_table("domain_orders"):
        return

    existing = {col["name"] for col in inspector.get_columns("domain_orders")}
    required_columns = {
        "callback_url": "ALTER TABLE domain_orders ADD COLUMN callback_url VARCHAR(1000) NULL",
        "address_in": "ALTER TABLE domain_orders ADD COLUMN address_in VARCHAR(255) NULL",
        "polygon_address_in": "ALTER TABLE domain_orders ADD COLUMN polygon_address_in VARCHAR(255) NULL",
        "ipn_token": "ALTER TABLE domain_orders ADD COLUMN ipn_token VARCHAR(1024) NULL",
        "paid_value_coin": "ALTER TABLE domain_orders ADD COLUMN paid_value_coin VARCHAR(100) NULL",
        "paid_coin": "ALTER TABLE domain_orders ADD COLUMN paid_coin VARCHAR(50) NULL",
        "txid_in": "ALTER TABLE domain_orders ADD COLUMN txid_in VARCHAR(255) NULL",
        "txid_out": "ALTER TABLE domain_orders ADD COLUMN txid_out VARCHAR(255) NULL",
        "value_forwarded_coin": "ALTER TABLE domain_orders ADD COLUMN value_forwarded_coin VARCHAR(100) NULL",
    }

    with engine.begin() as conn:
        for column_name, ddl in required_columns.items():
            if column_name not in existing:
                conn.execute(text(ddl))
