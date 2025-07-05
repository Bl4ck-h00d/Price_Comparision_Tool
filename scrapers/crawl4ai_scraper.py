import asyncio
import logging
import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from models import ScrapedProduct
from utils import parse_price, extract_currency, clean_product_name, is_valid_url

logger = logging.getLogger(__name__)


class Crawl4AIScraper:
    """
    Base class for Crawl4AI scrapers - handles web scraping, subclasses provide website-specific extraction
    """

    def __init__(self, website_name: str, base_url: str):
        self.website_name = website_name
        self.base_url = base_url
        self.crawler = None

    def validate_product(self, product: ScrapedProduct) -> bool:
        if not product.title or not product.price or not product.url:
            return False

        if not is_valid_url(product.url):
            return False

        parsed_price = parse_price(product.price)
        if parsed_price is None or parsed_price <= 0:
            return False

        return True

    def create_product(self, title: str, price: str, url: str, **kwargs) -> ScrapedProduct:
        title = clean_product_name(title)
        currency = extract_currency(price)

        if url.startswith('/'):
            url = self.base_url + url

        product = ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            url=url,
            website=self.website_name
        )

        return product

    async def search_products(self, query: str, limit: int = 10) -> List[ScrapedProduct]:

        try:
            search_url = self.get_search_url(query)
            logger.info(f"Scraping with Crawl4AI: {search_url}")

            async with AsyncWebCrawler(headless=True) as crawler:
                result = await crawler.arun(url=search_url)

                if not result.success:
                    logger.error(f"Crawl4AI failed: {result.error_message}")
                    return []

                products = await self._extract_products(result.html, query)

                if not products:
                    logger.warning("No products found")
                    return []

                return products[:limit]

        except Exception as e:
            logger.error(f"Crawl4AI scraping error: {e}")
            return []

    async def _extract_products(self, html_content: str, query: str) -> List[ScrapedProduct]:
        """
        Extract products from HTML content using BeautifulSoup
        """
        products = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.info(
                f"Parsing HTML content for {self.website_name}.")

            containers = self._find_product_containers(soup)

            for i, container in enumerate(containers):
                product = self._extract_product_info(container)
                if product and self.validate_product(product):
                    products.append(product)

            logger.info(
                f"Extracted {len(products)} valid products from {len(containers)} containers")

            if len(products) == 0 and len(containers) > 0:
                logger.warning(
                    f"{self.website_name}: Found {len(containers)} containers but extracted 0 products. This indicates extraction issues.")
              
                if containers:
                    sample_container = containers[0]
                    logger.debug(
                        f"Sample container HTML: {str(sample_container)}...")

        except Exception as e:
            logger.error(f"Product extraction error: {e}")

        return products

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """
        Find product containers - must be implemented by subclasses
        """
        raise NotImplementedError(
            "Subclasses must implement _find_product_containers")

    def _extract_product_info(self, container: BeautifulSoup) -> Optional[ScrapedProduct]:
        try:
            title = self._extract_title(container)
            if not title:
                return None

            price = self._extract_price(container)
            if not price:
                return None

            url = self._extract_url(container)
            if not url:
                return None

            return self.create_product(
                title=title,
                price=price,
                url=url
            )

        except Exception as e:
            logger.warning(f"Error extracting product info: {e}")
            return None

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement _extract_title")

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement _extract_price")

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement _extract_url")

    def get_search_url(self, query: str) -> str:
        raise NotImplementedError("Subclasses must implement get_search_url")
