# Opera Research Agentic System - Project Vision

## Executive Summary

Build a comprehensive **Opera Production Metadata Database** that enables data-driven insights through automated web scraping, structured data storage, and LLM-powered conversational analytics via Tableau MCP integration.

**End Goal:** Ask natural language questions about global opera trends, financial patterns, casting networks, and performance metrics through an AI agent that queries a rich, continuously-updated database and generates interactive Tableau visualizations.

---

## Vision Statement

Create the world's most comprehensive, queryable database of opera production metadata, enabling researchers, producers, and enthusiasts to discover insights about:
- Financial operating costs and revenue models
- Performance trends and repertoire patterns
- Cast member networks and career trajectories
- Venue capacities and geographic distribution
- Seasonal programming strategies
- Ticket pricing and accessibility

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Natural Language Queries → LLM Agent → Tableau MCP             │
│  "Show me soprano salary trends in European opera houses"       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   VISUALIZATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  • Tableau Desktop/Server                                       │
│  • Interactive Dashboards                                       │
│  • Geographic Visualizations                                    │
│  • Network Graphs (cast connections)                            │
│  • Time Series Analysis                                         │
│  • Financial Trend Visualization                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AI/LLM LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  • LLM Agent (OpenAI/Gemini)                                    │
│  • Tableau MCP Integration                                      │
│  • Natural Language → SQL Translation                           │
│  • Context-Aware Query Generation                               │
│  • Response Synthesis                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database:                                           │
│  ├── opera_companies (metadata, location, capacity)            │
│  ├── productions (season, opera title, dates, venue)           │
│  ├── performances (specific dates, times, attendance)          │
│  ├── cast_members (roles, singers, compensation estimates)     │
│  ├── financial_data (budgets, ticket prices, revenue)          │
│  ├── repertoire (composers, librettists, premiere info)        │
│  └── relationships (cast networks, company affiliations)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  DATA PROCESSING LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  • Data Extraction (LLM-powered parsing)                        │
│  • Entity Recognition (venues, performers, works)               │
│  • Data Normalization & Cleaning                                │
│  • Duplicate Detection & Merging                                │
│  • Data Enrichment (external APIs)                              │
│  • Quality Validation                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DATA COLLECTION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  • Compliant Web Scraper (current implementation) ✅            │
│  • robots.txt Compliance ✅                                     │
│  • Rate Limiting ✅                                             │
│  • Caching ✅                                                   │
│  • Request Logging ✅                                           │
│  • Multi-source orchestration (future)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. **Data Collection Engine** (Current Phase ✅)

**Status:** Foundation complete

**Capabilities:**
- ✅ Ethical web scraping with compliance
- ✅ robots.txt respect
- ✅ Rate limiting and caching
- ✅ Request logging and monitoring

**Next Steps:**
- HTML content extraction
- Structured data parsing with LLM
- Multi-site orchestration
- Error recovery and retry logic

### 2. **Data Extraction & Processing** (Next Phase)

**Goal:** Transform raw HTML into structured metadata

**Approach:**
- **LLM-Powered Extraction:** Use GPT-4/Gemini to extract structured data from opera websites
- **Entity Recognition:** Identify venues, performers, composers, works
- **Financial Data Extraction:** Parse ticket prices, seating charts, membership tiers
- **Performance Schedule Extraction:** Dates, times, venues, casting

**Schema Targets:**
```python
Production {
    id: UUID
    company_id: FK
    opera_title: str
    composer: str
    conductor: str
    director: str
    season: str (e.g., "2024-25")
    premiere_date: date
    closing_date: date
    total_performances: int
    venue: str
    estimated_budget: decimal
    ticket_price_range: json
}

CastMember {
    id: UUID
    production_id: FK
    performer_name: str
    role: str
    voice_type: str (soprano, tenor, etc.)
    performance_dates: json
    estimated_fee: decimal (if available)
}

FinancialData {
    id: UUID
    company_id: FK
    fiscal_year: int
    total_revenue: decimal
    ticket_revenue: decimal
    donations: decimal
    operating_costs: decimal
    artist_fees: decimal
    production_costs: decimal
}
```

### 3. **Database Layer** (Next Phase)

**Technology:** PostgreSQL with extensions
- **PostGIS:** Geographic queries (opera houses by region)
- **Full-Text Search:** Search across productions, performers
- **JSONB:** Flexible metadata storage

**Key Features:**
- Normalized schema for data integrity
- Indexes for fast querying
- Views for common analytics
- Materialized views for dashboards
- Row-level security for sensitive data

### 4. **Analytics & Visualization** (Phase 3)

**Tableau Integration:**
- Direct PostgreSQL connection
- Custom SQL queries for complex analysis
- Pre-built dashboard templates
- Interactive filtering and drilling

**Visualization Types:**
- **Geographic:** Opera houses on world map, regional trends
- **Network:** Cast member collaborations, career paths
- **Financial:** Budget trends, revenue models, pricing strategies
- **Temporal:** Repertoire trends over time, seasonal patterns
- **Comparative:** Cross-company analysis, market positioning

### 5. **LLM Agent with Tableau MCP** (Phase 4)

