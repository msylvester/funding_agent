#!/usr/bin/env python3
"""
Update Incomplete MongoDB Records

This script finds records with incomplete data in the MongoDB collection,
scrapes the article URL to get full content, and uses AI to extract
missing funding information.

Usage:
    python update_incomplete_records.py
    python update_incomplete_records.py --dry-run
    python update_incomplete_records.py --limit 5
"""

import os
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson import ObjectId

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system environment variables

# Import AI extraction function
from services.agents.custom.agents.agent_blog_data_struct import enhance_with_ai


class RecordUpdater:
    """Updates incomplete MongoDB records by scraping article URLs"""

    def __init__(self, db_name: str = 'funded_backup_20251105_121856', dry_run: bool = False):
        """
        Initialize the record updater

        Args:
            db_name: MongoDB database name
            dry_run: If True, don't actually update records
        """
        self.dry_run = dry_run
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

        if not self.openrouter_api_key:
            print("Warning: OPENROUTER_API_KEY not found. AI extraction will not be available.")
            if not dry_run:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    sys.exit(1)
            else:
                print("Dry-run mode enabled - continuing without API key")

        # Connect to MongoDB
        connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db['companies']

        print(f"Connected to database: {db_name}")
        print(f"Collection: companies")
        print(f"Dry run mode: {dry_run}")
        print()

    def find_incomplete_records(self) -> List[Dict[str, Any]]:
        """
        Find records with incomplete data

        Returns:
            List of incomplete records
        """
        query = {
            "$or": [
                {"company_name": {"$exists": False}},
                {"company_name": ""},
                {"company_name": "Not specified"},
                {"funding_amount": {"$exists": False}},
                {"funding_amount": ""},
                {"funding_amount": "Not specified"},
                {"description": {"$exists": False}},
                {"description": ""},
                {"sector": {"$exists": False}},
                {"sector": ""},
                {"investors": "Not specified"}
            ]
        }

        records = list(self.collection.find(query))
        print(f"Found {len(records)} incomplete records")
        return records

    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape article content from URL

        Args:
            url: Article URL

        Returns:
            Dictionary with title and content, or None if scraping fails
        """
        try:
            print(f"  Fetching: {url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = ""
            title_selectors = ['h1.entry-title', 'h1[class*="title"]', 'h1', '.entry-title']
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break

            # Extract content
            content = ""
            content_selectors = [
                '.entry-content',
                '[class*="content"]',
                '.article-content',
                'main',
                'article',
                '[class*="post"]',
                '.prose',
                '[role="main"]'
            ]

            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # Remove scripts and styles
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    content = content_element.get_text(strip=True)
                    break

            # Fallback: get content from body
            if not content:
                body = soup.find('body')
                if body:
                    for element in body(['nav', 'footer', 'aside', 'header', 'script', 'style']):
                        element.decompose()
                    content = body.get_text(strip=True)

            print(f"  Scraped {len(content)} characters")

            return {
                'title': title,
                'content': content
            }

        except Exception as e:
            print(f"  Error scraping article: {e}")
            return None

    def extract_data_with_ai(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract funding data using AI

        Args:
            title: Article title
            content: Article content

        Returns:
            Dictionary with extracted data, or None if extraction fails
        """
        if not self.openrouter_api_key:
            return None

        try:
            print(f"  Extracting data with AI...")
            extracted = enhance_with_ai(title, content, self.openrouter_api_key)

            if extracted and extracted.get('company_name') != 'Not specified':
                print(f"  ✓ Extracted: {extracted.get('company_name')} - {extracted.get('funding_amount')}")
                return extracted
            else:
                print(f"  ✗ AI could not extract meaningful data")
                return None

        except Exception as e:
            print(f"  Error extracting data with AI: {e}")
            return None

    def update_record(self, record_id: ObjectId, updates: Dict[str, Any]) -> bool:
        """
        Update a record in MongoDB

        Args:
            record_id: MongoDB ObjectId
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would update record {record_id}")
                print(f"  Updates: {updates}")
                return True

            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow()

            # Only update fields that are currently incomplete or missing
            # Build the update query to only update "Not specified" or missing fields
            update_query = {}
            for key, value in updates.items():
                # Skip if the new value is also "Not specified" or empty
                if value and value != "Not specified":
                    update_query[key] = value

            if not update_query:
                print(f"  No meaningful updates to apply")
                return False

            result = self.collection.update_one(
                {"_id": record_id},
                {"$set": update_query}
            )

            if result.modified_count > 0:
                print(f"  ✓ Updated record {record_id}")
                return True
            else:
                print(f"  No changes made to record {record_id}")
                return False

        except Exception as e:
            print(f"  Error updating record: {e}")
            return False

    def process_record(self, record: Dict[str, Any]) -> bool:
        """
        Process a single incomplete record

        Args:
            record: MongoDB record

        Returns:
            True if successful, False otherwise
        """
        record_id = record['_id']
        company_name = record.get('company_name', 'Unknown')
        url = record.get('url')

        print(f"\nProcessing: {company_name}")
        print(f"  ID: {record_id}")

        if not url:
            print(f"  ✗ No URL found, skipping")
            return False

        # Scrape the article
        scraped = self.scrape_article(url)
        if not scraped:
            return False

        # Extract data with AI
        extracted = self.extract_data_with_ai(scraped['title'], scraped['content'])
        if not extracted:
            return False

        # Update the record
        return self.update_record(record_id, extracted)

    def run(self, limit: Optional[int] = None, delay: float = 2.0):
        """
        Run the update process

        Args:
            limit: Maximum number of records to process (None = all)
            delay: Delay between requests in seconds
        """
        print("=" * 70)
        print("UPDATING INCOMPLETE RECORDS")
        print("=" * 70)

        # Find incomplete records
        incomplete_records = self.find_incomplete_records()

        if not incomplete_records:
            print("No incomplete records found!")
            return

        # Apply limit if specified
        if limit:
            incomplete_records = incomplete_records[:limit]
            print(f"Processing first {limit} records only")

        # Process each record
        stats = {
            'total': len(incomplete_records),
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }

        for i, record in enumerate(incomplete_records, 1):
            print(f"\n[{i}/{stats['total']}]", end=" ")

            try:
                success = self.process_record(record)
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1

                # Delay between requests (except for last one)
                if i < stats['total']:
                    print(f"  Waiting {delay}s before next request...")
                    time.sleep(delay)

            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")
                stats['failed'] += 1

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total records: {stats['total']}")
        print(f"Successfully updated: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success rate: {stats['successful'] / stats['total'] * 100:.1f}%")

        if self.dry_run:
            print("\n** DRY RUN MODE - No actual updates were made **")

    def close(self):
        """Close database connection"""
        self.client.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Update incomplete MongoDB records by scraping article URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--db',
        type=str,
        default='funded_backup_20251105_121856',
        help='Database name (default: funded_backup_20251105_121856)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be updated without making changes'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of records to process (default: all)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer")

    if args.delay < 0:
        parser.error("--delay must be non-negative")

    # Create updater and run
    updater = RecordUpdater(db_name=args.db, dry_run=args.dry_run)

    try:
        updater.run(limit=args.limit, delay=args.delay)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        updater.close()


if __name__ == '__main__':
    main()
