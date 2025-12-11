# ETaPprover Cronjob Setup Guide

## Overview

The ETaPprover system can run automatically via cronjob to check for new thesis submissions and send notifications. When run in cronjob mode, it captures all output and attaches it to the notification email for easy monitoring.

## Features in Cronjob Mode

✅ **Automatic Log Capture**: All console output is captured  
✅ **Email Attachment**: Log file is attached to notification email  
✅ **Timestamped Logs**: Each log file has a unique timestamp  
✅ **Status Emails**: Even when no submissions are found, you get a status email with log  
✅ **Execution Metrics**: Start time, end time, and duration included in log  
✅ **Silent Operation**: No manual interaction required  

## Running Modes

### 1. Cronjob Mode (Recommended for Automation)
```bash
python3 scrape.py --cron
```
- Captures all output to log
- Attaches log to notification email
- Perfect for unattended execution

### 2. Direct Scraper Mode
```bash
python3 scrape.py --mode scraper
```
- Runs scraper without log capture
- Good for manual testing

### 3. Direct Scraper with Log
```bash
python3 scrape.py --mode scraper --log
```
- Runs scraper WITH log capture
- Good for testing log functionality

### 4. Mattermost Test Mode
```bash
python3 scrape.py --mode test
```
- Interactive Mattermost testing
- Username lookup tool

### 5. Interactive Mode (Legacy)
```bash
python3 scrape.py
```
- Classic menu-based interface
- Choose mode interactively

## Cronjob Setup

### Example 1: Run Every Day at 9 AM
```bash
# Edit crontab
crontab -e

# Add this line:
0 9 * * * cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && /usr/bin/python3 scrape.py --cron
```

### Example 2: Run Every Hour (Business Hours)
```bash
# Run at the start of every hour from 8 AM to 6 PM, Monday-Friday
0 8-18 * * 1-5 cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && /usr/bin/python3 scrape.py --cron
```

### Example 3: Run Twice Daily
```bash
# Run at 9 AM and 3 PM every day
0 9,15 * * * cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && /usr/bin/python3 scrape.py --cron
```

### Example 4: Run Every 2 Hours
```bash
# Run every 2 hours, every day
0 */2 * * * cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && /usr/bin/python3 scrape.py --cron
```

## Cronjob Syntax Reference

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday=0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## Email Notification Format

### With Pending Submissions
```
Subject: New Pending Thesis Submissions - 2 item(s)

Hello,

There are 2 new thesis submission(s) pending approval:

1. Analysis of Neural Networks
   Author: Müller, Stefan
   Supervisors: Hornung, Johannes; Gaisdörfer, Marcel
   Type: Bachelor Thesis

2. Quantum Computing Applications
   Author: Schmidt, Anna
   Supervisors: Hornung, Johannes
   Type: Bachelor Thesis

Please review and approve these submissions.

See attached log file for detailed execution information.

Best regards,
ETaPprover

Attachments:
  - etapprover_log_20251121_090015.txt
```

### Without Pending Submissions
```
Subject: ETaPprover - No Pending Submissions

No pending thesis submissions found.

See attached log for details.

Attachments:
  - etapprover_log_20251121_090015.txt
```

## Log File Contents

The attached log contains:
- Execution timestamp (start/end)
- Login status
- API connection details
- Number of submissions fetched
- Bachelor thesis filtering
- Supervisor username resolution
- Mattermost connection status
- Message delivery status
- Execution duration
- Any errors or warnings

