import re
import os
import json
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from agents.agent_007 import is_funding_article_ai
from agents.agent_data_struct import enhance_with_ai


class ArticleProcessor:
    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            print("Warning: OPENROUTER_API_KEY not found. Falling back to keyword-based filtering.")
    
    def is_funding_article(self, title):
        """Check if article title indicates funding news using AI"""
        # print(f'Checking if funding article: {title}')
        
        # Quick check for immediate funding indicators
        title_lower = title.lower()
        immediate_funding_keywords = ['valuation', 'equity raise', 'raise', 'funding']
        if any(keyword in title_lower for keyword in immediate_funding_keywords):
            return True
        

        if not self.openrouter_api_key:
            return self._is_funding_article_keywords(title)
        
        # Use the AI agent function
        ai_result = is_funding_article_ai(title, self.openrouter_api_key)
        
        # If AI is available and returns a result, use it
        if ai_result is not None:
            return ai_result
        
        # Fallback to keyword-based detection
        return self._is_funding_article_keywords(title)
    
    def _is_funding_article_keywords(self, title):
        """Fallback keyword-based funding article detection"""
        title_lower = title.lower()
        
        # Exclude event/conference announcements
        exclude_keywords = [
            'disrupt', 'event', 'conference', 'agenda', 'winner', 'vote', 'session', 
            'speaker', 'roundtable', 'awards', 'summit', 'meetup', 'interview', 'podcast'
        ]
        if any(keyword in title_lower for keyword in exclude_keywords):
            return False
        
        # Check for funding keywords
        funding_keywords = ['closes', 'raises', 'raised', 'funded', 'funding', 'investment', 'series', 'round']
        return any(keyword in title_lower for keyword in funding_keywords)
    
    
    def extract_articles_from_page(self, soup):
        """Extract article links and titles from the page"""
        articles = []
        
        # Look for article links with date pattern
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
                
                # Skip if not a TechCrunch article
                if 'techcrunch.com' not in url or '/events/' in url:
                    continue
                
                # Skip duplicate titles
                if any(article['title'] == title for article in articles):
                    continue
                
                articles.append({
                    'title': title,
                    'url': url
                })
                
            except Exception:
                continue
        
        print(f"Found {len(articles)} articles on page")
        return articles
    
    def scrape_article_content(self, url):
        """Scrape individual article content"""
        try:
            response = self.session.get(url, timeout=10)



            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = "Not specified"
            title_selectors = ['h1.entry-title', 'h1[class*="title"]', 'h1', '.entry-title']


            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break
            
            # Extract content
            content = ""
            content_selectors = ['.entry-content', '[class*="content"]', '.article-content']
            
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
            
            # Try AI enhancement first, fall back to regex if needed
            if self.openrouter_api_key:
                ai_funding_details = enhance_with_ai(title, content, self.openrouter_api_key)
                if ai_funding_details and ai_funding_details.get('company_name') != 'Not specified':
                    return {
                        'source': 'TechCrunch',
                        'title': title,
                        'url': url,
                        'date': date,
                        'content': content[:500] if content else "",
                        'scraped_at': datetime.now().isoformat(),
                        **ai_funding_details
                    }
            
            # Fallback to regex extraction
            funding_details = self.extract_funding_details(title, content)
            
            return {
                'source': 'TechCrunch',
                'title': title,
                'url': url,
                'date': date,
                'content': content[:500] if content else "",
                'scraped_at': datetime.now().isoformat(),
                **funding_details
            }
            
        except Exception as e:
            print(f"Error scraping article {url}: {e}")
            return None
    
    def extract_funding_details(self, title, content=""):
        """Extract funding details using basic regex patterns"""
        text = f"{title} {content}".lower()
        
        # Extract funding amount
        funding_amount = "Not specified"
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(?:million|m)\b',
            r'\$(\d+(?:\.\d+)?)\s*(?:billion|b)\b',
            r'\$(\d+(?:\.\d+)?)\s*(?:thousand|k)\b'
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
        
        # Extract company name
        company_name = "Not specified"
        company_patterns = [
            r'^([A-Z][a-zA-Z\s&.-]+?)\s+(?:raises|raised|closes|closed|secures|secured)',
            r'(?:startup|company)\s+([A-Z][a-zA-Z\s&.-]+?)\s+(?:raises|raised|closes|closed)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, title)
            if match:
                company_name = match.group(1).strip()
                # Clean up common prefixes
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
            'series': series,
            'investors': "Not specified"
        }
    
    def is_valid_funding_data(self, funding_details):
        """Check if the extracted data is valid"""
        has_company = funding_details.get('company_name', 'Not specified') != 'Not specified'
        has_amount = funding_details.get('funding_amount', 'Not specified') != 'Not specified'
        return has_company and has_amount

    '''
    lets adda  function that writes, only correctly scraped companies to the stream
    That is, after the article is processed thorugh `enchaned_with_ai` (and succeeds), write it to the databse
    '''
