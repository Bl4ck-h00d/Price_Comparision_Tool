import re
import logging
from typing import Optional
from price_parser import Price

logger = logging.getLogger(__name__)


def parse_price(price_text: str) -> Optional[float]:
    """
    Parse price from text using price-parser library
    Returns the price as a float or None if parsing fails
    """
    try:
        if not price_text:
            return None

        price_text = price_text.strip()
        price = Price.fromstring(price_text)

        if price.amount is not None:
            return float(price.amount)

        # Fallback to regex parsing
        price_patterns = [
            # $1,234.56 or ₹1,234.56
            r'[\$₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            # 1234.56$ or 1234.56₹
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*[\$₹]?',
            r'[\$₹]?\s*(\d+\.?\d*)',  # $123.45 or ₹123.45
        ]

        for pattern in price_patterns:
            price_match = re.search(pattern, price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                parsed_price = float(price_str)

                # Sanity check: prices should be reasonable (between $1 and $50,000)
                if 1 <= parsed_price <= 50000:
                    return parsed_price

    except Exception as e:
        logger.warning(f"Failed to parse price '{price_text}': {e}")

    return None


def extract_currency(price_text: str) -> str:
    """
    Extract currency from price text
    """
    if not price_text:
        return "INR"

    price_lower = price_text.lower()

    if '₹' in price_text or 'rs.' in price_lower or 'rs ' in price_lower or 'inr' in price_lower:
        return 'INR'

    if '$' in price_text or 'usd' in price_lower:
        return 'USD'

    return "INR"  # Default currency


def clean_product_name(name: str) -> str:
    if not name:
        return ""

    name = ' '.join(name.split())

    # remove html tags
    name = re.sub(r'<[^>]+>', '', name)

    # remove special characters
    name = re.sub(r'[^\w\s\-\(\)]+$', '', name)

    return name.strip()


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    """
    if not url:
        return False

    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url) is not None


def get_currency_for_country(country: str) -> str:
    """
    Get default currency for a country
    """
    currency_map = {
        "US": "USD",
        "IN": "INR"
    }

    return currency_map.get(country.upper(), "INR")
