import requests
from bs4 import BeautifulSoup
import json
import time
from process_the_scrape import ArticleProcessor


class TechCrunchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://techcrunch.com"
        self.funding_data = []
        self.processor = ArticleProcessor(self.session, self.base_url)
    
    
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
                articles = self.processor.extract_articles_from_page(soup)
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
                        
                #     if self.processor.is_funding_article(article['title']):
                #         article_data = self.processor.scrape_article_content(article['url'])
                        
                #         if article_data and self.processor.is_valid_funding_data(article_data):
                #             self.funding_data.append(article_data)
                        
                #         processed_count += 1
                #         time.sleep(1)  # Rate limiting
                
                # page += 1
                # time.sleep(2)  # Delay between pages
                
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
