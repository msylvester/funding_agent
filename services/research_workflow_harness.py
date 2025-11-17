#!/usr/bin/env python3
"""
Test harness for research_workflow.py

This harness tests the research workflow with the same queries used in rag_service_agent.py
"""

import asyncio
import sys
import os

# Path setup for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.research_workflow import run_research_workflow


# Test data - same queries as in rag_service_agent.py
TEST_QUERIES = [
    # should at least select Vast Data
    {
        "query": "storage technology",
        "expected": "Vast Data",
        "description": "Should find storage technology companies like Vast Data"
    },
    # should at least select tahoe therapeutics
    {
        "query": "medical research",
        "expected": "Tahoe",
        "description": "Should find medical research companies like Tahoe Therapeutics"
    },
    # should at least select uno platform
    {
        "query": "enterprise grade developer tools",
        "expected": "Uno",
        "description": "Should find developer tools companies like Uno Platform"
    },
    # should at least describe Palabar
    {
        "query": "ai powered speech translation",
        "expected": "Palabra",
        "description": "Should find AI speech translation companies like Palabra AI"
    },
    # should at least describe 8 sleep
    {
        "query": "ai powered sleep tech",
        "expected": "Eight Sleep",
        "description": "Should find AI sleep tech companies like Eight Sleep"
    },
]


async def run_single_test(query_data: dict) -> dict:
    """Run a single test case."""
    query = query_data["query"]
    expected = query_data["expected"]
    description = query_data["description"]

    print(f"\nQuery: {query}")
    print(f"Expected to find: {expected}")
    print(f"Description: {description}")
    print("-" * 50)

    try:
        result = await run_research_workflow(query)

        # Check research results
        research = result.get("research", {})
        companies = research.get("companies", [])

        # Check summary results
        summary = result.get("summary", {})

        print(f"Research Results:")
        print(f"  Companies found: {len(companies)}")

        for i, company in enumerate(companies[:5]):  # Show first 5
            print(f"  {i+1}. {company.get('company_name', 'Unknown')}")
            print(f"     Industry: {company.get('industry', 'N/A')}")
            print(f"     Location: {company.get('headquarters_location', 'N/A')}")

        print(f"\nSummary Result:")
        print(f"  Company: {summary.get('company_name', 'N/A')}")
        print(f"  Industry: {summary.get('industry', 'N/A')}")
        print(f"  Description: {summary.get('description', 'N/A')[:200]}...")

        # Check if expected result is in the output
        all_text = str(result).lower()
        found_expected = expected.lower() in all_text

        return {
            "query": query,
            "success": True,
            "found_expected": found_expected,
            "companies_count": len(companies),
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
            "found_expected": False,
            "companies_count": 0
        }


async def run_all_tests():
    """Run all test cases."""
    print("Testing Research Workflow...")
    print("=" * 50)

    results = []

    for query_data in TEST_QUERIES:
        result = await run_single_test(query_data)
        results.append(result)
        print("=" * 50)

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    found_expected = sum(1 for r in results if r["found_expected"])

    print(f"Total tests: {total}")
    print(f"Successful executions: {successful}/{total}")
    print(f"Found expected results: {found_expected}/{total}")

    print("\nDetailed Results:")
    for i, result in enumerate(results):
        status = "PASS" if result["success"] and result["found_expected"] else "FAIL"
        print(f"  {i+1}. {result['query']}: {status}")
        if not result["success"]:
            print(f"     Error: {result.get('error', 'Unknown')}")
        elif not result["found_expected"]:
            print(f"     Warning: Expected result not found in output")

    return results


def run_tests_sync():
    """Synchronous wrapper for run_all_tests()."""
    return asyncio.run(run_all_tests())


if __name__ == "__main__":
    run_tests_sync()
