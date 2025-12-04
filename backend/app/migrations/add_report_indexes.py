"""
Migration: Add indexes for report queries optimization

Run this script once to add indexes to:
- guests.created_at
- guests.check_in_time  
- asset_log.created_at
- asset_log.expected_return_date
- asset_log.status

Author: Antigravity AI
Date: 04/12/2025
"""

import sqlite3
import sys
from pathlib import Path

# Adjust path to find the database
DB_PATH = Path(__file__).resolve().parent.parent.parent / "security_v2_3.db"

def add_report_indexes():
    """Add indexes to optimize report queries"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        print(f"Connected to database: {DB_PATH}")
        
        # List of indexes to create
        indexes = [
            ("idx_guests_created_at", "guests", "created_at"),
            ("idx_guests_check_in_time", "guests", "check_in_time"),
            ("idx_asset_log_created_at", "asset_log", "created_at"),
            ("idx_asset_log_expected_return_date", "asset_log", "expected_return_date"),
            ("idx_asset_log_status", "asset_log", "status"),
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"
                cursor.execute(sql)
                print(f"✅ Created index: {index_name} on {table_name}({column_name})")
            except Exception as e:
                print(f"⚠️  Error creating index {index_name}: {e}")
        
        conn.commit()
        print("\n🎉 All indexes created successfully!")
        
        # Show current indexes
        print("\n📊 Current indexes:")
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name")
        for row in cursor.fetchall():
            print(f"  - {row[0]} on {row[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add Report Indexes")
    print("=" * 60)
    add_report_indexes()
