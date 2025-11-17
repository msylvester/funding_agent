"""
MongoDB tools for AI agents to search funded companies and investors
These functions are designed to be used as tools by AI agents in workflows
"""

from typing import List, Dict, Any
from pymongo import MongoClient
from config.settings import DATABASE_CONFIG
import logging
from agents import function_tool

logger = logging.getLogger(__name__)


def get_mongo_client():
    """Get MongoDB client connection"""
    try:
        client = MongoClient(DATABASE_CONFIG['mongodb_uri'])
        return client
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise


@function_tool
def search_funded_companies_by_sector(sector: str) -> List[Dict[str, Any]]:
    """
    Search for funded companies by sector/industry.

    This tool searches the MongoDB database for companies that received funding
    in the specified sector. Returns company details including investors.

    Args:
        sector: Industry sector to search for (e.g., "SaaS", "AI", "fintech", "healthcare", "e-commerce", "food delivery")

    Returns:
        List of company records with fields:
            - company_name: Name of the company
            - sector: Industry sector
            - funding_amount: Amount raised
            - series: Funding series (seed, Series A, B, etc.)
            - investors: Comma-separated list of investor names
            - founded_year: Year company was founded
            - total_funding: Total funding raised to date
            - valuation: Company valuation
            - description: Company description
            - url: Source article URL
            - date: Date of funding announcement

    Example:
        results = search_funded_companies_by_sector("food delivery")
        # Returns companies like Calo, Kitopi, etc. with their investor details
    """
    try:
        client = get_mongo_client()
        db = client[DATABASE_CONFIG['database_name']]
        collection = db[DATABASE_CONFIG['collection_name']]

        # Case-insensitive regex search for sector
        query = {
            "sector": {"$regex": sector, "$options": "i"}
        }

        # Find companies matching the sector
        companies = list(collection.find(query).limit(50))  # Limit to 50 results

        # Convert ObjectId to string and clean up results
        results = []
        for company in companies:
            # Remove MongoDB ObjectId
            if '_id' in company:
                del company['_id']

            results.append({
                "company_name": company.get("company_name", "Unknown"),
                "sector": company.get("sector", "Unknown"),
                "funding_amount": company.get("funding_amount", "N/A"),
                "series": company.get("series", "N/A"),
                "investors": company.get("investors", ""),  # Comma-separated investor names
                "founded_year": company.get("founded_year", "N/A"),
                "total_funding": company.get("total_funding", "N/A"),
                "valuation": company.get("valuation", "N/A"),
                "description": company.get("description", ""),
                "url": company.get("url", ""),
                "date": company.get("date", "N/A")
            })

        client.close()

        logger.info(f"Found {len(results)} companies in sector: {sector}")
        return results

    except Exception as e:
        logger.error(f"Error searching companies by sector '{sector}': {e}")
        return []


@function_tool
def get_investors_for_sector(sector: str) -> List[Dict[str, Any]]:
    """
    Get aggregated investor activity for a specific sector.

    This tool analyzes funding data to find which investors are most active
    in a given sector and how many companies they've invested in.

    Args:
        sector: Industry sector to analyze (e.g., "SaaS", "AI", "fintech")

    Returns:
        List of investor activity records with fields:
            - investor_name: Name of the investor/firm
            - investment_count: Number of companies invested in within this sector
            - companies: List of company names they've invested in

    Example:
        results = get_investors_for_sector("AI")
        # Returns investors like Sequoia, a16z, etc. with their AI portfolio
    """
    try:
        client = get_mongo_client()
        db = client[DATABASE_CONFIG['database_name']]
        collection = db[DATABASE_CONFIG['collection_name']]

        # Find all companies in the sector
        query = {
            "sector": {"$regex": sector, "$options": "i"},
            "investors": {"$exists": True, "$ne": ""}
        }

        companies = list(collection.find(query).limit(100))

        # Aggregate investor data
        investor_map = {}

        for company in companies:
            company_name = company.get("company_name", "Unknown")
            investors_str = company.get("investors", "")

            # Split comma-separated investors
            if investors_str:
                investor_names = [inv.strip() for inv in investors_str.split(",") if inv.strip()]

                for investor_name in investor_names:
                    if investor_name not in investor_map:
                        investor_map[investor_name] = {
                            "investor_name": investor_name,
                            "investment_count": 0,
                            "companies": []
                        }

                    investor_map[investor_name]["investment_count"] += 1
                    investor_map[investor_name]["companies"].append(company_name)

        # Convert to list and sort by investment count
        results = sorted(
            investor_map.values(),
            key=lambda x: x["investment_count"],
            reverse=True
        )

        client.close()

        logger.info(f"Found {len(results)} investors active in sector: {sector}")
        return results

    except Exception as e:
        logger.error(f"Error getting investors for sector '{sector}': {e}")
        return []


@function_tool
def search_companies_by_name(company_name: str) -> List[Dict[str, Any]]:
    """
    Search for companies by name.

    Args:
        company_name: Company name to search for

    Returns:
        List of matching company records
    """
    try:
        client = get_mongo_client()
        db = client[DATABASE_CONFIG['database_name']]
        collection = db[DATABASE_CONFIG['collection_name']]

        # Case-insensitive regex search
        query = {
            "company_name": {"$regex": company_name, "$options": "i"}
        }

        companies = list(collection.find(query).limit(20))

        # Clean up results
        results = []
        for company in companies:
            if '_id' in company:
                del company['_id']
            results.append(company)

        client.close()

        logger.info(f"Found {len(results)} companies matching: {company_name}")
        return results

    except Exception as e:
        logger.error(f"Error searching companies by name '{company_name}': {e}")
        return []


# Make functions available for import
__all__ = [
    'search_funded_companies_by_sector',
    'get_investors_for_sector',
    'search_companies_by_name'
]


# Testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("\n=== Testing MongoDB Tools ===\n")

    # Test 1: Search companies by sector
    print("Test 1: Searching for 'food delivery' companies...")
    companies = search_funded_companies_by_sector("food delivery")
    print(f"Found {len(companies)} companies")
    for company in companies[:3]:
        print(f"  - {company['company_name']}: {company['investors']}")

    print("\nTest 2: Getting investors for 'AI' sector...")
    investors = get_investors_for_sector("AI")
    print(f"Found {len(investors)} investors")
    for investor in investors[:5]:
        print(f"  - {investor['investor_name']}: {investor['investment_count']} investments")
        print(f"    Companies: {', '.join(investor['companies'][:3])}")

    print("\n=== Tests complete ===\n")
