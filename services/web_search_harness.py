#!/usr/bin/env python3
"""
Integration test harness for RAG -> Web Search pipeline.

This harness tests the full research workflow:
1. RAG agent searches the vector database for companies
2. Web research agent gathers additional info via web search
"""

import asyncio
import sys
import os

# Path setup for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents import Runner, RunConfig, TResponseInputItem
from services.research_workflow import web_research_agent, rag_research_agent


# Test data - search queries to find companies
TEST_DATA = [
    {
        "input": "biotech AI drug discovery startups",
        "expected_in_results": ["biotech", "drug", "AI"],
        "description": "Should find biotech companies using AI for drug discovery"
    },
    {
        "input": "data storage infrastructure companies",
        "expected_in_results": ["data", "storage"],
        "description": "Should find data storage technology companies"
    },
    {
        "input": "ai sleep",
        "expected_in_results": ["sleep", "wellness"],
        "description": "Should find sleep tech or wellness companies"
    },
]


async def run_rag_research_harness(query: str) -> dict:
    """
    Run the RAG research agent for a given query.

    Args:
        query: Search query to find companies in RAG database

    Returns:
        Dictionary containing the RAG research results
    """
    rag_history: list[TResponseInputItem] = [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": query}],
        }
    ]

    result = await Runner.run(
        rag_research_agent,
        input=rag_history,
        run_config=RunConfig(
            trace_metadata={
                "__trace_source__": "integration-harness",
                "workflow_id": "integration_harness_test",
            }
        ),
    )

    return {
        "output_text": result.final_output.json(),
        "output_parsed": result.final_output.model_dump(),
    }


async def run_web_search_harness(company_names: list[str]) -> dict:
    """
    Run the web research agent for given company names.

    Args:
        company_names: List of company names to research

    Returns:
        Dictionary containing the web research results
    """
    if not company_names:
        return {"output_parsed": {"companies": {}}}

    web_research_prompt = ', '.join(company_names)

    web_research_history: list[TResponseInputItem] = [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": web_research_prompt}],
        }
    ]

    result = await Runner.run(
        web_research_agent,
        input=web_research_history,
        run_config=RunConfig(
            trace_metadata={
                "__trace_source__": "integration-harness",
                "workflow_id": "integration_harness_test",
            }
        ),
    )

    return {
        "output_text": result.final_output.json(),
        "output_parsed": result.final_output.model_dump(),
    }


async def run_integration_harness(query: str) -> dict:
    """
    Run the full RAG -> Web Search pipeline.

    Args:
        query: Search query to find and research companies

    Returns:
        Dictionary containing both RAG and web research results
    """
    # Step 1: RAG search
    rag_result = await run_rag_research_harness(query)

    # Step 2: Extract company names from RAG results
    rag_companies = rag_result["output_parsed"].get("companies", [])
    company_names = [c["company_name"] for c in rag_companies]

    # Step 3: Web research on found companies
    web_result = await run_web_search_harness(company_names)

    return {
        "rag_research": rag_result["output_parsed"],
        "web_research": web_result["output_parsed"],
        "company_names_found": company_names,
    }


