import asyncio
import argparse
from sector_agent import classify_sector, get_valid_sectors

# Define test cases for sector classification
TEST_CASES = [
     {
      "input": "Who would invest in my umbrellac compay",
      "expected": "Social Media",  # But AI might classify as "Healthcare" or "Fintech"
  },
 
        {
      "input": "Who would invest in my social media startup",
      "expected": "Social Media",  # But AI might classify as "Healthcare" or "Fintech"
  },
 
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


def print_valid_sectors():
    """Prints all valid sectors retrieved from MongoDB"""
    print("\n=== VALID SECTORS FROM DATABASE ===\n")

    try:
        sectors = get_valid_sectors()
        print(f"Total sectors found: {len(sectors)}\n")

        for i, sector in enumerate(sectors, 1):
            print(f"{i:3d}. {sector}")

        print(f"\n{'='*40}")
        print(f"Total: {len(sectors)} sectors")
        print(f"{'='*40}\n")

    except Exception as e:
        print(f"❌ Error retrieving sectors: {e}")


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
    parser = argparse.ArgumentParser(description="Sector classification testing harness")
    parser.add_argument(
        "--print_only",
        type=str,
        choices=["sectors"],
        help="Print specific information without running tests. Options: 'sectors' (prints all valid sectors from DB)"
    )

    args = parser.parse_args()

    if args.print_only == "sectors":
        print_valid_sectors()
    else:
        run_sector_tests()


