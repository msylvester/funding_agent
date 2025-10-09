"""
Service for fetching and processing open source project data
"""

import os
import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OpenSourceDataService:
    """Service for managing open source project data"""

    def __init__(self, github_token: str = None):
        self.github_api_base = "https://api.github.com"
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

        # Set up headers with authentication if token is available
        self.headers = {}
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
            logger.info("GitHub token configured - using authenticated requests")
        else:
            logger.warning("No GitHub token found - using unauthenticated requests (rate limit: 60/hour)")
        
    def get_trending_repositories(self, language: str = None, time_range: str = "daily") -> List[Dict[str, Any]]:
        """
        Fetch trending repositories from GitHub
        
        Args:
            language: Programming language filter (optional)
            time_range: Time range for trending (daily, weekly, monthly)
            
        Returns:
            List of repository data
        """
        try:
            # Calculate date range for pushed updates (GitHub trending considers recent activity)
            from datetime import datetime, timedelta
            
            if time_range == "daily":
                since_date = datetime.now() - timedelta(days=1)
            elif time_range == "weekly":
                since_date = datetime.now() - timedelta(weeks=1)
            elif time_range == "monthly":
                since_date = datetime.now() - timedelta(days=30)
            else:
                since_date = datetime.now() - timedelta(days=1)
                
            date_str = since_date.strftime("%Y-%m-%d")
            
            # Build search query to find recently active repos with minimal star threshold
            # Focus on repos that have recent activity and some community interest
            query = f"pushed:>{date_str} stars:>1"
            if language:
                query += f" language:{language}"
                
            # GitHub Search API endpoint
            url = f"{self.github_api_base}/search/repositories"
            params = {
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": 50  # Get more results to filter
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            for repo in data.get("items", [])[:20]:  # Take top 20
                repo_data = {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"],
                    "url": repo["html_url"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "pushed_at": repo["pushed_at"],
                    "owner": repo["owner"]["login"],
                    "topics": repo.get("topics", [])
                }
                repositories.append(repo_data)
                
            logger.info(f"Retrieved {len(repositories)} trending repositories")
            return repositories
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending repositories: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
        
    def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository details
        """
        try:
            url = f"{self.github_api_base}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            repo_data = response.json()

            # Get additional data like contributors and releases
            contributors_url = f"{url}/contributors"
            releases_url = f"{url}/releases"

            contributors_response = requests.get(contributors_url, headers=self.headers)
            releases_response = requests.get(releases_url, headers=self.headers)
            
            contributors = contributors_response.json() if contributors_response.status_code == 200 else []
            releases = releases_response.json() if releases_response.status_code == 200 else []
            
            details = {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data["description"],
                "stars": repo_data["stargazers_count"],
                "forks": repo_data["forks_count"],
                "watchers": repo_data["watchers_count"],
                "language": repo_data["language"],
                "url": repo_data["html_url"],
                "clone_url": repo_data["clone_url"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
                "pushed_at": repo_data["pushed_at"],
                "size": repo_data["size"],
                "default_branch": repo_data["default_branch"],
                "topics": repo_data.get("topics", []),
                "license": repo_data["license"]["name"] if repo_data.get("license") else None,
                "open_issues": repo_data["open_issues_count"],
                "contributors_count": len(contributors[:10]),  # Limit to first 10
                "latest_release": releases[0]["tag_name"] if releases else None,
                "owner": {
                    "login": repo_data["owner"]["login"],
                    "type": repo_data["owner"]["type"],
                    "avatar_url": repo_data["owner"]["avatar_url"]
                }
            }
            
            logger.info(f"Retrieved details for repository {owner}/{repo}")
            return details
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repository details for {owner}/{repo}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting repository details: {e}")
            return {}
        
    def search_repositories(self, query: str, sort: str = "stars") -> List[Dict[str, Any]]:
        """
        Search repositories by query
        
        Args:
            query: Search query
            sort: Sort criteria (stars, forks, updated)
            
        Returns:
            List of matching repositories
        """
        try:
            url = f"{self.github_api_base}/search/repositories"
            params = {
                "q": query,
                "sort": sort,
                "order": "desc",
                "per_page": 30
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            for repo in data.get("items", []):
                repo_data = {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"],
                    "url": repo["html_url"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "pushed_at": repo["pushed_at"],
                    "owner": repo["owner"]["login"],
                    "topics": repo.get("topics", []),
                    "license": repo["license"]["name"] if repo.get("license") else None,
                    "open_issues": repo["open_issues_count"]
                }
                repositories.append(repo_data)
                
            logger.info(f"Found {len(repositories)} repositories for query: {query}")
            return repositories
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching repositories: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching repositories: {e}")
            return []
        
    def get_awesome_lists(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Fetch curated awesome lists

        Args:
            category: Category filter (optional)

        Returns:
            List of awesome list repositories
        """
        try:
            # Calculate time windows for trending repos
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

            # Build query for quality repos with recent activity (no "awesome" bias)
            # Only include repos created in the last 2 years
            query = f"stars:>50 pushed:>{thirty_days_ago} created:>{two_years_ago}"
            if category:
                query += f" language:{category}"
            
            url = f"{self.github_api_base}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 25
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            awesome_lists = []

            for repo in data.get("items", []):
                repo_data = {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"],
                    "url": repo["html_url"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "owner": repo["owner"]["login"],
                    "topics": repo.get("topics", []),
                    "category": self._extract_awesome_category(repo["name"], repo["description"])
                }
                awesome_lists.append(repo_data)
                    
            logger.info(f"Found {len(awesome_lists)} awesome lists" + 
                       (f" for category: {category}" if category else ""))
            return awesome_lists
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching awesome lists: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching awesome lists: {e}")
            return []
    
    def _extract_awesome_category(self, name: str, description: str) -> str:
        """Extract category from awesome list name/description"""
        name_lower = name.lower()
        desc_lower = (description or "").lower()
        
        # Common awesome list patterns
        if "awesome-" in name_lower:
            return name_lower.split("awesome-", 1)[1].replace("-", " ").title()
        elif name_lower.startswith("awesome"):
            return name_lower.replace("awesome", "").replace("-", " ").strip().title()
        elif "python" in desc_lower:
            return "Python"
        elif "javascript" in desc_lower or "js" in desc_lower:
            return "JavaScript" 
        elif "machine learning" in desc_lower or "ml" in desc_lower:
            return "Machine Learning"
        elif "data" in desc_lower:
            return "Data Science"
        else:
            return "General"

if __name__ == "__main__":
    # Test the service
    service = OpenSourceDataService()
    print("Fetching trending repositories...")
    repos = service.get_trending_repositories(language="english")
    print(f"Found {len(repos)} repositories:")
    for repo in repos:  # Show all repositories
        print(f"- {repo['name']} ({repo['stars']} stars) - {repo['description'][:100] if repo['description'] else 'No description'}...")
