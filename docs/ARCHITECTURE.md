# ETaPprover - System Architecture

## Overview

ETaPprover is a Python-based notification system that monitors thesis submissions and automatically notifies relevant stakeholders via email and Mattermost.

## System Components

### 1. Core Scraper (`scrape.py`)

**Purpose**: Main application script with dual functionality:
- Automated thesis scraping and notification
- Interactive Mattermost testing

**Key Components**:
- Credential Management
- Repository/Zenodo Functions
- Email Notification System
- Mattermost Integration
- Smart Username Resolution
- Logging System

### 2. Test Utility (`test.py`)

**Purpose**: Standalone Mattermost testing tool

**Features**:
- Independent of scraping logic
- Direct messaging capabilities
- Username lookup testing
- Interactive menu interface

### 3. Configuration (`credentials.json`)

**Purpose**: Centralized credential storage

**Structure**:
```json
{
  "email": "repository-login",
  "password": "repository-password",
  "mattermost": {
    "api_url": "mattermost-server-url",
    "token": "bot-token"
  }
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ETaPprover System                     │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   scrape.py  │ │   test.py    │ │credentials.  │
    │   (Main App) │ │   (Testing)  │ │json (Config) │
    └──────────────┘ └──────────────┘ └──────────────┘
            │
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌─────────┐    ┌─────────────┐
│ Mode 1: │    │  Mode 2:    │
│ Scraper │    │Mattermost   │
│         │    │   Test      │
└────┬────┘    └─────────────┘
     │
     │
┌────┴──────────────────────────────┐
│  Scraper Workflow                 │
│  1. Login to Repository           │
│  2. Fetch Pending Submissions     │
│  3. Filter Bachelor Theses        │
│  4. Extract Metadata              │
│  5. Resolve Usernames             │
│  6. Send Notifications            │
└───────────────┬───────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
  ┌──────────┐    ┌──────────────┐
  │  Email   │    │ Mattermost   │
  │  (SMTP)  │    │ (Group DM)   │
  └──────────┘    └──────────────┘
```

## Data Flow

### Scraping Flow

```
Repository API
      ↓
  [Login]
      ↓
[Fetch Submissions]
      ↓
[Parse JSON Response]
      ↓
[Extract Metadata]
      ├─ Title
      ├─ Author
      ├─ Type
      └─ Supervisors
      ↓
[Filter Bachelor Theses]
      ↓
[Resolve Usernames]
      ├─ Check Manual Overrides
      ├─ Generate Variants
      └─ Verify with Mattermost API
      ↓
[Send Notifications]
      ├─ Email (always)
      └─ Mattermost (Bachelor only)
```

### Notification Flow

```
Pending Submission
      ↓
 [Is Bachelor?]
  /          \
YES           NO
 │             │
 ├─ Email ────┤
 │             │
 └─ Mattermost │
       │       │
       │       └─ Email Only
       │
    [Extract Supervisors]
       │
    [Resolve Usernames]
       │
  ┌────┴─────┐
  │ Manual   │
  │Override? │
  └────┬─────┘
       │
  ┌────┴─────┐
  │Generate  │
  │Variants  │
  └────┬─────┘
       │
  ┌────┴─────┐
  │ Verify   │
  │with MM   │
  └────┬─────┘
       │
   [Success?]
    /     \
  YES      NO
   │        │
[Send DM]  [ERROR]
```

## Key Design Decisions

### 1. Dual-Mode Operation

**Decision**: Separate interactive and automated modes

**Rationale**:
- Testing without affecting production
- Different use cases (development vs. cronjob)
- Easier debugging

### 2. Smart Username Resolution

**Decision**: Multi-pattern username generation with live verification

**Rationale**:
- Reduces manual configuration
- Handles naming variations automatically
- Validates before sending (prevents errors)
- Maintains manual override capability

### 3. Log Capture System

**Decision**: Capture all output and attach to emails

**Rationale**:
- Easy cronjob monitoring
- Full audit trail
- No need for separate log files
- Centralized in email

### 4. Bachelor Thesis Filtering

**Decision**: Only send Mattermost notifications for Bachelor theses

**Rationale**:
- Different approval processes
- Reduced notification noise
- Supervisor involvement varies by thesis type

### 5. Group DM vs Individual DMs

**Decision**: Use group DMs when multiple recipients

**Rationale**:
- Facilitates discussion among supervisors
- Single conversation thread
- Webadmin can see all context
- Reduces duplication

## Technology Stack

### Languages & Frameworks
- **Python 3.7+**: Main language
- **Requests**: HTTP client for API calls
- **BeautifulSoup4**: HTML parsing for web scraping
- **urllib3**: HTTP connection pooling and SSL handling

### External Services
- **Publish.etp.kit.edu**: Thesis repository
- **Mattermost API**: Messaging platform
- **SMTP Server**: Email delivery

### Standard Libraries
- `smtplib`: Email sending
- `email.mime.*`: Email message construction
- `json`: Configuration and API responses
- `datetime`: Timestamps and logging
- `argparse`: Command-line interface
- `sys`, `os`: System integration
- `io.StringIO`: Log capture

## Security Considerations

### 1. Credential Management
- Credentials stored in separate JSON file
- File excluded from version control (.gitignore)
- Recommended file permissions: 600 (owner read/write only)

