"""
Service for fetching and processing open source project data
"""

import os
import requests
from typing import List, Dict, Any
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class OpenSourceDataService:
    """Service for managing open source project data"""

    def __init__(self, github_token: str = None):
        self.github_api_base = "https://api.github.com"
        self.github_trending_url = "https://github.com/trending"
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

        # Set up headers with authentication if token is available
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
            logger.info("GitHub token configured - using authenticated requests")
        else:
            logger.warning("No GitHub token found - using unauthenticated requests (rate limit: 60/hour)")
        
    def get_trending_repositories(self, language: str = None, time_range: str = "daily") -> List[Dict[str, Any]]:
        """
        Fetch trending repositories from GitHub by scraping the trending page

        Args:
            language: Programming language filter (optional)
            time_range: Time range for trending (daily, weekly, monthly)

        Returns:
            List of repository data
        """
        try:
            # Build URL for trending page
            url = self.github_trending_url
            params = {}

            if language and language.lower() != "english":  # Skip invalid language filter
                params['spoken_language_code'] = language

            # Map time_range to GitHub's since parameter
            if time_range == "weekly":
                params['since'] = "weekly"
            elif time_range == "monthly":
                params['since'] = "monthly"
            else:
                params['since'] = "daily"

            # Fetch trending page HTML
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            repositories = []

            # Find all repository articles
            repo_articles = soup.find_all('article', class_='Box-row')

            for article in repo_articles[:25]:  # Get top 25 trending repos
                try:
                    # Extract repository name and owner
                    repo_link = article.find('h2', class_='h3').find('a')
                    if not repo_link:
                        continue

                    full_name = repo_link['href'].strip('/')
                    owner, name = full_name.split('/')

                    # Extract description
                    desc_elem = article.find('p', class_='col-9')
                    description = desc_elem.text.strip() if desc_elem else None

                    # Extract language
                    lang_spans = article.find_all('span', class_='d-inline-block')
                    language_name = None
                    for span in lang_spans:
                        # Language span has ml-0 mr-3 classes and contains the language name
                        if 'ml-0' in span.get('class', []) and 'mr-3' in span.get('class', []):
                            language_name = span.text.strip()
                            break

                    # Extract stars (total) - from link ending in /stargazers
                    stars = 0
                    stars_link = article.find('a', href=lambda x: x and '/stargazers' in x)
                    if stars_link:
                        stars_text = stars_link.text.strip().replace(',', '')
                        try:
                            stars = int(stars_text)
                        except ValueError:
                            stars = 0

                    # Extract forks - from link ending in /forks
                    forks = 0
                    forks_link = article.find('a', href=lambda x: x and '/forks' in x)
                    if forks_link:
                        forks_text = forks_link.text.strip().replace(',', '')
                        try:
                            forks = int(forks_text)
                        except ValueError:
                            forks = 0

                    # Extract stars gained today/this week/this month
                    stars_gained_elem = article.find('span', class_='d-inline-block float-sm-right')
                    stars_gained = 0
                    if stars_gained_elem:
                        gained_text = stars_gained_elem.text.strip()
                        # Extract number from text like "1,234 stars today"
                        import re
                        match = re.search(r'([\d,]+)\s+stars?', gained_text)
                        if match:
                            try:
                                stars_gained = int(match.group(1).replace(',', ''))
                            except ValueError:
                                stars_gained = 0

                    repo_data = {
                        "name": name,
                        "full_name": full_name,
                        "description": description,
                        "stars": stars,
                        "forks": forks,
                        "stars_gained": stars_gained,
                        "language": language_name,
                        "url": f"https://github.com/{full_name}",
                        "owner": owner
                    }
                    repositories.append(repo_data)

                except Exception as e:
                    logger.warning(f"Error parsing repository article: {e}")
                    continue

            logger.info(f"Retrieved {len(repositories)} trending repositories from GitHub trending page")
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
        
    def get_awesome_lists(self, category: str = None, time_range: str = "monthly") -> List[Dict[str, Any]]:
        """
        Fetch curated awesome lists

        Args:
            category: Category filter (optional)
            time_range: Time range for trending (daily, weekly, monthly)

        Returns:
            List of awesome list repositories
        """
        try:
            # Calculate time windows for trending repos
            from datetime import datetime, timedelta

            # Map time_range to days
            if time_range == "daily":
                days_ago = 1
            elif time_range == "weekly":
                days_ago = 7
            elif time_range == "monthly":
                days_ago = 30
            else:
                days_ago = 30  # Default to monthly

            since_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

            # Build query for quality repos with recent activity (no "awesome" bias)
            # Only include repos created in the last 2 years
            query = f"stars:>50 pushed:>{since_date} created:>{two_years_ago}"
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
    repos = service.get_trending_repositories()
    print(f"Found {len(repos)} repositories:")
    for repo in repos:
        stars_gained_text = f" (+{repo['stars_gained']} today)" if repo['stars_gained'] > 0 else ""
        desc = repo['description'][:80] + "..." if repo['description'] else "No description"
        print(f"- {repo['name']} ({repo['stars']:,} stars{stars_gained_text}) - {desc}")
