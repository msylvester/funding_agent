"""
GitHub Trending Scraper - scrapes https://github.com/trending directly
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

class GitHubTrendingScraper:
    """Scraper for GitHub trending repositories"""
    
    def __init__(self):
        self.base_url = "https://github.com/trending"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_trending(self, language: str = None, time_range: str = "daily") -> List[Dict[str, Any]]:
        """
        Scrape trending repositories from GitHub trending page
        
        Args:
            language: Programming language filter (optional)
            time_range: Time range (daily, weekly, monthly)
            
        Returns:
            List of repository data
        """
        try:
            # Build URL with parameters
            url = self.base_url
            params = {}
            
            if language:
                params['l'] = language
            if time_range == "weekly":
                params['since'] = 'weekly'
            elif time_range == "monthly":
                params['since'] = 'monthly'
            
            # Make request
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save HTML for debugging (optional)
            # with open('github_trending_debug.html', 'w', encoding='utf-8') as f:
            #     f.write(str(soup))
            
            # Find repository articles - try multiple selectors
            repos = []
            
            # Try different selectors that GitHub might use
            repo_articles = (
                soup.find_all('article', class_='Box-row') or
                soup.find_all('article') or
                soup.select('article[class*="Box"]') or
                soup.select('.repo-list-item') or
                soup.select('[data-testid="repository-card"]') or
                soup.select('div[class*="repo-list-item"]')
            )
            
            print(f"Found {len(repo_articles)} repository elements")  # Debug info
            print(f"Total articles on page: {len(soup.find_all('article'))}")  # More debug info
            
            for i, article in enumerate(repo_articles):
                repo_data = self._parse_repository(article)
                if repo_data:
                    repos.append(repo_data)
                else:
                    print(f"Failed to parse repository {i+1}")  # Debug info
            
            logger.info(f"Scraped {len(repos)} trending repositories")
            return repos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping GitHub trending: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_repository(self, article) -> Dict[str, Any]:
        """Parse repository data from article element"""
        try:
            # Get repository name and owner - try multiple selectors
            title_link = None
            
            # Try different ways to find the title link
            h2_elem = article.find('h2')
            if h2_elem:
                title_link = h2_elem.find('a')
            
            if not title_link:
                # Try alternative selectors
                title_link = article.find('a', href=re.compile(r'^/[^/]+/[^/]+$'))
            
            if not title_link:
                print(f"Could not find title link in article")
                return None
                
            full_name = title_link.get('href').strip('/')
            repo_name = full_name.split('/')[-1]
            owner = full_name.split('/')[0]
            
            # Get description - try multiple selectors
            description_elem = (
                article.find('p', class_='col-9') or
                article.find('p', class_=re.compile(r'.*color-fg-muted.*')) or
                article.find('p')
            )
            description = description_elem.text.strip() if description_elem else None
            
            # Get language - try multiple selectors
            language_elem = (
                article.find('span', itemprop='programmingLanguage') or
                article.find('span', {'data-view-component': 'true'})
            )
            language = language_elem.text.strip() if language_elem else None
            
            # Get stars (total) - try multiple selectors
            stars_elem = (
                article.find('a', href=re.compile(r'/stargazers$')) or
                article.find('a', href=re.compile(r'/stargazers'))
            )
            stars = 0
            if stars_elem:
                stars_text = stars_elem.text.strip()
                stars = self._parse_number(stars_text)
            
            # Get forks - try multiple selectors
            forks_elem = (
                article.find('a', href=re.compile(r'/forks$')) or
                article.find('a', href=re.compile(r'/forks'))
            )
            forks = 0
            if forks_elem:
                forks_text = forks_elem.text.strip()
                forks = self._parse_number(forks_text)
            
            # Get stars gained today/period
            stars_gained_elem = article.find('span', class_='d-inline-block')
            stars_gained = 0
            if stars_gained_elem and 'stars' in stars_gained_elem.text:
                stars_gained_text = stars_gained_elem.text.strip()
                stars_gained = self._parse_number(stars_gained_text.split()[0])
            
            return {
                'name': repo_name,
                'full_name': full_name,
                'owner': owner,
                'description': description,
                'language': language,
                'stars': stars,
                'forks': forks,
                'stars_gained': stars_gained,
                'url': f"https://github.com/{full_name}"
            }
            
        except Exception as e:
            print(f"Error parsing repository: {e}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (handles k, m suffixes)"""
        try:
            text = text.replace(',', '').strip()
            if 'k' in text.lower():
                return int(float(text.lower().replace('k', '')) * 1000)
            elif 'm' in text.lower():
                return int(float(text.lower().replace('m', '')) * 1000000)
            else:
                return int(text)
        except (ValueError, AttributeError):
            return 0

if __name__ == "__main__":
    # Test the scraper
    scraper = GitHubTrendingScraper()
    print("Scraping GitHub trending repositories...")
    repos = scraper.scrape_trending()
    print(f"Found {len(repos)} repositories:")
    
    # Show ALL repositories found
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo['full_name']} ({repo['stars']:,} stars)")
        print(f"   URL: {repo['url']}")
        if repo['description']:
            print(f"   {repo['description'][:80]}...")
        print(f"   Language: {repo['language'] or 'Unknown'} | Gained: {repo['stars_gained']} stars")
        print()