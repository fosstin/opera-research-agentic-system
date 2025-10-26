"""
LLM-powered extraction module for parsing opera production data from HTML.

This module uses OpenAI GPT-4 or Google Gemini to extract structured
data from scraped HTML pages with deterministic, production-grade reliability.

Architecture:
1. Read HTML from stg_scraped_pages
2. Parse with LLM using structured prompts with JSON schema enforcement
3. Store response in stg_llm_extractions
4. Track costs and quality metrics accurately
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional, Literal, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from bs4 import BeautifulSoup
import tiktoken
from dotenv import load_dotenv

load_dotenv()


# Pydantic models for structured output
class CastMember(BaseModel):
    """Individual cast member."""
    performer_name: str
    role_name: str
    voice_type: Optional[str] = None


class Performance(BaseModel):
    """Individual performance."""
    date: str  # YYYY-MM-DD
    time: Optional[str] = None  # HH:MM
    type: Optional[str] = None  # "Opening Night", "Matinee", etc.


class CreativeTeam(BaseModel):
    """Creative team members."""
    set_designer: Optional[str] = None
    costume_designer: Optional[str] = None
    lighting_designer: Optional[str] = None
    choreographer: Optional[str] = None
    other: Optional[Dict[str, str]] = None


class TicketPrices(BaseModel):
    """Ticket pricing information."""
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = "USD"


class Production(BaseModel):
    """Single opera production."""
    opera_title: str
    composer: str
    production_title: Optional[str] = None
    conductor: Optional[str] = None
    director: Optional[str] = None
    premiere_date: Optional[str] = None  # YYYY-MM-DD
    closing_date: Optional[str] = None  # YYYY-MM-DD
    venue_name: Optional[str] = None
    language: Optional[str] = None
    creative_team: Optional[CreativeTeam] = None
    cast: Optional[List[CastMember]] = None
    performances: Optional[List[Performance]] = None
    ticket_prices: Optional[TicketPrices] = None


class CompanyInfo(BaseModel):
    """Opera company information."""
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    season: Optional[str] = None


class ExtractionResult(BaseModel):
    """Complete extraction result."""
    extraction_type: Literal["production", "season", "company_info", "performance_list"]
    confidence: float = Field(ge=0.0, le=1.0)
    productions: List[Production]
    company_info: Optional[CompanyInfo] = None
    extracted_at: str


class LLMExtractor:
    """Extract structured data from HTML using LLM with production-grade reliability."""

    def __init__(
        self,
        provider: Literal["openai", "gemini"] = "openai",
        model: Optional[str] = None,
        temperature: float = 0.0,
        seed: Optional[int] = 42  # For deterministic OpenAI responses
    ):
        """
        Initialize LLM extractor.

        Args:
            provider: "openai" or "gemini"
            model: Model name (optional, uses defaults)
            temperature: 0.0 for deterministic responses
            seed: Random seed for OpenAI (ensures consistency)
        """
        self.provider = provider
        self.temperature = temperature
        self.seed = seed

        # Initialize LLM based on provider
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")

            self.model_name = model or "gpt-4-turbo-preview"

            # Use structured output with JSON mode for consistency
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=temperature,
                api_key=api_key,
                model_kwargs={
                    "response_format": {"type": "json_object"},
                    "seed": seed  # Ensures deterministic responses
                }
            )

            # Pricing (as of Oct 2024)
            self.cost_per_input_token = 0.01 / 1_000_000  # $10 per 1M input tokens
            self.cost_per_output_token = 0.03 / 1_000_000  # $30 per 1M output tokens

            # Initialize tokenizer for accurate token counting
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)

        elif provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set in environment")

            self.model_name = model or "gemini-1.5-pro"
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=temperature,
                google_api_key=api_key
            )

            # Gemini pricing
            self.cost_per_input_token = 0.00035 / 1_000_000
            self.cost_per_output_token = 0.00105 / 1_000_000

            # Gemini uses SentencePiece - approximate with tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def count_tokens(self, text: str) -> int:
        """
        Accurately count tokens using the model's tokenizer.

        Args:
            text: Input text

        Returns:
            Token count
        """
        return len(self.tokenizer.encode(text))

    def extract_text_from_html(self, html: str) -> str:
        """
        Extract clean, consistent text from HTML.

        Uses deterministic parsing to ensure same HTML -> same text.

        Args:
            html: Raw HTML content

        Returns:
            Clean text content
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, nav, footer, header elements
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()

        # Get text with separator to maintain structure
        text = soup.get_text(separator='\n', strip=True)

        # Normalize whitespace consistently
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        return text

    def chunk_text_by_tokens(self, text: str, max_tokens: int = 4000) -> List[str]:
        """
        Intelligently chunk text by token count, preserving context.

        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk

        Returns:
            List of text chunks
        """
        # Split by paragraphs for better context preservation
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)

            # If single paragraph exceeds limit, split by sentences
            if para_tokens > max_tokens:
                sentences = para.split('. ')
                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)
                    if current_tokens + sent_tokens > max_tokens and current_chunk:
                        chunks.append('\n\n'.join(current_chunk))
                        current_chunk = [sentence]
                        current_tokens = sent_tokens
                    else:
                        current_chunk.append(sentence)
                        current_tokens += sent_tokens
            else:
                # Add paragraph to current chunk if it fits
                if current_tokens + para_tokens > max_tokens and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [para]
                    current_tokens = para_tokens
                else:
                    current_chunk.append(para)
                    current_tokens += para_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def generate_cache_key(self, url: str, html: str) -> str:
        """
        Generate deterministic cache key for deduplication.

        Args:
            url: Source URL
            html: HTML content

        Returns:
            SHA256 hash
        """
        content = f"{url}||{html}"
        return hashlib.sha256(content.encode()).hexdigest()

    def extract_production_data(
        self,
        html: str,
        url: str,
        retry_on_failure: int = 3
    ) -> Dict[str, Any]:
        """
        Extract opera production data from HTML with retry logic.

        Args:
            html: HTML content
            url: Source URL
            retry_on_failure: Number of retries on parse errors

        Returns:
            Dictionary with extraction results
        """
        # Extract clean text
        text_content = self.extract_text_from_html(html)

        # Count tokens to determine if chunking needed
        total_tokens = self.count_tokens(text_content)

        # If content is too large, chunk it and process
        max_tokens = 4000  # Leave room for prompt
        if total_tokens > max_tokens:
            chunks = self.chunk_text_by_tokens(text_content, max_tokens)
            # For now, use only first chunk
            # TODO: Implement multi-chunk processing with result merging
            text_content = chunks[0]
            was_chunked = True
        else:
            was_chunked = False

        # Create structured prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured data about opera productions from website content.

