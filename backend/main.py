from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import analytics, auth, businesses, feedback, inventory, menu, orders, platform, qr, stock, tables
from backend.services.forecast_scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="SmartServe API", version="0.1.0")


@app.on_event("startup")
def start_background_forecast_scheduler():
    start_scheduler()


@app.on_event("shutdown")
def stop_background_forecast_scheduler():
    stop_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(businesses.router)
app.include_router(auth.router)
app.include_router(auth.login_router)
app.include_router(auth.platform_router)
app.include_router(platform.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(inventory.router)
app.include_router(qr.router)
app.include_router(tables.router)
app.include_router(stock.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "SmartServe"}
