#!/usr/bin/env python3
"""
Quick test to demonstrate error handling when username is not found
"""
import sys
from test import extract_supervisor_usernames, load_credentials

def test_invalid_username():
    """Test that the system throws an error for unknown usernames."""
    print("=" * 60)
    print("Testing Username Error Handling")
    print("=" * 60)
    
    # Load credentials
    creds = load_credentials()
    mattermost_config = {
        'api_url': creds['mattermost']['api_url'],
        'token': creds['mattermost']['token']
    }
    
    # Test 1: Valid username (should work)
    print("\n✅ Test 1: Valid username (Hornung, Johannes)")
    print("-" * 60)
    try:
        result = extract_supervisor_usernames(
            ['Hornung, Johannes'], 
            mattermost_config
        )
        print(f"✓ Success! Found: {result}")
    except ValueError as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 2: Invalid username (should throw error)
    print("\n❌ Test 2: Invalid username (FakePersonNotInSystem, John)")
    print("-" * 60)
    try:
        result = extract_supervisor_usernames(
            ['FakePersonNotInSystem, John'], 
            mattermost_config
        )
        print(f"✗ ERROR: Should have thrown an error but got: {result}")
    except ValueError as e:
        print(f"✓ Successfully caught error:")
        print(f"  {e}")
    
    # Test 3: Mix of valid and invalid (should fail on first invalid)
    print("\n⚠️  Test 3: Mix of valid and invalid usernames")
    print("-" * 60)
    try:
        result = extract_supervisor_usernames(
            ['Hornung, Johannes', 'InvalidName, Test'], 
            mattermost_config
        )
        print(f"✗ ERROR: Should have thrown an error but got: {result}")
    except ValueError as e:
        print(f"✓ Successfully caught error on invalid name:")
        print(f"  {e}")
    
    print("\n" + "=" * 60)
    print("✅ Error handling test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_invalid_username()
