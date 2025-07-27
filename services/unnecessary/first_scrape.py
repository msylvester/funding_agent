import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any


async def scrape_techcrunch_fundraising() -> List[Dict[str, Any]]:
    """
    Scrape fundraising articles from TechCrunch fundraising category page using Playwright.
    
    Returns:
        List of dictionaries containing article data
    """
    url = "https://techcrunch.com/category/fundraising/"
    
    async with async_playwright() as p:
        try:
            # Launch browser (headless by default)
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent to avoid blocking
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Navigate to the page
            await page.goto(url, wait_until='networkidle')
            
            # Wait a bit more for dynamic content to load
            await page.wait_for_timeout(3000)
            
            # Get the page content after JavaScript execution
            content = await page.content()
            
            # Close browser
            await browser.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            articles = []
            
            # Debug: Print some of the soup to see structure
            print("=== SOUP SAMPLE ===")
            print(soup.prettify()[:1000])
            print("=== END SAMPLE ===")
            
            # Try multiple selectors to find articles
            article_elements = (
                soup.find_all('article') or
                soup.find_all('div', class_='post-block') or
                soup.find_all('div', attrs={'data-module': 'PostBlock'}) or
                soup.find_all('div', class_='wp-block-tc23-post-picker') or
                soup.find_all('h2', class_='post-block__title') or
                soup.find_all('h3') or
                soup.find_all('a', href=lambda x: x and '/2024/' in x)  # Links with 2024 in URL
            )
            
            print(f"Found {len(article_elements)} article elements")
            
            for article in article_elements:
                article_data = {}
                
                # Extract title - try multiple approaches
                title_element = (
                    article.find('h2') or 
                    article.find('h3') or 
                    article.find('a', href=True)
                )
                
                if title_element:
                    if title_element.name in ['h2', 'h3']:
                        title_link = title_element.find('a')
                        if title_link:
                            article_data['title'] = title_link.get_text(strip=True)
                            article_data['url'] = title_link.get('href')
                        else:
                            article_data['title'] = title_element.get_text(strip=True)
                    else:  # It's an 'a' tag
                        article_data['title'] = title_element.get_text(strip=True)
                        article_data['url'] = title_element.get('href')
                
                # Extract excerpt/description
                excerpt_element = (
                    article.find('div', class_='post-block__content') or
                    article.find('p') or
                    article.find('div', class_='excerpt')
                )
                if excerpt_element:
                    article_data['excerpt'] = excerpt_element.get_text(strip=True)
                
                # Extract author
                author_element = (
                    article.find('span', class_='river-byline__authors') or
                    article.find('span', class_='author') or
                    article.find('div', class_='byline')
                )
                if author_element:
                    article_data['author'] = author_element.get_text(strip=True)
                
                # Extract date
                date_element = article.find('time')
                if date_element:
                    article_data['date'] = date_element.get('datetime') or date_element.get_text(strip=True)
                
                # Only add if we have at least a title
                if 'title' in article_data and article_data['title']:
                    articles.append(article_data)
            
            return articles
            
        except Exception as e:
            print(f"Error scraping TechCrunch: {e}")
            return []


def print_scraped_data(articles: List[Dict[str, Any]]) -> None:
    """
    Print the scraped article data in a formatted way.
    
    Args:
        articles: List of article dictionaries to print
    """
    if not articles:
        print("No articles found.")
        return
    
    print(f"\n=== TechCrunch Fundraising Articles ({len(articles)} found) ===\n")
    
    for i, article in enumerate(articles, 1):
        print(f"Article {i}:")
        print(f"  Title: {article.get('title', 'N/A')}")
        print(f"  URL: {article.get('url', 'N/A')}")
        print(f"  Author: {article.get('author', 'N/A')}")
        print(f"  Date: {article.get('date', 'N/A')}")
        excerpt = article.get('excerpt', 'N/A')
        if len(excerpt) > 100:
            excerpt = excerpt[:100] + '...'
        print(f"  Excerpt: {excerpt}")
        print("-" * 80)


async def main():
    """Main function to run the scraper and print results."""
    print("Scraping TechCrunch fundraising articles with Playwright...")
    articles = await scrape_techcrunch_fundraising()
    print_scraped_data(articles)


if __name__ == "__main__":
    asyncio.run(main())