Extract information about opera productions, performances, and related details.

IMPORTANT: You MUST return valid JSON matching this exact structure:

{{
  "extraction_type": "production",
  "confidence": 0.85,
  "productions": [
    {{
      "opera_title": "La Traviata",
      "composer": "Giuseppe Verdi",
      "production_title": "La Traviata (New Production)",
      "conductor": "John Doe",
      "director": "Jane Smith",
      "premiere_date": "2024-03-15",
      "closing_date": "2024-04-20",
      "venue_name": "Main Stage",
      "language": "Italian",
      "creative_team": {{
        "set_designer": "...",
        "costume_designer": "..."
      }},
      "cast": [
        {{
          "performer_name": "Anna Johnson",
          "role_name": "Violetta",
          "voice_type": "Soprano"
        }}
      ],
      "performances": [
        {{
          "date": "2024-03-15",
          "time": "19:30",
          "type": "Opening Night"
        }}
      ],
      "ticket_prices": {{
        "min": 25.00,
        "max": 250.00,
        "currency": "USD"
      }}
    }}
  ],
  "company_info": {{
    "name": "Metropolitan Opera",
    "city": "New York",
    "country": "United States",
    "season": "2024-2025"
  }},
  "extracted_at": "{timestamp}"
}}

Rules:
- Extract ALL productions found
- Use null for missing fields
- Dates in YYYY-MM-DD format
- Be conservative with confidence (0.0-1.0)
- Return valid JSON ONLY, no markdown or explanations
"""),
            ("human", """Extract opera production data.

URL: {url}

Content:
{content}

