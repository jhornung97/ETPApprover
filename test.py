#!/usr/bin/env python3
"""
Mattermost DM Bot - Send direct messages using bot credentials
"""
import requests
import json
import sys
import urllib3
import os

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_credentials():
    """Load bot credentials from JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(script_dir, 'credentials.json')
    
    try:
        with open(creds_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ Credentials file not found: {creds_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in credentials file: {creds_path}")
        sys.exit(1)

def test_connection(api_url, token):
    """Test Mattermost connection and get bot info."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("🔌 Testing Mattermost connection...")
        response = requests.get(f"{api_url}/v4/users/me", headers=headers, verify=False)
        response.raise_for_status()
        user = response.json()
        print(f"✓ Connected as: {user['username']} ({user['id']})")
        return True, user
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False, None

def get_user_by_username(api_url, token, username):
    """Look up a user by username."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Looking up user: {username}")
        response = requests.get(
            f"{api_url}/v4/users/username/{username}",
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        user = response.json()
        print(f"✓ Found user: {user['username']} ({user['id']})")
        return user
    except Exception as e:
        print(f"✗ User lookup failed: {e}")
        return None

def create_dm_channel(api_url, token, bot_id, target_user_id):
    """Create or get a DM channel between bot and target user."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("📨 Creating/getting DM channel...")
        response = requests.post(
            f"{api_url}/v4/channels/direct",
            headers=headers,
            json=[bot_id, target_user_id],
            verify=False
        )
        
        if response.status_code in [200, 201]:
            channel = response.json()
            print(f"✓ DM channel ready: {channel['id']}")
            return channel['id']
        
        # If creation failed, try to find existing DM
        print("  Searching for existing DM channel...")
        channels_response = requests.get(
            f"{api_url}/v4/users/{bot_id}/channels",
            headers=headers,
            verify=False
        )
        channels_response.raise_for_status()
        channels = channels_response.json()
        
        for ch in channels:
            if ch.get('type') == 'D':
                # Check if this DM includes the target user
                try:
                    members_response = requests.get(
                        f"{api_url}/v4/channels/{ch['id']}/members",
                        headers=headers,
                        verify=False
                    )
                    if members_response.status_code == 200:
                        members = members_response.json()
                        member_ids = [m['user_id'] for m in members]
                        if target_user_id in member_ids and bot_id in member_ids:
                            print(f"✓ Found existing DM channel: {ch['id']}")
                            return ch['id']
                except:
                    continue
        
        print("✗ Could not create or find DM channel")
        return None
        
    except Exception as e:
        print(f"✗ DM channel creation failed: {e}")
        return None

def create_group_dm_channel(api_url, token, bot_id, user_ids):
    """Create a group DM channel with multiple users."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"👥 Creating group DM with {len(user_ids)} participants...")
        
        # Include bot in the group
        all_user_ids = [bot_id] + user_ids
        
        response = requests.post(
            f"{api_url}/v4/channels/group",
            headers=headers,
            json=all_user_ids,
            verify=False
        )
        
        if response.status_code in [200, 201]:
            channel = response.json()
            print(f"✓ Group DM channel ready: {channel['id']}")
            return channel['id']
        else:
            print(f"✗ Failed to create group DM: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
        
    except Exception as e:
        print(f"✗ Group DM creation failed: {e}")
        return None

def send_message_to_channel(api_url, token, channel_id, message):
    """Send a message to a specific channel."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("📤 Sending message...")
        post_payload = {
            'channel_id': channel_id,
            'message': message
        }
        
        response = requests.post(
            f"{api_url}/v4/posts",
            headers=headers,
            json=post_payload,
            verify=False
        )
        
        response.raise_for_status()
        print("✓ Message sent successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Error details: {e.response.text}")
        return False

def send_dm_to_user(api_url, token, bot_id, username, message):
    """Send a DM to a specific user."""
    # Look up the target user
    target_user = get_user_by_username(api_url, token, username)
    if not target_user:
        return False
    
    # Create/get DM channel
    channel_id = create_dm_channel(api_url, token, bot_id, target_user['id'])
    if not channel_id:
        print("\n💡 TIP: Try opening Mattermost and starting a DM with the bot first!")
        return False
    
    # Send the message
    return send_message_to_channel(api_url, token, channel_id, message)

def send_group_dm(api_url, token, bot_id, usernames, message):
    """Send a message to a group DM with multiple users."""
    print(f"👥 Setting up group DM with: {', '.join(usernames)}")
    
    # Look up all target users
    user_ids = []
    for username in usernames:
        user = get_user_by_username(api_url, token, username)
        if not user:
            print(f"❌ Failed to find user: {username}")
            return False
        user_ids.append(user['id'])
    
    # Create group DM channel
    channel_id = create_group_dm_channel(api_url, token, bot_id, user_ids)
    if not channel_id:
        return False
    
    # Send the message
    return send_message_to_channel(api_url, token, channel_id, message)

