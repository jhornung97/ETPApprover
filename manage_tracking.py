#!/usr/bin/env python3
"""
Utility script to manage processed submissions tracking
"""
import json
import os
import sys
from datetime import datetime

def load_tracking_data():
    """Load the tracking data file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tracking_file = os.path.join(script_dir, 'processed_submissions.json')
    
    if not os.path.exists(tracking_file):
        return {"processed": []}
    
    try:
        with open(tracking_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"processed": []}

def save_tracking_data(data):
    """Save the tracking data file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tracking_file = os.path.join(script_dir, 'processed_submissions.json')
    
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)

def list_processed():
    """List all processed submissions."""
    data = load_tracking_data()
    processed = data.get('processed', [])
    
    if not processed:
        print("No processed submissions found.")
        return
    
    print("=" * 80)
    print(f"Processed Submissions ({len(processed)} total)")
    print("=" * 80)
    
    for i, entry in enumerate(processed, 1):
        print(f"\n{i}. [{entry.get('record_id')}] {entry.get('title')}")
        print(f"   Author: {entry.get('author')}")
        print(f"   Processed at: {entry.get('processed_at')}")

def clear_all():
    """Clear all processed submissions."""
    confirm = input("⚠️  Are you sure you want to clear ALL processed submissions? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        save_tracking_data({"processed": []})
        print("✓ All processed submissions cleared.")
    else:
        print("❌ Cancelled.")

def remove_by_record_id():
    """Remove a specific submission by record ID."""
    data = load_tracking_data()
    processed = data.get('processed', [])
    
    if not processed:
        print("No processed submissions to remove.")
        return
    
    list_processed()
    
    record_id = input("\nEnter record ID to remove: ").strip()
    
    initial_count = len(processed)
    data['processed'] = [e for e in processed if str(e.get('record_id')) != record_id]
    
    if len(data['processed']) < initial_count:
        save_tracking_data(data)
        print(f"✓ Removed submission with record ID {record_id}")
    else:
        print(f"❌ No submission found with record ID {record_id}")

def stats():
    """Show statistics about processed submissions."""
    data = load_tracking_data()
    processed = data.get('processed', [])
    
    if not processed:
        print("No processed submissions.")
        return
    
    print("=" * 80)
    print("Statistics")
    print("=" * 80)
    print(f"Total processed submissions: {len(processed)}")
    
    # Group by date
    by_date = {}
    for entry in processed:
        date = entry.get('processed_at', '').split()[0]
        if date:
            by_date[date] = by_date.get(date, 0) + 1
    
    if by_date:
        print(f"\nProcessed by date:")
        for date in sorted(by_date.keys(), reverse=True):
            print(f"  {date}: {by_date[date]} submission(s)")
    
    # Most recent
    if processed:
        most_recent = max(processed, key=lambda x: x.get('processed_at', ''))
        print(f"\nMost recent:")
        print(f"  {most_recent.get('title')}")
        print(f"  Author: {most_recent.get('author')}")
        print(f"  Processed at: {most_recent.get('processed_at')}")

def main():
    """Main menu."""
    while True:
        print("\n" + "=" * 80)
        print("ETaPprover - Processed Submissions Manager")
        print("=" * 80)
        print("\nOptions:")
        print("  1. List all processed submissions")
        print("  2. Show statistics")
        print("  3. Remove specific submission by record ID")
        print("  4. Clear all processed submissions")
        print("  5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == '1':
            list_processed()
        elif choice == '2':
            stats()
        elif choice == '3':
            remove_by_record_id()
        elif choice == '4':
            clear_all()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please choose 1-5.")

if __name__ == "__main__":
    main()
