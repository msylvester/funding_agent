"""
Aggregation node for GitHub workflow
Combines trending and awesome repos into a single deduplicated list
"""

from typing import Dict, Any, List
import logging
from services.workflows.github.state import GitHubState

logger = logging.getLogger(__name__)


def aggregate_repos_node(state: GitHubState) -> Dict[str, Any]:
    """
    Aggregate trending and awesome repositories into a single list
    Deduplicates by full_name (owner/repo) and merges metadata

    Args:
        state: Current workflow state with trending_repos and awesome_lists

    Returns:
        Dict with aggregated_repos list
    """
    logger.info("🔄 Aggregating repositories from multiple sources...")

    trending = state.get('trending_repos', [])
    awesome = state.get('awesome_lists', [])

    logger.info(f"  📊 Trending repos: {len(trending)}")
    logger.info(f"  ⭐ Awesome lists: {len(awesome)}")

    # Use dict to deduplicate by full_name
    repo_map = {}

    # Add all repos, using full_name as unique key
    for repo in trending + awesome:
        full_name = repo.get('full_name') or f"{repo.get('owner')}/{repo.get('name')}"

        if full_name in repo_map:
            # Repo exists - merge data (prefer more complete data)
            existing = repo_map[full_name]
            # Keep the one with more fields populated
            if len(repo) > len(existing):
                repo_map[full_name] = repo
                logger.debug(f"  Updated {full_name} with more complete data")
        else:
            # New repo
            repo_map[full_name] = repo

    # Convert back to list
    aggregated = list(repo_map.values())

    logger.info(f"✅ Aggregated {len(aggregated)} unique repositories (removed {len(trending) + len(awesome) - len(aggregated)} duplicates)")

    return {"aggregated_repos": aggregated}