def send_dm_to_multiple_users(api_url, token, bot_id, usernames, message):
    """Send a DM to multiple users."""
    results = {}
    
    print(f"📬 Sending message to {len(usernames)} users...")
    
    for i, username in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] Processing @{username}...")
        
        success = send_dm_to_user(api_url, token, bot_id, username, message)
        results[username] = success
        
        if success:
            print(f"  ✅ Success")
        else:
            print(f"  ❌ Failed")
    
    # Summary
    print(f"\n📊 Summary:")
    successful = [user for user, success in results.items() if success]
    failed = [user for user, success in results.items() if not success]
    
    print(f"  ✅ Successful: {len(successful)}")
    if successful:
        print(f"     {', '.join(successful)}")
    
    print(f"  ❌ Failed: {len(failed)}")
    if failed:
        print(f"     {', '.join(failed)}")
    
    return results

def try_username_with_mattermost(api_url, token, username):
    """Test if a username exists in Mattermost.
    
    Args:
        api_url: Mattermost API URL
        token: API token
        username: Username to test
    
    Returns:
        True if user exists, False otherwise
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{api_url}/v4/users/username/{username}",
            headers=headers,
            verify=False
        )
        return response.status_code == 200
    except:
        return False

def generate_username_variants(supervisor_name):
    """Generate possible Mattermost username variants from a supervisor name.
    
    Args:
        supervisor_name: Name in format "Lastname, Firstname" or "Lastname"
    
    Returns:
        List of username variants to try (in order of likelihood)
    """
    import re
    
    variants = []
    
    # Parse the name
    parts = supervisor_name.split(',')
    lastname = parts[0].strip()
    firstname = parts[1].strip() if len(parts) > 1 else ""
    
    # Remove umlauts and special characters
    def normalize(text):
        text = text.lower()
        # Replace umlauts
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        # Remove spaces and special characters except hyphens
        text = re.sub(r'[^\w\-]', '', text)
        return text
    
    lastname_normalized = normalize(lastname)
    firstname_normalized = normalize(firstname) if firstname else ""
    
    # Pattern 1: first letter + lastname (most common for non-professors)
    if firstname_normalized:
        variants.append(firstname_normalized[0] + lastname_normalized)
    
    # Pattern 2: lastname only (for professors)
    variants.append(lastname_normalized)
    
    # Pattern 3: full firstname + lastname (rare but possible)
    if firstname_normalized:
        variants.append(firstname_normalized + lastname_normalized)
    
    # Pattern 4: With hyphenated names, try without hyphen
    if '-' in lastname_normalized:
        lastname_no_hyphen = lastname_normalized.replace('-', '')
        if firstname_normalized:
            variants.append(firstname_normalized[0] + lastname_no_hyphen)
        variants.append(lastname_no_hyphen)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique_variants.append(v)
    
    return unique_variants

def extract_supervisor_usernames(supervisors, mattermost_config=None):
    """Extract Mattermost usernames from supervisor names with smart detection.
    
    Args:
        supervisors: List of supervisor names like "Gaisdörfer, Marcel; Hornung, Johannes"
        mattermost_config: Optional dict with 'api_url' and 'token' for auto-verification
    
    Returns:
        List of usernames extracted from names
    """
    usernames = []
    
    # Manual override mapping (for special cases)
    manual_overrides = {
        'hornung': 'jhornung',
        #'gaisdörfer': 'mgais',
        #'gaisdorfer': 'mgais',
        'quiroga-trivino': 'aquiroga',
        'guthmann': 'dorian.guthmann'
    }
    
    for supervisor in supervisors:
        supervisor = supervisor.strip()
        if not supervisor:
            continue
        
        print(f"  🔍 Processing supervisor: {supervisor}")
        
        # Check manual overrides first
        lastname_lower = supervisor.lower().split(',')[0].strip()
        found_override = False
        for name_key, username in manual_overrides.items():
            if name_key in lastname_lower:
                print(f"    ✓ Using manual override: @{username}")
                usernames.append(username)
                found_override = True
                break
        
        if found_override:
            continue
        
        # Generate username variants
        variants = generate_username_variants(supervisor)
        print(f"    💡 Generated variants: {', '.join(variants)}")
        
        # If Mattermost config is provided, test each variant
        if mattermost_config:
            found = False
            for variant in variants:
                if try_username_with_mattermost(
                    mattermost_config['api_url'], 
                    mattermost_config['token'], 
                    variant
                ):
                    print(f"    ✓ Found valid username: @{variant}")
                    usernames.append(variant)
                    found = True
                    break
            
            if not found:
                error_msg = f"❌ ERROR: No valid Mattermost username found for '{supervisor}'"
                print(f"    {error_msg}")
                print(f"    Tried variants: {', '.join(variants)}")
                print(f"    Please add a manual override in the script.")
                raise ValueError(error_msg)
        else:
            # Without Mattermost config, use first variant
            username = variants[0]
            print(f"    → Using generated username: @{username}")
            usernames.append(username)
    
    return usernames

def main():
    """Main function to send DMs via Mattermost bot."""
    print("🤖 Mattermost DM Bot")
    print("=" * 50)
    
    # Load credentials
    try:
        creds = load_credentials()
        api_url = creds['mattermost']['api_url']
        token = creds['mattermost']['token']
    except KeyError as e:
        print(f"✗ Missing credential: {e}")
        sys.exit(1)
    
    # Test connection
    success, bot_user = test_connection(api_url, token)
    if not success:
        sys.exit(1)
    
    bot_id = bot_user['id']
    bot_username = bot_user['username']
    
    print(f"\n📋 Bot Info:")
    print(f"  Username: {bot_username}")
    print(f"  User ID: {bot_id}")
    print(f"  API URL: {api_url}")
    
    # Interactive DM sending
    print("\n" + "=" * 50)
    
    while True:
        print("\n📨 Mattermost Test Menu")
        print("Options:")
        print("  1. Send to one person")
        print("  2. Send to multiple people (individual DMs)")
        print("  3. Send to group DM (all people in same conversation)")
        print("  4. Test username lookup")
        print("  5. Quit")
        
        choice = input("Choose option (1/2/3/4/5): ").strip()
        
        if choice == '5' or choice.lower() in ['quit', 'exit', 'q']:
            break
        
        if choice not in ['1', '2', '3', '4']:
            print("Please choose 1, 2, 3, 4, or 5.")
            continue
        
        # Username lookup tool
        if choice == '4':
            print("\n" + "=" * 50)
            print("🔍 Username Lookup Tool")
            print("=" * 50)
            print("Enter supervisor name(s) in format 'Lastname, Firstname'")
            print("(one per line, press Enter twice when done):")
            
            names = []
            empty_lines = 0
            
            while empty_lines < 2:
                name = input().strip()
                if name == "":
                    empty_lines += 1
                else:
                    empty_lines = 0
                    names.append(name)
            
            if not names:
                print("No names entered.")
                continue
            
            print("\n" + "-" * 50)
            print("📊 Username Lookup Results:")
            print("-" * 50)
            
            mattermost_config = {
                'api_url': api_url,
                'token': token
            }
            
            usernames = extract_supervisor_usernames(names, mattermost_config)
            
            print("\n✓ Generated username mapping:")
            for i, name in enumerate(names):
                if i < len(usernames):
                    print(f"  {name} → @{usernames[i]}")
            
            print("-" * 50)
            continue
        
        # Get target username(s)
        if choice == '1':
            target_username = input("Enter target username: ").strip()
            if not target_username:
                print("Please enter a valid username.")
                continue
            usernames = [target_username]
        else:  # choice == '2' or '3'
            if choice == '2':
                print("Enter usernames for individual DMs (one per line, press Enter twice when done):")
            else:  # choice == '3'
                print("Enter usernames for group DM (one per line, press Enter twice when done):")
            
            usernames = []
            empty_lines = 0
            
            while empty_lines < 2:
                username = input().strip()
                if username == "":
                    empty_lines += 1
                else:
                    empty_lines = 0
                    usernames.append(username)
            
            if not usernames:
                print("Please enter at least one username.")
                continue
            
            if choice == '3' and len(usernames) < 2:
                print("Group DMs require at least 2 participants.")
                continue
            
            print(f"Target users: {', '.join(usernames)}")
        
        # Get message
        print("\nEnter your message (press Enter twice to finish):")
        message_lines = []
        empty_lines = 0
        
        while empty_lines < 2:
            line = input()
            if line == "":
                empty_lines += 1
            else:
                empty_lines = 0
            message_lines.append(line)
        
        # Remove trailing empty lines
        while message_lines and message_lines[-1] == "":
            message_lines.pop()
        
        message = "\n".join(message_lines)
        
        if not message.strip():
            print("Message cannot be empty. Try again.")
            continue
        
        # Show preview and confirm
        print("\n" + "-" * 30)
        print("MESSAGE PREVIEW:")
        print("-" * 30)
        print(message)
        print("-" * 30)
        
        # Show confirmation
        if choice == '1':
            confirm_msg = f"\nSend this message to @{usernames[0]}? (y/n): "
        elif choice == '2':
            confirm_msg = f"\nSend individual DMs to {len(usernames)} users ({', '.join(usernames)})? (y/n): "
        else:  # choice == '3'
            confirm_msg = f"\nSend this message to group DM with {len(usernames)} users ({', '.join(usernames)})? (y/n): "
        
        confirm = input(confirm_msg).strip().lower()
        
        if confirm in ['y', 'yes']:
            print("\n" + "=" * 50)
            
            if choice == '1':
                success = send_dm_to_user(api_url, token, bot_id, usernames[0], message)
                if success:
                    print(f"✅ Message delivered to @{usernames[0]}!")
                else:
                    print(f"❌ Failed to deliver message to @{usernames[0]}")
            elif choice == '2':
                results = send_dm_to_multiple_users(api_url, token, bot_id, usernames, message)
                successful_count = sum(1 for success in results.values() if success)
                print(f"\n🎯 Individual DMs complete: {successful_count}/{len(usernames)} successful")
            else:  # choice == '3'
                success = send_group_dm(api_url, token, bot_id, usernames, message)
                if success:
                    print(f"✅ Group DM message sent to {len(usernames)} participants!")
                else:
                    print(f"❌ Failed to send group DM message")
        else:
            print("Message cancelled.")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()