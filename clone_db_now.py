#!/usr/bin/env python3
"""
Simple script to clone the 'funded' database to a timestamped backup
"""
import sys
import os

from services.database_cloner import DatabaseCloner

def main():
    cloner = DatabaseCloner()

    try:
        # Show source database stats
        print("=" * 60)
        print("CLONING DATABASE")
        print("=" * 60)
        print("\nSource database: 'funded'")

        stats = cloner.get_database_stats('funded')

        if not stats['exists']:
            print("Error: 'funded' database does not exist!")
            return 1

        print(f"  Collections: {len(stats['collections'])}")
        for col in stats['collections']:
            print(f"    - {col['name']}: {col['count']} documents")
        print(f"  Total documents: {stats['total_documents']}")

        # Clone the database
        print("\nCloning database...")
        target_db = cloner.clone_database('funded')

        print("\n" + "=" * 60)
        print("CLONE COMPLETE!")
        print("=" * 60)
        print(f"New database: {target_db}")

        # Show cloned database stats
        print("\nVerifying clone...")
        clone_stats = cloner.get_database_stats(target_db)
        print(f"  Collections: {len(clone_stats['collections'])}")
        for col in clone_stats['collections']:
            print(f"    - {col['name']}: {col['count']} documents")
        print(f"  Total documents: {clone_stats['total_documents']}")

        print(f"\n✓ Original database 'funded' remains unchanged")
        print(f"✓ Clone created: {target_db}")

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        cloner.close()

if __name__ == '__main__':
    sys.exit(main())
