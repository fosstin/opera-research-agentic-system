"""
FastAPI application for Opera Research Intelligence Platform.

This API layer sits on top of the PostgreSQL data warehouse,
providing REST endpoints for programmatic access to opera data.

Architecture:
- Data Layer: PostgreSQL (staging → core → analytics via dbt)
- API Layer: FastAPI (this file)
- Frontend: React/Vue (separate)
- Analytics: Tableau + LLM Agent

Endpoints:
- /companies - Opera house information
- /productions - Production data
- /artists - Performer information
- /performances - Individual show data
- /metadata - Scraping metadata and lineage
- /search - Vector-powered semantic search (future)
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import date

from backend.db.connectors import get_db, engine
from backend.db import models
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Opera Research Intelligence API",
    description="REST API for opera production data, built on PostgreSQL data warehouse",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class CompanyResponse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    tier: Optional[str]
    website_url: str
    venue_capacity: Optional[int]

    class Config:
        from_attributes = True

class ProductionResponse(BaseModel):
    id: str
    company_name: str
    opera_title: str
    composer: str
    conductor: Optional[str]
    director: Optional[str]
    premiere_date: Optional[date]
    total_performances: Optional[int]

    class Config:
        from_attributes = True

class ArtistResponse(BaseModel):
    id: str
    name: str
    voice_type: Optional[str]
    nationality: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# Health check endpoint
@app.get("/")
async def root():
    """Health check and API information."""
    return {
        "status": "healthy",
        "api": "Opera Research Intelligence Platform",
        "version": "1.0.0",
        "documentation": "/docs",
        "data_warehouse": "PostgreSQL with dbt transformations",
        "endpoints": {
            "companies": "/companies",
            "productions": "/productions",
            "artists": "/artists",
            "metadata": "/metadata"
        }
    }


# Companies endpoints
@app.get("/companies", response_model=List[CompanyResponse])
async def get_companies(
    country: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of opera companies.

    Filters:
    - country: Filter by country name
    - tier: Filter by tier (tier-1, tier-2, etc.)
    - limit: Maximum results (default 100, max 1000)
    - offset: Pagination offset
    """
    query = db.query(models.Company).filter(models.Company.is_active == True)

    if country:
        query = query.filter(models.Company.country == country)
    if tier:
        query = query.filter(models.Company.tier == tier)

    companies = query.offset(offset).limit(limit).all()

    return [
        CompanyResponse(
            id=str(c.id),
            name=c.name,
            city=c.city,
            country=c.country,
            tier=c.tier,
            website_url=c.website_url,
            venue_capacity=c.venue_capacity
        )
        for c in companies
    ]


@app.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific company."""
    company = db.query(models.Company).filter(models.Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        city=company.city,
        country=company.country,
        tier=company.tier,
        website_url=company.website_url,
        venue_capacity=company.venue_capacity
    )


# Productions endpoints
@app.get("/productions", response_model=List[ProductionResponse])
async def get_productions(
    company_id: Optional[str] = None,
    composer: Optional[str] = None,
    season: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of productions.

    Filters:
    - company_id: Filter by company UUID
    - composer: Filter by composer name
    - season: Filter by season (e.g., "2024-25")
    - limit: Maximum results
    - offset: Pagination offset

    Note: Uses the analytics mart (mart_production_summary) for optimized queries.
    """
    # In production, query from mart_production_summary for better performance
    query = db.query(models.Production)

    if company_id:
        query = query.filter(models.Production.company_id == company_id)
    if composer:
        query = query.join(models.OperaWork).filter(models.OperaWork.composer.ilike(f"%{composer}%"))

    productions = query.offset(offset).limit(limit).all()

    return [
        ProductionResponse(
            id=str(p.id),
            company_name=p.company.name if p.company else "Unknown",
            opera_title=p.opera_work.title if p.opera_work else "Unknown",
            composer=p.opera_work.composer if p.opera_work else "Unknown",
            conductor=p.conductor,
            director=p.director,
            premiere_date=p.premiere_date,
            total_performances=p.total_performances
        )
        for p in productions
    ]


