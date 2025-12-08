"""
Database Migration Script: Add print_count column to asset_logs table

Usage:
    python add_print_count_column.py

This script adds a 'print_count' column to track the number of times
an asset form has been printed.
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists (SQLite compatible)
            check_query = text("""
                PRAGMA table_info(asset_log)
            """)
            result = conn.execute(check_query)
            columns = [row[1] for row in result.fetchall()]  # row[1] is column name
            
            if 'print_count' in columns:
                print("✓ Column 'print_count' already exists. Skipping migration.")
                return
            
            # Add column
            print("Adding 'print_count' column to asset_log table...")
            alter_query = text("""
                ALTER TABLE asset_log 
                ADD COLUMN print_count INTEGER NOT NULL DEFAULT 0
            """)
            conn.execute(alter_query)
            conn.commit()
            
            print("✓ Successfully added 'print_count' column!")
            print("  - Column: print_count")
            print("  - Type: INTEGER")
            print("  - Default: 0")
            print("  - NOT NULL")
            
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add print_count column")
    print("=" * 60)
    
    add_print_count_column()
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
