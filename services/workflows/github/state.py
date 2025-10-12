"""
State definition for GitHub workflow
"""

from typing_extensions import TypedDict
from typing import List, Dict, Any


class GitHubState(TypedDict):
    """State object passed through the workflow"""
    trending_repos: List[Dict[str, Any]]
    awesome_lists: List[Dict[str, Any]]
    aggregated_repos: List[Dict[str, Any]]  # Combined trending + awesome (deduplicated)
    enriched_repos: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    must_see_repos: List[Dict[str, Any]]
    query_params: Dict[str, Any]
