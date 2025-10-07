"""
LangGraph-based workflow for GitHub open source data processing
Replaces sequential execution with DAG-based parallel processing
"""

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
from services.open_source_data import OpenSourceDataService
from services.agents.open_source_agent import OpenSourceAgent
import logging

logger = logging.getLogger(__name__)

# State definition
class GitHubState(TypedDict):
    """State object passed through the workflow"""
    trending_repos: List[Dict[str, Any]]
    awesome_lists: List[Dict[str, Any]]
    enriched_repos: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    must_see_repos: List[Dict[str, Any]]
    query_params: Dict[str, Any]


# ============ Node Definitions ============

def fetch_trending_node(state: GitHubState) -> Dict[str, Any]:
    """
    Fetch trending repositories from GitHub
    Runs in parallel with fetch_awesome_node
    """
    logger.info("🔄 Fetching trending repositories...")
    service = OpenSourceDataService()
    params = state.get('query_params', {})

    # Extract parameters
    language = params.get('language')
    time_range = params.get('time_range', 'daily')

    repos = service.get_trending_repositories(
        language=language,
        time_range=time_range
    )

    logger.info(f"✅ Fetched {len(repos)} trending repositories")
    return {"trending_repos": repos}


def fetch_awesome_node(state: GitHubState) -> Dict[str, Any]:
    """
    Fetch awesome lists from GitHub
    Runs in parallel with fetch_trending_node
    """
    logger.info("🔄 Fetching awesome lists...")
    service = OpenSourceDataService()
    params = state.get('query_params', {})

    category = params.get('awesome_category')
    awesome = service.get_awesome_lists(category=category)

    logger.info(f"✅ Fetched {len(awesome)} awesome lists")
    return {"awesome_lists": awesome}


def enrich_details_node(state: GitHubState) -> Dict[str, Any]:
    """
    Enrich high-quality repositories with detailed information
    Only processes repos that meet quality threshold (>50 stars)
    """
    logger.info("🔄 Enriching repository details...")
    service = OpenSourceDataService()
    repos = state['trending_repos']
    enriched = []

    for repo in repos:
        stars = repo.get('stars', 0)

        if stars > 50:
            # High-quality repo: fetch detailed info
            logger.info(f"  Enriching {repo['name']} ({stars} stars)")
            details = service.get_repository_details(
                repo['owner'],
                repo['name']
            )
            if details:
                enriched.append(details)
            else:
                enriched.append(repo)  # Fallback to basic data
        else:
            # Low-quality repo: keep basic data
            enriched.append(repo)

    logger.info(f"✅ Enriched {len(enriched)} repositories")
    return {"enriched_repos": enriched}


def analyze_trends_node(state: GitHubState) -> Dict[str, Any]:
    """
    Analyze ecosystem trends using statistical methods
    Uses enriched repos if available, otherwise uses basic trending repos
    """
    logger.info("🔄 Analyzing ecosystem trends...")

    # Use enriched repos if available, otherwise fall back to trending repos
    repos = state.get('enriched_repos', state.get('trending_repos', []))

    if not repos:
        logger.warning("⚠️ No repositories to analyze")
        return {"analysis": {}}

    # Statistical analysis
    from collections import Counter

    languages = [r.get('language') for r in repos if r.get('language')]
    topics = []
    for r in repos:
        topics.extend(r.get('topics', []))

    total_stars = sum(r.get('stars', 0) for r in repos)
    avg_stars = total_stars // len(repos) if repos else 0

    language_counts = Counter(languages)
    topic_counts = Counter(topics)

    analysis = {
        "total_repos_analyzed": len(repos),
        "trending_languages": [
            {"language": lang, "count": count}
            for lang, count in language_counts.most_common(5)
        ],
        "hot_topics": [
            {"topic": topic, "count": count}
            for topic, count in topic_counts.most_common(10)
        ],
        "average_stars": avg_stars,
        "total_stars": total_stars,
        "summary": f"Analyzed {len(repos)} repositories. Top language: {language_counts.most_common(1)[0][0] if language_counts else 'N/A'}"
    }

    logger.info(f"✅ Analysis complete: {analysis['summary']}")
    return {"analysis": analysis}


