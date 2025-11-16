"""
Nodes package for GitHub workflow
"""

from services.github_workflows.github.nodes.fetch import fetch_trending_node, fetch_awesome_node
from services.github_workflows.github.nodes.enrich import enrich_details_node
from services.github_workflows.github.nodes.select import select_must_see_node

__all__ = [
    'fetch_trending_node',
    'fetch_awesome_node',
    'enrich_details_node',
    'select_must_see_node'
]
