from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class SupportedCountry(str, Enum):
    US = "US"
    IN = "IN"


class PriceComparisonRequest(BaseModel):
    country: SupportedCountry = Field(...,
                                      description="Country code for price comparison")
    query: str = Field(..., min_length=1, max_length=500,
                       description="Product search query")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ProductResult(BaseModel):
    link: str = Field(..., description="Product URL")
    price: str = Field(..., description="Product price as string")
    currency: str = Field(..., description="Currency code (USD, INR)")
    productName: str = Field(..., description="Product name")
    website: str = Field(..., description="Website name")
   


class PriceComparisonResponse(BaseModel):
    results: List[ProductResult] = Field(...,
                                         description="List of products sorted by price")
    query: str = Field(..., description="Original search query")
    country: str = Field(..., description="Country searched")
    total_results: int = Field(...,
                               description="Total number of results found")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: int = Field(..., description="Error code")


class ScrapedProduct(BaseModel):
    """Internal model for scraped product data"""
    title: str
    price: str
    currency: str
    url: str
    website: str

