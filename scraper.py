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
    
    def scrape_techcrunch_funding(self, load_more_clicks=3):
        """Improved TechCrunch scraping with better content filtering and dynamic loading"""
        print("Scraping TechCrunch funding news...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            url = "https://techcrunch.com/category/fundraising/"
            print(f"Scraping URL: {url}")
            
            try:
                response = page.goto(url, wait_until='networkidle')
                print(f"TechCrunch status: {response.status}")
                
                # Wait for initial content to load
                page.wait_for_timeout(3000)
                
                # Try to click "Load More" button multiple times to get more articles
                for i in range(load_more_clicks):
                    try:
                        load_more_button = page.locator('text="Load More"').first
                        if load_more_button.is_visible():
                            load_more_button.click()
                            page.wait_for_timeout(2000)  # Wait for new content to load
                            print(f"Clicked Load More button {i+1} times")
                        else:
                            print("Load More button not found or not visible")
                            break
                    except Exception as e:
                        print(f"Error clicking Load More: {e}")
                        break
                
                # Get page content after loading more articles
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find articles with more specific selectors
                articles = soup.find_all('article') or soup.find_all('div', class_='post-block')
                
                print(f"Found {len(articles)} total articles")
                
                relevant_articles = 0
                for article in articles:
                    # Get title with better selectors
                    title_elem = (article.find('h2', class_='post-block__title') or
                                 article.find('h3') or
                                 article.find('h2') or
                                 article.find('a'))
                    
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    
                    # Skip if title is too short
                    if not title or len(title) < 20:
                        continue
                    
                    # Apply relevance filtering
                    if not self.is_relevant_funding_article(title):
                        continue
                    
                    # Get article content for better extraction
                    content_elem = article.find('div', class_='post-block__content')
                    article_content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    # Extract funding details
                    details = self.extract_funding_details(title, article_content)
                    if not details or not details['company'] or not details['amount']:
                        continue
                    
                    # Get link
                    link = None
                    if title_elem.name == 'a':
                        link = title_elem.get('href')
                    else:
                        link_elem = title_elem.find('a')
                        link = link_elem.get('href') if link_elem else None
                    
                    # Make sure link is absolute
                    if link and link.startswith('/'):
                        link = f"https://techcrunch.com{link}"
                    
                    # Get date
                    date_elem = article.find('time')
                    date = date_elem.get('datetime') if date_elem else None
                    
                    self.funding_data.append({
                        'source': 'TechCrunch',
                        'title': title,
                        'url': link,
                        'date': date,
                        'scraped_at': datetime.now().isoformat(),
                        'company_name': details['company'],
                        'funding_amount': details['amount'],
                        'funder': details['funder'],
                        'is_recent': self.is_recent_funding(date)
                    })
                    relevant_articles += 1
                    print(f"✓ Selected: {details['company']} - {details['amount']}")
                
                print(f"Selected {relevant_articles} relevant funding articles out of {len(articles)} total")
                
            except Exception as e:
                print(f"Error scraping TechCrunch: {e}")
            
            browser.close()
    
    def scrape_crunchbase_news(self):
        """Scrape Crunchbase news with improved filtering"""
        print("Scraping Crunchbase news...")
        
        url = "https://news.crunchbase.com/news-type/funding/"
        
        try:
            response = self.session.get(url)
            print(f"Crunchbase status: {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = (soup.find_all('article', class_='post') or
                       soup.find_all('article') or
                       soup.find_all('div', class_='post'))
            
            print(f"Found {len(articles)} Crunchbase articles")
            
            relevant_articles = 0
            for article in articles[:20]:
                title_elem = article.find('h2') or article.find('h3') or article.find('h1')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if not title or not self.is_relevant_funding_article(title):
                    continue
                    
                link_elem = title_elem.find('a')
                link = link_elem.get('href') if link_elem else None
                
                date_elem = article.find('time')
                date = date_elem.get('datetime') if date_elem else None
                
                content_elem = article.find('div', class_='entry-content') or article.find('div', class_='content')
                article_content = content_elem.get_text(strip=True) if content_elem else ""
                
                details = self.extract_funding_details(title, article_content)
                if not details or not details['company'] or not details['amount']:
                    continue
                
                self.funding_data.append({
                    'source': 'Crunchbase News',
                    'title': title,
                    'url': link,
                    'date': date,
                    'scraped_at': datetime.now().isoformat(),
                    'company_name': details['company'],
                    'funding_amount': details['amount'],
                    'funder': details['funder'],
                    'is_recent': self.is_recent_funding(date)
                })
                relevant_articles += 1
                print(f"✓ Selected Crunchbase: {details['company']} - {details['amount']}")
            
            print(f"Selected {relevant_articles} relevant Crunchbase articles")
                
        except Exception as e:
            print(f"Error scraping Crunchbase: {e}")
    
    def scrape_tech_startups(self):
        """Scrape Tech Startups funding news with improved filtering"""
        print("Scraping Tech Startups...")
        
        url = "https://techstartups.com/category/funding/"
        print(f"Scraping URL: {url}")
        
        try:
            response = self.session.get(url)
            print(f"Tech Startups status: {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')
            print(f"Found {len(articles)} Tech Startups articles")
            
            relevant_articles = 0
            for article in articles[:15]:
                title_elem = article.find('h2') or article.find('h3') or article.find('h1')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if not title or not self.is_relevant_funding_article(title):
                    continue
                    
                link_elem = title_elem.find('a')
                link = link_elem.get('href') if link_elem else None
                
                date_elem = article.find('time')
                date = date_elem.get('datetime') if date_elem else None
                
                content_elem = article.find('div', class_='entry-content') or article.find('div', class_='content')
                article_content = content_elem.get_text(strip=True) if content_elem else ""
                
                details = self.extract_funding_details(title, article_content)
                if not details or not details['company'] or not details['amount']:
                    continue
                
                self.funding_data.append({
                    'source': 'Tech Startups',
                    'title': title,
                    'url': link,
                    'date': date,
                    'scraped_at': datetime.now().isoformat(),
                    'company_name': details['company'],
                    'funding_amount': details['amount'],
                    'funder': details['funder'],
                    'is_recent': self.is_recent_funding(date)
                })
                relevant_articles += 1
                print(f"✓ Selected Tech Startups: {details['company']} - {details['amount']}")
            
            print(f"Selected {relevant_articles} relevant Tech Startups articles")
                
        except Exception as e:
            print(f"Error scraping Tech Startups: {e}")
    
    def is_relevant_funding_article(self, title):
        """Filter for relevant funding articles based on selection criteria"""
        title_lower = title.lower()
        
        # Skip promotional/event articles
        skip_keywords = [
            'techcrunch all stage', 'techcrunch disrupt', 'event', 'conference',
            'save up to', 'ticket', 'register', 'learn how', 'brings', 'shares',
            'days until', 'kicks off', 'playbook', 'strategy', 'conversation',
            'prep for', 'must-see', 'powerhouse', 'newsletter', 'podcast'
        ]
        
        if any(keyword in title_lower for keyword in skip_keywords):
            return False
        
        # Skip spinoff/subsidiary articles
        spinoff_keywords = ['spinoff', 'subsidiary', 'division']
        if any(keyword in title_lower for keyword in spinoff_keywords):
            return False
        
        # Skip rumor/talks articles
        rumor_keywords = ['in talks', 'reportedly', 'rumored', 'allegedly', 'sources say']
        if any(keyword in title_lower for keyword in rumor_keywords):
            return False
        
        # Skip well-established mega companies (focus on startups)
        mega_company_keywords = ['spacex', 'tesla', 'apple', 'google', 'microsoft', 'amazon', 'meta']
        if any(keyword in title_lower for keyword in mega_company_keywords):
            return False
        
        # Must contain funding indicators
        funding_keywords = [
            'raises', 'raised', 'funding', 'series a', 'series b', 'series c',
            'seed', 'round', 'million', 'billion', 'investment', 'capital'
        ]
        
        if not any(keyword in title_lower for keyword in funding_keywords):
            return False
        
        # Must be completed funding (not just talks)
        completed_keywords = ['raises', 'raised', 'secures', 'closes', 'gets']
        if not any(keyword in title_lower for keyword in completed_keywords):
            return False
        
        return True
    
    def extract_funding_details(self, title, content=""):
        """Extract funding amount, company name, and funder from title and content"""
        
        # Improved amount patterns
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)',
            r'(\d+(?:\.\d+)?)\s*million',
            r'(\d+(?:\.\d+)?)\s*billion',
            r'raises\s+\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)?',
            r'raised\s+\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)?'
        ]
        
        amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2 and match.group(2):
                    amount = f"${match.group(1)} {match.group(2)}"
                else:
                    amount = f"${match.group(1)} million"
                break
        
        # Extract company name (improved patterns)
        company_patterns = [
            r'^([^,]+?)\s+raises',
            r'^([^,]+?)\s+raised',
            r'^([A-Za-z0-9\s&.-]+?)\s+(?:raises|raised|gets|secures)',
            r'^([^,]+)'
        ]
        
        company = None
        for pattern in company_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up common prefixes
                company = re.sub(r'^(startup|company)\s+', '', company, flags=re.IGNORECASE)
                break
        
        # Extract funder/investor information
        funder_patterns = [
            r'led by ([^,]+)',
            r'from ([^,]+)',
            r'investors? include ([^,]+)',
            r'backed by ([^,]+)',
            r'funding from ([^,]+)'
        ]
        
        funder = None
        search_text = f"{title} {content}"
        for pattern in funder_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                funder = match.group(1).strip()
                break
        
        return {
            'company': company,
            'amount': amount,
            'funder': funder
        }
    
    def process_funding_data(self):
        """Process and enrich the scraped data"""
        print("Processing funding data...")
        
        # Data is already processed during scraping, just return it
        return self.funding_data
    
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
        
        # Scrape different sources with improved filtering
        self.scrape_techcrunch_funding(load_more_clicks=3)
        time.sleep(3)
        
        self.scrape_crunchbase_news()
        time.sleep(3)
        
        self.scrape_tech_startups()
        
        print(f"\nTotal relevant articles scraped: {len(self.funding_data)}")
        
        # Save data
        df = self.save_to_csv()
        self.save_to_json()
        
        # Show recent funding summary
        if not df.empty and 'is_recent' in df.columns:
            recent_funding = df[df['is_recent'] == True]
            print(f"\nFound {len(recent_funding)} recent funding announcements")
            
            # Show selected articles
            print("\nSelected Funding Articles:")
            for _, row in df.iterrows():
                print(f"✓ {row['company_name']}: {row['funding_amount']} ({row['source']})")
        else:
            print("\nNo funding data found to analyze")
            recent_funding = pd.DataFrame()
        
        return df

# Usage example
if __name__ == "__main__":
    scraper = FundingScraper()
    
    # Run the scraper
    funding_df = scraper.run_scraper()
    
    # Display selected funding
    if not funding_df.empty:
        print(f"\nSuccessfully selected {len(funding_df)} relevant funding articles")
    else:
        print("\nNo relevant funding announcements found")
