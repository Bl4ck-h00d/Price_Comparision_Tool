import asyncio
import logging
import re
from typing import List, Optional
from bs4 import BeautifulSoup
import urllib.parse

from scrapers.crawl4ai_scraper import Crawl4AIScraper
from models import ScrapedProduct

logger = logging.getLogger(__name__)


class GenericWebScraper(Crawl4AIScraper):
    """
    Generic web scraper that can search multiple e-commerce sites
    """

    def __init__(self, website_name: str, base_url: str, search_pattern: str):
        super().__init__(website_name, base_url)
        self.search_pattern = search_pattern

    def get_search_url(self, query: str) -> str:
        encoded_query = urllib.parse.quote_plus(query)
        return self.search_pattern.format(query=encoded_query, base_url=self.base_url)


class EbayScraper(GenericWebScraper):

    def __init__(self, country: str = "US"):
        domains = {
            "US": "ebay.com",
            "IN": "ebay.in"
        }

        domain = domains.get(country, "ebay.com")
        base_url = f"https://www.{domain}"
        search_pattern = f"{base_url}/sch/i.html?_nkw={{query}}&_sacat=0"

        super().__init__(f"eBay {country}", base_url, search_pattern)

        self.country = country
        self.domain = domain

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:

        selectors = [
            '.s-item',
            '[data-view="mi:1686|iid:1"]',
            '.srp-results .s-item'
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} eBay containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'h3.s-item__title',
            '.s-item__title',
            'a.s-item__link h3'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            '.s-item__price',
            '.notranslate',
            '[data-testid="item-price"]'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and re.search(r'[\d\$₹]', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:
        """Extract eBay product URL and ensure it uses the correct country domain"""
        link = container.select_one('a.s-item__link, .s-item__link')
        if link and link.get('href'):
            href = link.get('href')
            if href.startswith('http'):
                if 'ebay.com' in href and self.domain != 'ebay.com':
                    href = href.replace('ebay.com', self.domain)
                elif 'ebay.in' in href and self.domain != 'ebay.in':
                    href = href.replace('ebay.in', self.domain)
                return href
            elif href.startswith('/'):
                return self.base_url + href

        return None


class WalmartScraper(GenericWebScraper):
    def __init__(self, country: str = "US"):
        base_url = "https://www.walmart.com"
        search_pattern = f"{base_url}/search?q={{query}}"

        super().__init__(f"Walmart {country}", base_url, search_pattern)

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        selectors = [
            '[data-item-id]',
            '[data-automation-id="product-tile"]',
            '.search-result-gridview-item'
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} Walmart containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            '[data-automation-id="product-title"]',
            'span.w_iUH7',
            '.product-title-link',
            '.normal.dark-gray'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            '[data-automation-id="product-price"] span.w_iUH7',
            'span.w_iUH7',
            '[data-automation-id="product-price"]',
            '.price-current',
            '.price-group'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # price patterns
                if text and re.search(r'(current price|\$[\d,]+\.?\d*)', text):
                    # extract price from text, e.g "current price $12.98"
                    price_match = re.search(r'\$[\d,]+\.?\d*', text)
                    if price_match:
                        return price_match.group()
                elif text and re.search(r'[\d\$]', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'a.w-100.h-100',
            'a[link-identifier]',
            'a[href*="walmart.com"]',
            'a'
        ]

        for selector in selectors:
            link = container.select_one(selector)
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return self.base_url + href

        return None


class FlipkartScraper(GenericWebScraper):

    def __init__(self, country: str = "IN"):
        base_url = "https://www.flipkart.com"
        search_pattern = f"{base_url}/search?q={{query}}"

        super().__init__(f"Flipkart {country}", base_url, search_pattern)

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """
        Find Flipkart product containers
        """
        selectors = [
            'div._75nlfW',  # Based on actual HTML structure
            'div.tUxRFH',   # Alternative container class
            '._1AtVbE',     # Legacy selector
            '._13oc-S',     # Legacy selector
            '._2kHMtA',     # Legacy selector
            '.s1Q9rs',      # Legacy selector
            '.gqcAol',      # Legacy selector
            '.DOjaWF'       # Legacy selector
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} Flipkart containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_brand(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            '.syl9yP',
            '._2WkVRV',
            '._16Jk6d'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 1:
                    return text

        return None

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            '.KzDlHZ',
            '.WKTcLC',
            '._4rR01T',
            '.s1Q9rs',
            '.IRpwTa',
            '._2WkVRV'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            '.Nx9bqj',
            '._30jeq3',
            '._1_WHN1',
            '._25b18c',
            '._3I9_wc'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and re.search(r'[₹\d]', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'a.CGtC98',
            'a.rPDeLR',
            'a'
        ]

        for selector in selectors:
            link = container.select_one(selector)
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return self.base_url + href

        return None


class TataCliqScraper(GenericWebScraper):

    def __init__(self, country: str = "IN"):
        base_url = "https://www.tatacliq.com"
        search_pattern = f"{base_url}/search/?text={{query}}"

        super().__init__(f"Tata CLiQ {country}", base_url, search_pattern)

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:

        selectors = [
            'div.Grid__element',
            '[data-testid="product-tile"]',
            '.ProductTileWrapper',
            '.product-tile'
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} Tata CLiQ containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_brand(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'h3.ProductDescription__boldText',
            '.ProductDescription__brand',
            '.brand'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 1 and not re.search(r'^[₹\d\s,.-]+$', text):
                    return text

        return None

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'h2.ProductDescription__description',
            '.ProductName',
            '.product-title',
            '[data-testid="product-name"]'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Lowered threshold
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'div.ProductDescription__discount h3.ProductDescription__boldText',
            '.PriceHolder',
            '.product-price',
            '[data-testid="price"]'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and re.search(r'[₹\d]', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:
        selectors = [
            'a.ProductModule__base',
            'a'
        ]

        for selector in selectors:
            link = container.select_one(selector)
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return self.base_url + href

        return None


class MyntraScraper(GenericWebScraper):

    def __init__(self, country: str = "IN"):
        base_url = "https://www.myntra.com"
        search_pattern = f"{base_url}/{{query}}"

        super().__init__(f"Myntra {country}", base_url, search_pattern)

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        selectors = [
            'li.product-base',
            '.product-base',
            'li[id]'
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} Myntra containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        brand_elem = container.select_one('.product-brand')
        product_elem = container.select_one('.product-product')

        brand = brand_elem.get_text(strip=True) if brand_elem else ""
        product = product_elem.get_text(strip=True) if product_elem else ""

        if brand and product:
            return f"{brand} {product}"
        elif product:
            return product
        elif brand:
            return brand

        fallback_selectors = [
            '.product-productName',
            'h3',
            'h4'
        ]

        for selector in fallback_selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            '.product-discountedPrice',
            '.product-price span',
            '.product-strike',
            '[class*="price"]'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Look for Rs. or ₹ followed by numbers
                if text and re.search(r'(Rs\.\s*\d+|₹\s*\d+|\d+)', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:

        link = container.select_one('a[href]')
        if link and link.get('href'):
            href = link.get('href')
            if href.startswith('http'):
                return href
            elif href.startswith('/'):
                return self.base_url + href
            else:
                # Myntra uses relative URLs
                return f"{self.base_url}/{href}"

        return None


class AmazonScraper(GenericWebScraper):

    def __init__(self, country: str = "US"):
        self.country = country

        domains = {
            "US": "amazon.com",
            "IN": "amazon.in"
        }

        domain = domains.get(country, "amazon.com")
        base_url = f"https://www.{domain}"
        search_pattern = f"{base_url}/s?k={{query}}"

        super().__init__(f"Amazon {country}", base_url, search_pattern)

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:

        selectors = [
            '[data-component-type="s-search-result"]',
            '.s-result-item',
            '[data-asin]'
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} Amazon containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            'h2.s-size-mini span',
            '.s-product-title',
            'h2 a span',
            '.a-text-normal'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '.a-price-range',
            '.s-price'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and re.search(r'[\d\$₹]', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:

        link = container.select_one('h2 a, .s-link-style a, [data-asin] a')
        if link and link.get('href'):
            href = link.get('href')
            if href.startswith('/'):
                return self.base_url + href
            elif href.startswith('http'):
                return href

        return None


class BestBuyScraper(GenericWebScraper):

    def __init__(self, country: str = "US"):
        base_url = "https://www.bestbuy.com"
        search_pattern = f"{base_url}/site/searchpage.jsp?st={{query}}"

        super().__init__(f"Best Buy {country}", base_url, search_pattern)

    def _find_product_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:

        selectors = [
            'li.product-list-item',
            '[data-testid]',
            '.sku-item',
            '.sr-item'
        ]

        containers = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers.extend(found)
                logger.info(
                    f"Found {len(found)} Best Buy containers with selector: {selector}")
                break

        return containers[:50]

    def _extract_brand(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            'span.first-title',
            '.brand-name',
            '.product-brand'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 1:
                    return text

        return None

    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            'h2.product-title',
            'h4.sr-title',
            'h3.sr-title',
            'a.sr-title',
            '.sku-title'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text

        return None

    def _extract_price(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            'div.customer-price',
            '[data-testid="medium-customer-price"]',
            '.sr-price',
            '.pricing-price__range',
            '.visuallyhidden'
        ]

        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)

                if 'current price' in text.lower():
                    text = text.replace('current price', '').strip()
                if text and re.search(r'[\d\$₹]', text):
                    return text

        return None

    def _extract_url(self, container: BeautifulSoup) -> Optional[str]:

        selectors = [
            'a.product-list-item-link',
            'a.sr-title',
            '.sku-item a'
        ]

        for selector in selectors:
            link = container.select_one(selector)
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('/'):
                    return self.base_url + href
                elif href.startswith('http'):
                    return href

        return None
