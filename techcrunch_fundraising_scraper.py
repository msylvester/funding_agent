import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse
import logging

class TechCrunchFundraisingScaper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://techcrunch.com"
        self.funding_data = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def is_funding_article(self, title):
        """Check if article title indicates funding news"""
        title_lower = title.lower()
        
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
            
            self.logger.info(f"Scraping page {page}: {url}")
            
            try:
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                articles = self.extract_articles_from_page(soup)
                
                if not articles:
                    self.logger.info(f"No articles found on page {page}, stopping")
                    break
                
                # Process each article
                for article in articles:
                    if self.is_funding_article(article['title']):
                        self.logger.info(f"Processing funding article: {article['title']}")
                        article_data = self.scrape_article_content(article['url'])
                        if article_data:
                            self.funding_data.append(article_data)
                        time.sleep(1)  # Be respectful to the server
                
                page += 1
                time.sleep(2)  # Delay between pages
                
            except Exception as e:
                self.logger.error(f"Error scraping page {page}: {e}")
                break
    
    def extract_articles_from_page(self, soup):
        """Extract article links and titles from the page"""
        articles = []
        
        # Look for article containers
        article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|entry'))
        
        if not article_elements:
            # Fallback: look for links that might be articles
            article_elements = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))
        
        for element in article_elements:
            try:
                # Try to find the title and URL
                title_element = element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|headline'))
                if not title_element:
                    title_element = element.find('a')
                
                if title_element:
                    if title_element.name == 'a':
                        title = title_element.get_text(strip=True)
                        url = title_element.get('href')
                    else:
                        link = title_element.find('a')
                        if link:
                            title = link.get_text(strip=True)
                            url = link.get('href')
                        else:
                            continue
                    
                    if url and title:
                        # Make URL absolute
                        if url.startswith('/'):
                            url = urljoin(self.base_url, url)
                        
                        # Skip if not a TechCrunch article
                        if 'techcrunch.com' not in url:
                            continue
                        
                        articles.append({
                            'title': title,
                            'url': url
                        })
            except Exception as e:
                self.logger.debug(f"Error extracting article: {e}")
                continue
        
        return articles
    
    def scrape_article_content(self, url):
        """Scrape individual article content"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_element = soup.find(['h1', 'h2'], class_=re.compile(r'title|headline|entry-title'))
            title = title_element.get_text(strip=True) if title_element else "N/A"
            
            # Extract content
            content_element = soup.find(['div', 'section'], class_=re.compile(r'content|entry-content|article-content'))
            content = ""
            if content_element:
                # Get text content, removing scripts and styles
                for script in content_element(["script", "style"]):
                    script.decompose()
                content = content_element.get_text(strip=True)
            
            # Extract date
            date_element = soup.find('time') or soup.find(class_=re.compile(r'date|time'))
            date = ""
            if date_element:
                date = date_element.get('datetime') or date_element.get_text(strip=True)
            
            # Extract funding details
            funding_details = self.extract_funding_details(title, content)
            
            article_data = {
                'source': 'TechCrunch Fundraising',
                'title': title,
                'url': url,
                'date': date,
                'content': content[:1000],  # Limit content length
                'scraped_at': datetime.now().isoformat(),
                **funding_details
            }
            
            return article_data
            
        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {e}")
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
            'is_recent': True,
            'is_unicorn': False,
            'unicorn_month': None,
            'unicorn_year': None
        }
    
    def save_to_json(self, filename='scraped_one.json'):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.funding_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.funding_data)} articles to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to {filename}: {e}")
    
    def run_scraper(self, max_pages=3):
        """Run the complete scraping process"""
        self.logger.info("Starting TechCrunch fundraising scraper...")
        self.scrape_fundraising_page(max_pages)
        
        if self.funding_data:
            self.save_to_json('scraped_one.json')
            self.logger.info(f"Scraping completed. Found {len(self.funding_data)} funding articles.")
        else:
            self.logger.warning("No funding articles found.")
        
        return self.funding_data

def main():
    scraper = TechCrunchFundraisingScaper()
    data = scraper.run_scraper(max_pages=3)
    
    print(f"\nScraping Summary:")
    print(f"Total articles scraped: {len(data)}")
    
    if data:
        print("\nSample articles:")
        for i, article in enumerate(data[:3], 1):
            print(f"{i}. {article['title']}")
            print(f"   Company: {article['company_name']}")
            print(f"   Funding: {article['funding_amount']}")
            print(f"   URL: {article['url']}")
            print()

if __name__ == "__main__":
    main()
