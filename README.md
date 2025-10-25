# Opera Research Agentic System

An agentic application to identify and scrape web pages of opera companies worldwide for research on financial operating costs, performance trends, and cast member networking.

## Features
- Automated web scraping and data collection
- Financial data extraction and analysis
- Performance trend analysis
- Cast member networking insights

## Setup

### Prerequisites
- Python 3.9+

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/austinkness/opera-research-agentic-system.git
   cd opera-research-agentic-system
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add any required API keys
   ```

## Project Structure

```
opera-research-agentic-system/
├── README.md                 # Project overview and instructions
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── src/                    # Source code
│   ├── __init__.py
│   ├── scraping/           # Web scraping modules
│   ├── processing/         # Data extraction and processing
│   ├── db/                 # Database interactions
│   └── analytics/          # Analysis and visualization
├── data/                   # Data storage
│   ├── raw/                # Raw scraped data
│   └── processed/          # Processed data
└── tests/                  # Unit tests
```

## Usage

```bash
python src/main.py
```

## Development Guide

See [Opera-Research-Guide.md](Opera-Research-Guide.md) for detailed implementation steps and development guidance.

## Roadmap
1. ✅ Repository and foundation setup
2. Initial web scraper prototype
3. Financial data extraction
4. Performance trend analysis
5. Cast networking insights
6. Global scaling

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
