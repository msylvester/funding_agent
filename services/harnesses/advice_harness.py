"""
Advice Agent Evaluation Harness

Run this from the parent directory:
    cd /Users/mikress/funding_scraper
    python3 services/advice_harness.py
"""
import json
import os
import sys

rom services.advice_workflow import get_investor_advice_sync

# Load test cases from advice_eval.json
eval_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'advice_eval.json')
with open(eval_path, 'r') as f:
    TEST_CASES = json.load(f)


def run_advice_tests():
    """Runs test cases through get_investor_advice_sync() and prints results"""
    results = []

    for case in TEST_CASES:
        query = case["input"]
        sector = case.get("sector", "unknown")
        confidence = case.get("confidence", 0.0)
        expected_min = case["expected"]["min_investors"]

        try:
            result = get_investor_advice_sync(query)
            actual_count = len(result["investors"])
            strategic_advice = result["strategic_advice"]

            # Truncate strategic advice for display
            advice_snippet = strategic_advice[:100] + "..." if len(strategic_advice) > 100 else strategic_advice

            status = "✅ PASS" if actual_count >= expected_min else "❌ FAIL"
            results.append([query, sector, confidence, expected_min, actual_count, status, advice_snippet])

        except Exception as e:
            results.append([query, sector, confidence, expected_min, "ERROR", "❌ FAIL", str(e)])

    print("\n=== ADVICE AGENT TEST RESULTS ===\n")
    for i, (query, sector, confidence, expected_min, actual_count, status, advice_snippet) in enumerate(results, 1):
        print(f"Test {i}:")
        print(f"  Query: {query}")
        print(f"  [SECTOR: {sector}] (confidence: {confidence:.2f})")
        print(f"  Expected: >= {expected_min} investors")
        print(f"  Actual: {actual_count} investors")
        print(f"  Status: {status}")
        print(f"  Advice Snippet: {advice_snippet}")
        print()


if __name__ == "__main__":
    run_advice_tests()
