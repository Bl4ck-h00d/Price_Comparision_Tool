import asyncio
import logging
import openai
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from config import config
from models import ScrapedProduct, ProductResult, PriceComparisonRequest
from scrapers.web_scraper import AmazonScraper, BestBuyScraper, EbayScraper, WalmartScraper, FlipkartScraper, TataCliqScraper, MyntraScraper
from utils import parse_price, get_currency_for_country

logger = logging.getLogger(__name__)


class PriceComparisonService:

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.executor = ThreadPoolExecutor(
            max_workers=config.MAX_CONCURRENT_REQUESTS)

    async def compare_prices(self, request: PriceComparisonRequest) -> List[ProductResult]:
        logger.info(
            f"Starting price comparison for: {request.query} in {request.country}")

        scrapers = self._get_scrapers_for_country(request.country)

        if not scrapers:
            logger.warning(
                f"No scrapers available for country: {request.country}")
            return []

        # Search products across all scrapers concurrently
        all_products = await self._search_all_scrapers(scrapers, request.query)
        logger.info(f"Found {len(all_products)} total products")

        if not all_products:
            return []

        # use GPT to filter and rank products
        filtered_products = await self._filter_with_ai(request.query, all_products)
        logger.info(
            f"After AI filtering: {len(filtered_products)} products remain")

        # convert to results and sort by price
        results = self._convert_to_results(filtered_products, request.country)
        results.sort(key=lambda x: parse_price(x.price) or float('inf'))

        logger.info(
            f"Returning {len(results)} results for query: {request.query}")
        return results

    def _get_scrapers_for_country(self, country: str) -> List:

        scraper_mapping = {
            "US": [
                AmazonScraper("US"),
                EbayScraper("US"),
                WalmartScraper("US"),
                BestBuyScraper("US"),
            ],
            "IN": [
                AmazonScraper("IN"),
                EbayScraper("IN"),
                MyntraScraper("IN"),
                FlipkartScraper("IN"),
                TataCliqScraper("IN"),
            ]
        }

        return scraper_mapping.get(country, [])

    async def _search_all_scrapers(self, scrapers: List, query: str) -> List[ScrapedProduct]:
        """
        Search for products across all scrapers concurrently
        """
        tasks = []
        for scraper in scrapers:
            task = self._search_single_scraper(scraper, query)
            tasks.append(task)

        # execute all scraping tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # merge results
        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraper error: {result}")

        return all_products

    async def _search_single_scraper(self, scraper, query: str) -> List[ScrapedProduct]:
        """
        Search for products using a single scraper
        """
        try:
            products = await scraper.search_products(query, limit=10)
            logger.info(
                f"Found {len(products)} products from {scraper.website_name}")
            return products
        except Exception as e:
            logger.error(f"Error with {scraper.website_name}: {e}")
            return []

    async def _filter_with_ai(self, query: str, products: List[ScrapedProduct]) -> List[ScrapedProduct]:

        if not self.client:
            logger.error(
                "OpenAI client not available - cannot filter products")
            return []

        if not products:
            logger.warning("No products to filter")
            return []

        try:
            # Prepare product data for GPT
            product_data = []
            for i, product in enumerate(products):
                product_data.append(
                    f"{i}: {product.title} - {product.price} - {product.website}")

            logger.debug(f"Product data for AI:\n{chr(10).join(product_data)}")
            prompt = f"""
You are a product comparison expert. Given the search query "{query}", analyze the following products and select the MOST RELEVANT ones for price comparison.

Instructions:
- Select products that directly match the search query
- PRIORITIZE DIVERSITY: Include products from different websites when possible for better price comparison
- Exclude obvious accessories (cases, chargers, cables) unless specifically requested
- Exclude fake/knockoff products (marked as "fake", "replica", "clone")
- Have eBay products on low priority unless they are significantly cheaper and authentic
- Include authentic products with reasonable prices
- Select at max top 2 most relevant products total from each website 
- When multiple similar products exist, prefer variety across different websites

Products:
{chr(10).join(product_data)}

Return only the indices of relevant products as a comma-separated list (e.g., "0,2,5,7"):
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0
            )

            ai_response = response.choices[0].message.content.strip()
            selected_indices = []

            for idx in ai_response.split(','):
                try:
                    index = int(idx.strip())
                    if 0 <= index < len(products):
                        selected_indices.append(index)
                except:
                    continue

            filtered_products = [products[i] for i in selected_indices]
            logger.info(
                f"GPT selected {len(filtered_products)} relevant products")

            return filtered_products

        except Exception as e:
            logger.error(f"AI filtering error: {e}")
            return []

    def _convert_to_results(self, products: List[ScrapedProduct], country: str) -> List[ProductResult]:

        results = []
        default_currency = get_currency_for_country(country)

        for product in products:
            try:

                parsed_price = parse_price(product.price)
                if parsed_price is None or parsed_price <= 0:
                    continue

                result = ProductResult(
                    link=product.url,
                    price=str(int(parsed_price)),
                    currency=product.currency if product.currency else default_currency,
                    productName=product.title,
                    website=product.website,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error converting product: {e}")
                continue

        return results

    async def health_check(self) -> Dict[str, str]:

        return {
            "status": "healthy",
            "ai_enabled": "yes" if self.client else "no",
            "supported_countries": "US,IN",
            "scrapers": "amazon,ebay,walmart,bestbuy,myntra,flipkart,tatacliq"
        }
