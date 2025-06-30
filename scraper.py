import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import re
from playwright.sync_api import sync_playwright

class FundingScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.funding_data = []
        self.playwright = None
        self.browser = None
    
    def scrape_techcrunch_funding(self, pages=5):
        """Scrape TechCrunch funding news using Playwright"""
        print("Scraping TechCrunch funding news...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for page_num in range(1, pages + 1):
                url = f"https://techcrunch.com/category/fundraising/page/{page_num}/"
                print(f"Scraping URL: {url}")
                
                try:
                    response = page.goto(url, wait_until='networkidle')
                    print(f"TechCrunch page {page_num} status: {response.status}")
                    
                    # Wait for content to load
                    page.wait_for_selector('article, .post-block', timeout=10000)
                    
                    # Get page content
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Try multiple selectors for articles
                    articles = (soup.find_all('article') or 
                               soup.find_all('div', class_='post-block') or
                               soup.find_all('li'))
                    
                    print(f"Found {len(articles)} articles on page {page_num}")
                    
                    for article in articles:
                        # Try multiple selectors for title
                        title_elem = (article.find('h3') or
                                     article.find('h2') or
                                     article.find('h1') or
                                     article.find('a'))
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        if not title or len(title) < 10:  # Skip very short titles
                            continue
                            
                        link = None
                        if title_elem.name == 'a':
                            link = title_elem.get('href')
                        else:
                            link_elem = title_elem.find('a')
                            link = link_elem.get('href') if link_elem else None
                        
                        # Make sure link is absolute
                        if link and link.startswith('/'):
                            link = f"https://techcrunch.com{link}"
                        
                        # All articles in fundraising category are funding-related
                        date_elem = article.find('time')
                        date = date_elem.get('datetime') if date_elem else None
                        
                        self.funding_data.append({
                            'source': 'TechCrunch',
                            'title': title,
                            'url': link,
                            'date': date,
                            'scraped_at': datetime.now().isoformat()
                        })
                        print(f"Found funding article: {title[:50]}...")
                    
                    time.sleep(2)  # Be respectful to the server
                    
                except Exception as e:
                    print(f"Error scraping TechCrunch page {page_num}: {e}")
            
            browser.close()
    
    def scrape_crunchbase_news(self):
        """Scrape Crunchbase news (requires API key for full access)"""
        print("Scraping Crunchbase news...")
        
        # Note: For full Crunchbase data, you'd need their API
        # This is a simplified version for their public news
        url = "https://news.crunchbase.com/news-type/funding/"
        
        try:
            response = self.session.get(url)
            print(f"Crunchbase status: {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for articles
            articles = (soup.find_all('article', class_='post') or
                       soup.find_all('article') or
                       soup.find_all('div', class_='post'))
            
            print(f"Found {len(articles)} Crunchbase articles")
            
            for article in articles[:20]:  # Limit to recent articles
                title_elem = article.find('h2') or article.find('h3') or article.find('h1')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if not title:
                    continue
                    
                link_elem = title_elem.find('a')
                link = link_elem.get('href') if link_elem else None
                
                date_elem = article.find('time')
                date = date_elem.get('datetime') if date_elem else None
                
                self.funding_data.append({
                    'source': 'Crunchbase News',
                    'title': title,
                    'url': link,
                    'date': date,
                    'scraped_at': datetime.now().isoformat()
                })
                print(f"Found Crunchbase article: {title[:50]}...")
                
        except Exception as e:
            print(f"Error scraping Crunchbase: {e}")
    
    def scrape_tech_startups(self):
        """Scrape Tech Startups funding news"""
        print("Scraping Tech Startups...")
        
        url = "https://techstartups.com/category/funding/"
        print(f"Scraping URL: {url}")
        
        try:
            response = self.session.get(url)
            print(f"Tech Startups status: {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')
            print(f"Found {len(articles)} Tech Startups articles")
            
            for article in articles[:15]:
                title_elem = article.find('h2') or article.find('h3') or article.find('h1')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if not title:
                    continue
                    
                link_elem = title_elem.find('a')
                link = link_elem.get('href') if link_elem else None
                
                date_elem = article.find('time')
                date = date_elem.get('datetime') if date_elem else None
                
                self.funding_data.append({
                    'source': 'Tech Startups',
                    'title': title,
                    'url': link,
                    'date': date,
                    'scraped_at': datetime.now().isoformat()
                })
                print(f"Found Tech Startups article: {title[:50]}...")
                
        except Exception as e:
            print(f"Error scraping Tech Startups: {e}")
    
    def extract_funding_details(self, title):
        """Extract funding amount and company name from title"""
        # Regex patterns for common funding formats
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)',
            r'(\d+(?:\.\d+)?)\s*million',
            r'(\d+(?:\.\d+)?)\s*billion'
        ]
        
        amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    amount = f"${match.group(1)} {match.group(2)}"
                else:
                    amount = f"${match.group(1)} million"
                break
        
        # Extract company name (usually at the beginning)
        company_match = re.match(r'^([^,]+)', title)
        company = company_match.group(1).strip() if company_match else None
        
        return {
            'company': company,
            'amount': amount
        }
    
    def process_funding_data(self):
        """Process and enrich the scraped data"""
        print("Processing funding data...")
        
        processed_data = []
        for item in self.funding_data:
            details = self.extract_funding_details(item['title'])
            
            processed_item = {
                **item,
                'company_name': details['company'],
                'funding_amount': details['amount'],
                'is_recent': self.is_recent_funding(item['date'])
            }
            processed_data.append(processed_item)
        
        return processed_data
    
    def is_recent_funding(self, date_str, days=7):
        """Check if funding is within specified days"""
        if not date_str:
            return False
            
        try:
            funding_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            cutoff_date = datetime.now() - timedelta(days=days)
            return funding_date >= cutoff_date
        except:
            return False
    
    def save_to_csv(self, filename='funding_data.csv'):
        """Save data to CSV file"""
        processed_data = self.process_funding_data()
        df = pd.DataFrame(processed_data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return df
    
    def save_to_json(self, filename='funding_data.json'):
        """Save data to JSON file"""
        processed_data = self.process_funding_data()
        with open(filename, 'w') as f:
            json.dump(processed_data, f, indent=2)
        print(f"Data saved to {filename}")
    
    def run_scraper(self):
        """Run the complete scraping process"""
        print("Starting funding data scraper...")
        
        # Scrape different sources
        self.scrape_techcrunch_funding(pages=3)
        time.sleep(3)
        
        self.scrape_crunchbase_news()
        time.sleep(3)
        
        self.scrape_tech_startups()
        
        print(f"Scraped {len(self.funding_data)} articles")
        
        # Save data
        df = self.save_to_csv()
        self.save_to_json()
        
        # Show recent funding summary
        if not df.empty and 'is_recent' in df.columns:
            recent_funding = df[df['is_recent'] == True]
            print(f"\nFound {len(recent_funding)} recent funding announcements")
        else:
            print("\nNo funding data found to analyze")
            recent_funding = pd.DataFrame()
        
        return df

# Usage example
if __name__ == "__main__":
    scraper = FundingScraper()
    
    # Run the scraper
    funding_df = scraper.run_scraper()
    
    # Display recent funding
    if not funding_df.empty and 'is_recent' in funding_df.columns:
        recent_funding = funding_df[funding_df['is_recent'] == True]
        print("\nRecent Funding Announcements:")
        for _, row in recent_funding.iterrows():
            print(f"- {row['company_name']}: {row['funding_amount']} ({row['source']})")
    else:
        print("\nNo recent funding announcements found")