async def run_single_test(test_data: dict) -> dict:
    """Run a single integration test case."""
    query = test_data["input"]
    expected_keywords = test_data["expected_in_results"]
    description = test_data["description"]

    print(f"\nQuery: {query}")
    print(f"Expected keywords: {expected_keywords}")
    print(f"Description: {description}")
    print("-" * 50)

    try:
        result = await run_integration_harness(query)

        # RAG Results
        rag_companies = result["rag_research"].get("companies", [])
        print(f"\nRAG RESEARCH RESULTS:")
        print(f"  Companies found: {len(rag_companies)}")

        for company in rag_companies:
            print(f"\n  - {company.get('company_name', 'Unknown')}")
            print(f"     Description: {company.get('description', 'N/A')[:80]}...")
            print(f"     Industry: {company.get('industry', 'N/A')}")
            if company.get('relevance_score'):
                print(f"     Relevance: {company.get('relevance_score')}")

        # Web Research Results
        web_companies = result["web_research"].get("companies", {})
        print(f"\nWEB RESEARCH RESULTS:")
        print(f"  Companies researched: {len(web_companies)}")

        for company_name, details in web_companies.items():
            print(f"\n  - {company_name}")
            print(f"     Website: {details.get('website', 'N/A')}")
            print(f"     Size: {details.get('company_size', 'N/A')}")
            print(f"     Location: {details.get('headquarters_location', 'N/A')}")
            print(f"     Founded: {details.get('founded_year', 'N/A')}")
            print(f"     Industry: {details.get('industry', 'N/A')}")
            print(f"     Description: {details.get('description', 'N/A')[:100]}...")

        # Validate results
        all_text = str(result).lower()
        keywords_found = sum(1 for kw in expected_keywords if kw.lower() in all_text)
        keywords_match = keywords_found >= len(expected_keywords) // 2  # At least half the keywords

        # Validate schema completeness for web research
        schema_complete = True
        for company_name, details in web_companies.items():
            required_fields = ["website", "company_size", "headquarters_location", "founded_year", "industry", "description"]
            for field in required_fields:
                if field not in details or details[field] is None:
                    schema_complete = False
                    print(f"\n  Warning: Missing field '{field}' for {company_name}")

        # Pipeline success metrics
        rag_found_companies = len(rag_companies) > 0
        web_enriched_companies = len(web_companies) > 0
        pipeline_connected = len(rag_companies) == len(web_companies) if rag_found_companies else True

        print(f"\n  Pipeline Status:")
        print(f"    RAG found companies: {rag_found_companies}")
        print(f"    Web enriched companies: {web_enriched_companies}")
        print(f"    Pipeline connected: {pipeline_connected}")
        print(f"    Keywords matched: {keywords_found}/{len(expected_keywords)}")

        return {
            "query": query,
            "success": True,
            "rag_companies_count": len(rag_companies),
            "web_companies_count": len(web_companies),
            "keywords_match": keywords_match,
            "schema_complete": schema_complete,
            "pipeline_connected": pipeline_connected,
            "result": result
        }

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "rag_companies_count": 0,
            "web_companies_count": 0,
            "keywords_match": False,
            "schema_complete": False,
            "pipeline_connected": False
        }


async def run_all_tests():
    """Run all integration test cases."""
    print("Testing RAG -> Web Search Integration Pipeline...")
    print("=" * 60)

    results = []

    for test_data in TEST_DATA:
        result = await run_single_test(test_data)
        results.append(result)
        print("=" * 60)

    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    rag_found = sum(1 for r in results if r["rag_companies_count"] > 0)
    web_enriched = sum(1 for r in results if r["web_companies_count"] > 0)
    keywords_matched = sum(1 for r in results if r["keywords_match"])
    schema_complete = sum(1 for r in results if r.get("schema_complete", False))
    pipeline_connected = sum(1 for r in results if r.get("pipeline_connected", False))

    print(f"Total tests: {total}")
    print(f"Successful executions: {successful}/{total}")
    print(f"RAG found companies: {rag_found}/{total}")
    print(f"Web enriched companies: {web_enriched}/{total}")
    print(f"Keywords matched: {keywords_matched}/{total}")
    print(f"Schema complete: {schema_complete}/{total}")
    print(f"Pipeline connected (RAG → Web): {pipeline_connected}/{total}")

    print("\nDetailed Results:")
    for i, result in enumerate(results):
        if result["success"] and result["pipeline_connected"] and result["schema_complete"]:
            status = "PASS"
        elif result["success"]:
            status = "PARTIAL"
        else:
            status = "FAIL"

        print(f"  {i+1}. Query: '{result['query'][:40]}...'")
        print(f"     Status: {status}")
        print(f"     RAG: {result['rag_companies_count']} companies | Web: {result['web_companies_count']} companies")

        if not result["success"]:
            print(f"     Error: {result.get('error', 'Unknown')}")
        elif not result["pipeline_connected"]:
            print(f"     Warning: Pipeline disconnect (RAG and Web counts differ)")
        elif not result.get("schema_complete", False):
            print(f"     Warning: Schema fields incomplete")

    return results


def run_tests_sync():
    """Synchronous wrapper for run_all_tests()."""
    return asyncio.run(run_all_tests())


if __name__ == "__main__":
    run_tests_sync()
