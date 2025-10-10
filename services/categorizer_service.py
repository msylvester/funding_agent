"""
Service for categorizing GitHub repositories based on their metadata
"""

from typing import Dict, Any
import logging
from services.models.categories import RepoCategory

logger = logging.getLogger(__name__)


class RepoCategorizer:
    """Service for categorizing GitHub repositories"""

    def __init__(self):
        """Initialize the categorizer service"""
        logger.info("RepoCategorizer initialized")

    def categorize(self, repo: Dict[str, Any]) -> RepoCategory:
        """
        Categorize a repository based on description, topics, and metadata

        This method analyzes the repository's description, topics, and other
        metadata to determine which category it belongs to. The categorization
        uses keyword matching with precedence rules to ensure every repository
        fits into exactly one category.

        Args:
            repo: Repository data dictionary containing:
                - description (str): Repository description
                - topics (list): List of GitHub topics
                - language (str): Primary programming language
                - name (str): Repository name

        Returns:
            RepoCategory: The determined category for this repository

        Example:
            >>> categorizer = RepoCategorizer()
            >>> repo = {
            ...     "description": "A modern web framework for Python",
            ...     "topics": ["web", "framework", "python"],
            ...     "language": "Python"
            ... }
            >>> category = categorizer.categorize(repo)
            >>> print(category.value)
            'Web Frameworks & Backend'
        """
        # TODO: Implement categorization logic
        # For now, return OTHER as placeholder
        logger.warning(f"Categorization not implemented, defaulting to OTHER for repo: {repo.get('name', 'unknown')}")
        return RepoCategory.OTHER
