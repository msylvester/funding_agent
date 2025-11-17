"""
Service for categorizing GitHub repositories based on their metadata
"""

from typing import Dict, Any
import logging
from services.models.categories import RepoCategory
from services.agents.custom.agent_cat import categorize_repo

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
        uses AI-powered analysis to ensure every repository fits into exactly
        one category.

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
        # Use AI agent to categorize the repository
        category_name = categorize_repo(
            description=repo.get('description'),
            topics=repo.get('topics'),
            language=repo.get('language')
        )

        # Convert category name string to RepoCategory enum
        for category in RepoCategory:
            if category.value == category_name:
                logger.info(f"Categorized {repo.get('name', 'unknown')} as: {category_name}")
                return category

        # Fallback to OTHER if category name doesn't match any enum
        logger.warning(f"Category '{category_name}' not found in enum, defaulting to OTHER for repo: {repo.get('name', 'unknown')}")
        return RepoCategory.OTHER
