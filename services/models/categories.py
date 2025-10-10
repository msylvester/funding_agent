"""
Repository category definitions
"""

from enum import Enum
from typing import List


class RepoCategory(Enum):
    """Enumeration of all possible repository categories"""

    # Web & Backend
    WEB_FRAMEWORKS = "Web Frameworks & Backend"
    FRONTEND_UI = "Frontend & UI Libraries"
    MOBILE_DEV = "Mobile Development"

    # Data & AI
    AI_ML = "AI & Machine Learning"
    DATA_SCIENCE = "Data Science & Analytics"
    DATABASES = "Databases & Storage"

    # Infrastructure & Operations
    DEVOPS = "DevOps & Infrastructure"
    CI_CD = "CI/CD & Automation"
    CLOUD_SERVERLESS = "Cloud & Serverless"
    MONITORING = "Monitoring & Observability"

    # Development Tools
    CLI_TOOLS = "CLI Tools & Utilities"
    DEVELOPER_TOOLS = "Developer Tools & IDEs"
    TESTING = "Testing & Quality Assurance"

    # Security & Networking
    SECURITY = "Security & Authentication"
    NETWORKING = "Networking & Communication"

    # Emerging Tech
    BLOCKCHAIN = "Blockchain & Web3"
    IOT_HARDWARE = "IoT & Hardware"
    GAME_DEV = "Game Development"

    # Application Types
    DESKTOP_APPS = "Desktop Applications"
    API_INTEGRATION = "API & Integration"
    CMS = "Content Management"

    # Content & Learning
    DOCUMENTATION = "Documentation & Wikis"
    EDUCATIONAL = "Educational & Learning"
    TEMPLATES = "Templates & Boilerplates"

    # Productivity
    PRODUCTIVITY = "Productivity & Utilities"

    # Fallback
    OTHER = "Other & Miscellaneous"

    @classmethod
    def get_all_categories(cls) -> List[str]:
        """
        Get list of all category names

        Returns:
            List of category display names
        """
        return [category.value for category in cls]

    @classmethod
    def get_category_count(cls) -> int:
        """
        Get total number of categories

        Returns:
            Number of categories
        """
        return len(cls)