def select_must_see_node(state: GitHubState) -> Dict[str, Any]:
    """
    Select must-see repositories using AI agent
    Uses existing OpenSourceAgent for selection
    """
    logger.info("🔄 Selecting must-see repositories...")

    # Use enriched repos if available, otherwise fall back to trending repos
    repos = state.get('enriched_repos', state.get('trending_repos', []))

    if not repos:
        logger.warning("⚠️ No repositories to select from")
        return {"must_see_repos": []}

    # Use existing OpenSourceAgent for AI-powered selection
    agent = OpenSourceAgent()
    must_see = agent.select_top_repositories(repos, top_n=5)

    logger.info(f"✅ Selected {len(must_see)} must-see repositories")
    return {"must_see_repos": must_see}


# ============ Conditional Edge Logic ============

def should_enrich(state: GitHubState) -> str:
    """
    Decide whether to enrich repositories based on quality threshold

    Returns:
        "enrich" if >= 5 repos have >50 stars
        "skip_enrich" otherwise
    """
    repos = state.get('trending_repos', [])

    if not repos:
        return "skip_enrich"

    high_quality_count = sum(1 for r in repos if r.get('stars', 0) > 50)

    if high_quality_count >= 5:
        logger.info(f"🎯 Found {high_quality_count} high-quality repos → enriching")
        return "enrich"
    else:
        logger.info(f"⚡ Only {high_quality_count} high-quality repos → skipping enrichment")
        return "skip_enrich"


# ============ Graph Construction ============

def create_github_workflow() -> StateGraph:
    """
    Build the LangGraph workflow for GitHub data processing

    Graph structure:
        START → fetch_trending (parallel) → should_enrich? → [enrich_details] → analyze_trends → select_must_see → END
              → fetch_awesome  (parallel) ────────────────────────────────────┘

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(GitHubState)

    # Add all nodes
    graph.add_node("fetch_trending", fetch_trending_node)
    graph.add_node("fetch_awesome", fetch_awesome_node)
    graph.add_node("enrich_details", enrich_details_node)
    graph.add_node("analyze_trends", analyze_trends_node)
    graph.add_node("select_must_see", select_must_see_node)

    # Define parallel entry points
    graph.add_edge(START, "fetch_trending")
    graph.add_edge(START, "fetch_awesome")

    # Conditional enrichment path
    graph.add_conditional_edges(
        "fetch_trending",
        should_enrich,
        {
            "enrich": "enrich_details",
            "skip_enrich": "analyze_trends"
        }
    )

    # Continue flow after enrichment
    graph.add_edge("enrich_details", "analyze_trends")
    graph.add_edge("analyze_trends", "select_must_see")

    # Awesome lists join back to main flow (not blocking)
    # They're available in state but don't gate the workflow

    # End at must_see selection
    graph.add_edge("select_must_see", END)

    return graph.compile()


# ============ Execution Functions ============

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
        "enriched_repos": [],
        "analysis": {},
        "must_see_repos": []
    }

    logger.info("🚀 Starting GitHub workflow...")
    result = workflow.invoke(initial_state)
    logger.info("✅ Workflow complete!")

    return result


# ============ Main Execution ============

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

    print("\n📉 ECOSYSTEM ANALYSIS")
    analysis = result['analysis']
    print(f"  Total analyzed: {analysis.get('total_repos_analyzed', 0)}")
    print(f"  Average stars: {analysis.get('average_stars', 0)}")
    print(f"  Summary: {analysis.get('summary', 'N/A')}")

    print("\n  Top Languages:")
    for lang_data in analysis.get('trending_languages', [])[:3]:
        print(f"    - {lang_data['language']}: {lang_data['count']} repos")

    print("\n  Hot Topics:")
    for topic_data in analysis.get('hot_topics', [])[:5]:
        print(f"    - {topic_data['topic']}: {topic_data['count']} repos")

    print("\n🌟 MUST-SEE REPOSITORIES\n")
    for i, repo in enumerate(result['must_see_repos'], 1):
        print(f"{i}. {repo['name']} ({repo['stars']} stars)")
        print(f"   {repo.get('description', 'No description')[:80]}...")
        if 'ai_reasoning' in repo:
            print(f"   💡 {repo['ai_reasoning']}")
        print()

    print("="*60 + "\n")
