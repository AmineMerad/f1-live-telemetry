"""Live dashboard API: predictions with evidence, uncertainty, freshness."""

from fastapi import FastAPI
from fastapi.responses import Response

from f1_api.data import router as data_router
from f1_api.ui import router as ui_router
from f1_api.workflows import router as workflows_router

app = FastAPI(title="F1 Live Intelligence (scaffold)")
app.include_router(data_router)
app.include_router(workflows_router)
app.include_router(ui_router)


@app.get("/")
def index() -> dict:
    return {
        "service": "f1-live-intelligence",
        "scaffold": True,
        "routes": ["/health", "/ui", "/predictions/{driver_pair}", "/freshness"],
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "scaffold": True}


@app.get("/predictions/{driver_pair}")
def get_prediction(driver_pair: str) -> dict:
    return {
        "driver_pair": driver_pair,
        "probability_a_ahead": None,
        "detail": "unimplemented — week 5/6",
    }


@app.get("/freshness")
def freshness() -> dict:
    return {"freshness": "unknown", "detail": "unimplemented — week 3"}
