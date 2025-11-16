"""
LangGraph-based workflow for GitHub open source data processing
Replaces sequential execution with DAG-based parallel processing

REFACTORED: This module now imports from the modular workflows/github/ structure.
All functionality is preserved for backward compatibility.
"""

# Import everything from the refactored structure
from services.github_workflows.github.state import GitHubState
from services.github_workflows.github.nodes.fetch import fetch_trending_node, fetch_awesome_node
from services.github_workflows.github.nodes.enrich import enrich_details_node
from services.github_workflows.github.nodes.select import select_must_see_node
from services.github_workflows.github.conditions import should_enrich
from services.github_workflows.github.graph import create_github_workflow
from services.github_workflows.github.runner import run_github_workflow

# Re-export for backward compatibility
__all__ = [
    'GitHubState',
    'fetch_trending_node',
    'fetch_awesome_node',
    'enrich_details_node',
    'select_must_see_node',
    'should_enrich',
    'create_github_workflow',
    'run_github_workflow'
]

# Keep main execution block for direct script execution
if __name__ == "__main__":
    import logging

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
