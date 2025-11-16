"""
AI Agent for selecting must-see open source repositories
Uses AI to analyze and rank repositories based on quality signals
"""

import os
import json
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OpenSourceAgent:
    """Agent for AI-powered open source repository selection"""

    def __init__(self, openrouter_api_key: str = None):
        self.openrouter_api_key = openrouter_api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            logger.warning("No OPENROUTER_API_KEY found - AI selection will not be available")

    def select_top_repositories(self, repositories: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Select top repositories using AI analysis

        Args:
            repositories: List of repository data
            top_n: Number of top repositories to select

        Returns:
            List of selected must-see repositories with AI reasoning
        """
        if not self.openrouter_api_key:
            logger.warning("No API key available - returning top repositories by stars only")
            return self._fallback_selection(repositories, top_n)

        if not repositories:
            logger.warning("No repositories to select from")
            return []

        try:
            # Prepare repository data for AI analysis
            repo_summaries = []
            for i, repo in enumerate(repositories[:50]):  # Limit to 50 for token efficiency
                summary = {
                    "index": i,
                    "name": repo.get('name', 'Unknown'),
                    "full_name": repo.get('full_name', 'Unknown'),
                    "description": repo.get('description', 'No description')[:200],
                    "stars": repo.get('stars', 0),
                    "forks": repo.get('forks', 0),
                    "language": repo.get('language', 'Unknown'),
                    "topics": repo.get('topics', [])[:5],  # Limit topics
                    "stars_gained": repo.get('stars_gained')
                }
                repo_summaries.append(summary)

            # Create AI prompt
            prompt = self._create_selection_prompt(repo_summaries, top_n)

            # Call AI API
            ai_response = self._call_ai_api(prompt)

            if ai_response:
                selected = self._parse_ai_response(ai_response, repositories)
                if selected:
                    logger.info(f"AI selected {len(selected)} must-see repositories")
                    return selected[:top_n]

            # Fallback if AI fails
            logger.warning("AI selection failed - using fallback")
            return self._fallback_selection(repositories, top_n)

        except Exception as e:
            logger.error(f"Error in AI repository selection: {e}")
            return self._fallback_selection(repositories, top_n)

    def _create_selection_prompt(self, repo_summaries: List[Dict], top_n: int) -> str:
        """Create prompt for AI to select top repositories"""
        repos_json = json.dumps(repo_summaries, indent=2)

        prompt = f"""
You are an expert at identifying high-quality, trending open source projects that developers should pay attention to.

Analyze the following {len(repo_summaries)} repositories and select the TOP {top_n} most interesting and valuable projects.

Consider these factors:
1. Innovation and uniqueness (novel ideas, new approaches)
2. Community engagement (stars, forks, recent activity)
3. Practical utility (solving real problems)
4. Code quality indicators (documentation, topics, description quality)
5. Momentum (stars gained, recent updates)
6. Developer relevance (useful for developers, not just trendy)

Repositories:
{repos_json}

Return ONLY a JSON array with the top {top_n} selections in this exact format:
[
  {{
    "index": 0,
    "reasoning": "Brief explanation (1-2 sentences) of why this repo is must-see"
  }},
  ...
]

Return only the JSON array, no other text. Order by priority (most important first).
"""
        return prompt

    def _call_ai_api(self, prompt: str) -> str:
        """Call OpenRouter AI API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/funding-scraper',
                'X-Title': 'Open Source Repository Selector'
            }

            data = {
                'model': 'anthropic/claude-3-haiku',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 2000,
                'temperature': 0.3
            }

            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"AI API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            return None

    def _parse_ai_response(self, ai_response: str, original_repos: List[Dict]) -> List[Dict[str, Any]]:
        """Parse AI response and enrich with repository data"""
        try:
            # Clean up response if it has markdown code blocks
            response_text = ai_response.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text.rsplit('\n', 1)[0]
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()

            selections = json.loads(response_text)

            if not isinstance(selections, list):
                logger.error("AI response is not a list")
                return None

            selected_repos = []
            for selection in selections:
                index = selection.get('index')
                reasoning = selection.get('reasoning', 'Selected by AI')

                if index is not None and 0 <= index < len(original_repos):
                    repo = original_repos[index].copy()
                    repo['ai_reasoning'] = reasoning
                    selected_repos.append(repo)

            return selected_repos

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"AI response was: {ai_response}")
            return None
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None

    def _fallback_selection(self, repositories: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
        """Fallback selection based on simple heuristics (stars, recent activity)"""
        logger.info("Using fallback selection (sorting by stars)")

        # Sort by stars and take top_n
        sorted_repos = sorted(
            repositories,
            key=lambda r: r.get('stars', 0),
            reverse=True
        )

        selected = sorted_repos[:top_n]

        # Add fallback reasoning
        for repo in selected:
            repo['ai_reasoning'] = f"High-starred repository ({repo.get('stars', 0):,} stars)"

        return selected


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)

    test_repos = [
        {
            "name": "test-repo-1",
            "full_name": "user/test-repo-1",
            "description": "A revolutionary AI framework",
            "stars": 5000,
            "forks": 500,
            "language": "Python",
            "topics": ["ai", "machine-learning"]
        },
        {
            "name": "test-repo-2",
            "full_name": "user/test-repo-2",
            "description": "Fast web framework",
            "stars": 3000,
            "forks": 300,
            "language": "JavaScript",
            "topics": ["web", "framework"]
        }
    ]

    agent = OpenSourceAgent()
    selected = agent.select_top_repositories(test_repos, top_n=2)

    print(f"\nSelected {len(selected)} repositories:")
    for repo in selected:
        print(f"- {repo['full_name']}: {repo.get('ai_reasoning', 'No reasoning')}")
