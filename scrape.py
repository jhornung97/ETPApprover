#!/usr/bin/env python3
"""
ETaPprover - Thesis submission notification system
Scrapes pending thesis submissions and sends Mattermost notifications
"""
import requests
from bs4 import BeautifulSoup
import os
import sys
import json
import smtplib
import urllib3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from io import StringIO
from datetime import datetime

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# Logging System
# ============================================================================

class TeeOutput:
    """Capture stdout/stderr while still printing to console."""
    def __init__(self):
        self.buffer = StringIO()
        self.terminal = sys.stdout
        
    def write(self, message):
        self.terminal.write(message)
        self.buffer.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.buffer.flush()
    
    def getvalue(self):
        return self.buffer.getvalue()

# ============================================================================
# Credential Management
# ============================================================================

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

# ============================================================================
# Zenodo/Repository Functions
# ============================================================================

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
    thesis_subtype = resource_type.get('subtype', 'N/A')
    
    # Get author (first creator)
    creators = metadata.get('creators', [])
    author = creators[0].get('name', 'N/A') if creators else 'N/A'
    
    # Get supervisors
    supervisors = []
    thesis = metadata.get('thesis', {})
    thesis_supervisors = thesis.get('supervisors', [])
    for supervisor in thesis_supervisors:
        supervisors.append(supervisor.get('name', 'Unknown'))
    
    return {
        'record_id': record_id,
        'title': title,
        'thesis_type': thesis_type,
        'thesis_subtype': thesis_subtype,
        'author': author,
        'supervisors': supervisors,
        'status': submission.get('status', 'unknown'),
        'approval_status': submission.get('approval_status', 'unknown')
    }

def process_all_submissions(session, api_url):
    """Process all pending submissions."""
    submissions = get_pending_submissions(session, api_url)
    
    if not submissions:
        print("\n⚠ No pending submissions found!")
        return []
    
    results = []
    for i, submission in enumerate(submissions, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(submissions)}] Processing submission")
        print(f"{'='*60}")
        
        data = extract_submission_data(submission)
        
        print(f"  Record ID: {data['record_id']}")
        print(f"  Title: {data['title']}")
        print(f"  Author: {data['author']}")
        print(f"  Supervisors: {'; '.join(data['supervisors']) if data['supervisors'] else 'N/A'}")
        print(f"  Type: {data['thesis_type']}")
        print(f"  Approval: {data['approval_status']}")
        
        results.append(data)
    
    return results

# ============================================================================
# Email Notification Functions
# ============================================================================