**Capabilities:**
```
User: "Show me the top 10 most-performed operas in European houses over the last 5 years"

Agent:
1. Interprets natural language query
2. Generates SQL:
   SELECT o.title, COUNT(*) as performance_count,
          ARRAY_AGG(DISTINCT c.name) as companies
   FROM productions p
   JOIN opera_works o ON p.opera_id = o.id
   JOIN companies c ON p.company_id = c.id
   WHERE c.region = 'Europe'
   AND p.season_year >= 2019
   GROUP BY o.title
   ORDER BY performance_count DESC
   LIMIT 10

3. Executes query via Tableau MCP
4. Generates visualization in Tableau
5. Provides natural language summary
```

**Advanced Queries:**
- "How do soprano salaries compare across tier-1 vs tier-2 houses?"
- "What's the correlation between production budget and ticket sales?"
- "Show me the career trajectory of [famous singer]"
- "Which repertoire is trending up in the 2024-25 season?"
- "Compare Met Opera's programming strategy to La Scala"

---

## Data Sources Strategy

### Primary Sources (Web Scraping)

**Tier 1 - Major International Houses:**
- Metropolitan Opera (New York)
- Royal Opera House (London)
- Wiener Staatsoper (Vienna)
- Teatro alla Scala (Milan)
- Paris Opera
- Bavarian State Opera (Munich)
- Deutsche Oper Berlin
- Teatro Real (Madrid)

**Tier 2 - Regional Houses:**
- San Francisco Opera
- Lyric Opera of Chicago
- Los Angeles Opera
- Houston Grand Opera
- Canadian Opera Company
- Opera Australia
- Netherlands Opera
- And 50+ more...

**Data to Extract:**
- Season schedules and repertoire
- Cast lists and role assignments
- Performance dates and venues
- Ticket pricing structures
- Company financials (when public)
- Historical programming data

### Secondary Sources (APIs & Data Feeds)

- **OperaBase:** Commercial opera database API
- **MusicBrainz:** Open music metadata
- **Wikidata:** Structured data about operas, composers
- **IMSLP:** Public domain scores and metadata
- **Company APIs:** Some houses offer structured data

### Tertiary Sources (Manual/Research)

- Annual reports and financial statements
- Industry publications (Opera News, etc.)
- Academic research databases
- Historical archives

---

## Technology Stack

### Current Stack ✅
- **Language:** Python 3.13
- **Web Scraping:** BeautifulSoup, Playwright, Requests
- **Compliance:** Custom middleware (robots.txt, rate limiting)
- **Caching:** File-based JSON
- **Testing:** Pytest

### Planned Additions

**Data Processing:**
- **LangChain:** LLM orchestration for data extraction
- **LlamaIndex:** Document parsing and indexing
- **Pandas:** Data transformation and cleaning
- **spaCy/NLTK:** Natural language processing

**Database:**
- **PostgreSQL 15+:** Primary database
- **SQLAlchemy:** ORM and query builder
- **Alembic:** Database migrations
- **PostGIS:** Geographic extensions

**LLM Integration:**
- **OpenAI API:** GPT-4 for extraction and querying
- **Google Gemini:** Alternative LLM provider
- **LangChain:** Agent framework
- **Semantic Kernel:** Agent orchestration

**Visualization:**
- **Tableau Desktop/Server:** Primary visualization
- **Tableau MCP:** LLM agent integration
- **Plotly/Matplotlib:** Quick visualizations
- **NetworkX:** Cast network analysis

**Infrastructure:**
- **Docker:** Containerization
- **Docker Compose:** Multi-service orchestration
- **GitHub Actions:** CI/CD
- **Cloud:** AWS/GCP for production (optional)

---

## Development Roadmap

### Phase 1: Foundation ✅ **COMPLETE**
- [x] Project structure
- [x] Compliant web scraper
- [x] robots.txt compliance
- [x] Rate limiting and caching
- [x] Documentation
- [x] Testing framework

**Timeline:** Complete

### Phase 2: Data Extraction & Storage (Next 4-6 weeks)

**Week 1-2: Database Design**
- [ ] Design comprehensive schema
- [ ] Set up PostgreSQL database
- [ ] Create migrations with Alembic
- [ ] Add indexes and constraints
- [ ] Set up test database

**Week 3-4: LLM-Powered Extraction**
- [ ] Implement LLM-based HTML parsing
- [ ] Extract production metadata
- [ ] Extract cast information
- [ ] Extract financial data
- [ ] Build extraction pipeline

**Week 5-6: Data Processing**
- [ ] Entity normalization
- [ ] Duplicate detection
- [ ] Data validation
- [ ] Quality scoring
- [ ] Automated data ingestion pipeline

**Deliverables:**
- Working database with sample data from 10+ opera houses
- Automated extraction pipeline
- Data quality metrics

### Phase 3: Analytics & Initial Visualization (Weeks 7-10)

**Week 7-8: Database Analytics**
- [ ] Create analytical views
- [ ] Build summary tables
- [ ] Implement aggregation queries
- [ ] Performance optimization
- [ ] Data export utilities

