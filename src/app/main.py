from urllib.parse import urlencode
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routes import (
    auth_router, 
    account_router, 
    user_router, 
    brand_router, 
    product_router, 
    cosmetic_router, 
    apiclient_router,
    error_report_router,
    export_router,
    checking_router,
)
from app.log import get_logger

app = FastAPI(title="321Vegan API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost',
        'http://localhost:3000',
        'http://localhost:8080',
        "https://321vegan.fr",
        "https://www.321vegan.fr",
        "https://www.tool.321vegan.fr",
        "https://tool.321vegan.fr",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log = get_logger(__name__)

@app.middleware("http")
async def flatten_query_string_lists(request: Request, call_next):
    """
    Middleware to turn comma-delimited query parameter strings 
    into repeated query parameters
    """
    flattened = []
    for key, value in request.query_params.multi_items():
        flattened.extend((key, entry) for entry in value.split(','))
    request.scope["query_string"] = urlencode(flattened, doseq=True).encode("utf-8")
    return await call_next(request)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.error(f"Validation error: {exc.errors()}")
    log.error(f"Request body: {exc.body}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(account_router, prefix="/me", tags=["account"])
app.include_router(user_router, prefix="/users", tags=["user"])
app.include_router(brand_router, prefix="/brands", tags=["brand"])
app.include_router(product_router, prefix="/products", tags=["product"])
app.include_router(cosmetic_router, prefix="/cosmetics", tags=["cosmetic"])
app.include_router(apiclient_router, prefix="/apiclients", tags=["apiclient"])
app.include_router(error_report_router, prefix="/error-reports", tags=["error_report"])
app.include_router(export_router, prefix="/export", tags=["export"])
app.include_router(checking_router, prefix="/checkings", tags=["checking"])
