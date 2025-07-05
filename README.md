# Price Comparison Tool


![Watch the video](https://cdn.loom.com/sessions/thumbnails/88c213d189df47e1bc7722a3fbbf91f1-with-play.gif)](https://www.loom.com/share/88c213d189df47e1bc7722a3fbbf91f1)


A comprehensive price comparison API that fetches the best prices for products from multiple websites across different countries using AI-powered scraping and ranking.

## Architecture

The price comparison tool follows a modular architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │ PriceComparison  │    │   Scrapers      │
│   REST API      │───►│     Service      │───►│   (Crawl4AI)    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   OpenAI API     │
                       │   (Ranking &     │
                       │   Filtering)     │
                       └──────────────────┘
```

**Key Components:**
- **FastAPI**: RESTful API interface with async processing
- **PriceComparisonService**: Orchestrates scraping across multiple websites
- **Crawl4AI Scrapers**: Intelligent web scraping with JavaScript support
- **OpenAI Integration**: GPT-3.5-turbo model for product ranking and relevance filtering
- **Multi-Platform Support**: 
  - **US**: Amazon, eBay, Walmart, Best Buy
  - **India**: Amazon, eBay, Flipkart, Myntra, Tata CLiQ


## Features

- **AI-Powered Scraping**: Uses Crawl4AI for intelligent web scraping and content extraction
- **OpenAI Ranking**: Uses GPT-3.5-turbo for accurate product relevance ranking
- **Multi-Website Support**: Searches across major e-commerce platforms
- **Country-Specific**: Supports US and India markets with localized websites
- **Fast & Scalable**: Asynchronous processing with concurrent scraping


## Supported Websites

### United States (US)
- Amazon.com
- eBay.com
- Walmart.com
- Best Buy

### India (IN)
- Amazon.in
- eBay.in
- Flipkart.com
- Myntra.com
- Tata CLiQ

## Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- **OpenAI API Key (REQUIRED)** - Get one from [OpenAI Platform](https://platform.openai.com/api-keys)

### Method 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd price-comparison-tool
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env file with your OpenAI API key (REQUIRED)
```

3. **Important**: Edit the `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_actual_openai_api_key_here
```

4. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### Method 2: Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd price-comparison-tool
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

5. Set environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"  # REQUIRED
export API_PORT=8000
```

6. Run the application:
```bash
python main.py
```

## Usage

### API Endpoints

#### 1. Price Comparison
**POST** `/compare`

Search for products and get price comparison results.

**Request Body:**
```json
{
  "country": "US",
  "query": "iPhone 16 Pro, 128GB"
}
```

**Response:**
```json
{
  "results": [
    {
      "link": "https://www.amazon.com/...",
      "price": "999",
      "currency": "USD",
      "productName": "Apple iPhone 16 Pro",
      "website": "Amazon US",
    }
  ],
  "query": "iPhone 16 Pro, 128GB",
  "country": "US",
  "total_results": 1
}
```

#### 2. Health Check
**GET** `/health`

Check the service health status and view enabled scrapers.

**Response:**
```json
{
  "status": "healthy",
  "scrapers": "amazon,ebay,walmart,bestbuy",
  "crawl4ai_enabled": "yes"
}
```


## Testing

### Manual Testing

```bash
# Test with different products
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "US",
    "query": "MacBook Pro M3"
  }'

# Test with different countries
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "IN",
    "query": "Samsung Galaxy S24"
  }'
```



## Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for AI-powered features (**REQUIRED**)
- `API_PORT`: Port for the API server (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent scraping requests (default: 5)
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 30)




