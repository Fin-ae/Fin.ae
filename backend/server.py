from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.db import close_db, init_db
from core.seed import seed_data
from routers import (
    applications,
    auth,
    chat,
    health,
    news,
    policies,
    recommendations,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_data()
    yield
    close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(policies.router)
app.include_router(recommendations.router)
app.include_router(news.router)
app.include_router(applications.router)
