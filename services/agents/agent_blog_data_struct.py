import os
import json
import requests
from typing import Optional, Dict, Any


def enhance_with_ai_blog(title: str, content: str, openrouter_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Use Haiku via OpenRouter to extract structured funding data from company blogs and news articles.
    
    Handles both first-party company announcements (e.g., "We're thrilled to announce...") 
    and third-party news articles (e.g., "Company X raises...").
    
    Args:
        title: Article title
        content: Article content 
        openrouter_api_key: OpenRouter API key (optional, uses env var if not provided)
        
    Returns:
        Dictionary with extracted funding data or None if extraction fails
    """
    if not openrouter_api_key:
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_api_key:
        return None
        
    try:
        prompt = f"""
Extract structured funding information from this article. This could be either:
1. A first-party company announcement (e.g., "We're thrilled to announce that [Company] has raised...")
2. A third-party news article (e.g., "[Company] raises $X million...")

Return ONLY a valid JSON object with these exact fields:

{{
    "company_name": "exact company name",
    "funding_amount": "amount with unit like $50M, $2.5B, or 'Not specified'",
    "valuation": "valuation with unit like $500M, $1.2B, or 'Not specified'",
    "series": "Series A, Series B, Seed, Pre-seed, or 'Not specified'",
    "founded_year": "year as string like '2020' or 'Not specified'",
    "total_funding": "total funding raised with unit or 'Not specified'",
    "investors": "comma-separated list of investors or 'Not specified'",
    "description": "brief company description or 'Not specified'",
    "sector": "industry/sector or 'Not specified'"
}}

EXTRACTION EXAMPLES:

First-party announcement: "We're thrilled to announce that Exa has raised an $85m Series B"
→ company_name: "Exa", funding_amount: "$85M", series: "Series B"

Third-party article: "AI startup OpenAI raises $6.6 billion in Series C funding"
→ company_name: "OpenAI", funding_amount: "$6.6B", series: "Series C"

IMPORTANT NOTES:
- For first-party announcements, look for "we", "our company", "our team", company domain names
- Distinguish between funding amount and valuation (funding is what was raised, valuation is company worth)
- Extract ALL investors mentioned, not just lead investors
- If company description isn't explicit, infer from context
- Pay attention to the full content, not just the first paragraph

Article Title: {title}

Article Content: {content[:3000]}

Return only the JSON object, no other text. If this article is NOT about a company receiving funding, return {{"company_name": "Not specified"}}.
"""

        headers = {
            'Authorization': f'Bearer {openrouter_api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/funding-scraper',
            'X-Title': 'Blog Funding Data Extractor'
        }
        
        data = {
            'model': 'anthropic/claude-3-haiku',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 800,  # Increased for more comprehensive responses
            'temperature': 0.1
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # Try to parse the JSON response
            try:
                # Remove any markdown code blocks if present
                if ai_response.startswith('```json'):
                    ai_response = ai_response.split('\n', 1)[1]
                elif ai_response.startswith('```'):
                    ai_response = ai_response.split('\n', 1)[1]
                    
                if ai_response.endswith('```'):
                    ai_response = ai_response.rsplit('\n', 1)[0]
                
                # Clean up any extra whitespace or newlines
                ai_response = ai_response.strip()
                
                enhanced_data = json.loads(ai_response)
                
                # Validate that we have the required structure
                if not isinstance(enhanced_data, dict):
                    print(f"Blog AI agent returned non-dict response: {type(enhanced_data)}")
                    return None
                
                company_name = enhanced_data.get('company_name', 'Unknown')
                print(f"Blog AI agent successfully extracted data for: {company_name}")
                print(f"Funding: {enhanced_data.get('funding_amount', 'N/A')}, Series: {enhanced_data.get('series', 'N/A')}")
                print(f"Content sent to AI (first 300 chars): {content[:300]}...")
                print(f"Full AI response: {enhanced_data}")
                
                return enhanced_data
                
            except json.JSONDecodeError as e:
                print(f"Blog AI agent failed to parse JSON response: {e}")
                print(f"Raw AI response was: {repr(ai_response)}")
                return None
        else:
            print(f"Blog AI agent OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Blog AI agent error calling OpenRouter API: {e}")
        return None


# Backwards compatibility alias
def enhance_with_ai(title: str, content: str, openrouter_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Backwards compatibility wrapper for the enhanced blog AI agent"""
    return enhance_with_ai_blog(title, content, openrouter_api_key)
