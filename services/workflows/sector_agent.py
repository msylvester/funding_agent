"""
Sector Classification Agent

This module provides sector/industry classification for user queries using OpenAI.
It dynamically fetches valid sectors from MongoDB and uses structured output
to ensure accurate classification with confidence scoring.
"""

import os
import sys
import logging
from typing import Optional

# Add project root to path to enable config imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pydantic import BaseModel, Field
from pymongo import MongoClient
from openai import OpenAI

# Import database configuration
from config.settings import DATABASE_CONFIG

logger = logging.getLogger(__name__)


# ===============================
# SCHEMA
# ===============================

class SectorClassification(BaseModel):
    """Schema for sector classification output"""
    sector: str = Field(..., description="The classified industry sector")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    rationale: str = Field(default="", description="Brief explanation for the classification")


# ===============================
# HELPER FUNCTIONS
# ===============================

def get_valid_sectors() -> list[str]:
    """
    Fetch distinct sectors from MongoDB companies collection.

    Returns:
        List of valid sector strings from the database

    Raises:
        Exception: If connection fails or no sectors found
    """
    client = None
    try:
        client = MongoClient(DATABASE_CONFIG['mongodb_uri'])
        db = client[DATABASE_CONFIG['database_name']]
        collection = db[DATABASE_CONFIG['collection_name']]

        # Get distinct sectors, filtering out None/empty values
        sectors = collection.distinct("sector")
        sectors = [s for s in sectors if s and isinstance(s, str) and s.strip()]

        if not sectors:
            logger.warning("No sectors found in database, using defaults")
            # Fallback to common sectors if database is empty
            return [
                "Technology", "SaaS", "AI", "Fintech", "Healthcare",
                "E-commerce", "Food Delivery", "General"
            ]

        # Add "General" as a catch-all option
        if "General" not in sectors and "Technology" not in sectors:
            sectors.append("General")

        logger.info(f"Found {len(sectors)} valid sectors from database")
        return sorted(sectors)

    except Exception as e:
        logger.error(f"Error fetching sectors from MongoDB: {e}")
        # Return default sectors as fallback
        return [
            "Technology", "SaaS", "AI", "Fintech", "Healthcare",
            "E-commerce", "Food Delivery", "General"
        ]
    finally:
        if client:
            client.close()


# ===============================
# MAIN CLASSIFICATION FUNCTION
# ===============================

def classify_sector(
    query: str,
    model: str = "gpt-4o-mini",
    min_confidence: float = 0.6,
    default_sector: str = "Technology"
) -> SectorClassification:
    """
    Classify the sector/industry from a user query using OpenAI.

    This function:
    1. Fetches valid sectors from MongoDB
    2. Uses OpenAI with structured output to classify the query
    3. Returns sector with confidence score
    4. Falls back to default sector if confidence is too low

    Args:
        query: User's query text describing their product/startup
        model: OpenAI model to use (default: gpt-4o-mini - supports structured outputs)
        min_confidence: Minimum confidence threshold (default: 0.6)
        default_sector: Fallback sector for low confidence (default: "Technology")

    Returns:
        SectorClassification with sector, confidence, and rationale

    Example:
        >>> result = classify_sector("Our startup builds AI tools for hospitals")
        >>> print(result.sector)  # "Healthcare" or "AI"
        >>> print(result.confidence)  # 0.85
    """
    try:
        # Step 1: Get valid sectors from database
        valid_sectors = get_valid_sectors()
        logger.info(f"Classifying query with {len(valid_sectors)} possible sectors")

        # Step 2: Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key)

        # Step 3: Create JSON schema for structured output
        # This enforces that the sector must be one of the valid values
        schema = {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "enum": valid_sectors,
                    "description": "The classified industry sector"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence score between 0 and 1"
                },
                "rationale": {
                    "type": "string",
                    "description": "Brief explanation for the classification"
                }
            },
            "required": ["sector", "confidence", "rationale"],
            "additionalProperties": False
        }

        # Step 4: Call OpenAI with structured output
        system_prompt = f"""You are a startup sector classification expert.

Your task: Identify what sector/industry the USER'S STARTUP or COMPANY operates in.

Valid sectors: {', '.join(valid_sectors)}

Guidelines:
- Focus ONLY on what the user's startup/company/business DOES or BUILDS
- Ignore any mentions of investors, funding sources, or "who would invest"
- Example: "Who would invest in my social media startup?" → classify as "Social Media" (their startup's sector)
- Example: "We're building a fintech app" → classify as fintech-related sector
- Choose the MOST specific sector that matches the user's business
- If multiple sectors apply, choose the primary/dominant one
- Provide a confidence score (0-1) based on how clear the business sector is
- Give a brief rationale explaining your choice

Remember: You are classifying the USER'S BUSINESS SECTOR, not investor types or funding sources."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "sector_classification",
                    "strict": True,
                    "schema": schema
                }
            },
            temperature=0.1  # Low temperature for more consistent classification
        )

        # Step 5: Parse the response
        result = response.choices[0].message.content
        import json
        classification_data = json.loads(result)

        classification = SectorClassification(**classification_data)

        # Step 6: Handle low confidence
        if classification.confidence < min_confidence:
            logger.warning(
                f"Low confidence ({classification.confidence:.2f}) for sector '{classification.sector}', "
                f"using default: {default_sector}"
            )
            classification.sector = default_sector
            classification.rationale = (
                f"Original classification: {classification.sector} (confidence {classification.confidence:.2f}). "
                f"Using default '{default_sector}' due to low confidence."
            )

        logger.info(
            f"Classified sector: {classification.sector} "
            f"(confidence: {classification.confidence:.2f})"
        )

        return classification

    except Exception as e:
        logger.error(f"Error classifying sector: {e}")
        # Return default sector on error
        return SectorClassification(
            sector=default_sector,
            confidence=0.0,
            rationale=f"Error during classification: {str(e)}. Using default sector."
        )


# ===============================
# TESTING
# ===============================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n=== Sector Classification Agent Test ===\n")

    # Test cases
    test_queries = [
        "What investors would be interested in my SaaS product for managing teams?",
        "How should I pitch my AI startup that uses machine learning for healthcare?",
        "We're building a fintech app for digital payments",
        "Our food delivery platform connects restaurants with customers",
        "I'm building a general technology product"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = classify_sector(query)
        print(f"  Sector: {result.sector}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Rationale: {result.rationale}")

    print("\n=== Test Complete ===\n")
