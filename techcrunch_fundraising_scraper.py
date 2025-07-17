import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse
import os

class TechCrunchFundraisingScaper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://techcrunch.com"
        self.funding_data = []
        
        # OpenRouter API setup
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            print("OPENROUTER_API_KEY not found in environment variables. AI enhancement will be disabled.")
    
    def is_funding_article(self, title):
        """Check if article title indicates funding news"""
        title_lower = title.lower()
        
        # Exclude event/conference announcements and non-funding content
        exclude_keywords = [
            'disrupt', 'event', 'conference', 'agenda', 'winner', 'vote', 'session', 
            'speaker', 'roundtable', 'breakout', 'awards', 'summit', 'meetup',
            'interview', 'podcast', 'webinar', 'demo day', 'pitch', 'competition'
        ]
        if any(keyword in title_lower for keyword in exclude_keywords):
            return False
        
        # Check for dollar amounts
        dollar_pattern = r'\$\d+(?:\.\d+)?[kmb]?'
        if re.search(dollar_pattern, title_lower):
            return True
        
        # Check for funding keywords
        funding_keywords = ['closes', 'raises', 'raised', 'funded', 'funding', 'investment', 'series', 'round']
        return any(keyword in title_lower for keyword in funding_keywords)
    
    def scrape_fundraising_page(self, max_pages=3):
        """Scrape the TechCrunch fundraising category page"""
        page = 1
        
        while page <= max_pages:
            if page == 1:
                url = "https://techcrunch.com/category/fundraising/"
            else:
                url = f"https://techcrunch.com/category/fundraising/page/{page}/"
            
        
            
            try:
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                articles = self.extract_articles_from_page(soup)
                
                if not articles:
                    print(f"No articles found on page {page}, stopping")
                    break
                
                # Process each article (limit to prevent getting stuck)
                processed_count = 0
                max_articles_per_page = 10
                
                for article in articles:
                    if processed_count >= max_articles_per_page:
                        print(f"Reached max articles per page ({max_articles_per_page})")
                        break
                        
                    if self.is_funding_article(article['title']):
                        # print(f"Processing funding article: {article['title']}")
                        article_data = self.scrape_article_content(article['url'])
                        
                        if article_data:
                            # Handle both single company and multi-company articles
                            if isinstance(article_data, list):
                                # Multiple companies found
                                for single_article_data in article_data:
                                    if self.is_valid_funding_data(single_article_data):
                                        self.funding_data.append(single_article_data)
                            else:
                                # Single company article
                                if self.is_valid_funding_data(article_data):
                                    self.funding_data.append(article_data)
                        
                        processed_count += 1
                        time.sleep(1)  # Be respectful to the server
                
                page += 1
                time.sleep(2)  # Delay between pages
                
            except Exception as e:
                # print(f"Error scraping page {page}: {e}")
                break
    
    def extract_articles_from_page(self, soup):
        """Extract article links and titles from the page"""
        articles = []
        
        # TechCrunch specific selectors - look for article links
        article_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))
        
        for link in article_links:
            try:
                title = link.get_text(strip=True)
                url = link.get('href')
                
                if not title or not url:
                    continue
                
                # Make URL absolute
                if url.startswith('/'):
                    url = urljoin(self.base_url, url)
                
                # Skip if not a TechCrunch article or if it's an event/non-article page
                if 'techcrunch.com' not in url or '/events/' in url:
                    continue
                
                # Skip duplicate titles
                if any(article['title'] == title for article in articles):
                    continue
                
                articles.append({
                    'title': title,
                    'url': url
                })
                
            except Exception as e:
                continue
        
        print(f"Found {len(articles)} articles on page")
        return articles
    
    def scrape_article_content(self, url):
        """Scrape individual article content - now handles multiple companies"""
        try:
            # print(f"Scraping article: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title - try multiple selectors
            title = "N/A"
            title_selectors = [
                'h1.entry-title',
                'h1[class*="title"]',
                'h1',
                '.entry-title',
                '[class*="headline"]'
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break
            
            # Extract content - try multiple selectors
            content = ""
            content_selectors = [
                '.entry-content',
                '[class*="content"]',
                '.article-content',
                '.post-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # Remove scripts and styles
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    content = content_element.get_text(strip=True)
                    break
            
            # Extract date
            date = ""
            date_element = soup.find('time')
            if date_element:
                date = date_element.get('datetime') or date_element.get_text(strip=True)
            
            # Check if article has multiple companies using AI
            has_multiple_companies = False
            if self.openrouter_api_key:
                has_multiple_companies = self.detect_multiple_companies_with_ai(title, content)
            
            articles = []
            
            if has_multiple_companies:
                # Extract multiple companies using AI
                companies_data = self.extract_multiple_companies_with_ai(title, content)
                
                if companies_data:
                    print(f"Found {len(companies_data)} companies in article: {title}")
                    for company_details in companies_data:
                        if company_details.get('company_name', 'Not specified') != 'Not specified':
                            article_data = {
                                'source': 'TechCrunch Fundraising',
                                'title': title,
                                'url': url,
                                'date': date,
                                'content': content[:1000] if content else "",
                                'scraped_at': datetime.now().isoformat(),
                                **company_details
                            }
                            articles.append(article_data)
                else:
                    # Fallback to single company extraction
                    has_multiple_companies = False
            
            if not has_multiple_companies:
                # Single company article - use existing logic
                funding_details = self.extract_funding_details(title, content)
                
                # Enhance with AI if API key is available
                if self.openrouter_api_key:
                    enhanced_details = self.enhance_with_ai(title, content[:2000])
                    if enhanced_details:
                        funding_details.update(enhanced_details)
                
                article_data = {
                    'source': 'TechCrunch Fundraising',
                    'title': title,
                    'url': url,
                    'date': date,
                    'content': content[:1000] if content else "",
                    'scraped_at': datetime.now().isoformat(),
                    **funding_details
                }
                articles.append(article_data)
            
            # print(f"Successfully scraped: {title} - {len(articles)} companies")
            return articles if len(articles) > 1 else articles[0] if articles else None
            
        except Exception as e:
            # print(f"Error scraping article {url}: {e}")
            return None
    
    def extract_funding_details(self, title, content=""):
        """Extract funding details from title and content"""
        text = f"{title} {content}".lower()
        
        # Extract funding amount
        funding_amount = "Not specified"
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(?:million|m)\b',
            r'\$(\d+(?:\.\d+)?)\s*(?:billion|b)\b',
            r'\$(\d+(?:\.\d+)?)\s*(?:thousand|k)\b',
            r'\$(\d+(?:\.\d+)?)\s*(?:m|b|k)\b'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1)
                if 'billion' in match.group(0) or 'b' in match.group(0):
                    funding_amount = f"${amount}B"
                elif 'million' in match.group(0) or 'm' in match.group(0):
                    funding_amount = f"${amount}M"
                elif 'thousand' in match.group(0) or 'k' in match.group(0):
                    funding_amount = f"${amount}K"
                break
        
        # Extract company name (simple heuristic)
        company_name = "Not specified"
        # Look for patterns like "Company raises" or "Company closes"
        company_patterns = [
            r'^([A-Z][a-zA-Z\s&]+?)\s+(?:raises|raised|closes|closed|secures|secured)',
            r'(?:startup|company)\s+([A-Z][a-zA-Z\s&]+?)\s+(?:raises|raised|closes|closed)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, title)
            if match:
                company_name = match.group(1).strip()
                # Clean up common prefixes/suffixes
                company_name = re.sub(r'\b(?:startup|company|the)\b', '', company_name, flags=re.IGNORECASE).strip()
                if len(company_name.split()) <= 3:  # Reasonable company name length
                    break
        
        # Extract series information
        series = "Not specified"
        series_match = re.search(r'series\s+([a-z]+)', text)
        if series_match:
            series = f"Series {series_match.group(1).upper()}"
        elif 'seed' in text:
            series = "Seed"
        elif 'pre-seed' in text:
            series = "Pre-seed"
        
        return {
            'company_name': company_name,
            'funding_amount': funding_amount,
            'valuation': "Not specified",
            'series': series,
            'founded_year': "Not specified",
            'total_funding': "Not specified",
            'investors': "Not specified",
            'description': "Not specified",
            'is_recent': True
        }
    
    def is_valid_funding_data(self, funding_details):
        """Check if the extracted funding data represents a real funding event"""
        # Must have at least company name and funding amount specified
        has_company = funding_details.get('company_name', 'Not specified') != 'Not specified'
        has_amount = funding_details.get('funding_amount', 'Not specified') != 'Not specified'
        
        # If AI enhancement provided data, check for key fields
        if funding_details.get('sector') and funding_details.get('sector') != 'Not specified':
            # AI provided data, be more lenient but still require company name
            return has_company
        
        # For non-AI data, require both company and amount
        return has_company and has_amount
    
    def detect_multiple_companies_with_ai(self, title, content):
        """Use AI to detect if article mentions multiple companies with funding"""
        if not self.openrouter_api_key:
            return False
        
        try:
            prompt = f"""
Analyze this TechCrunch article and determine if it mentions multiple companies that received funding.

Return ONLY a JSON object with this format:
{{
    "multiple_companies": true/false,
    "company_count": number_of_companies_with_funding
}}

Look for:
- Articles that list multiple companies with funding amounts
- Roundup articles about funding
- Articles with titles like "every", "all", "startups that raised", etc.

Article Title: {title}

Article Content: {content[:2000]}

Return only the JSON object, no other text.
"""

            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/your-repo',
                'X-Title': 'TechCrunch Funding Scraper'
            }
            
            data = {
                'model': 'anthropic/claude-3-haiku',
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
                    if ai_response.startswith('```'):
                        ai_response = ai_response.split('\n', 1)[1]
                    if ai_response.endswith('```'):
                        ai_response = ai_response.rsplit('\n', 1)[0]
                    
                    detection_result = json.loads(ai_response)
                    return detection_result.get('multiple_companies', False)
                    
                except json.JSONDecodeError:
                    return False
            
            return False
                
        except Exception as e:
            print(f"Error detecting multiple companies: {e}")
            return False

    def extract_multiple_companies_with_ai(self, title, content):
        """Use AI to extract multiple companies from an article"""
        if not self.openrouter_api_key:
            return []
        
        try:
            prompt = f"""
Extract ALL companies that received funding from this TechCrunch article. Return a JSON array where each company is an object with these fields:

[
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
]

Article Title: {title}

Article Content: {content[:3000]}

Return only the JSON array, no other text. Include ALL companies mentioned that received funding.
"""

            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/your-repo',
                'X-Title': 'TechCrunch Funding Scraper'
            }
            
            data = {
                'model': 'anthropic/claude-3-haiku',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 1500,
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
                    if ai_response.startswith('```'):
                        ai_response = ai_response.split('\n', 1)[1]
                    if ai_response.endswith('```'):
                        ai_response = ai_response.rsplit('\n', 1)[0]
                    
                    companies_data = json.loads(ai_response)
                    return companies_data if isinstance(companies_data, list) else []
                    
                except json.JSONDecodeError as e:
                    print(f"Failed to parse multiple companies JSON: {e}")
                    return []
            
            return []
                
        except Exception as e:
            print(f"Error extracting multiple companies: {e}")
            return []

    def enhance_with_ai(self, title, content):
        """Use Haiku via OpenRouter to extract structured funding data"""
        if not self.openrouter_api_key:
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
                'Authorization': f'Bearer {self.openrouter_api_key}',
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
                    # print(f"Successfully enhanced data with AI for: {enhanced_data.get('company_name', 'Unknown')}")
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
    
    def save_to_json(self, filename='scraped_one.json'):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.funding_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.funding_data)} articles to {filename}")
        except Exception as e:
            print(f"Error saving to {filename}: {e}")
    
    def run_scraper(self, max_pages=3):
        """Run the complete scraping process"""
        # print("Starting TechCrunch fundraising scraper...")
        self.scrape_fundraising_page(max_pages)
        
        if self.funding_data:
            self.save_to_json('scraped_one.json')
            # print(f"Scraping completed. Found {len(self.funding_data)} funding articles.")
        # else:
            # print("No funding articles found.")
        
        return self.funding_data

def main():
    scraper = TechCrunchFundraisingScaper()
    data = scraper.run_scraper(max_pages=3)

if __name__ == "__main__":
    main()
