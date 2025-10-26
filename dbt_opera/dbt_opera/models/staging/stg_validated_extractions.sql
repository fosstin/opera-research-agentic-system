-- Validated LLM extractions
-- Filters for high-quality, validated extractions ready for transformation

{{
  config(
    materialized='view',
    schema='staging'
  )
}}

SELECT
    e.id AS extraction_id,
    e.scraped_page_id,
    p.url,
    p.domain,
    p.company_name,
    e.extraction_type,
    e.raw_response,
    e.parsed_data,
    e.llm_model,
    e.llm_provider,
    e.confidence_score,
    e.extraction_quality,
    e.tokens_total,
    e.estimated_cost_usd,
    e.extracted_at,
    p.scraped_at,
    -- Extract number of productions found
    jsonb_array_length(e.parsed_data->'productions') AS num_productions

FROM {{ source('staging', 'stg_llm_extractions') }} AS e
INNER JOIN {{ source('staging', 'stg_scraped_pages') }} AS p
    ON e.scraped_page_id = p.id

WHERE
    -- Only validated extractions
    e.is_validated = TRUE
    -- Minimum confidence threshold (configurable via vars)
    AND e.confidence_score >= {{ var('min_confidence_score', 0.7) }}
    -- Has at least one production
    AND jsonb_array_length(e.parsed_data->'productions') > 0
    -- No extraction errors
    AND e.extraction_error IS NULL

ORDER BY e.extracted_at DESC
