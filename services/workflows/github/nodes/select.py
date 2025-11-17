"""
Selection node for GitHub workflow
"""

from typing import Dict, Any
import logging
from services.agents.custom.agents.open_source_agent import OpenSourceAgent
from services.workflows.github.state import GitHubState

logger = logging.getLogger(__name__)


def select_must_see_node(state: GitHubState) -> Dict[str, Any]:
    """
    Select must-see repositories using AI agent
    Uses existing OpenSourceAgent for selection
    Works on aggregated data from both trending and awesome sources
    """
    logger.info("🔄 Selecting must-see repositories...")

    # Use enriched repos if available, otherwise fall back to aggregated repos
    repos = state.get('enriched_repos', state.get('aggregated_repos', []))

    if not repos:
        logger.warning("⚠️ No repositories to select from")
        return {"must_see_repos": []}

    # Use existing OpenSourceAgent for AI-powered selection
    agent = OpenSourceAgent()
    must_see = agent.select_top_repositories(repos, top_n=5)

    logger.info(f"✅ Selected {len(must_see)} must-see repositories")
    return {"must_see_repos": must_see}
