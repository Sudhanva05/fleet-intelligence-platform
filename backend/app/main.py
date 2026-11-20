
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import vehicles
from backend.app.routers import analytics
from backend.app.routers import alerts


app = FastAPI(
    title="Fleet Intelligence API",
    description="Real-time fleet monitoring and analytics platform",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(vehicles.router)
app.include_router(analytics.router)
app.include_router(alerts.router)


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Fleet Intelligence API is running"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }
