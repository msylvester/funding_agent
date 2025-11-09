"""
Repository categorization agent using AI
"""

import os
import json
import requests
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def categorize_repo(description: Optional[str], topics: Optional[List[str]], language: Optional[str]) -> str:
    """
    Categorize a GitHub repository using AI analysis

    Args:
        description: Repository description
        topics: List of GitHub topics/tags
        language: Primary programming language

    Returns:
        str: Category name matching one of the RepoCategory enum values
    """

    # Available categories (must match RepoCategory enum values exactly)
    CATEGORIES = [
        "Web Frameworks & Backend",
        "Frontend & UI Libraries",
        "Mobile Development",
        "AI & Machine Learning",
        "Data Science & Analytics",
        "Databases & Storage",
        "DevOps & Infrastructure",
        "CI/CD & Automation",
        "Cloud & Serverless",
        "Monitoring & Observability",
        "CLI Tools & Utilities",
        "Developer Tools & IDEs",
        "Testing & Quality Assurance",
        "Security & Authentication",
        "Networking & Communication",
        "Blockchain & Web3",
        "IoT & Hardware",
        "Game Development",
        "Desktop Applications",
        "API & Integration",
        "Content Management",
        "Documentation & Wikis",
        "Educational & Learning",
        "Templates & Boilerplates",
        "Productivity & Utilities",
        "Other & Miscellaneous"
    ]

    # Get OpenRouter API key
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

    if not openrouter_api_key:
        logger.warning("No OPENROUTER_API_KEY found - using fallback categorization")
        return _fallback_categorization(description, topics, language)

    # Prepare repository info for AI
    repo_info = {
        "description": description or "No description",
        "topics": topics or [],
        "language": language or "Unknown"
    }

    # Create categorization prompt
    prompt = f"""Analyze this GitHub repository and categorize it into EXACTLY ONE category from the list below.

Repository Information:
- Description: {repo_info['description']}
- Topics: {', '.join(repo_info['topics']) if repo_info['topics'] else 'None'}
- Language: {repo_info['language']}

Available Categories:
{chr(10).join(f'- {cat}' for cat in CATEGORIES)}

Rules:
1. Choose the SINGLE most appropriate category
2. Return ONLY the category name, nothing else
3. The category name must match EXACTLY one from the list above
4. If uncertain, choose "Other & Miscellaneous"

Category:"""

    try:
        headers = {
            'Authorization': f'Bearer {openrouter_api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/funding-scraper',
            'X-Title': 'GitHub Repository Categorizer'
        }

        data = {
            'model': 'anthropic/claude-3-haiku',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 100,
            'temperature': 0.1
        }

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            category = result['choices'][0]['message']['content'].strip()

            # Validate the category is in our list
            if category in CATEGORIES:
                logger.info(f"Categorized as: {category}")
                return category
            else:
                logger.warning(f"AI returned invalid category '{category}', using fallback")
                return _fallback_categorization(description, topics, language)
        else:
            logger.error(f"API error: {response.status_code}")
            return _fallback_categorization(description, topics, language)

    except Exception as e:
        logger.error(f"Error in AI categorization: {e}")
        return _fallback_categorization(description, topics, language)