# Artists endpoints
@app.get("/artists", response_model=List[ArtistResponse])
async def get_artists(
    voice_type: Optional[str] = None,
    nationality: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of artists/performers.

    Filters:
    - voice_type: Filter by voice type (soprano, tenor, etc.)
    - nationality: Filter by nationality
    - active_only: Only show active artists (default True)
    - limit: Maximum results
    - offset: Pagination offset
    """
    query = db.query(models.Performer)

    if active_only:
        query = query.filter(models.Performer.is_active == True)
    if voice_type:
        query = query.filter(models.Performer.voice_type == voice_type)
    if nationality:
        query = query.filter(models.Performer.nationality == nationality)

    artists = query.offset(offset).limit(limit).all()

    return [
        ArtistResponse(
            id=str(a.id),
            name=a.name,
            voice_type=a.voice_type,
            nationality=a.nationality,
            is_active=a.is_active
        )
        for a in artists
    ]


# Metadata endpoint for data lineage
@app.get("/metadata/scraping-stats")
async def get_scraping_stats(db: Session = Depends(get_db)):
    """
    Get scraping metadata and statistics.
    Shows data lineage, scraping quality, and source information.
    """
    from sqlalchemy import func, text

    # Get stats from staging tables
    total_pages = db.execute(
        text("SELECT COUNT(*) FROM stg_scraped_pages")
    ).scalar()

    processed_pages = db.execute(
        text("SELECT COUNT(*) FROM stg_scraped_pages WHERE is_processed = TRUE")
    ).scalar()

    total_extractions = db.execute(
        text("SELECT COUNT(*) FROM stg_llm_extractions")
    ).scalar()

    avg_confidence = db.execute(
        text("SELECT AVG(confidence_score) FROM stg_llm_extractions WHERE is_validated = TRUE")
    ).scalar()

    return {
        "scraping_metadata": {
            "total_pages_scraped": total_pages,
            "pages_processed": processed_pages,
            "processing_rate": f"{(processed_pages/total_pages*100):.1f}%" if total_pages > 0 else "0%",
            "total_llm_extractions": total_extractions,
            "average_confidence_score": float(avg_confidence) if avg_confidence else 0.0
        },
        "data_lineage": {
            "source_layer": "stg_scraped_pages (raw HTML)",
            "extraction_layer": "stg_llm_extractions (LLM-parsed JSON)",
            "transformation_layer": "dbt models (core tables)",
            "analytics_layer": "dbt marts (analytics tables)"
        }
    }


# Future: Vector search endpoint (placeholder)
@app.get("/search/semantic")
async def semantic_search(
    query: str,
    limit: int = 10
):
    """
    Semantic search using vector embeddings.

    Future feature: Will use ChromaDB or pgvector for semantic similarity search.
    Currently returns placeholder.
    """
    return {
        "status": "not_implemented",
        "message": "Semantic search will be implemented with vector embeddings",
        "planned_features": [
            "Natural language queries",
            "Similarity search for productions",
            "Artist network exploration",
            "Repertoire recommendations"
        ],
        "query_received": query
    }


# Future: LLM Agent endpoint (placeholder)
@app.post("/agent/query")
async def llm_agent_query(query: str):
    """
    LLM Agent for natural language queries.

    Future feature: Will integrate LangChain SQL agent + Tableau MCP.
    Currently returns placeholder.
    """
    return {
        "status": "not_implemented",
        "message": "LLM agent will be integrated via LangChain and MCP",
        "planned_capabilities": [
            "Natural language to SQL translation",
            "Tableau dashboard generation",
            "Conversational data exploration",
            "Multi-turn context awareness"
        ],
        "query_received": query
    }


if __name__ == "__main__":
    import uvicorn

    # Create tables if they don't exist
    models.Base.metadata.create_all(bind=engine)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
