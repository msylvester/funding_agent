"""
Graph construction for GitHub workflow
"""

from langgraph.graph import StateGraph, START, END
from services.workflows.github.state import GitHubState
from services.workflows.github.nodes.fetch import fetch_trending_node, fetch_awesome_node
from services.workflows.github.nodes.aggregate import aggregate_repos_node
from services.workflows.github.nodes.enrich import enrich_details_node
from services.workflows.github.nodes.select import select_must_see_node
from services.workflows.github.conditions import should_enrich


def create_github_workflow() -> StateGraph:
    """
    Build the LangGraph workflow for GitHub data processing

    Graph structure:
        START → fetch_trending (parallel) ─┐
              → fetch_awesome  (parallel) ─┤
                                           ↓
                                    aggregate_repos → should_enrich? → [enrich_details] → select_must_see → END

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(GitHubState)

    # Add all nodes
    graph.add_node("fetch_trending", fetch_trending_node)
    graph.add_node("fetch_awesome", fetch_awesome_node)
    graph.add_node("aggregate_repos", aggregate_repos_node)
    graph.add_node("enrich_details", enrich_details_node)
    graph.add_node("select_must_see", select_must_see_node)

    # Define parallel entry points
    graph.add_edge(START, "fetch_trending")
    graph.add_edge(START, "fetch_awesome")

    # Both fetch nodes feed into aggregation
    graph.add_edge("fetch_trending", "aggregate_repos")
    graph.add_edge("fetch_awesome", "aggregate_repos")

    # Conditional enrichment path (on aggregated data)
    graph.add_conditional_edges(
        "aggregate_repos",
        should_enrich,
        {
            "enrich": "enrich_details",
            "skip_enrich": "select_must_see"
        }
    )

    # Continue flow after enrichment
    graph.add_edge("enrich_details", "select_must_see")

    # End at must_see selection
    graph.add_edge("select_must_see", END)

    return graph.compile()