Example log excerpt:
```
============================================================
ETaPprover - Thesis Submission Scraper
Execution started: 2025-11-21 09:00:15
============================================================
✓ Login successful.
✓ Total submissions fetched: 5
✓ Pending submissions: 2

============================================================
[1/2] Processing submission
============================================================
  Record ID: 12345
  Title: Analysis of Neural Networks
  Author: Müller, Stefan
  Supervisors: Hornung, Johannes; Gaisdörfer, Marcel
  Type: Bachelor Thesis
  Approval: pending

============================================================
📨 Sending Mattermost Notifications
============================================================

--- Processing: Analysis of Neural Networks... ---
✓ Bachelor thesis detected, preparing notification...
  🔍 Processing supervisor: Hornung, Johannes
    ✓ Using manual override: @jhornung
  🔍 Processing supervisor: Gaisdörfer, Marcel
    ✓ Using manual override: @mgais
Recipients: jhornung, mgais
Sending group DM to 2 recipients...
✓ Message sent successfully

============================================================
Execution completed: 2025-11-21 09:00:23
Total duration: 8.34 seconds
============================================================
```

## Monitoring Best Practices

### 1. Check Email Regularly
- Review notification emails
- Check attached logs for errors
- Look for WARNING messages

### 2. Test First
Before setting up cronjob, test manually:
```bash
python3 scrape.py --cron
```

### 3. Verify Credentials
Ensure `credentials.json` is readable:
```bash
ls -la credentials.json
# Should show: -rw------- (600 permissions)
```

### 4. Check Cronjob Logs
View cron execution history:
```bash
# On systemd systems
journalctl -u cron -f

# Or check mail
mail
```

### 5. Test Email Delivery
Verify SMTP server is accessible:
```bash
telnet localhost 25
```

## Troubleshooting

### Cronjob Not Running
```bash
# Check if cron service is running
systemctl status cron

# Check crontab syntax
crontab -l

# Check system logs
grep CRON /var/log/syslog
```

### No Email Received
- Check SMTP server: `localhost:25`
- Verify `from_email` and `to_email` in script
- Check spam folder
- Review log file for email errors

### Permission Errors
```bash
# Make script executable
chmod +x scrape.py

# Check credentials file permissions
chmod 600 credentials.json
```

### Python Not Found
Use full path in cronjob:
```bash
# Find Python path
which python3

# Use in crontab
0 9 * * * cd /path/to/script && /usr/bin/python3 scrape.py --cron
```

## Environment Variables

If you need to set environment variables for cronjob:
```bash
# In crontab
MAILTO=webadmin@etp.kit.edu
PATH=/usr/local/bin:/usr/bin:/bin

0 9 * * * cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && python3 scrape.py --cron
```

## Advanced: Redirect Output to File (Alternative)

If you want to keep local log files in addition to email:
```bash
# Create log directory
mkdir -p /home/johannes/Documents/Scripts/webmaster/automatic_messaging/logs

# Cronjob with output redirection
0 9 * * * cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && python3 scrape.py --cron >> logs/cron_$(date +\%Y\%m\%d).log 2>&1
```

## Testing the Setup

### Step 1: Test Manual Execution
```bash
cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging
python3 scrape.py --cron
```

### Step 2: Check Email
Verify you received the email with log attachment

### Step 3: Test Cronjob (One-Time)
```bash
# Add temporary cronjob to run in 5 minutes
crontab -e
# Add: */5 * * * * cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && python3 scrape.py --cron
```

### Step 4: Monitor Execution
```bash
# Watch for cronjob execution
tail -f /var/log/syslog | grep CRON
```

### Step 5: Remove Test Cronjob
```bash
crontab -e
# Remove or comment out the test line
```

## Production Recommendation

For production use, run every 2-4 hours during business hours:
```bash
# Run at 8 AM, 12 PM, and 4 PM on weekdays
0 8,12,16 * * 1-5 cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && /usr/bin/python3 scrape.py --cron
```

This ensures:
- ✅ Timely notifications
- ✅ Not too frequent (avoids spam)
- ✅ Only during work hours
- ✅ Complete audit trail via logs

## Support

If issues persist:
1. Check attached log files in emails
2. Run manually: `python3 scrape.py --mode scraper --log`
3. Test Mattermost: `python3 scrape.py --mode test`
4. Review `USERNAME_LOOKUP_GUIDE.md` for username issues
