"""FastAPI app — LICTER Dashboard API."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .loaders import latest_run_dir
from .routers import benchmark, cx, recommendations, reputation, summary

app = FastAPI(title="LICTER Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(reputation.router, prefix="/api")
app.include_router(benchmark.router, prefix="/api")
app.include_router(cx.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(summary.router, prefix="/api")


@app.get("/api/health")
def health():
    run_dir = latest_run_dir("ai")
    run_name = run_dir.name if run_dir else None
    # run_name format: 20260314T153443594082Z_bd1c44
    # Parse: YYYYMMDDTHHMMSS
    label = None
    if run_name and len(run_name) >= 15:
        ts = run_name[:15]  # 20260314T153443
        try:
            label = f"{ts[6:8]}/{ts[4:6]}/{ts[:4]} {ts[9:11]}:{ts[11:13]}"
        except Exception:
            label = run_name
    return {"status": "ok", "last_run": run_name, "label": label}
