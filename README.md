# ETaPprover - Thesis Submission Notification System

Automated system for monitoring thesis submissions and notifying supervisors via email and Mattermost.

## 🎯 Features

- **Automated Thesis Scraping**: Monitors pending Bachelor thesis submissions from publish.etp.kit.edu
- **Smart Username Detection**: Automatically generates and verifies Mattermost usernames from supervisor names
- **Multi-Channel Notifications**: 
  - Email notifications to webadmin
  - Mattermost group DMs to supervisors (Bachelor theses and Master theses only)
- **Cronjob Ready**: Captures execution logs and attaches them to notification emails
- **Error Handling**: Validates usernames before sending, with clear error messages
- **Interactive Testing**: Built-in tools for testing Mattermost messaging and username lookup

## 📋 Requirements

- Python 3.7+
- Required packages: `requests`, `beautifulsoup4`, `urllib3`
- Access to:
  - Thesis repository (publish.etp.kit.edu)
  - Mattermost server with bot token
  - SMTP server for email notifications

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd etapprover

# Install dependencies
pip install -r requirements.txt

# Copy and configure credentials
cp credentials.json.example credentials.json
nano credentials.json
```

### 2. Configure Credentials

Edit `credentials.json`:

```json
{
  "email": "your-email@kit.edu",
  "password": "your-password",
  "mattermost": {
    "api_url": "https://mattermost.etp.kit.edu/api",
    "token": "your-bot-token"
  }
}
```

### 3. Test the System

```bash
# Test Mattermost connection and username lookup
python3 scrape.py --mode test

# Test scraper with log capture
python3 scrape.py --mode scraper --log
```

### 4. Set Up Cronjob

```bash
# Edit crontab
crontab -e

# Run every 2 hours during business hours (9 AM - 5 PM, Mon-Fri)
0 9-17/2 * * 1-5 cd /path/to/etapprover && /usr/bin/python3 scrape.py --cron
```

## 📖 Usage

### Command-Line Options

```bash
# Interactive mode (menu-based)
python3 scrape.py

# Cronjob mode (captures log, attaches to email)
python3 scrape.py --cron

# Direct scraper mode
python3 scrape.py --mode scraper

# Mattermost test mode
python3 scrape.py --mode test

# Interactive testing mode (ask before sending each notification)
python3 scrape.py --interactive

# Dry-run mode (preview without sending, implies --interactive)
python3 scrape.py --dry-run

# Scraper with log capture
python3 scrape.py --mode scraper --log

# Show help
python3 scrape.py --help
```

### Interactive Mode Menu

1. **Run thesis scraper** - Check for pending submissions and send notifications
2. **Mattermost messaging test** - Interactive DM testing with 4 options:
   - Send to one person
   - Send to multiple people (individual DMs)
   - Send to group DM (all in same conversation)
   - Test username lookup
3. **Interactive testing** - Run scraper with confirmation prompts (safe for testing with real data)
4. **Exit**

## 🔧 Configuration

### Email Configuration

Email settings are in `scrape.py` (`run_scraper` function):

```python
smtp_config = {
    'smtp_server': 'localhost',
    'smtp_port': 25,
    'from_email': 'etp-admin@lists.kit.edu',
    'to_email': 'webadmin@etp.kit.edu',
    'use_tls': False
}
```

### Username Mappings

Manual username overrides in `scrape.py` and `test.py`:

```python
manual_overrides = {
    'hornung': 'jhornung',
    'gaisdörfer': 'mgais',
    'quiroga-trivino': 'aquiroga'
}
```

## 📚 Documentation

- **[CRONJOB_SETUP.md](docs/CRONJOB_SETUP.md)** - Detailed cronjob setup guide
- **[USERNAME_LOOKUP.md](docs/USERNAME_LOOKUP.md)** - Username detection system documentation
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design decisions
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## 🧪 Testing

### Test Scripts

```bash
# Test username lookup functionality
python3 tests/test_username_error.py

# Test log capture system
python3 tests/test_log_capture.py

