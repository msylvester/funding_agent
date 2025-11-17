import re
import os
import json
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
'''
Start of custom services
'''
from services.agents.custom.agents.agent_007 import is_funding_article_ai
from services.agents.custom.agents.agent_blog_data_struct import enhance_with_ai
from services.database.database import FundingDatabase


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
    
    def scrape_article_content(self, url, auto_save=True):
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
            
            # Extract content with more comprehensive selectors
            content = ""
            content_selectors = [
                '.entry-content', 
                '[class*="content"]', 
                '.article-content',
                'main',
                'article', 
                '[class*="post"]',
                '[class*="blog"]',
                '.prose',
                '[role="main"]'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # Remove scripts and styles
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    content = content_element.get_text(strip=True)
                    print(f"Content extracted using selector '{selector}': {len(content)} characters")
                    break
            
            # Fallback: try to get content from body if no specific content area found
            if not content:
                body = soup.find('body')
                if body:
                    # Remove navigation, footer, sidebar elements
                    for element in body(['nav', 'footer', 'aside', 'header', 'script', 'style']):
                        element.decompose()
                    content = body.get_text(strip=True)
                    print(f"Content extracted using body fallback: {len(content)} characters")
            
            print(f"Final content preview (first 200 chars): {content[:200]}...")
            
            # Extract date with multiple strategies
            date = ""
            
            # Strategy 1: Look for <time> element
            date_element = soup.find('time')
            if date_element:
                date = date_element.get('datetime') or date_element.get_text(strip=True)
                print(f"Date extracted from <time> element: {date}")
            
            # Strategy 2: Look for comprehensive date selectors
            if not date:
                date_selectors = [
                    # Generic class patterns (case-insensitive)
                    '[class*="date" i]',
                    '[class*="Date" i]', 
                    '[class*="publish" i]',
                    '[class*="Publish" i]',
                    '[class*="time" i]',
                    '[class*="Time" i]',
                    
                    # Specific element types with date classes
                    'p[class*="date" i]',
                    'p[class*="Date" i]', 
                    'p[class*="publish" i]',
                    'p[class*="Publish" i]',
                    'span[class*="date" i]',
                    'span[class*="Date" i]',
                    'div[class*="date" i]',
                    'div[class*="Date" i]',
                    
                    # Common class names
                    '.post-date',
                    '.publish-date', 
                    '.article-date',
                    '.published-date',
                    '.date-published',
                    '.post-meta',
                    '.article-meta',
                    '.entry-date',
                    '.timestamp'
                ]
                
                for selector in date_selectors:
                    date_element = soup.select_one(selector)
                    if date_element:
                        date = date_element.get_text(strip=True)
                        print(f"Date extracted from selector '{selector}': {date}")
                        break
            
            # Strategy 3: Look for structured data and meta tags
            if not date:
                # First try JSON-LD structured data
                json_ld_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_ld_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        
                        # Handle single object or array
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        
                        # Look for common date fields
                        date_fields = ['datePublished', 'publishedDate', 'dateCreated', 'date']
                        for field in date_fields:
                            if field in data:
                                date = data[field]
                                print(f"Date extracted from JSON-LD '{field}': {date}")
                                break
                        
                        if date:
                            break
                            
                    except (json.JSONDecodeError, AttributeError, TypeError):
                        continue
                
                # Then try meta tags if JSON-LD didn't work
                if not date:
                    meta_selectors = [
                        'meta[property="article:published_time"]',
                        'meta[property="article:published"]',
                        'meta[name="publish-date"]',
                        'meta[name="date"]',
                        'meta[name="publishdate"]',
                        'meta[name="DC.date"]',
                        'meta[name="dcterms.created"]',
                        'meta[property="og:updated_time"]',
                        'meta[name="twitter:data1"]'
                    ]
                    
                    for selector in meta_selectors:
                        meta_element = soup.select_one(selector)
                        if meta_element:
                            date = meta_element.get('content', '')
                            print(f"Date extracted from meta tag '{selector}': {date}")
                            break
            
            # Strategy 4: Regex pattern matching in content
            if not date:
                import re
                
                # Search in a focused area first (title + first 1000 chars)
                search_text = f"{title} {content[:1000]}"
                
                date_patterns = [
                    # Full month names: "September 3, 2025", "Sep 3, 2025"
                    r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                    
                    # Numeric formats: "2025-09-03", "09/03/2025", "03/09/2025"
                    r'\b\d{4}-\d{2}-\d{2}\b',
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    
                    # European format: "3 September 2025"
                    r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
                    r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, search_text, re.IGNORECASE)
                    if match:
                        date = match.group(0)
                        print(f"Date extracted from regex pattern '{pattern}': {date}")
                        break
            
            # Strategy 5: Date normalization and formatting
            if date:
                date = self._normalize_date(date)
                print(f"Normalized date: '{date}'")
            
            print(f"Final extracted date: '{date}'")
            
            # Try AI enhancement first, fall back to regex if needed
            if self.openrouter_api_key:
                print(f"ArticleProcessor: Calling AI with title='{title}' and {len(content)} chars of content")
                ai_funding_details = enhance_with_ai(title, content, self.openrouter_api_key)
                print(f"ArticleProcessor: AI returned: {ai_funding_details}")
                if ai_funding_details and ai_funding_details.get('company_name') != 'Not specified':
                    article_data = {
                        'source': 'Blog',
                        'title': title,
                        'url': url,
                        'date': date,
                        'content': content[:500] if content else "",
                        'scraped_at': datetime.now().isoformat(),
                        **ai_funding_details
                    }
                    
                    # Write successfully processed company to database
                    if auto_save:
                        self.write_company_to_db(article_data)
                    
                    return article_data
            
            # Fallback to regex extraction
            print(f"ArticleProcessor: AI failed, falling back to regex extraction")
            funding_details = self.extract_funding_details(title, content)
            print(f"ArticleProcessor: Regex extracted: {funding_details}")
            
            article_data = {
                'source': 'TechCrunch',
                'title': title,
                'url': url,
                'date': date,
                'content': content[:500] if content else "",
                'scraped_at': datetime.now().isoformat(),
                **funding_details
            }
            
            # Write to database if we have valid funding data
            if auto_save and self.is_valid_funding_data(funding_details):
                self.write_company_to_db(article_data)
            
            return article_data
            
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

        # Extract company name with improved patterns
        company_name = "Not specified"
        company_patterns = [
            # Pattern for "Company lands/raises/secures $X"
            r'^([A-Z][a-zA-Z\s&.-]+?)\s+(?:lands|raises|raised|closes|closed|secures|secured|gets)',
            # Pattern for "Company raises" at start
            r'^([A-Z][a-zA-Z\s&.-]+?)\s+(?:raises|raised|closes|closed)',
            # Pattern for "startup/company NAME raises"
            r'(?:startup|company)\s+([A-Z][a-zA-Z\s&.-]+?)\s+(?:raises|raised|closes|closed)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, title)
            if match:
                company_name = match.group(1).strip()
                # Clean up common prefixes
                company_name = re.sub(r'\b(?:startup|company|the)\b', '', company_name, flags=re.IGNORECASE).strip()
                if len(company_name.split()) <= 4:  # Reasonable company name length (increased from 3 to 4)
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

    def _normalize_date(self, date_str):
        """Normalize various date formats to a consistent format"""
        if not date_str or date_str.strip() == '':
            return ''
        
        try:
            from datetime import datetime
            import re
            
            # Clean up the date string
            date_str = date_str.strip()
            
            # Remove common prefixes/suffixes
            date_str = re.sub(r'^(Published|Posted|Date)(\s+ON)?\s*:?\s*', '', date_str, flags=re.IGNORECASE)
            date_str = re.sub(r'^(PUBLISHED|POSTED|DATE)(\s+ON)?\s*', '', date_str, flags=re.IGNORECASE)
            date_str = re.sub(r'\s*(UTC|GMT|EST|PST).*$', '', date_str, flags=re.IGNORECASE)
            
            # Try to parse various formats
            date_formats = [
                '%B %d, %Y',          # September 3, 2025
                '%b %d, %Y',          # Sep 3, 2025  
                '%Y-%m-%d',           # 2025-09-03
                '%m/%d/%Y',           # 09/03/2025
                '%d/%m/%Y',           # 03/09/2025
                '%d %B %Y',           # 3 September 2025
                '%d %b %Y',           # 3 Sep 2025
                '%Y-%m-%dT%H:%M:%S',  # ISO format
                '%Y-%m-%dT%H:%M:%SZ', # ISO with Z
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # Return in a consistent format: "Sep 3, 2025"
                    return parsed_date.strftime('%b %d, %Y')
                except ValueError:
                    continue
            
            # If no format matches, try to extract just the date part from complex strings
            # Look for recognizable date patterns
            import re
            date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b', date_str, re.IGNORECASE)
            if date_match:
                return date_match.group(0)
            
            # If all else fails, return cleaned original
            return date_str
            
        except Exception as e:
            print(f"Date normalization error: {e}")
            return date_str

    def write_company_to_db(self, company_data):
        """
        Write successfully scraped company to MongoDB database
        Only writes if the company isn't already in the database
        
        Args:
            company_data: Dictionary containing company funding information
            
        Returns:
            str or None: The ObjectId of the created document as string, or None if not created
        """
        try:
            # Initialize database connection
            db = FundingDatabase()
            
            # Check if company already exists in database
            company_name = company_data.get('company_name', '')
            url = company_data.get('url', '')
            
            if not company_name or company_name == 'Not specified':
                print(f"Skipping database write - no valid company name")
                db.close_connection()
                return None
            
            # Check for existing records by company name and URL
            existing_companies = db.read_companies_by_name(company_name)
            
            # Check if this exact article already exists (by URL)
            if url:
                for existing in existing_companies:
                    if existing.get('url') == url:
                        print(f"Company {company_name} with URL {url} already exists in database")
                        db.close_connection()
                        return None
            
            # If no duplicate found, create new record
            company_id = db.create_company(company_data)
            print(f"Successfully wrote {company_name} to database with ID: {company_id}")
            
            db.close_connection()
            return company_id
            
        except Exception as e:
            print(f"Error writing company to database: {e}")
            return None