### 2. SSL/TLS
- Self-signed certificate warnings suppressed (internal servers)
- HTTPS used for all API communication
- verify=False for internal Mattermost (controlled environment)

### 3. Bot Token
- Uses bot account, not personal tokens
- Limited scope (DM sending only)
- Token never logged or printed

### 4. Error Messages
- No credential exposure in error messages
- Safe error handling throughout
- Detailed errors only in attached logs (sent to admin)

## Performance Characteristics

### Resource Usage
- **Memory**: Low (~20-30 MB typical)
- **CPU**: Minimal (I/O bound)
- **Network**: Moderate (multiple API calls)

### Execution Time
- **Login**: 1-2 seconds
- **Fetch Submissions**: 1-3 seconds
- **Username Resolution**: 0.1-0.5s per supervisor
- **Send Notifications**: 1-2 seconds per notification
- **Total**: Typically 5-15 seconds for 1-5 submissions

### Scalability
- Current: Handles 1-20 submissions efficiently
- Bottleneck: Sequential processing of notifications
- Future: Could parallelize notifications if needed

## Error Handling Strategy

### 1. Fail Fast
- Login failure → immediate exit
- Invalid credentials → immediate exit
- Mattermost connection failure → skip Mattermost, continue with email

### 2. Graceful Degradation
- Username resolution failure → skip that submission's Mattermost notification
- Email failure → log error, continue
- One submission error → continue with others

### 3. Clear Error Messages
- User-friendly error descriptions
- Suggested actions (e.g., "add manual override")
- Full stack traces in logs (when captured)

## Testing Strategy

### 1. Unit Tests
- `tests/test_username_error.py`: Username validation
- `tests/test_log_capture.py`: Logging system

### 2. Integration Tests
- `test.py`: Full Mattermost integration
- Interactive mode testing

### 3. Manual Testing
- `--mode test`: Safe testing environment
- Username lookup tool (Option 4)
- Preview before sending

## Deployment Models

### 1. Cronjob (Recommended)
```bash
0 9-17/2 * * 1-5 python3 scrape.py --cron
```
- Automated execution
- Log capture enabled
- Email audit trail

### 2. Manual Execution
```bash
python3 scrape.py --mode scraper
```
- On-demand checking
- Development/debugging
- One-time runs

### 3. Interactive Mode
```bash
python3 scrape.py
```
- Menu-driven interface
- Learning/exploration
- Testing features

## Future Architecture Improvements

### Potential Enhancements

1. **Database Integration**
   - Track notification history
   - Prevent duplicate notifications
   - Generate reports

2. **Message Queue**
   - Decouple scraping from notification
   - Better error recovery
   - Parallel processing

3. **Configuration File**
   - Separate config from credentials
   - YAML/TOML for settings
   - Environment-specific configs

4. **Microservices**
   - Separate scraper service
   - Separate notification service
   - REST API for integration

5. **Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Alert on failures

## Code Organization

### File Structure
```
scrape.py
├── Imports & Setup
├── Logging System (TeeOutput)
├── Credential Management
├── Zenodo/Repository Functions
│   ├── login()
│   ├── get_pending_submissions()
│   ├── extract_submission_data()
│   └── process_all_submissions()
├── Email Notification Functions
│   └── send_notification_email()
├── Mattermost Functions
│   ├── test_mattermost_connection()
│   ├── get_user_by_username()
│   ├── create_dm_channel()
│   ├── create_group_dm_channel()
│   ├── send_message_to_channel()
│   ├── send_dm_to_user()
│   ├── send_group_dm()
│   └── send_dm_to_multiple_users()
├── Username Resolution
│   ├── try_username_with_mattermost()
│   ├── generate_username_variants()
│   └── extract_supervisor_usernames()
├── Main Functions
│   ├── send_mattermost_notifications()
│   ├── run_scraper()
│   └── run_mattermost_test()
└── Entry Point (CLI argument parsing)
```

### Code Principles
- **Single Responsibility**: Each function has one clear purpose
- **DRY**: Shared functionality extracted to helper functions
- **Clear Naming**: Function names describe what they do
- **Documentation**: Docstrings for all major functions
- **Error Handling**: Try-except blocks with meaningful messages
- **Logging**: Print statements for transparency and debugging

## Maintenance Guidelines

### Regular Tasks
- Review and update manual username overrides
- Monitor email logs for errors
- Test after Mattermost API changes
- Update dependencies periodically

### When to Update
- New supervisor joins (add to overrides if needed)
- Mattermost API changes (update API calls)
- Repository API changes (update parsing logic)
- New thesis types added (update filtering)

### Backup Strategy
- Keep `credentials.json` backed up securely
- Maintain `.backup` copy of working version
- Document any manual username overrides
- Export crontab configuration

## Support & Documentation

- **README.md**: Quick start and overview
- **docs/CRONJOB_SETUP.md**: Cronjob configuration
- **docs/USERNAME_LOOKUP.md**: Username system details
- **docs/ARCHITECTURE.md**: This file (technical details)
- **CHANGELOG.md**: Version history

---

**Last Updated**: 2025-11-21  
**Version**: 2.0.0  
**Maintainer**: webadmin@etp.kit.edu