def send_notification_email(submissions, smtp_config, log_content=None):
    """Send email notification about pending submissions with optional log attachment."""
    if not submissions:
        return False
    
    subject = f"New Pending Thesis Submissions - {len(submissions)} item(s)"
    
    body = f"Hello,\n\n"
    body += f"There are {len(submissions)} new thesis submission(s) pending approval:\n\n"
    
    for i, sub in enumerate(submissions, 1):
        body += f"{i}. {sub['title']}\n"
        body += f"   Author: {sub['author']}\n"
        body += f"   Supervisors: {', '.join(sub['supervisors'])}\n"
        body += f"   Type: {sub['thesis_type']}\n\n"
    
    body += "Please review and approve these submissions.\n\n"
    
    if log_content:
        body += "See attached log file for detailed execution information.\n\n"
    
    body += "Best regards,\n"
    body += "ETaPprover"
    
    msg = MIMEMultipart()
    msg['From'] = smtp_config.get('from_email', 'etp-admin@lists.kit.edu')
    msg['To'] = smtp_config.get('to_email', 'webadmin@etp.kit.edu')
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach log file if provided
    if log_content:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"etapprover_log_{timestamp}.txt"
        
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(log_content.encode('utf-8'))
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={log_filename}')
        msg.attach(attachment)
        
        print(f"✓ Log file attached: {log_filename} ({len(log_content)} bytes)")
    
    try:
        smtp_server = smtp_config.get('smtp_server', 'localhost')
        smtp_port = smtp_config.get('smtp_port', 25)
        
        print(f"\n📧 Sending notification email to {msg['To']}...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_config.get('use_tls', False):
                server.starttls()
            
            if 'smtp_user' in smtp_config and 'smtp_password' in smtp_config:
                server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
            
            server.send_message(msg)
        
        print("✓ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False

# ============================================================================
# Mattermost Functions
# ============================================================================

def test_mattermost_connection(api_url, token):
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

def search_user(api_url, token, search_term):
    """Search for a user by name or username."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Searching for user: {search_term}")
        
        response = requests.get(
            f"{api_url}/v4/users/search",
            headers=headers,
            params={"term": search_term},
            verify=False
        )
        response.raise_for_status()
        users = response.json()
        
        if users:
            print(f"✓ Found {len(users)} user(s):")
            for user in users[:5]:
                print(f"  - {user.get('username')} (ID: {user['id']}) - {user.get('first_name', '')} {user.get('last_name', '')}")
            return users
        else:
            print("✗ No users found")
            return []
    except Exception as e:
        print(f"✗ Search failed: {e}")
        
        # Try direct username lookup
        try:
            print(f"  Trying direct username lookup...")
            return [get_user_by_username(api_url, token, search_term)]
        except:
            print(f"✗ Username lookup also failed")
            return []

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
    target_user = get_user_by_username(api_url, token, username)
    if not target_user:
        return False
    
    channel_id = create_dm_channel(api_url, token, bot_id, target_user['id'])
    if not channel_id:
        print("\n💡 TIP: Try opening Mattermost and starting a DM with the bot first!")
        return False
    
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
    """Send individual DMs to multiple users."""
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

def format_submission_message(submissions):
    """Format submissions into a Mattermost message."""
    if not submissions:
        return "No pending submissions."
    
    message = f"## 📚 Pending Thesis Submissions ({len(submissions)})\n\n"
    
    for i, sub in enumerate(submissions, 1):
        message += f"### {i}. {sub['title']}\n"
        message += f"- **Author**: {sub['author']}\n"
        message += f"- **Type**: {sub['thesis_type']}\n"
        if sub['supervisors']:
            message += f"- **Supervisors**: {', '.join(sub['supervisors'])}\n"
        message += f"- **Status**: {sub['approval_status']}\n"
        message += f"- **Record ID**: {sub['record_id']}\n\n"
    
    message += "\n---\n_Automated notification from ETaPprover_"
    
    return message

# ============================================================================
# Main Program
# ============================================================================

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
        supervisor_name: Name in any format:
            - "Lastname, Firstname" (standard academic format)
            - "Firstname, Lastname" (reversed with comma)
            - "Firstname Lastname" (natural order)
            - "Lastname" (single name)
    
    Returns:
        List of username variants to try (in order of likelihood)
    """
    import re
    
    variants = []
    
    # Parse the name - handle multiple formats
    if ',' in supervisor_name:
        # Format with comma: could be "Lastname, Firstname" or "Firstname, Lastname"
        parts = supervisor_name.split(',')
        part1 = parts[0].strip()
        part2 = parts[1].strip() if len(parts) > 1 else ""
        
        # Heuristic: If part1 looks like a firstname (common first names, or shorter),
        # treat it as "Firstname, Lastname", otherwise "Lastname, Firstname"
        # Common academic titles that suggest lastname comes first
        academic_indicators = ['prof', 'dr', 'professor', 'doktor']
        has_title = any(indicator in part1.lower() for indicator in academic_indicators)
        
        # Check if part2 contains spaces (suggesting it might be a compound lastname)
        part2_has_spaces = ' ' in part2
        
        # If part1 is much longer than part2 and part2 doesn't have spaces,
        # it's likely "Lastname, Firstname" (traditional academic format)
        if (len(part1) > len(part2) * 1.5 and not part2_has_spaces) or has_title:
            # Traditional format: "Lastname, Firstname"
            lastname = part1
            firstname = part2
        else:
            # Could be reversed: "Firstname, Lastname"
            # Try both interpretations
            # First, assume it's reversed
            firstname_option1 = part1
            lastname_option1 = part2
            # Second, assume it's traditional
            firstname_option2 = part2
            lastname_option2 = part1
            
            # We'll generate variants for both interpretations
            # The traditional format is still more common, so we'll prioritize it
            firstname = part2  # traditional
            lastname = part1   # traditional
            firstname_alt = part1  # reversed
            lastname_alt = part2   # reversed
    else:
        # Format without comma: "Firstname Lastname" or just "Lastname"
        parts = supervisor_name.strip().split()
        if len(parts) >= 2:
            # Assume last part is lastname, everything else is firstname
            firstname = ' '.join(parts[:-1])
            lastname = parts[-1]
            firstname_alt = None
            lastname_alt = None
        else:
            # Just one name, assume it's the lastname
            lastname = parts[0] if parts else supervisor_name.strip()
            firstname = ""
            firstname_alt = None
            lastname_alt = None
    
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
    
    # Pattern 5: If we have alternate interpretation (reversed format), try those too
    if 'firstname_alt' in locals() and firstname_alt and lastname_alt:
        lastname_alt_normalized = normalize(lastname_alt)
        firstname_alt_normalized = normalize(firstname_alt) if firstname_alt else ""
        
        if firstname_alt_normalized:
            variants.append(firstname_alt_normalized[0] + lastname_alt_normalized)
        variants.append(lastname_alt_normalized)
        if firstname_alt_normalized:
            variants.append(firstname_alt_normalized + lastname_alt_normalized)
        
        # With hyphenated names (alt version)
        if '-' in lastname_alt_normalized:
            lastname_alt_no_hyphen = lastname_alt_normalized.replace('-', '')
            if firstname_alt_normalized:
                variants.append(firstname_alt_normalized[0] + lastname_alt_no_hyphen)
            variants.append(lastname_alt_no_hyphen)
    
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
        'gaisdörfer': 'mgais',
        'gaisdorfer': 'mgais',
        'gaisdoerfer': 'mgais',
        'quiroga-trivino': 'aquiroga'
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

def extract_author_username(author_name, mattermost_config=None):
    """Extract Mattermost username from author name.
    
    Args:
        author_name: Author name in format "Lastname, Firstname" or "Lastname"
        mattermost_config: Optional dict with 'api_url' and 'token' for auto-verification
    
    Returns:
        Username string or None if not found
    """
    if not author_name or author_name == 'N/A':
        return None
    
    print(f"  🔍 Processing author: {author_name}")
    
    # Generate username variants
    variants = generate_username_variants(author_name)
    print(f"    💡 Generated variants: {', '.join(variants)}")
    
    # If Mattermost config is provided, test each variant
    if mattermost_config:
        for variant in variants:
            if try_username_with_mattermost(
                mattermost_config['api_url'], 
                mattermost_config['token'], 
                variant
            ):
                print(f"    ✓ Found valid username: @{variant}")
                return variant
        
        print(f"    ⚠️  No valid Mattermost username found for '{author_name}'")
        print(f"    Tried variants: {', '.join(variants)}")
        return None
    else:
        # Without Mattermost config, use first variant
        username = variants[0]
        print(f"    → Using generated username: @{username}")
        return username

def send_mattermost_notifications(submissions, mattermost_config, interactive=False):
    """Send Mattermost notifications for pending submissions.
    
    Args:
        submissions: List of submission dicts
        mattermost_config: Dict with api_url and token
        interactive: If True, ask for confirmation before each notification
    """
    if not submissions:
        return False
    
    api_url = mattermost_config['api_url']
    token = mattermost_config['token']
    
    # Test connection
    success, bot_user = test_mattermost_connection(api_url, token)
    if not success:
        print("⚠ Skipping Mattermost notifications (connection failed)")
        return False
    
    bot_id = bot_user['id']
    
    print("\n" + "=" * 60)
    if interactive:
        print("📨 Mattermost Notifications (INTERACTIVE MODE)")
    else:
        print("📨 Sending Mattermost Notifications")
    print("=" * 60)
    
    for submission in submissions:
        print(f"\n--- Processing: {submission['title'][:50]}... ---")
        
        # Check if this is a Bachelor Thesis
        thesis_type = submission['thesis_type'].lower()
        is_bachelor = 'bachelor' in thesis_type
        is_master = 'master' in thesis_type
        
        if not (is_bachelor or is_master):
            print(f"⏭ Skipping Mattermost notification (not a Bachelor thesis or Master thesis: {submission['thesis_type']})")
            continue
        
        print(f"✓ Bachelor thesis detected, preparing notification...")
        
        # Prepare notification recipients (supervisors + webadmin only)
        recipients = ['jhornung']  # Always notify webadmin
        
        # Add supervisors if available
        if submission['supervisors']:
            try:
                supervisor_usernames = extract_supervisor_usernames(
                    submission['supervisors'], 
                    mattermost_config
                )
                recipients.extend(supervisor_usernames)
            except ValueError as e:
                print(f"\n⚠️  WARNING: Could not resolve all supervisor usernames")
                print(f"    {str(e)}")
                print(f"    Skipping Mattermost notification for this submission.")
                print(f"    Email notification was still sent.\n")
                continue
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        print(f"Recipients: {', '.join(recipients)}")
        
        # Format author name (convert "Last, First" to "First Last")
        author_parts = submission['author'].split(',')
        if len(author_parts) == 2:
            author_display = f"{author_parts[1].strip()} {author_parts[0].strip()}"
        else:
            author_display = submission['author']
        
        # Format the message
        message = f"Hi,\n{author_display} has submitted their thesis into publish.\n\n"
        message += f"**Title**: {submission['title']}\n"
        message += f"**Author**: {submission['author']}\n"
        message += f"**Type**: {submission['thesis_type']}\n\n"
        message += f"Can this be uploaded to publish with open access rights?\n"
        message += f"If this isn't possible, please contact the author directly to clarify.\n"
        message += f"Also, if some supervisors are missing from this notification, please inform @{recipients[0]}.\n\n"
        message += f"Cheers,\nETPApprover Bot for the Webbadmin"
        
        # Interactive mode - show preview and ask for confirmation
        if interactive:
            print("\n" + "=" * 60)
            print("SUPERVISOR NOTIFICATION PREVIEW")
            print("=" * 60)
            print(f"To: {', '.join(recipients)}")
            print("-" * 60)
            print(message)
            print("=" * 60)
            
            confirm = input("\n📤 Send this notification to supervisors? (y/n/skip): ").strip().lower()
            
            if confirm == 'skip':
                print("⏭  Skipping supervisor notification for this thesis")
                continue
            elif confirm not in ['y', 'yes']:
                print("❌ Notification cancelled")
                continue
            
            print("✓ Sending supervisor notification...")
        
        # Send as group DM if multiple recipients, otherwise individual DM
        if len(recipients) > 1:
            print(f"Sending group DM to {len(recipients)} recipients...")
            success = send_group_dm(api_url, token, bot_id, recipients, message)
        else:
            print(f"Sending DM to {recipients[0]}...")
            success = send_dm_to_user(api_url, token, bot_id, recipients[0], message)
        
        if success:
            print(f"✓ Notification sent successfully")
        else:
            print(f"✗ Failed to send notification")
        
        # Send separate message to author asking for permission
        print(f"\n--- Contacting author for permission ---")
        author_username = extract_author_username(submission['author'], mattermost_config)
        
        if author_username:
            # Create group DM with author and jhornung
            author_recipients = ['jhornung', author_username]
            
            # Remove duplicates (in case author is already jhornung)
            author_recipients = list(set(author_recipients))
            
            # Extract first name for more personal greeting
            author_parts = submission['author'].split(',')
            if len(author_parts) == 2:
                # Format is "Lastname, Firstname" - use firstname
                author_firstname = author_parts[1].strip().split()[0]  # Get first part of firstname
            else:
                # Fallback to full display name
                author_firstname = author_display.split()[0]
            
            # Format author's permission request message
            author_message = f"Hi {author_firstname},\n\n"
            author_message += f"Your thesis **\"{submission['title']}\"** has been submitted to our repository. Congratulations for handing in :partyparrot:\n\n"
            author_message += f"We would like to confirm: Do you give permission to publish this thesis with **open access rights**? "
            author_message += f"This means your thesis will be publicly accessible online.\n\n"
            author_message += f"Please reply with your confirmation.\n\n"
            author_message += f"Cheers,\nETPApprover Bot for the Webbadmin"
            
            print(f"Author recipients: {', '.join(author_recipients)}")
            
            # Interactive mode - show author message preview
            if interactive:
                print("\n" + "=" * 60)
                print("AUTHOR PERMISSION REQUEST PREVIEW")
                print("=" * 60)
                print(f"To: {', '.join(author_recipients)}")
                print("-" * 60)
                print(author_message)
                print("=" * 60)
                
                confirm = input("\n📤 Send this permission request to author? (y/n/skip): ").strip().lower()
                
                if confirm == 'skip':
                    print("⏭  Skipping author permission request")
                    continue
                elif confirm not in ['y', 'yes']:
                    print("❌ Author notification cancelled")
                    continue
                
                print("✓ Sending author permission request...")
            
            # Send as group DM if author is not jhornung, otherwise just notify jhornung
            if len(author_recipients) > 1:
                print(f"Sending permission request to author (with jhornung in DM)...")
                author_success = send_group_dm(api_url, token, bot_id, author_recipients, author_message)
            else:
                # Author is jhornung, just send a note
                print(f"Author is jhornung, sending self-notification...")
                author_success = send_dm_to_user(api_url, token, bot_id, 'jhornung', 
                    f"Note: You are the author of \"{submission['title']}\" - permission request skipped.")
            
            if author_success:
                print(f"✓ Author permission request sent successfully")
            else:
                print(f"✗ Failed to send author permission request")
        else:
            print(f"⚠️  Could not find Mattermost username for author: {submission['author']}")
            print(f"    Skipping author permission request.")
    
    return True

def run_scraper(capture_log=False, interactive=False):
    """Run the thesis scraper and send notifications.
    
    Args:
        capture_log: If True, capture all output and attach to email
        interactive: If True, ask for confirmation before sending each notification
    """
    # Set up log capturing if requested
    tee = None
    if capture_log:
        tee = TeeOutput()
        sys.stdout = tee
        sys.stderr = tee
    
    try:
        start_time = datetime.now()
        print("=" * 60)
        print("ETaPprover - Thesis Submission Scraper")
        if interactive:
            print("MODE: Interactive (confirmation required)")
        print(f"Execution started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        base_url = "https://publish.etp.kit.edu"
        login_url = f"{base_url}/login/?next=%2F"
        api_url = f"{base_url}/api/deposit/depositions"
        
        creds = load_credentials()
        
        # Login to repository
        session = login(login_url, creds['email'], creds['password'])
        if not session:
            print("\n✗ Login failed, exiting")
            sys.exit(1)
        
        # Process submissions
        results = process_all_submissions(session, api_url)
        
        print(f"\n{'='*60}")
        print(f"✓ Processed {len(results)} submissions")
        print(f"{'='*60}")
        
        if results:
            # Send Mattermost notifications first (before capturing log)
            if 'mattermost' in creds:
                mattermost_config = {
                    'api_url': creds['mattermost']['api_url'],
                    'token': creds['mattermost']['token']
                }
                send_mattermost_notifications(results, mattermost_config, interactive=interactive)
            else:
                print("\n⚠ Mattermost credentials not found, skipping Mattermost notifications")
            
            # Now capture log content AFTER all output is complete
            log_content = tee.getvalue() if tee else None
            
            # Send email notification with complete log
            smtp_config = {
                'smtp_server': 'localhost',
                'smtp_port': 25,
                'from_email': 'etp-admin@lists.kit.edu',
                'to_email': 'webadmin@etp.kit.edu',
                'use_tls': False
            }
            
            # In interactive mode, ask about email
            if interactive:
                print("\n" + "=" * 60)
                print("EMAIL NOTIFICATION")
                print("=" * 60)
                print(f"To: {smtp_config['to_email']}")
                print(f"Subject: New Pending Thesis Submissions - {len(results)} item(s)")
                print(f"\nThis email will contain:")
                for i, sub in enumerate(results, 1):
                    print(f"  {i}. {sub['title']}")
                    print(f"     Author: {sub['author']}")
                
                confirm = input("\n📧 Send email notification? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    send_notification_email(results, smtp_config, log_content)
                else:
                    print("❌ Email notification skipped")
            else:
                send_notification_email(results, smtp_config, log_content)
        else:
            print("\n✓ No pending submissions found")
        
        # Print completion time and duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"Execution completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"{'='*60}")
        
        # Send status email with log if there were no submissions
        if not results and capture_log:
            log_content = tee.getvalue() if tee else None
            if log_content:
                smtp_config = {
                    'smtp_server': 'localhost',
                    'smtp_port': 25,
                    'from_email': 'etp-admin@lists.kit.edu',
                    'to_email': 'webadmin@etp.kit.edu',
                    'use_tls': False
                }
                # Send a simple status email
                msg = MIMEMultipart()
                msg['From'] = smtp_config.get('from_email')
                msg['To'] = smtp_config.get('to_email')
                msg['Subject'] = 'ETaPprover - No Pending Submissions'
                msg.attach(MIMEText('No pending thesis submissions found.\n\nSee attached log for details.', 'plain'))
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_filename = f"etapprover_log_{timestamp}.txt"
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(log_content.encode('utf-8'))
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename={log_filename}')
                msg.attach(attachment)
                
                try:
                    with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                        server.send_message(msg)
                    print("✓ Status email with log sent")
                except Exception as e:
                    print(f"✗ Failed to send status email: {e}")
        
        return results
        
    except Exception as e:
        # Handle any errors - send error email with log if in cron mode
        import traceback
        error_msg = f"ERROR: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"\n{'='*60}")
        print("❌ FATAL ERROR OCCURRED")
        print(f"{'='*60}")
        print(error_msg)
        print(f"{'='*60}")
        
        # Send error email with log if we're capturing logs
        if capture_log and tee:
            log_content = tee.getvalue()
            smtp_config = {
                'smtp_server': 'localhost',
                'smtp_port': 25,
                'from_email': 'etp-admin@lists.kit.edu',
                'to_email': 'webadmin@etp.kit.edu',
                'use_tls': False
            }
            
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from_email')
            msg['To'] = smtp_config.get('to_email')
            msg['Subject'] = '❌ ETaPprover - ERROR Occurred'
            
            body = f"An error occurred while running ETaPprover:\n\n{error_msg}\n\n"
            body += "See attached log file for complete details."
            msg.attach(MIMEText(body, 'plain'))
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"etapprover_error_log_{timestamp}.txt"
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(log_content.encode('utf-8'))
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename={log_filename}')
            msg.attach(attachment)
            
            try:
                with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                    server.send_message(msg)
                print("✓ Error notification email sent with log attached")
            except Exception as email_error:
                print(f"✗ Failed to send error email: {email_error}")
        
        raise  # Re-raise the exception after logging
        
    finally:
        # Restore original stdout/stderr
        if tee:
            sys.stdout = tee.terminal
            sys.stderr = tee.terminal

def run_mattermost_test():
    """Interactive Mattermost messaging test."""
    print("=" * 60)
    print("ETaPprover - Mattermost Messaging")
    print("=" * 60)
    
    # Load credentials
    creds = load_credentials()
    api_url = creds['mattermost']['api_url']
    token = creds['mattermost']['token']
    
    # Test connection
    success, bot_user = test_mattermost_connection(api_url, token)
    if not success:
        sys.exit(1)
    
    bot_id = bot_user['id']
    bot_username = bot_user['username']
    
    print(f"\n📋 Bot Info:")
    print(f"  Username: {bot_username}")
    print(f"  User ID: {bot_id}")
    print(f"  API URL: {api_url}")
    
    # Interactive messaging
    print("\n" + "=" * 60)
    
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
            print("\n" + "=" * 60)
            print("🔍 Username Lookup Tool")
            print("=" * 60)
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
            
            print("\n" + "-" * 60)
            print("📊 Username Lookup Results:")
            print("-" * 60)
            
            mattermost_config = {
                'api_url': api_url,
                'token': token
            }
            
            usernames = extract_supervisor_usernames(names, mattermost_config)
            
            print("\n✓ Generated username mapping:")
            for i, name in enumerate(names):
                if i < len(usernames):
                    print(f"  {name} → @{usernames[i]}")
            
            print("-" * 60)
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
            print("\n" + "=" * 60)
            
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
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ETaPprover - Thesis submission notification system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scrape.py                    # Interactive mode
  python3 scrape.py --cron             # Cronjob mode (with log capture)
  python3 scrape.py --mode scraper     # Direct scraper mode
  python3 scrape.py --mode test        # Mattermost test mode
  python3 scrape.py --interactive      # Test with real data (asks before sending)
        """
    )
    
    parser.add_argument(
        '--cron',
        action='store_true',
        help='Run in cronjob mode (capture and attach log to email)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['scraper', 'test'],
        help='Run mode: scraper (thesis scraper) or test (Mattermost test)'
    )
    
    parser.add_argument(
        '--log',
        action='store_true',
        help='Capture log even in non-cron mode'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Ask for confirmation before sending each notification (for testing)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be sent without actually sending (implies --interactive)'
    )
    
    args = parser.parse_args()
    
    # Dry-run implies interactive
    if args.dry_run:
        args.interactive = True
    
    # Cronjob mode - run scraper with log capture
    if args.cron:
        run_scraper(capture_log=True, interactive=False)
        sys.exit(0)
    
    # Interactive testing mode
    if args.interactive:
        print("=" * 60)
        print("INTERACTIVE MODE")
        print("You will be asked to confirm each notification before sending")
        print("=" * 60)
        run_scraper(capture_log=args.log, interactive=True)
        sys.exit(0)
    
    # Direct mode specified
    if args.mode:
        if args.mode == 'scraper':
            run_scraper(capture_log=args.log, interactive=False)
        elif args.mode == 'test':
            run_mattermost_test()
        sys.exit(0)
    
    # Interactive mode (backward compatible)
    print("=" * 60)
    print("ETaPprover")
    print("=" * 60)
    print("\nSelect mode:")
    print("  1. Run thesis scraper (scrape pending submissions)")
    print("  2. Mattermost messaging test")
    print("  3. Interactive testing (ask before sending)")
    print("  4. Exit")
    
    mode = input("\nChoose mode (1/2/3/4): ").strip()
    
    if mode == '1':
        run_scraper(capture_log=False, interactive=False)
    elif mode == '2':
        run_mattermost_test()
    elif mode == '3':
        print("\n" + "=" * 60)
        print("INTERACTIVE TESTING MODE")
        print("You will be asked to confirm each notification")
        print("=" * 60)
        run_scraper(capture_log=False, interactive=True)
    else:
        print("Exiting.")
        sys.exit(0)
