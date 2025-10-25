# Getting Started

Quick guide to get up and running with the Opera Research Agentic System.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/austinkness/opera-research-agentic-system.git
   cd opera-research-agentic-system
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (if using Playwright)
   ```bash
   playwright install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred text editor and add any API keys
   ```

## Running the Application

### Run the main scraper
```bash
python src/main.py
```

### Run tests
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_scraper.py
```

### Test the scraper module directly
```bash
python src/scraping/scraper.py
```

## Project Structure

```
opera-research-agentic-system/
├── src/
│   ├── main.py              # Main entry point
│   ├── scraping/
│   │   └── scraper.py       # Web scraper implementation
│   ├── processing/          # Data processing (coming soon)
│   ├── db/                  # Database operations (coming soon)
│   └── analytics/           # Data analysis (coming soon)
├── tests/
│   └── test_scraper.py      # Scraper unit tests
├── data/
│   ├── raw/                 # Raw scraped data
│   └── processed/           # Processed data
└── requirements.txt         # Python dependencies
```

## Current Features

- ✅ Basic web scraping with BeautifulSoup
- ✅ URL fetching with requests
- ✅ Link extraction
- ✅ Metadata extraction (title, description)
- ✅ Unit tests (8 tests, all passing)
- ✅ Successfully tested with real opera company websites

## Next Steps

1. Add data extraction for financial information
2. Implement data storage (database)
3. Add performance trend analysis
4. Implement cast member networking insights
5. Scale to handle multiple opera companies globally

## Troubleshooting

### Virtual environment issues
If you have issues with the virtual environment, try:
```bash
deactivate  # if already in a venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Import errors
Make sure you're running scripts from the project root directory and the virtual environment is activated.

### Network errors
The scraper requires internet access. Check your connection if you see network-related errors.

## Contributing

1. Create a new branch for your feature
2. Write tests for new functionality
3. Ensure all tests pass (`pytest`)
4. Commit with descriptive messages
5. Push and create a pull request

## License

MIT
