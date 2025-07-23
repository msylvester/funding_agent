#!/usr/bin/env python3
"""
URL Scraper Script

This script takes a URL as input, scrapes the content, and extracts structured 
funding data using AI enhancement, following the same schema as the MongoDB database.

Usage:
    python url_scraper.py <url>
    python url_scraper.py --url <url>
    python url_scraper.py --url <url> --save-to-db
"""

import argparse
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from typing import Dict, Any, Optional
import os
from urllib.parse import urlparse

# Import the AI enhancement method from techcrunch scraper
from techcrunch_fundraising_scraper import TechCrunchFundraisingScaper
from database import FundingDatabase

class URLScraper:
    def __init__(self):
        """Initialize the URL scraper with session and AI enhancer"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize the TechCrunch scraper to use its AI enhancement method
        self.ai_enhancer = TechCrunchFundraisingScaper()
    
    def scrape_url_content(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from the given URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        try:
            print(f"🌐 Scraping URL: {url}")
            
            # Make request to the URL
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic metadata
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            date = self._extract_date(soup, url)
            source = self._extract_source(url)
            
            # Create base data structure
            scraped_data = {
                'url': url,
                'title': title,
                'content': content,
                'date': date,
                'source': source,
                'scraped_at': datetime.utcnow().isoformat(),
                'is_recent': self._is_recent_date(date)
            }
            
            print(f"✅ Successfully scraped content from {source}")
            print(f"   Title: {title[:80]}{'...' if len(title) > 80 else ''}")
            print(f"   Content length: {len(content)} characters")
            
            return scraped_data
            
        except requests.RequestException as e:
            raise Exception(f"Error fetching URL {url}: {e}")
        except Exception as e:
            raise Exception(f"Error scraping URL {url}: {e}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from the page"""
        # Try multiple title selectors
        title_selectors = [
            'h1',
            'title',
            '.entry-title',
            '.post-title',
            '.article-title',
            '[data-testid="headline"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                return title_elem.get_text(strip=True)
        
        return "No title found"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try multiple content selectors
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content',
            'article',
            '.main-content',
            '[data-testid="article-content"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True, separator=' ')
                if len(content) > 100:  # Ensure we have substantial content
                    return content
        
        # Fallback: get all paragraph text
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return content if content else "No content found"
    
    def _extract_date(self, soup: BeautifulSoup, url: str) -> str:
        """Extract publication date from the page"""
        # Try multiple date selectors and attributes
        date_selectors = [
            'time[datetime]',
            '.date',
            '.published',
            '.post-date',
            '[data-testid="timestamp"]',
            'meta[property="article:published_time"]',
            'meta[name="date"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                # Try datetime attribute first
                date_value = date_elem.get('datetime') or date_elem.get('content')
                if date_value:
                    return date_value
                
                # Try text content
                date_text = date_elem.get_text(strip=True)
                if date_text:
                    return date_text
        
        # Fallback: use current date
        return datetime.utcnow().isoformat()
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Map common domains to readable names
        source_mapping = {
            'techcrunch.com': 'TechCrunch',
            'crunchbase.com': 'Crunchbase',
            'venturebeat.com': 'VentureBeat',
            'techstartups.com': 'Tech Startups',
            'bloomberg.com': 'Bloomberg',
            'reuters.com': 'Reuters',
            'wsj.com': 'Wall Street Journal',
            'forbes.com': 'Forbes'
        }
        
        for domain_key, source_name in source_mapping.items():
            if domain_key in domain:
                return source_name
        
        # Default: capitalize domain name
        return domain.replace('www.', '').replace('.com', '').title()
    
    def _is_recent_date(self, date_str: str) -> bool:
        """Check if the date is recent (within last 30 days)"""
        try:
            # Try to parse the date
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return True  # Default to recent if can't parse
            
            # Check if within last 30 days
            days_diff = (datetime.utcnow() - date_obj.replace(tzinfo=None)).days
            return days_diff <= 30
            
        except Exception:
            return True  # Default to recent if can't determine
    
    def enhance_with_ai(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to extract structured funding data from scraped content
        
        Args:
            scraped_data: Raw scraped data
            
        Returns:
            Enhanced data with structured funding information
        """
        try:
            print("🤖 Enhancing data with AI...")
            
            title = scraped_data.get('title', '')
            content = scraped_data.get('content', '')
            
            # Use the AI enhancement method from TechCrunch scraper
            enhanced_data = self.ai_enhancer.enhance_with_ai(title, content)
            
            if enhanced_data:
                # Merge the enhanced data with original scraped data
                final_data = {**scraped_data, **enhanced_data}
                
                # Ensure all required MongoDB schema fields are present
                final_data = self._ensure_schema_compliance(final_data)
                
                print("✅ AI enhancement completed successfully")
                print(f"   Company: {final_data.get('company_name', 'N/A')}")
                print(f"   Funding: {final_data.get('funding_amount', 'N/A')}")
                print(f"   Series: {final_data.get('series', 'N/A')}")
                
                return final_data
            else:
                print("⚠️  AI enhancement returned no structured data")
                return self._ensure_schema_compliance(scraped_data)
                
        except Exception as e:
            print(f"❌ Error during AI enhancement: {e}")
            return self._ensure_schema_compliance(scraped_data)
    
    def _ensure_schema_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the data complies with MongoDB schema
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Schema-compliant data dictionary
        """
        # Define the expected schema fields with defaults
        schema_fields = {
            'source': 'Unknown',
            'title': 'No title',
            'url': '',
            'date': datetime.utcnow().isoformat(),
            'content': '',
            'scraped_at': datetime.utcnow().isoformat(),
            'company_name': 'Not specified',
            'funding_amount': 'Not specified',
            'valuation': 'Not specified',
            'series': 'Not specified',
            'founded_year': 'Not specified',
            'total_funding': 'Not specified',
            'investors': 'Not specified',
            'description': 'Not specified',
            'is_recent': True
        }
        
        # Ensure all required fields are present
        for field, default_value in schema_fields.items():
            if field not in data or data[field] is None:
                data[field] = default_value
        
        return data
    
    def save_to_database(self, data: Dict[str, Any]) -> str:
        """
        Save the extracted data to MongoDB
        
        Args:
            data: Structured funding data
            
        Returns:
            ObjectId of the inserted document
        """
        try:
            print("💾 Saving to MongoDB database...")
            
            db = FundingDatabase()
            document_id = db.create_company(data)
            db.close_connection()
            
            print(f"✅ Successfully saved to database with ID: {document_id}")
            return document_id
            
        except Exception as e:
            raise Exception(f"Error saving to database: {e}")
    
    def save_to_json(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Save the extracted data to a JSON file
        
        Args:
            data: Structured funding data
            filename: Output filename (optional)
            
        Returns:
            Path to the saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"scraped_funding_data_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 Saved data to: {filename}")
            return filename
            
        except Exception as e:
            raise Exception(f"Error saving to JSON: {e}")

def main():
    """Main function to handle command line arguments and execute scraping"""
    
    parser = argparse.ArgumentParser(
        description="Scrape funding data from a URL using AI enhancement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python url_scraper.py https://techcrunch.com/2025/07/17/substack-raises-100m/
  python url_scraper.py --url https://example.com/funding-news --save-to-db
  python url_scraper.py --url https://example.com/news --output data.json
        """
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        help='URL to scrape (can also use --url flag)'
    )
    
    parser.add_argument(
        '--url',
        help='URL to scrape'
    )
    
    parser.add_argument(
        '--save-to-db',
        action='store_true',
        help='Save extracted data to MongoDB database'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON filename (default: auto-generated)'
    )
    
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Skip AI enhancement and only extract basic content'
    )
    
    args = parser.parse_args()
    
    # Get URL from positional argument or --url flag
    url = args.url or args.url
    if not url:
        parser.error("URL is required. Provide it as an argument or use --url flag.")
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print("🚀 Starting URL Scraping Process")
    print("=" * 50)
    print(f"Target URL: {url}")
    
    try:
        # Initialize scraper
        scraper = URLScraper()
        
        # Step 1: Scrape basic content
        scraped_data = scraper.scrape_url_content(url)
        
        # Step 2: Enhance with AI (unless disabled)
        if not args.no_ai:
            enhanced_data = scraper.enhance_with_ai(scraped_data)
        else:
            enhanced_data = scraper._ensure_schema_compliance(scraped_data)
            print("⚠️  AI enhancement skipped")
        
        # Step 3: Display results
        print("\n📊 Extracted Data Summary:")
        print("-" * 40)
        print(f"Company: {enhanced_data.get('company_name', 'N/A')}")
        print(f"Funding: {enhanced_data.get('funding_amount', 'N/A')}")
        print(f"Series: {enhanced_data.get('series', 'N/A')}")
        print(f"Source: {enhanced_data.get('source', 'N/A')}")
        print(f"Date: {enhanced_data.get('date', 'N/A')}")
        
        # Step 4: Save data
        if args.save_to_db:
            document_id = scraper.save_to_database(enhanced_data)
            print(f"\n🎉 Data saved to MongoDB with ID: {document_id}")
        
        # Always save to JSON as well
        json_file = scraper.save_to_json(enhanced_data, args.output)
        print(f"📄 Data also saved to: {json_file}")
        
        print("\n✅ Scraping process completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
