"""
Fetch nodes for GitHub workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from typing import Dict, Any
import logging
from services.open_source_data import OpenSourceDataService
from services.github_trending import GitHubTrendingScraper
from services.workflows.github.state import GitHubState

logger = logging.getLogger(__name__)


def fetch_trending_node(state: GitHubState) -> Dict[str, Any]:
    """
    Fetch trending repositories from GitHub
    Runs in parallel with fetch_awesome_node
    """
    logger.info("🔄 Fetching trending repositories...")
    scraper = GitHubTrendingScraper()
    params = state.get('query_params', {})

    # Extract parameters
    language = params.get('language')
    time_range = params.get('time_range', 'daily')

    repos = scraper.scrape_trending(
        language=language,
        time_range=time_range
    )

    logger.info(f"✅ Fetched {len(repos)} trending repositories")
    return {"trending_repos": repos}


def fetch_awesome_node(state: GitHubState) -> Dict[str, Any]:
    """
    Fetch awesome lists from GitHub
    Runs in parallel with fetch_trending_node
    """
    logger.info("🔄 Fetching awesome lists...")
    service = OpenSourceDataService()
    params = state.get('query_params', {})

    # Extract language and time_range parameters
    language = params.get('language')
    time_range = params.get('time_range', 'daily')

    awesome = service.get_awesome_lists(category=language, time_range=time_range)

    logger.info(f"✅ Fetched {len(awesome)} awesome lists")
    return {"awesome_lists": awesome}
