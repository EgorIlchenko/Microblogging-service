import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import (
    Instrumentator,
    PrometheusFastApiInstrumentator,
)

from .api.tweet.routes import router as tweets_router
from .api.user.routes import router as users_router
from .config.config import logger
from .database.database import Base, engine

app = FastAPI()

instrumentator: PrometheusFastApiInstrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

app.include_router(tweets_router)
app.include_router(users_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/", StaticFiles(directory="app/api/static", html=True), name="static")
templates = Jinja2Templates(directory="app/api/static")


@app.on_event("startup")
async def startup():
    """
    Startup event handler for the FastAPI application.

    This function initializes the database schema by creating all tables
    defined in the ORM models. It is executed when the application starts.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def start_page(request: Request):
    """
    Render the start page of the application.

    This route serves the homepage using a Jinja2 template.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        TemplateResponse: The rendered "index.html" template with the request context.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for HTTPException.

    Logs the details of the HTTP exception and returns a standardized JSON response.

    Args:
        request (Request): The incoming HTTP request object.
        exc (HTTPException): The raised HTTP exception.

    Returns:
        JSONResponse: A JSON response containing the error details and HTTP status code.
    """
    logger.warning("HTTPException: %s}", exc.detail)
    return JSONResponse(
        content={
            "result": False,
            "error_type": exc.__class__.__name__,
            "error_message": exc.detail,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.

    Logs the details of any unhandled exception and returns a standardized JSON response.

    Args:
        request (Request): The incoming HTTP request object.
        exc (Exception): The raised exception.

    Returns:
        JSONResponse: A JSON response containing the error details.
    """
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        content={
            "result": False,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
