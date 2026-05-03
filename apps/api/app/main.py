from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routes.assets import router as assets_router
from app.routes.convert import router as convert_router
from app.routes.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    for d in (
        settings.uploads_dir,
        settings.outputs_dir,
        settings.jobs_dir,
        settings.hf_home,
        settings.xdg_cache_home,
    ):
        d.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="MinerU Local API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
    )


app.include_router(convert_router)
app.include_router(jobs_router)
app.include_router(assets_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
