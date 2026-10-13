from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import db_healthcheck, init_db
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.budgets import router as budgets_router
from app.routers.submissions import router as submissions_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="NYC Council Reporting API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(budgets_router)
app.include_router(submissions_router)
app.include_router(users_router)
app.include_router(admin_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/db/health")
def database_health() -> dict[str, str]:
    return {"status": "ok" if db_healthcheck() else "unavailable"}
