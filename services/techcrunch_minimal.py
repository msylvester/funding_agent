import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from urllib.parse import urljoin


class TechCrunchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://techcrunch.com"
        self.funding_data = []
    
    def is_funding_article(self, title):
        """Check if article title indicates funding news"""
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
    
    def scrape_fundraising_page(self, max_pages=3):
        """Scrape the TechCrunch fundraising category pages"""
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
                print(f'the articles are {articles}')
                if not articles:
                    print(f"No articles found on page {page}, stopping")
                    break
                return
                
                # # Process articles
                # processed_count = 0
                # max_articles_per_page = 10
                
                # for article in articles:
                #     if processed_count >= max_articles_per_page:
                #         break
                        
                #     if self.is_funding_article(article['title']):
                #         article_data = self.scrape_article_content(article['url'])
                        
                #         if article_data and self.is_valid_funding_data(article_data):
                #             self.funding_data.append(article_data)
                        
                #         processed_count += 1
                #         time.sleep(1)  # Rate limiting
                
                # page += 1
                # time.sleep(2)  # Delay between pages
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break
    
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
            
            # Extract funding details
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
    
    def save_to_json(self, filename='techcrunch_minimal.json'):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.funding_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.funding_data)} articles to {filename}")
        except Exception as e:
            print(f"Error saving to {filename}: {e}")
    
    def run_scraper(self, max_pages=3):
        """Run the complete scraping process"""
        print("Starting minimal TechCrunch scraper...")
        self.scrape_fundraising_page(max_pages)
        
        if self.funding_data:
            self.save_to_json()
            print(f"Scraping completed. Found {len(self.funding_data)} funding articles.")
        else:
            print("No funding articles found.")
        
        return self.funding_data


def main():
    scraper = TechCrunchScraper()
    data = scraper.run_scraper(max_pages=3)
    return data


if __name__ == "__main__":
    main()
