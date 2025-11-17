"""
Enrichment node for GitHub workflow
"""

from typing import Dict, Any
import logging
from services.scrapers.open_source_data import OpenSourceDataService
from services.workflows.github.state import GitHubState

logger = logging.getLogger(__name__)


def enrich_details_node(state: GitHubState) -> Dict[str, Any]:
    """
    Enrich high-quality repositories with detailed information
    Only processes repos that meet quality threshold (>50 stars)
    Works on aggregated repos (both trending and awesome sources)
    """
    logger.info("🔄 Enriching repository details...")
    service = OpenSourceDataService()
    repos = state['aggregated_repos']
    enriched = []

    for repo in repos:
        stars = repo.get('stars', 0)

        if stars > 50:
            # High-quality repo: fetch detailed info
            logger.info(f"  Enriching {repo['name']} ({stars} stars)")
            details = service.get_repository_details(
                repo['owner'],
                repo['name']
            )
            if details:
                enriched.append(details)
            else:
                enriched.append(repo)  # Fallback to basic data
        else:
            # Low-quality repo: keep basic data
            enriched.append(repo)

    logger.info(f"✅ Enriched {len(enriched)} repositories")
    return {"enriched_repos": enriched}
