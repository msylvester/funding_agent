"""
Execution and CLI for GitHub workflow
"""

from typing import Dict, Any
import logging
from services.github_workflows.github.graph import create_github_workflow

logger = logging.getLogger(__name__)


def run_github_workflow(
    language: str = None,
    time_range: str = "daily",
    awesome_category: str = None
) -> Dict[str, Any]:
    """
    Execute the GitHub data workflow

    Args:
        language: Programming language filter (optional)
        time_range: Time range for trending (daily, weekly, monthly)
        awesome_category: Category for awesome lists (optional)

    Returns:
        Final state with all processed data
    """
    workflow = create_github_workflow()

    initial_state = {
        "query_params": {
            "language": language,
            "time_range": time_range,
            "awesome_category": awesome_category
        },
        "trending_repos": [],
        "awesome_lists": [],
        "aggregated_repos": [],
        "enriched_repos": [],
        "analysis": {},
        "must_see_repos": []
    }

    logger.info("🚀 Starting GitHub workflow...")
    result = workflow.invoke(initial_state)
    logger.info("✅ Workflow complete!")

    return result


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*60)
    print("GitHub Open Source Data - LangGraph Workflow")
    print("="*60 + "\n")

    # Run workflow
    result = run_github_workflow(time_range="daily")

    # Display results
    print("\n📊 WORKFLOW RESULTS\n")

    print(f"📈 Trending Repositories: {len(result['trending_repos'])}")
    print(f"⭐ Awesome Lists: {len(result['awesome_lists'])}")
    print(f"🔍 Enriched Repositories: {len(result['enriched_repos'])}")

    print("\n🌟 MUST-SEE REPOSITORIES\n")
    for i, repo in enumerate(result['must_see_repos'], 1):
        print(f"{i}. {repo['name']} ({repo['stars']} stars)")
        print(f"   {repo.get('description', 'No description')[:80]}...")
        if 'ai_reasoning' in repo:
            print(f"   💡 {repo['ai_reasoning']}")
        print()

    print("="*60 + "\n")
