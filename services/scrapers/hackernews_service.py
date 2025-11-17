"""
Service for fetching and analyzing Hacker News stories
Scrapes HN front page and uses AI to identify most significant stories
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HackerNewsService:
    """Service for fetching and analyzing Hacker News stories"""

    def __init__(self, openrouter_api_key: str = None, openrouter_base_url: str = None, default_model: str = None):
        """
        Initialize HackerNews service

        Args:
            openrouter_api_key: OpenRouter API key for AI analysis
            openrouter_base_url: OpenRouter base URL
            default_model: Default model to use for analysis
        """
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_base_url = openrouter_base_url or "https://openrouter.ai/api/v1"
        self.default_model = default_model or "anthropic/claude-3-haiku"
        self.hn_base_url = "https://news.ycombinator.com"

    def get_top_analyzed_stories(self, story_limit: int = 30) -> Dict[str, Any]:
        """
        Get top stories from HN and analyze them with AI

        Args:
            story_limit: Maximum number of stories to fetch

        Returns:
            Dict with success status, stories, and analysis
        """
        try:
            # Scrape stories from HN
            stories = self._scrape_stories(limit=story_limit)

            if not stories:
                return {
                    "success": False,
                    "message": "No stories found",
                    "stories": [],
                    "total_scraped": 0
                }

            # If no API key, return stories without AI analysis
            if not self.openrouter_api_key:
                logger.warning("No OpenRouter API key - returning stories without AI analysis")
                return {
                    "success": True,
                    "message": "Stories fetched successfully (no AI analysis)",
                    "stories": stories[:10],  # Return top 10 by default
                    "total_scraped": len(stories),
                    "analysis": "AI analysis not available - no API key provided",
                    "analysis_success": False
                }

            # Analyze stories with AI
            analysis_result = self._analyze_stories_with_ai(stories)

            if analysis_result["success"]:
                return {
                    "success": True,
                    "message": "Stories analyzed successfully",
                    "stories": analysis_result["highlighted_stories"],
                    "total_scraped": len(stories),
                    "analysis": analysis_result.get("full_analysis", ""),
                    "analysis_success": True
                }
            else:
                # Return stories without analysis on AI failure
                return {
                    "success": True,
                    "message": "Stories fetched but AI analysis failed",
                    "stories": stories[:10],
                    "total_scraped": len(stories),
                    "analysis": f"AI analysis failed: {analysis_result.get('message', 'Unknown error')}",
                    "analysis_success": False
                }

        except Exception as e:
            logger.error(f"Error in get_top_analyzed_stories: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "stories": [],
                "total_scraped": 0
            }

    def _scrape_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape stories from Hacker News front page

        Args:
            limit: Maximum number of stories to scrape

        Returns:
            List of story dictionaries
        """
        try:
            # Fetch HN front page
            response = requests.get(f"{self.hn_base_url}/news", timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            stories = []
            story_rows = soup.select('tr.athing')

            for i, row in enumerate(story_rows[:limit], 1):
                try:
                    # Get story ID
                    story_id = row.get('id')

                    # Get title and URL
                    title_element = row.select_one('span.titleline > a')
                    title = title_element.text if title_element else "No title"
                    url = title_element.get('href', '') if title_element else ''

                    # Get domain
                    domain_element = row.select_one('span.sitestr')
                    domain = domain_element.text if domain_element else None

                    # Get metadata from next row
                    meta_row = row.find_next_sibling('tr')
                    if meta_row:
                        # Points
                        points_element = meta_row.select_one('span.score')
                        points = int(points_element.text.split()[0]) if points_element else 0

                        # Author
                        author_element = meta_row.select_one('a.hnuser')
                        author = author_element.text if author_element else None

                        # Time posted
                        time_element = meta_row.select_one('span.age')
                        time_posted = time_element.get('title', time_element.text) if time_element else None

                        # Comments
                        comments_links = meta_row.select('a')
                        comments_count = 0
                        for link in comments_links:
                            if 'comment' in link.text.lower():
                                try:
                                    comments_count = int(link.text.split()[0].replace('\xa0', ''))
                                except (ValueError, IndexError):
                                    comments_count = 0
                                break
                    else:
                        points = 0
                        author = None
                        time_posted = None
                        comments_count = 0

                    # Build HN URL
                    hn_url = f"{self.hn_base_url}/item?id={story_id}" if story_id else ""

                    # Make URL absolute if relative
                    if url and not url.startswith('http'):
                        url = f"{self.hn_base_url}/{url}"

                    story = {
                        "rank": i,
                        "id": story_id,
                        "title": title,
                        "url": url,
                        "domain": domain,
                        "points": points,
                        "author": author,
                        "time_posted": time_posted,
                        "comments_count": comments_count,
                        "hn_url": hn_url
                    }

                    stories.append(story)

                except Exception as e:
                    logger.warning(f"Error parsing story {i}: {e}")
                    continue

            logger.info(f"Scraped {len(stories)} stories from Hacker News")
            return stories

        except Exception as e:
            logger.error(f"Error scraping HN stories: {e}")
            return []

    def _analyze_stories_with_ai(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze stories using AI to identify most significant ones

        Args:
            stories: List of story dictionaries

        Returns:
            Dict with highlighted stories and analysis
        """
        try:
            # Prepare stories for AI (simplified format)
            stories_for_ai = []
            for story in stories:
                stories_for_ai.append({
                    "rank": story["rank"],
                    "title": story["title"],
                    "domain": story.get("domain"),
                    "points": story["points"],
                    "comments": story["comments_count"]
                })

            # Create prompt
            prompt = f"""
You are an expert tech analyst reviewing today's Hacker News front page stories.

Analyze these {len(stories_for_ai)} stories and select the TOP 5-10 most significant ones that developers and tech professionals should pay attention to.

Consider:
1. **Tech relevance** - Innovation, new technologies, tools, or frameworks
2. **Industry impact** - Breaking news, major announcements, market shifts
3. **Community engagement** - High points/comments indicate strong interest
4. **Emerging trends** - Early signals of important developments
5. **Practical value** - Useful knowledge, tutorials, insights

Stories:
{json.dumps(stories_for_ai, indent=2)}

Return a JSON object with this exact format:
{{
  "selected_story_ranks": [1, 3, 5],
  "full_analysis": "2-3 paragraph overview of key themes and trends in today's stories",
  "story_analyses": {{
    "1": {{
      "significance": "Why this story matters (1 sentence)",
      "insights": "Key takeaways (1-2 sentences)",
      "community_interest": "Why the community cares (1 sentence)"
    }},
    "3": {{ ... }},
    ...
  }}
}}

Return ONLY the JSON object, no other text.
"""

            # Call AI API
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/funding-scraper',
                'X-Title': 'HackerNews Story Analyzer'
            }

            data = {
                'model': self.default_model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 3000,
                'temperature': 0.3
            }

            response = requests.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code != 200:
                logger.error(f"AI API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"API error: {response.status_code}"
                }

            # Parse AI response
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()

            # Clean up response
            if ai_response.startswith('```'):
                ai_response = ai_response.split('\n', 1)[1]
            if ai_response.endswith('```'):
                ai_response = ai_response.rsplit('\n', 1)[0]
            if ai_response.startswith('json'):
                ai_response = ai_response[4:].strip()

            analysis_data = json.loads(ai_response)

            # Build highlighted stories list
            highlighted_stories = []
            selected_ranks = analysis_data.get("selected_story_ranks", [])
            story_analyses = analysis_data.get("story_analyses", {})

            for rank in selected_ranks:
                # Find the story with this rank
                story = next((s for s in stories if s["rank"] == rank), None)
                if story:
                    story_copy = story.copy()
                    # Add AI analysis if available
                    if str(rank) in story_analyses:
                        story_copy["analysis"] = story_analyses[str(rank)]
                    highlighted_stories.append(story_copy)

            return {
                "success": True,
                "highlighted_stories": highlighted_stories,
                "full_analysis": analysis_data.get("full_analysis", "")
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "success": False,
                "message": "Failed to parse AI response"
            }
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                "success": False,
                "message": str(e)
            }


if __name__ == "__main__":
    # Test the service
    import logging
    logging.basicConfig(level=logging.INFO)

    service = HackerNewsService()
    print("\n=== Testing HackerNewsService ===\n")

    result = service.get_top_analyzed_stories(story_limit=20)

    if result["success"]:
        print(f"✅ Success! Found {result['total_scraped']} stories\n")
        print(f"Top {len(result['stories'])} stories:")
        for story in result['stories']:
            print(f"  #{story['rank']}: {story['title']}")
            print(f"    Points: {story['points']}, Comments: {story['comments_count']}")
            print(f"    URL: {story['url']}\n")
    else:
        print(f"❌ Failed: {result['message']}")
