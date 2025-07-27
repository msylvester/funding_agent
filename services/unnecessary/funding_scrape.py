import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
import time


def scrape_techcrunch_fundraising() -> List[Dict[str, Any]]:
    """
    Scrape fundraising articles from TechCrunch fundraising category page.
    
    Returns:
        List of dictionaries containing article data
    """
    url = "https://techcrunch.com/category/fundraising/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Find article elements (TechCrunch uses specific classes for articles)
        article_elements = soup.find_all('article', class_='post-block')
        print(f'the article elements are {article_elements}')
        
        for article in article_elements:
            article_data = {}
            
            # Extract title
            title_element = article.find('h2', class_='post-block__title')
            if title_element:
                title_link = title_element.find('a')
                if title_link:
                    article_data['title'] = title_link.get_text(strip=True)
                    article_data['url'] = title_link.get('href')
            
            # Extract excerpt/description
            excerpt_element = article.find('div', class_='post-block__content')
            if excerpt_element:
                article_data['excerpt'] = excerpt_element.get_text(strip=True)
            
            # Extract author
            author_element = article.find('span', class_='river-byline__authors')
            if author_element:
                article_data['author'] = author_element.get_text(strip=True)
            
            # Extract date
            date_element = article.find('time')
            if date_element:
                article_data['date'] = date_element.get('datetime') or date_element.get_text(strip=True)
            
            # Only add if we have at least a title
            if 'title' in article_data:
                articles.append(article_data)
        
        return articles
        
    except requests.RequestException as e:
        print(f"Error scraping TechCrunch: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
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
        print(f"  Excerpt: {article.get('excerpt', 'N/A')[:100]}{'...' if len(article.get('excerpt', '')) > 100 else ''}")
        print("-" * 80)


def main():
    """Main function to run the scraper and print results."""
    print("Scraping TechCrunch fundraising articles...")
    articles = scrape_techcrunch_fundraising()
    print_scraped_data(articles)


if __name__ == "__main__":
    main()
