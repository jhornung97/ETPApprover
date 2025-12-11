#!/usr/bin/env python3
"""
Mark all currently pending submissions as already processed.

This is useful when:
- Setting up the system for the first time
- After manually processing submissions
- When you want to start fresh without sending duplicate notifications

This script will:
1. Login to the repository
2. Fetch all pending submissions
3. Add them to processed_submissions.json
4. NOT send any notifications
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from datetime import datetime

def load_credentials():
    """Load credentials from JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'credentials.json')

    if not os.path.exists(config_path):
        print(f"✗ Credentials file not found at {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in credentials file")
        sys.exit(1)

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

def login(login_url, email, password):
    """Login to the repository system."""
    session = requests.Session()

    try:
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.text, 'html.parser')

        csrf_token = soup.find('input', {'id': 'csrf_token'})
        if not csrf_token:
            print("✗ CSRF token not found on login page.")
            return None

        login_data = {
            'email': email,
            'password': password,
            'csrf_token': csrf_token['value'],
            'next': '/deposit'
        }

        response = session.post(login_url, data=login_data)

        if response.status_code != 200:
            print("✗ Login failed.")
            return None

        soup_response = BeautifulSoup(response.text, 'html.parser')
        if soup_response.find('a', href='/logout') or 'logout' in response.text.lower():
            print("✓ Login successful.")
            return session
        else:
            print("✗ Login failed.")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def get_pending_submissions(session, api_url):
    """Fetch pending thesis submissions from API."""
    try:
        headers = {'Accept': 'application/vnd.zenodo.v1+json'}
        response = session.get(api_url, headers=headers)
        response.raise_for_status()

        data = response.json()

        all_submissions = []
        if isinstance(data, list):
            all_submissions = data
        elif isinstance(data, dict) and 'hits' in data:
            all_submissions = data['hits'].get('hits', [])

        pending_submissions = [
            sub for sub in all_submissions 
            if sub.get('approval_status') == 'pending'
        ]

        print(f"✓ Total submissions fetched: {len(all_submissions)}")
        print(f"✓ Pending submissions: {len(pending_submissions)}")
        return pending_submissions

    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching submissions: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON response: {e}")
        return []

def extract_submission_data(submission):
    """Extract relevant data from submission JSON."""
    metadata = submission.get('metadata', {})
    
    record_id = submission.get('id') or submission.get('recid')
    title = metadata.get('title', 'N/A')
    
    # Get thesis type
    resource_type = metadata.get('resource_type', {})
    thesis_type = resource_type.get('title', 'N/A')
    
    # Get author (first creator)
    creators = metadata.get('creators', [])
    author = creators[0].get('name', 'N/A') if creators else 'N/A'
    
    return {
        'record_id': record_id,
        'title': title,
        'thesis_type': thesis_type,
        'author': author,
        'approval_status': submission.get('approval_status', 'unknown')
    }

def is_already_processed(record_id, author, tracking_data):
    """Check if a submission is already in the tracking file."""
    for entry in tracking_data.get('processed', []):
        if entry.get('record_id') == record_id and entry.get('author') == author:
            return True
    return False

def main():
    """Main function."""
    print("=" * 80)
    print("Mark Current Pending Submissions as Processed")
    print("=" * 80)
    print()
    print("This script will fetch all currently pending submissions and mark them")
    print("as already processed, so they won't trigger notifications in future runs.")
    print()
    
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("\n" + "=" * 80)
    print("Fetching pending submissions...")
    print("=" * 80)
    
    # Load credentials
    creds = load_credentials()
    
    # Setup URLs
    base_url = "https://publish.etp.kit.edu"
    login_url = f"{base_url}/login/?next=%2F"
    api_url = f"{base_url}/api/deposit/depositions"
    
    # Login
    session = login(login_url, creds['email'], creds['password'])
    if not session:
        print("\n✗ Login failed, exiting")
        sys.exit(1)
    
    # Fetch pending submissions
    submissions = get_pending_submissions(session, api_url)
    
    if not submissions:
        print("\n✓ No pending submissions found. Nothing to mark.")
        return
    
    # Load tracking data
    tracking_data = load_tracking_data()
    
    print("\n" + "=" * 80)
    print("Processing submissions...")
    print("=" * 80)
    
    added_count = 0
    skipped_count = 0
    
    for i, submission in enumerate(submissions, 1):
        data = extract_submission_data(submission)
        
        print(f"\n[{i}/{len(submissions)}] {data['title'][:60]}")
        print(f"  Record ID: {data['record_id']}")
        print(f"  Author: {data['author']}")
        print(f"  Type: {data['thesis_type']}")
        
        # Check if already processed
        if is_already_processed(data['record_id'], data['author'], tracking_data):
            print(f"  ⏭  Already in tracking file - skipping")
            skipped_count += 1
            continue
        
        # Add to tracking
        entry = {
            'record_id': data['record_id'],
            'author': data['author'],
            'title': data['title'],
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if 'processed' not in tracking_data:
            tracking_data['processed'] = []
        
        tracking_data['processed'].append(entry)
        print(f"  ✓ Marked as processed")
        added_count += 1
    
    # Save tracking data
    if added_count > 0:
        save_tracking_data(tracking_data)
        print("\n" + "=" * 80)
        print("✓ Tracking file updated!")
        print("=" * 80)
        print(f"Added: {added_count} submission(s)")
        print(f"Skipped (already tracked): {skipped_count} submission(s)")
        print(f"Total now tracked: {len(tracking_data.get('processed', []))} submission(s)")
    else:
        print("\n" + "=" * 80)
        print("✓ No new submissions to add")
        print("=" * 80)
        print(f"All {skipped_count} pending submission(s) already tracked")

if __name__ == "__main__":
    main()
