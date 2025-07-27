import requests
from bs4 import BeautifulSoup
import json
import time
from article_processor import ArticleProcessor
from database import FundingDatabase


class TechCrunchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://techcrunch.com"
        self.funding_data = []
        self.failed_funding_articles = []  # Track funding articles that failed validation
        self.processor = ArticleProcessor(self.session, self.base_url)
    
    
    def scrape_fundraising_page(self, max_pages=1):
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
                articles = self.processor.extract_articles_from_page(soup)
                if not articles:
                    print(f"No articles found on page {page}, stopping")
                    break
                
                # Process articles using the imported processor
                processed_count = 0
                max_articles_per_page = 10
                total_articles_funded = []
                
                for article in articles:
                    if processed_count >= max_articles_per_page:
                        break
                    if self.processor.is_funding_article(article['title']):
                        total_articles_funded.append(article['title'])
                        article_data = self.processor.scrape_article_content(article['url'])
                        
                        if article_data and self.processor.is_valid_funding_data(article_data):
                            self.funding_data.append(article_data)
                        else:
                            # Track failed funding articles
                            failed_article = {
                                'title': article['title'],
                                'url': article['url'],
                                'reason': 'No data extracted' if not article_data else f"Invalid data - Company: {article_data.get('company_name', 'None')}, Amount: {article_data.get('funding_amount', 'None')}"
                            }
                            self.failed_funding_articles.append(failed_article)
                            
                            if article_data:
                                print(f"❌ Failed validation: {article_data.get('company_name', 'No company')} - {article_data.get('funding_amount', 'No amount')}")
                            else:
                                print(f"❌ Failed to scrape content from {article['url']}")
                        
                        processed_count += 1
                        time.sleep(1)  # Rate limiting

                page += 1
                time.sleep(2)  # Delay between pages
                print(f'Page {page-1}: Found {len(total_articles_funded)} funding articles')
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break
    
    
    def save_to_json(self, filename='techcrunch_minimal.json'):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.funding_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.funding_data)} articles to {filename}")
        except Exception as e:
            print(f"Error saving to {filename}: {e}")

    def write(self):
        # make  GET
        # compare count of result of GET with the self.funding_data
        # if self.funding_data larger 
        # write the new elements to the db 
        pass
    
    def run_scraper(self, max_pages=1):
        """Run the complete scraping process"""
        print("Starting minimal TechCrunch scraper...")
        self.scrape_fundraising_page(max_pages)
        
        print(f"\n📊 Scraping Summary:")
        print(f"Total articles that passed title filtering: {len(self.failed_funding_articles) + len(self.funding_data)}")
        print(f"Articles that failed validation: {len(self.failed_funding_articles)}")
        print(f"Articles successfully saved: {len(self.funding_data)}")
        
        if self.funding_data:
            self.save_to_json()
            print(f"\n✅ Scraping completed. Found {len(self.funding_data)} funding articles.")
            print(f"💾 Data saved to techcrunch_minimal.json")
        else:
            print("\n❌ No valid funding articles found to save to JSON.")
            if self.failed_funding_articles:
                print("However, some articles were identified as funding but failed validation:")
                for failed in self.failed_funding_articles[:3]:  # Show first 3
                    print(f"  • {failed['title'][:80]}...")
                if len(self.failed_funding_articles) > 3:
                    print(f"  ... and {len(self.failed_funding_articles) - 3} more")
        
        return self.funding_data


def main():
    scraper = TechCrunchScraper()
    data = scraper.run_scraper(max_pages=1)
    return data


if __name__ == "__main__":
    main()