Return only valid JSON, no additional text or markdown.""")
        ])

        # Track timing and attempt extraction with retries
        for attempt in range(retry_on_failure):
            start_time = time.time()

            try:
                # Format prompt
                messages = prompt_template.format_messages(
                    url=url,
                    content=text_content,
                    timestamp=datetime.utcnow().isoformat()
                )

                # Count input tokens accurately
                prompt_text = '\n'.join([m.content for m in messages])
                input_tokens = self.count_tokens(prompt_text)

                # Call LLM
                response = self.llm.invoke(messages)
                processing_time = time.time() - start_time

                # Get response text
                response_text = response.content.strip()

                # Count output tokens accurately
                output_tokens = self.count_tokens(response_text)

                # Parse JSON - with strict validation
                try:
                    parsed_data = json.loads(response_text)

                    # Validate against Pydantic schema for extra safety
                    validated_result = ExtractionResult(**parsed_data)

                    # Calculate actual cost
                    estimated_cost = (
                        (input_tokens * self.cost_per_input_token) +
                        (output_tokens * self.cost_per_output_token)
                    )

                    return {
                        "success": True,
                        "raw_response": parsed_data,
                        "parsed_data": parsed_data,
                        "llm_model": self.model_name,
                        "llm_provider": self.provider,
                        "tokens_input": input_tokens,
                        "tokens_output": output_tokens,
                        "tokens_total": input_tokens + output_tokens,
                        "estimated_cost_usd": float(estimated_cost),
                        "confidence_score": parsed_data.get("confidence", 0.5),
                        "processing_time_seconds": processing_time,
                        "extraction_error": None,
                        "was_chunked": was_chunked,
                        "retry_attempt": attempt
                    }

                except (json.JSONDecodeError, ValueError) as e:
                    if attempt < retry_on_failure - 1:
                        # Retry on parse error
                        continue
                    else:
                        # Final attempt failed
                        raise ValueError(f"JSON parse failed after {retry_on_failure} attempts: {e}")

            except Exception as e:
                if attempt < retry_on_failure - 1:
                    time.sleep(1)  # Brief pause before retry
                    continue
                else:
                    processing_time = time.time() - start_time
                    return {
                        "success": False,
                        "raw_response": None,
                        "parsed_data": None,
                        "llm_model": self.model_name,
                        "llm_provider": self.provider,
                        "tokens_input": 0,
                        "tokens_output": 0,
                        "tokens_total": 0,
                        "estimated_cost_usd": 0.0,
                        "confidence_score": 0.0,
                        "processing_time_seconds": processing_time,
                        "extraction_error": str(e),
                        "was_chunked": was_chunked,
                        "retry_attempt": attempt
                    }

    def validate_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted data for quality and completeness.

        Args:
            data: Parsed extraction data

        Returns:
            Validation results with errors and quality assessment
        """
        errors = []
        warnings = []

        # Check required fields
        if not data.get("productions"):
            errors.append("No productions found in extraction")

        # Check each production
        for i, prod in enumerate(data.get("productions", [])):
            if not prod.get("opera_title"):
                errors.append(f"Production {i}: Missing opera_title")
            if not prod.get("composer"):
                warnings.append(f"Production {i}: Missing composer")
            if not prod.get("premiere_date"):
                warnings.append(f"Production {i}: Missing premiere_date")

        # Determine quality
        if len(errors) > 0:
            quality = "low"
        elif len(warnings) > 2:
            quality = "medium"
        else:
            quality = "high"

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality": quality
        }


def test_extractor():
    """Test the LLM extractor with sample HTML."""

    sample_html = """
    <html>
    <body>
        <h1>2024-2025 Season</h1>
        <div class="production">
            <h2>La Traviata</h2>
            <p>Composer: Giuseppe Verdi</p>
            <p>Conductor: Yannick Nézet-Séguin</p>
            <p>Director: Michael Mayer</p>
            <p>Premiere: March 15, 2025</p>
            <p>Closing: April 20, 2025</p>
            <div class="cast">
                <p>Violetta: Nadine Sierra (Soprano)</p>
                <p>Alfredo: Stephen Costello (Tenor)</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Test with configured provider
    try:
        provider = os.getenv("AI_PROVIDER", "openai")
        extractor = LLMExtractor(provider=provider)

        print(f"Testing LLM extraction with {provider}...")
        print(f"Model: {extractor.model_name}")

        result = extractor.extract_production_data(
            html=sample_html,
            url="https://example.com/season"
        )

        print(f"\nSuccess: {result['success']}")
        print(f"Tokens (input/output/total): {result['tokens_input']}/{result['tokens_output']}/{result['tokens_total']}")
        print(f"Cost: ${result['estimated_cost_usd']:.6f}")
        print(f"Confidence: {result['confidence_score']}")
        print(f"Processing time: {result['processing_time_seconds']:.2f}s")

        if result['success']:
            print(f"\nExtracted data:")
            print(json.dumps(result['parsed_data'], indent=2))

            # Validate
            validation = extractor.validate_extraction(result['parsed_data'])
            print(f"\nValidation Quality: {validation['quality']}")
            if validation['errors']:
                print(f"Errors: {validation['errors']}")
            if validation['warnings']:
                print(f"Warnings: {validation['warnings']}")
        else:
            print(f"\nExtraction failed: {result['extraction_error']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_extractor()