# Test Mattermost connection
python3 test.py
```

### Testing with Real Data

**IMPORTANT**: When there are real thesis submissions in the system, use interactive mode to safely test:

```bash
# Interactive testing mode - asks before sending each notification
python3 scrape.py --interactive
```

**What happens in interactive mode:**
1. ✅ Fetches real pending submissions from repository
2. ✅ Shows preview of email notification with list of theses
3. ❓ **Asks: "Send email notification? (y/n)"**
4. ✅ For each thesis, shows supervisor notification preview
5. ❓ **Asks: "Send this notification to supervisors? (y/n/skip)"**
6. ✅ Shows author permission request preview
7. ❓ **Asks: "Send this permission request to author? (y/n/skip)"**

**Options for each prompt:**
- `y` or `yes` - Send the notification
- `n` or `no` - Skip and cancel (continues to next)
- `skip` - Skip this specific notification

This allows you to:
- ✅ Test with real data safely
- ✅ Preview all messages before sending
- ✅ Selectively send only some notifications
- ✅ Verify username resolution works correctly
- ✅ Check message formatting

### Manual Testing

Use the interactive test mode:
```bash
python3 scrape.py --mode test
# Choose Option 4: Test username lookup
```

## 🏗️ Project Structure

```
etapprover/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── credentials.json.example     # Template for credentials
├── credentials.json             # Your credentials (gitignored)
├── scrape.py                    # Main scraper script
├── test.py                      # Standalone Mattermost test tool
├── docs/                        # Documentation
│   ├── CRONJOB_SETUP.md        # Cronjob configuration guide
│   ├── USERNAME_LOOKUP.md      # Username detection docs
│   └── ARCHITECTURE.md         # Technical architecture
├── tests/                       # Test scripts
│   ├── test_username_error.py  # Username error handling tests
│   └── test_log_capture.py     # Log capture tests
└── .gitignore                   # Git ignore rules
```

## 🔒 Security

- **Never commit `credentials.json`** - Add to `.gitignore`
- **Protect credentials file**: `chmod 600 credentials.json`
- **Use bot token**: Don't use personal Mattermost tokens
- **SSL warnings**: Self-signed certificates warnings are suppressed (expected for internal servers)

## 🐛 Troubleshooting

### Common Issues

**Issue**: Username not found for supervisor
```bash
# Test username lookup
python3 scrape.py --mode test
# Choose Option 4, enter supervisor name
# Add manual override if needed
```

**Issue**: Cronjob not running
```bash
# Check crontab syntax
crontab -l

# Check system logs
grep CRON /var/log/syslog

# Test manually first
python3 scrape.py --cron
```

**Issue**: No email received
- Check SMTP server: `telnet localhost 25`
- Verify email addresses in script
- Check spam folder
- Review log attachment for errors

See [CRONJOB_SETUP.md](docs/CRONJOB_SETUP.md) for more troubleshooting.

## 📝 How It Works

1. **Login** to thesis repository
2. **Fetch** pending submissions via API
3. **Filter** for Bachelor theses only
4. **Extract** supervisor names from metadata
5. **Resolve** supervisor Mattermost usernames (smart detection)
6. **Send** email notification with log attachment
7. **Send** Mattermost group DMs to webadmin + supervisors

### Notification Flow

```
Pending Submission Detected
         ↓
   Bachelor Thesis?
    /           \
  YES            NO
   ↓              ↓
Extract      Email Only
Supervisors      ↓
   ↓           Skip MM
Resolve 
Usernames
   ↓
Send Email
(with log)
   ↓
Send Group DM
(Mattermost)
```

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature-name`
2. Make changes and test thoroughly
3. Update documentation if needed
4. Commit with clear messages: `git commit -m "Add feature"`
5. Push and create pull request

## 📜 License

Internal tool for ETP KIT. Not for public distribution.

## 👥 Authors

- Johannes Hornung - Initial development
- GitHub Copilot - Smart username lookup & cronjob features

## 📞 Support

For issues or questions:
- Check documentation in `docs/`
- Review test scripts in `tests/`
- Contact: webadmin@etp.kit.edu

## 🗓️ Version

**Current Version**: 2.0  
**Last Updated**: 2025-11-21

See [CHANGELOG.md](CHANGELOG.md) for version history.
