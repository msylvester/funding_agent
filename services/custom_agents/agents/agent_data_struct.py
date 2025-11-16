import os
import json
import requests


def enhance_with_ai(title, content, openrouter_api_key=None):
    """Use Haiku via OpenRouter to extract structured funding data"""
    if not openrouter_api_key:
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_api_key:
        return None
        
    try:
        prompt = f"""
Extract structured funding information from this TechCrunch article. Return ONLY a valid JSON object with these exact fields:

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

Article Title: {title}

Article Content: {content[:1500]}

Return only the JSON object, no other text. If this article is NOT about a company receiving funding, return {{"company_name": "Not specified"}}.
"""

        headers = {
            'Authorization': f'Bearer {openrouter_api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-repo',
            'X-Title': 'TechCrunch Funding Scraper'
        }
        
        data = {
            'model': 'anthropic/claude-3-haiku',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 500,
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
                if ai_response.startswith('```'):
                    ai_response = ai_response.split('\n', 1)[1]
                if ai_response.endswith('```'):
                    ai_response = ai_response.rsplit('\n', 1)[0]
                
                enhanced_data = json.loads(ai_response)
                print(f"Successfully enhanced data with AI for: {enhanced_data.get('company_name', 'Unknown')}")
                return enhanced_data
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse AI response as JSON: {e}")
                print(f"AI response was: {ai_response}")
                return None
        else:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None