def _fallback_categorization(description: Optional[str], topics: Optional[List[str]], language: Optional[str]) -> str:
    """
    Fallback rule-based categorization when AI is not available

    Args:
        description: Repository description
        topics: List of topics
        language: Programming language

    Returns:
        str: Category name
    """

    # Combine all text for keyword matching
    text = " ".join([
        description or "",
        " ".join(topics or []),
        language or ""
    ]).lower()

    # Rule-based categorization
    if any(keyword in text for keyword in ['ai', 'machine learning', 'ml', 'neural', 'deep learning', 'llm', 'gpt', 'transformer']):
        return "AI & Machine Learning"

    if any(keyword in text for keyword in ['web framework', 'backend', 'api', 'rest', 'graphql', 'server', 'express', 'django', 'flask']):
        return "Web Frameworks & Backend"

    if any(keyword in text for keyword in ['react', 'vue', 'angular', 'frontend', 'ui', 'component', 'css', 'tailwind', 'svelte']):
        return "Frontend & UI Libraries"

    if any(keyword in text for keyword in ['mobile', 'ios', 'android', 'react native', 'flutter', 'swift']):
        return "Mobile Development"

    if any(keyword in text for keyword in ['data science', 'analytics', 'visualization', 'pandas', 'numpy', 'jupyter']):
        return "Data Science & Analytics"

    if any(keyword in text for keyword in ['database', 'sql', 'nosql', 'mongodb', 'postgres', 'mysql', 'redis']):
        return "Databases & Storage"

    if any(keyword in text for keyword in ['devops', 'kubernetes', 'docker', 'container', 'infrastructure', 'terraform']):
        return "DevOps & Infrastructure"

    if any(keyword in text for keyword in ['ci/cd', 'github actions', 'jenkins', 'automation', 'pipeline']):
        return "CI/CD & Automation"

    if any(keyword in text for keyword in ['cloud', 'aws', 'azure', 'gcp', 'serverless', 'lambda']):
        return "Cloud & Serverless"

    if any(keyword in text for keyword in ['monitoring', 'observability', 'logging', 'metrics', 'prometheus', 'grafana']):
        return "Monitoring & Observability"

    if any(keyword in text for keyword in ['cli', 'command line', 'terminal', 'shell']):
        return "CLI Tools & Utilities"

    if any(keyword in text for keyword in ['ide', 'editor', 'vscode', 'developer tool', 'debugger']):
        return "Developer Tools & IDEs"

    if any(keyword in text for keyword in ['test', 'testing', 'qa', 'quality', 'jest', 'pytest', 'selenium']):
        return "Testing & Quality Assurance"

    if any(keyword in text for keyword in ['security', 'authentication', 'auth', 'oauth', 'encryption', 'cybersecurity']):
        return "Security & Authentication"

    if any(keyword in text for keyword in ['network', 'networking', 'http', 'websocket', 'communication']):
        return "Networking & Communication"

    if any(keyword in text for keyword in ['blockchain', 'web3', 'crypto', 'ethereum', 'solidity', 'smart contract']):
        return "Blockchain & Web3"

    if any(keyword in text for keyword in ['iot', 'hardware', 'embedded', 'raspberry pi', 'arduino']):
        return "IoT & Hardware"

    if any(keyword in text for keyword in ['game', 'gaming', 'unity', 'unreal', 'game engine']):
        return "Game Development"

    if any(keyword in text for keyword in ['desktop', 'electron', 'tauri', 'desktop app']):
        return "Desktop Applications"

    if any(keyword in text for keyword in ['cms', 'content management', 'wordpress', 'blog']):
        return "Content Management"

    if any(keyword in text for keyword in ['documentation', 'docs', 'wiki', 'markdown']):
        return "Documentation & Wikis"

    if any(keyword in text for keyword in ['educational', 'learning', 'tutorial', 'course', 'teach']):
        return "Educational & Learning"

    if any(keyword in text for keyword in ['template', 'boilerplate', 'starter', 'scaffold']):
        return "Templates & Boilerplates"

    if any(keyword in text for keyword in ['productivity', 'utility', 'tool']):
        return "Productivity & Utilities"

    # Default fallback
    return "Other & Miscellaneous"


# Testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Test cases
    test_repos = [
        {
            "description": "A modern web framework for Python",
            "topics": ["web", "framework", "python"],
            "language": "Python"
        },
        {
            "description": "Machine learning toolkit for computer vision",
            "topics": ["ai", "ml", "computer-vision"],
            "language": "Python"
        },
        {
            "description": "React component library with beautiful UI",
            "topics": ["react", "ui", "components"],
            "language": "TypeScript"
        }
    ]

    for repo in test_repos:
        category = categorize_repo(
            description=repo["description"],
            topics=repo["topics"],
            language=repo["language"]
        )
        print(f"Description: {repo['description']}")
        print(f"Category: {category}\n")
