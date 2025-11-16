"""
Conditional logic for GitHub workflow
"""

import logging
from services.github_workflows.github.state import GitHubState

logger = logging.getLogger(__name__)


def should_enrich(state: GitHubState) -> str:
    """
    Decide whether to enrich repositories based on quality threshold
    Checks aggregated repos (both trending and awesome sources)

    Returns:
        "enrich" if >= 5 repos have >50 stars
        "skip_enrich" otherwise
    """
    repos = state.get('aggregated_repos', [])

    if not repos:
        return "skip_enrich"

    high_quality_count = sum(1 for r in repos if r.get('stars', 0) > 50)

    if high_quality_count >= 5:
        logger.info(f"🎯 Found {high_quality_count} high-quality repos → enriching")
        return "enrich"
    else:
        logger.info(f"⚡ Only {high_quality_count} high-quality repos → skipping enrichment")
        return "skip_enrich"
