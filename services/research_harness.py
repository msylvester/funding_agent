"""
Research Agent Evaluation Harness

Run this from the parent directory:
    cd /Users/mikress/funding_scraper
    python3 services/research_harness.py
"""
import asyncio
import json
import os
import sys

# Add parent directory to path to enable services. imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Remove the services directory from sys.path to avoid shadowing the agents library
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

from services.local_research_workflow import run_research_workflow

TEST_CASES = [
    {
        "input": "are there any companies that invovle microtrucks that have recently been fudned",
        "expected": {
            "company_names": ["Also", "Telo"],
            "min_companies": 2
        }
    }
]


async def run_research_tests():
    """Runs test cases through run_research_workflow() and prints results"""
    results = []

    for case in TEST_CASES:
        query = case["input"]
        expected_companies = case["expected"]["company_names"]
        expected_min = case["expected"]["min_companies"]

        try:
            result = await run_research_workflow(query)

            # Extract company names from the result
            companies = result.get("research", {}).get("companies", [])
            actual_company_names = [c.get("company_name", "") for c in companies]
            actual_count = len(actual_company_names)

            # Check if expected companies are in the actual results
            found_companies = [name for name in expected_companies if name in actual_company_names]
            status = "✅ PASS" if actual_count >= expected_min else "❌ FAIL"

            results.append([query, expected_companies, found_companies, expected_min, actual_count, status, actual_company_names])

        except Exception as e:
            results.append([query, expected_companies, [], expected_min, "ERROR", "❌ FAIL", str(e)])

    print("\n=== RESEARCH AGENT TEST RESULTS ===\n")
    for i, row in enumerate(results, 1):
        if len(row) == 7:
            query, expected_companies, found_companies, expected_min, actual_count, status, actual_names = row
            print(f"Test {i}:")
            print(f"  Query: {query}")
            print(f"  Expected Companies: {expected_companies}")
            print(f"  Found Expected: {found_companies}")
            print(f"  Expected: >= {expected_min} companies")
            print(f"  Actual: {actual_count} companies")
            print(f"  Status: {status}")
            print(f"  All Companies Found: {actual_names}")
            print()


if __name__ == "__main__":
    asyncio.run(run_research_tests())
