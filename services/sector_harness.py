import asyncio
from sector_agent import classify_sector

# Define test cases for sector classification
TEST_CASES = [

        {
      "input": "Who would invest in my finntech company",
      "expected": "Technology",  # But AI might classify as "Healthcare" or "Fintech"
  },
 

        {
      "input": "We're building an fintech platform",
      "expected": "Technology",  # But AI might classify as "Healthcare" or "Fintech"
  },
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

    print("\n=== SECTOR CLASSIFICATION TEST RESULTS ===\n")

    for i, case in enumerate(TEST_CASES, 1):
        query = case["input"]
        expected = case["expected"]

        try:
            result = classify_sector(query)
            predicted = result.sector
            rationale = result.rationale
            confidence = result.confidence

            status = "✅ PASS" if predicted == expected else "❌ FAIL"
            results.append([query, expected, predicted, f"{confidence:.2f}", status, rationale])

            # Print immediately after each classification
            print(f"Test {i}:")
            print(f"  Query: {query}")
            print(f"  Expected: {expected}")
            print(f"  Predicted: {predicted}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Status: {status}")
            print(f"  Rationale: {rationale}")
            print()

        except Exception as e:
            results.append([query, expected, "ERROR", "0.00", "❌ FAIL", str(e)])

            # Print error immediately
            print(f"Test {i}:")
            print(f"  Query: {query}")
            print(f"  Expected: {expected}")
            print(f"  Predicted: ERROR")
            print(f"  Confidence: 0.00")
            print(f"  Status: ❌ FAIL")
            print(f"  Rationale: {str(e)}")
            print()

    # Print summary
    passed = sum(1 for r in results if r[4] == "✅ PASS")
    failed = len(results) - passed
    print(f"=== SUMMARY ===")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    run_sector_tests()


