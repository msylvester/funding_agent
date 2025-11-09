import asyncio
from tabulate import tabulate
from sector_agent import classify_sector

# Define test cases for sector classification
TEST_CASES = [
    {
        "input": "Who would be interested in my food delivery startup?",
        "expected": "Food delivery",  # Updated to match database sector
    },
    {
        "input": "I'm building an automotive AI company. What investors should I pitch?",
        "expected": "Automotive, AI",  # Updated to match database sector
    },
    {
        "input": "I'm building an accounting software startup",
        "expected": "Enterprise software",  # Updated to match database sector
    },
    {
        "input": "We're creating a SaaS platform for team collaboration",
        "expected": "Enterprise software",  # SaaS is classified as Enterprise software
    },
    {
        "input": "Our healthcare startup uses AI for diagnostics",
        "expected": "Healthcare",
    },
]


def run_sector_tests():
    """Runs test cases through classify_sector() and prints results"""
    results = []

    for case in TEST_CASES:
        query = case["input"]
        expected = case["expected"]

        try:
            result = classify_sector(query)
            predicted = result.sector
            rationale = result.rationale
            confidence = result.confidence

            status = "✅ PASS" if predicted == expected else "❌ FAIL"
            results.append([query, expected, predicted, f"{confidence:.2f}", status, rationale])

        except Exception as e:
            results.append([query, expected, "ERROR", "0.00", "❌ FAIL", str(e)])

    print("\n=== SECTOR CLASSIFICATION TEST RESULTS ===\n")
    print(
        tabulate(
            results,
            headers=["Query", "Expected", "Predicted", "Confidence", "Status", "Rationale"],
            tablefmt="grid",
            maxcolwidths=[30, 15, 15, 10, 8, 50],
        )
    )


if __name__ == "__main__":
    run_sector_tests()


