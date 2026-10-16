from math import isfinite

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers import items, reservations

app = FastAPI(title="GearShare API", version="0.1.0")
app.include_router(items.router)
app.include_router(reservations.router)


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    # A JSON number such as 1e309 becomes inf when parsed. Keep error details
    # JSON-compatible too, so rejecting it returns 422 instead of causing 500.
    errors = jsonable_encoder(
        exc.errors(),
        custom_encoder={float: lambda value: value if isfinite(value) else str(value)},
    )
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/health", tags=["monitoring"])
def health() -> dict[str, str]:
    return {"status": "ok", "message": "Hello, World!!"}
