import asyncio
import os
import sys
from tabulate import tabulate

# Add project root to path to enable services. imports
from services.workflows.orchestrator_workflow import classify_intent

# Define your test cases
TEST_CASES = [
    {"input": "What investors would be interested in my SaaS product?", "expected": "advice"},
    {"input": "Research Tesla", "expected": "research"},
    {"input": "Tell me about SpaceX funding", "expected": "research"},
    {"input": "How should I pitch my AI startup?", "expected": "advice"},
    {"input": "Look up Stripe’s investors", "expected": "research"},
    {"input": "Should I raise a seed round now?", "expected": "advice"},
]

async def run_classification_tests():
    """Runs test cases through classify_intent() and prints results"""
    results = []

    for case in TEST_CASES:
        query = case["input"]
        expected = case["expected"]

        try:
            result = await classify_intent(query)
            predicted = result["intent"]
            reasoning = result["reasoning"]

            status = "✅ PASS" if predicted == expected else "❌ FAIL"
            results.append([query, expected, predicted, status, reasoning])

        except Exception as e:
            results.append([query, expected, "ERROR", "❌ FAIL", str(e)])

    print("\n=== INTENT CLASSIFICATION TEST RESULTS ===\n")
    print(
        tabulate(
            results,
            headers=["Query", "Expected", "Predicted", "Status", "Reasoning"],
            tablefmt="grid",
            maxcolwidths=[30, 10, 10, 8, 50],
        )
    )

if __name__ == "__main__":
    asyncio.run(run_classification_tests())