**Week 9-10: Tableau Integration**
- [ ] Connect Tableau to PostgreSQL
- [ ] Create initial dashboards
- [ ] Build visualization templates
- [ ] Document Tableau workflows
- [ ] User testing

**Deliverables:**
- 5-10 interactive Tableau dashboards
- Documented analytics patterns
- Performance benchmarks

### Phase 4: LLM Agent with Tableau MCP (Weeks 11-14)

**Week 11-12: LLM Agent Development**
- [ ] Set up LangChain agent
- [ ] Implement NL to SQL translation
- [ ] Add context awareness
- [ ] Build query validation
- [ ] Error handling and fallbacks

**Week 13-14: Tableau MCP Integration**
- [ ] Integrate Tableau MCP
- [ ] Connect agent to Tableau
- [ ] Implement visualization generation
- [ ] Add conversational context
- [ ] User acceptance testing

**Deliverables:**
- Working conversational interface
- NL query to visualization pipeline
- Demo videos and documentation

### Phase 5: Scale & Production (Weeks 15+)

- [ ] Scale to 100+ opera houses
- [ ] Automated scheduling and updates
- [ ] Performance optimization
- [ ] Production deployment
- [ ] Monitoring and alerting
- [ ] Public API (optional)

---

## Success Metrics

### Data Coverage Goals
- **Year 1:** 50+ opera companies, 5,000+ productions
- **Year 2:** 150+ companies, 20,000+ productions
- **Year 3:** 300+ companies, 50,000+ productions

### Quality Metrics
- Data accuracy: >95%
- Duplicate rate: <2%
- Missing data: <10% for core fields
- Update frequency: Weekly for active seasons

### User Experience
- Query response time: <3 seconds
- Visualization generation: <10 seconds
- Natural language understanding: >90% accuracy
- User satisfaction: >4.5/5

---

## Use Cases

### 1. **Opera Producer/Artistic Director**
"Which contemporary operas are gaining traction? What's the ROI on new commissions vs. traditional repertoire?"

### 2. **Performer/Agent**
"What are typical fee ranges for lyric sopranos at tier-1 houses? Which companies are casting my voice type most frequently?"

### 3. **Academic Researcher**
"How has opera repertoire diversity changed over the last 30 years? What's the geographic distribution of Verdi vs. Wagner performances?"

### 4. **Arts Journalist**
"What are the programming trends for the 2025-26 season? Which companies are taking creative risks?"

### 5. **Opera Enthusiast**
"Show me where I can see [favorite opera] in the next 6 months. What's the relationship between [two famous singers]?"

---

## Risk Mitigation

### Legal/Compliance Risks
- **Mitigation:** Robust compliance system (implemented ✅)
- **Action:** Regular ToS reviews, legal consultation for commercial use
- **Backup:** Focus on public domain data, use APIs where available

### Data Quality Risks
- **Mitigation:** Multi-source validation, human review sampling
- **Action:** Automated quality scoring, community feedback
- **Backup:** Clearly label data confidence levels

### Technical Risks
- **Mitigation:** Modular architecture, comprehensive testing
- **Action:** Graceful degradation, error logging, monitoring
- **Backup:** Manual fallback procedures

### Sustainability Risks
- **Mitigation:** Automated pipelines, efficient caching
- **Action:** Cost monitoring, scalability planning
- **Backup:** Tiered data collection (priority companies first)

---

## Open Questions

1. **Business Model:** Free research project vs. commercial product?
2. **Data Sharing:** Open data vs. proprietary database?
3. **Community:** Build contributor network for data validation?
4. **Partnerships:** Collaborate with existing opera databases (OperaBase)?
5. **Scope:** Focus on current seasons vs. historical archive?

---

## Getting Started (Next Immediate Steps)

1. **Design Database Schema** (3-5 days)
   - Entity-relationship diagram
   - Table definitions
   - Sample data model

2. **Set Up PostgreSQL** (1-2 days)
   - Local development database
   - Docker container
   - Initial migrations

3. **Build Extraction Pipeline** (1-2 weeks)
   - LLM prompt engineering for extraction
   - Test with Met Opera data
   - Validate extracted data

4. **Proof of Concept** (1 week)
   - Scrape 5 opera houses
   - Extract structured data
   - Load into database
   - Create simple Tableau dashboard
   - Demo NL query

---

## Long-Term Vision

**Ultimate Goal:** Transform how the opera industry understands itself through data.

Enable insights like:
- "The opera industry is shifting toward shorter, contemporary works in smaller venues"
- "Cross-pollination between European and American houses peaks in summer festivals"
- "Early-career sopranos who perform X role have 80% chance of tier-1 house debuts within 3 years"
- "Ticket pricing elasticity varies significantly by repertoire genre"

**Impact:**
- **Artistic:** Data-driven programming decisions
- **Financial:** Revenue optimization and cost benchmarking
- **Educational:** Academic research on cultural trends
- **Accessibility:** Help audiences discover performances

---

**Next Action:** Choose path forward
- A) Start database schema design
- B) Build LLM extraction prototype
- C) Create detailed technical architecture document
- D) All of the above in sequence

Which would you like to prioritize?
