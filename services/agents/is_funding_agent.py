import os
import json
import requests


def is_funding_article_ai(title, openrouter_api_key=None):
    """Check if article title indicates funding news using AI"""
    
    if openrouter_api_key is None:
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_api_key:
        return None  # Return None to indicate AI is not available
    
    try:
        prompt = f"""
Analyze this article title and determine if it's about a company receiving funding/investment.

Return ONLY a JSON object with this format:
{{
    "is_funding": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}

Look for:
- Companies raising money (Series A, B, C, seed rounds, etc.)
- Investment announcements  
- Funding rounds
- Venture capital deals
- Equity raises
- Valuations mentioned with funding context
- Terms like "raises", "raised", "nabs", "gets", "secures", "seeking"
- Dollar amounts with funding context (e.g., "$4.3B equity raise", "$40M at $4B valuation")

Exclude:
- Events, conferences, awards
- Product launches
- General business news
- Interviews or podcasts

Article Title: "{title}"

Return only the JSON object, no other text.
"""

        headers = {
            'Authorization': f'Bearer {openrouter_api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-repo',
            'X-Title': 'TechCrunch Funding Classifier'
        }
        
        data = {
            'model': 'openai/o3-mini',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 200,
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
            
            try:
                # Clean up response if it has markdown
                if ai_response.startswith('```'):
                    ai_response = ai_response.split('\n', 1)[1]
                if ai_response.endswith('```'):
                    ai_response = ai_response.rsplit('\n', 1)[0]
                
                classification = json.loads(ai_response)
                is_funding = classification.get('is_funding', False)
                confidence = classification.get('confidence', 0.0)
                reason = classification.get('reason', 'No reason provided')
                
                print(f"AI Classification: {is_funding} (confidence: {confidence:.2f}) - {reason}")
                return is_funding
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse AI response: {e}")
                return None
        else:
            print(f"OpenRouter API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error calling AI for funding classification: {e}")
        return None
