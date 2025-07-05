import logging
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import config
from models import (
    PriceComparisonRequest,
    PriceComparisonResponse,
    ErrorResponse,
    ProductResult
)
from price_comparison_service import PriceComparisonService

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance
service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service

    logger.info("Starting Price Comparison Service...")
    service = PriceComparisonService()

    yield

    logger.info("Shutting down Price Comparison Service...")
    if service and hasattr(service, 'executor'):
        service.executor.shutdown(wait=True)

app = FastAPI(
    title="Price Comparison API",
    description="API for comparing product prices across multiple websites",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Price Comparison API",
        "version": "1.0.0",
        "endpoints": {
            "compare": "/compare",
            "health": "/health",
        }
    }


@app.get("/health")
async def health_check():
    try:
        health_status = await service.health_check()
        return JSONResponse(content=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.post("/compare", response_model=PriceComparisonResponse)
async def compare_prices(request: PriceComparisonRequest):
    """
    Compare prices for a product across multiple websites
    """
    try:
        logger.info(f"Received request: {request.query} in {request.country}")

        # Validate request
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )

        results = await service.compare_prices(request)

        response = PriceComparisonResponse(
            results=results,
            query=request.query,
            country=request.country,
            total_results=len(results)
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in price comparison: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )




@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
   
    logger.error(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=str(exc),
            code=500
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
