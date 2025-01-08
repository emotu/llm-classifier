"""
main.py

@author: Emotu Balogun
@created: December 1, 2024


FastAPI Application Entry Point

This module serves as the main entry point for the FastAPI application,
handling route definitions and application configuration.
"""

from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.models import init_db
from app.routers.downloads import router as downloads_router
from app.routers.public import router as public_router

from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await init_db()
    yield
    # Shutdown code


app = FastAPI(lifespan=lifespan)


app.include_router(public_router)
app.include_router(downloads_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", status_code=HTTPStatus.OK)
async def root():
    app_specs = dict(
        api_name=settings.API_NAME,
        api_version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
    )
    return app_specs


@app.get("/health", status_code=HTTPStatus.OK)
async def health():
    return {"status": "ok"}
