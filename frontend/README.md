# Opera Research Platform - Frontend

Web interface for the Opera Research Intelligence Platform.

## Architecture

This frontend connects to the FastAPI backend and provides:
- Browse opera companies, productions, and artists
- Search and filter functionality
- Data visualization dashboards
- Future: LLM-powered conversational interface

## Technology Stack (Planned)

- **Framework:** React or Vue.js
- **Styling:** Tailwind CSS
- **State Management:** React Query / Pinia
- **API Client:** Axios
- **Charts:** Chart.js or D3.js
- **Deployment:** Cloudflare Pages (free tier)

## Getting Started

### Prerequisites
- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API client and services
│   │   └── apiClient.js
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   └── styles/         # Global styles
├── package.json
└── tailwind.config.js
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

Example API call:

```javascript
import { apiClient } from './services/apiClient';

// Get all companies
const companies = await apiClient.get('/companies');

// Search productions
const productions = await apiClient.get('/productions', {
  params: {
    composer: 'Verdi',
    limit: 20
  }
});
```

## Features (Planned)

### Phase 1 - Basic UI
- [ ] Company directory
- [ ] Production listings
- [ ] Artist profiles
- [ ] Search and filters

### Phase 2 - Visualizations
- [ ] Geographic map of opera houses
- [ ] Repertoire trends charts
- [ ] Cast network graphs
- [ ] Financial dashboards

### Phase 3 - AI Features
- [ ] Natural language search
- [ ] LLM-powered recommendations
- [ ] Conversational data exploration

## Development Status

🚧 **Under Development** - Frontend scaffold created, implementation pending.

See main project [README.md](../README.md) for overall roadmap.
