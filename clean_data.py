#!/usr/bin/env python3
"""
MongoDB Data Cleaning CLI

This script cleans and enriches company funding records in MongoDB by fetching
full article content from URLs and extracting missing information.

IMPORTANT: By default, this script will clone your database to a backup before
cleaning to avoid data loss.

Usage:
    python clean_data.py                    # Clone database and clean all records
    python clean_data.py --limit 10         # Clone and clean first 10 records
    python clean_data.py --dry-run          # Preview without cloning or updating
    python clean_data.py --no-clone         # Clean original database (DANGEROUS!)
    python clean_data.py --db funded_test   # Clean specific database (no cloning)
"""

import argparse
import sys
import os

from services.data_cleaner import DataCleaner
from services.database_cloner import DatabaseCloner


def main():
    """Main entry point for the data cleaning CLI"""

    parser = argparse.ArgumentParser(
        description='Clean and enrich MongoDB company funding records',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Clone database and clean all records
  %(prog)s --limit 10           Clone and clean first 10 records (for testing)
  %(prog)s --dry-run            Preview what would be cleaned (no cloning)
  %(prog)s --no-clone           Clean original database WITHOUT cloning (dangerous!)
  %(prog)s --db funded_test     Clean a specific database (no cloning)
  %(prog)s --source-db funded   Specify source database to clone from
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        metavar='N',
        help='Maximum number of records to process (default: all)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without cloning or updating the database'
    )

    parser.add_argument(
        '--no-clone',
        action='store_true',
        help='Clean the original database WITHOUT cloning first (DANGEROUS!)'
    )

    parser.add_argument(
        '--db',
        type=str,
        default=None,
        metavar='NAME',
        help='Specific database to clean (skips cloning, cleans this database directly)'
    )

    parser.add_argument(
        '--source-db',
        type=str,
        default='funded',
        metavar='NAME',
        help='Source database to clone from (default: funded)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=1.5,
        metavar='SECONDS',
        help='Delay between requests in seconds (default: 1.5)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default='data_cleaning_errors.log',
        metavar='PATH',
        help='Path to error log file (default: data_cleaning_errors.log)'
    )

    parser.add_argument(
        '--all-records',
        action='store_true',
        help='Process ALL records (for company name re-extraction), not just incomplete ones'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer")

    if args.delay < 0:
        parser.error("--delay must be non-negative")

    if args.no_clone and args.db:
        parser.error("Cannot use --no-clone and --db together")

    # Check for required environment variables
    if not os.getenv('MONGODB_URI') and not os.path.exists('/etc/mongodb.conf'):
        print("Warning: MONGODB_URI environment variable not set.")
        print("Using default: mongodb://localhost:27017/")
        print()

    if not os.getenv('OPENROUTER_API_KEY'):
        print("Warning: OPENROUTER_API_KEY environment variable not set.")
        print("AI extraction will not be available - cleaning may be less effective.")
        print()

        if not args.dry_run:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return 1

    # Determine target database
    target_db = None
    cloner = None

    try:
        # CASE 1: Dry run - no cloning needed
        if args.dry_run:
            print("DRY RUN MODE - No cloning or updates will be performed")
            target_db = args.db or args.source_db

        # CASE 2: Specific database provided - use it directly
        elif args.db:
            print(f"Using database: {args.db}")
            target_db = args.db

        # CASE 3: --no-clone flag - clean original database
        elif args.no_clone:
            print("⚠️  WARNING: You are about to clean the ORIGINAL database!")
            print(f"Database: {args.source_db}")
            print("This will modify your production data.")
            print()
            response = input("Are you SURE you want to continue? (yes/NO): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return 0
            target_db = args.source_db

        # CASE 4: Default - clone database first
        else:
            print("Initializing database cloner...")
            cloner = DatabaseCloner()

            # Show source database stats
            print(f"\nSource database: {args.source_db}")
            stats = cloner.get_database_stats(args.source_db)

            if not stats['exists']:
                print(f"Error: Source database '{args.source_db}' does not exist")
                return 1

            print(f"  Collections: {len(stats['collections'])}")
            for col in stats['collections']:
                print(f"    - {col['name']}: {col['count']} documents")
            print(f"  Total documents: {stats['total_documents']}")

            # Clone the database
            print("\nCloning database...")
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_db = cloner.clone_database(args.source_db)

            print(f"\n✓ Clone complete: {target_db}")

    except KeyboardInterrupt:
        print("\n\nAborted by user")
        if cloner:
            cloner.close()
        return 130

    except Exception as e:
        print(f"\nError during cloning: {e}")
        if cloner:
            cloner.close()
        return 1

    # Initialize cleaner
    try:
        print(f"\nInitializing data cleaner for database: {target_db}")
        cleaner = DataCleaner(log_file=args.log_file, db_name=target_db)
    except Exception as e:
        print(f"Error initializing data cleaner: {e}")
        if cloner:
            cloner.close()
        return 1

    # Run cleaning process
    try:
        stats = cleaner.clean_all(
            limit=args.limit,
            dry_run=args.dry_run,
            delay=args.delay,
            all_records=args.all_records
        )

        # Print next steps
        if not args.dry_run and target_db != args.source_db:
            print("\n" + "=" * 60)
            print("NEXT STEPS")
            print("=" * 60)
            print(f"1. Review the cleaned data in database: {target_db}")
            print(f"2. If satisfied, you can:")
            print(f"   - Update your application to use: {target_db}")
            print(f"   - Or manually rename {target_db} to {args.source_db}")
            print(f"   - Or copy cleaned data back to {args.source_db}")
            print(f"3. Original database '{args.source_db}' remains unchanged")

        # Exit with error code if there were failures
        if stats['errors']:
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\nCleaning interrupted by user")
        return 130

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        cleaner.close()
        if cloner:
            cloner.close()


if __name__ == '__main__':
    sys.exit(main())
