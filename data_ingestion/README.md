# Data Ingestion Package

This package provides components for retrieving and processing financial data from various sources.

## Components

### API Agent

The API Agent uses the AlphaVantage API to fetch stock prices, earnings data, and other financial information.

```python
from data_ingestion.api_agent.alphavantage_client import get_price, get_earnings_surprise

# Get latest price for Apple stock
apple_price = get_price("AAPL")

# Get earnings surprise for Microsoft
msft_surprise = get_earnings_surprise("MSFT")
```

### Scraper Agent

The Scraper Agent fetches SEC filings and other financial documents.

```python
from data_ingestion.scraper_agent.sec_scraper import get_filings_for_ticker, get_latest_asian_tech_filings

# Get latest filings for Apple
apple_filings = get_filings_for_ticker("AAPL", count=3)

# Get filings for Asian tech companies
asian_filings = get_latest_asian_tech_filings(days_back=30)
```

## Configuration

Configure the data ingestion components by setting environment variables:

- `ALPHAVANTAGE_KEY`: Your AlphaVantage API key (default: "demo")

You can set these variables in a `.env` file at the project root.

## Caching

All API responses and scraped documents are cached to reduce API calls and respect rate limits. Cache files are stored in:

- API cache: `./cache/api/`
- Scraper cache: `./cache/scraper/` 