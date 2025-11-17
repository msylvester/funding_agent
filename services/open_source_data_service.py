"""
Aggregation service that combines results from GitHub API and web scraping
"""

import sys
import os

from services.github_trending import GitHubTrendingScraper
from services.open_source_data import OpenSourceDataService
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AggregatedOpenSourceService:
    """Service that aggregates results from multiple GitHub data sources"""
    
    def __init__(self):
        self.github_scraper = GitHubTrendingScraper()
        self.api_service = OpenSourceDataService()
    
    def get_aggregated_trending(self, language: str = None, time_range: str = "daily") -> List[Dict[str, Any]]:
        """
        Get trending repositories from both API and web scraping, then merge/deduplicate
        
        Args:
            language: Programming language filter 
            time_range: Time range for trending data
            
        Returns:
            Aggregated and deduplicated list of repositories
        """
        try:
            print("Fetching from GitHub trending page...")
            # Get results from web scraper (actual trending page)
            trending_repos = self.github_scraper.scrape_trending(language=language, time_range=time_range)
            
            print("Fetching from GitHub API...")
            # Get results from API service (search-based approach)
            # Convert "english" to None for API calls since it expects programming languages
            api_language = None if language == "english" else language
            api_repos = self.api_service.get_trending_repositories(language=api_language, time_range=time_range)
            
            # Merge and deduplicate results
            aggregated = self._merge_repositories(trending_repos, api_repos)
            
            logger.info(f"Aggregated {len(aggregated)} unique repositories from {len(trending_repos)} trending + {len(api_repos)} API results")
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating trending repositories: {e}")
            return []
    
    def _merge_repositories(self, trending_repos: List[Dict], api_repos: List[Dict]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate repositories from different sources
        Priority: trending page results > API results
        """
        merged = {}
        
        # Add API results first (lower priority)
        for repo in api_repos:
            full_name = repo.get('full_name', f"{repo.get('owner', '')}/{repo.get('name', '')}")
            merged[full_name] = {
                'name': repo.get('name'),
                'full_name': full_name,
                'owner': repo.get('owner'),
                'description': repo.get('description'),
                'language': repo.get('language'),
                'stars': repo.get('stars', 0),
                'forks': repo.get('forks', 0),
                'url': repo.get('url'),
                'stars_gained': None,  # API doesn't provide this
                'source': 'api',
                'topics': repo.get('topics', []),
                'created_at': repo.get('created_at'),
                'updated_at': repo.get('updated_at')
            }
        
        # Add trending results (higher priority - will overwrite duplicates)
        for repo in trending_repos:
            full_name = repo.get('full_name')
            if full_name:
                existing = merged.get(full_name, {})
                merged[full_name] = {
                    'name': repo.get('name'),
                    'full_name': full_name,
                    'owner': repo.get('owner'),
                    'description': repo.get('description'),
                    'language': repo.get('language'),
                    'stars': repo.get('stars', existing.get('stars', 0)),
                    'forks': repo.get('forks', existing.get('forks', 0)),
                    'url': repo.get('url'),
                    'stars_gained': repo.get('stars_gained'),  # Only trending has this
                    'source': 'trending' if not existing else 'both',
                    'topics': existing.get('topics', []),
                    'created_at': existing.get('created_at'),
                    'updated_at': existing.get('updated_at')
                }
        
        # Convert back to list and sort by stars (descending)
        result = list(merged.values())
        result.sort(key=lambda x: x.get('stars', 0), reverse=True)
        
        return result

def aggregate_github_data():
    """Main function to aggregate and display results"""
    service = AggregatedOpenSourceService()
    
    print("=== Aggregating GitHub Trending Data ===")
    repos = service.get_aggregated_trending(language=None)  # Don't filter by language for trending
    
    print(f"\nFound {len(repos)} unique repositories:")
    print("=" * 80)
    
    for i, repo in enumerate(repos, 1):
        source_indicator = {
            'trending': '🔥',
            'api': '🔍', 
            'both': '⭐'
        }.get(repo['source'], '❓')
        
        stars_gained_text = f" (+{repo['stars_gained']} today)" if repo['stars_gained'] else ""
        
        print(f"{i:2d}. {source_indicator} {repo['full_name']} ({repo['stars']:,} stars{stars_gained_text})")
        if repo['description']:
            print(f"    📝 {repo['description'][:100]}...")
        print(f"    🌐 {repo['url']}")
        print(f"    💻 {repo['language'] or 'Unknown language'}")
        print()

if __name__ == "__main__":
    aggregate_github_data()
