# Interactive Testing Mode - Quick Guide

## Purpose

The interactive mode allows you to **safely test the notification system with real thesis data** by previewing and confirming each notification before it's sent.

## When to Use

✅ Testing the system with actual pending theses  
✅ Verifying username resolution works correctly  
✅ Checking message formatting and content  
✅ Selectively sending notifications (e.g., only to one thesis)  
✅ First-time setup and validation  

## How to Run

```bash
# Method 1: Command-line flag
python3 scrape.py --interactive

# Method 2: Interactive menu
python3 scrape.py
# Then choose Option 3: "Interactive testing"

# Method 3: Dry-run mode (same as interactive)
python3 scrape.py --dry-run
```

## What Happens

### Step 1: Repository Login & Fetch
```
============================================================
ETaPprover - Thesis Submission Scraper
MODE: Interactive (confirmation required)
Execution started: 2025-12-11 15:30:00
============================================================
✓ Login successful.
✓ Total submissions fetched: 3
✓ Pending submissions: 2
```

### Step 2: Email Preview
```
============================================================
EMAIL NOTIFICATION
============================================================
To: webadmin@etp.kit.edu
Subject: New Pending Thesis Submissions - 2 item(s)

This email will contain:
  1. Analysis of Neural Networks in Particle Physics
     Author: Müller, Stefan
  2. Quantum Computing Applications in High Energy Physics
     Author: Schmidt, Anna

📧 Send email notification? (y/n):
```

**Your options:**
- `y` or `yes` → Send the email
- `n` or `no` → Skip email (won't send)

### Step 3: Supervisor Notification Preview (for each thesis)
```
--- Processing: Analysis of Neural Networks in Particle... ---
✓ Bachelor thesis detected, preparing notification...
  🔍 Processing supervisor: Hornung, Johannes
    ✓ Using manual override: @jhornung
  🔍 Processing supervisor: Gaisdörfer, Marcel
    ✓ Using manual override: @mgais
Recipients: jhornung, mgais

============================================================
SUPERVISOR NOTIFICATION PREVIEW
============================================================
To: jhornung, mgais
------------------------------------------------------------
Hi,
Stefan Müller has submitted their thesis into publish.

**Title**: Analysis of Neural Networks in Particle Physics
**Author**: Müller, Stefan
**Type**: Bachelor Thesis

Can this be uploaded to publish with open access rights?
If this isn't possible, please contact the author directly to clarify.

Cheers,
ETPApprover Bot
============================================================

📤 Send this notification to supervisors? (y/n/skip):
```

**Your options:**
- `y` or `yes` → Send this notification
- `n` or `no` → Cancel and move to next thesis
- `skip` → Skip supervisor notification, but continue to author request

### Step 4: Author Permission Request Preview
```
--- Contacting author for permission ---
  🔍 Processing author: Müller, Stefan
    💡 Generated variants: smueller, mueller, stefanmueller
    ✓ Found valid username: @smueller
Author recipients: jhornung, smueller

============================================================
AUTHOR PERMISSION REQUEST PREVIEW
============================================================
To: jhornung, smueller
------------------------------------------------------------
Hi Stefan Müller,

Your thesis **"Analysis of Neural Networks in Particle Physics"** has been submitted to our repository. Congratulations for handing in :partyparrot:

We would like to confirm: Do you give permission to publish this thesis with **open access rights**? This means your thesis will be publicly accessible online.

Please reply with your confirmation.

Cheers,
ETPApprover Bot
============================================================

📤 Send this permission request to author? (y/n/skip):
```

**Your options:**
- `y` or `yes` → Send author request
- `n` or `no` → Cancel (move to next thesis)
- `skip` → Skip author request for this thesis

### Step 5: Repeat for Each Thesis

The process repeats for each pending submission.

## Example Session

```bash
$ python3 scrape.py --interactive

============================================================
INTERACTIVE MODE
You will be asked to confirm each notification before sending
============================================================
============================================================
ETaPprover - Thesis Submission Scraper
MODE: Interactive (confirmation required)
Execution started: 2025-12-11 15:30:00
============================================================

✓ Login successful.
✓ Total submissions fetched: 3
✓ Pending submissions: 2

# ... fetching continues ...

📧 Send email notification? (y/n): n
❌ Email notification skipped

# First thesis
📤 Send this notification to supervisors? (y/n/skip): y
✓ Sending supervisor notification...
✓ Notification sent successfully

📤 Send this permission request to author? (y/n/skip): n
❌ Author notification cancelled

# Second thesis
📤 Send this notification to supervisors? (y/n/skip): skip
⏭  Skipping supervisor notification for this thesis

# Done
✓ Execution completed: 2025-12-11 15:32:15
Total duration: 135.45 seconds
```

## Common Workflows

### Workflow 1: Test Everything Without Sending
```bash
python3 scrape.py --interactive
# Answer 'n' to all prompts
# Result: Preview all messages, send nothing
```

### Workflow 2: Send Only to Specific Thesis
```bash
python3 scrape.py --interactive
# Email: n
# Thesis 1: skip, skip
# Thesis 2: y, y  ← Send this one
# Thesis 3: skip, skip
```

### Workflow 3: Test Username Resolution
```bash
python3 scrape.py --interactive
# Watch the username generation output
# Answer 'n' to all sending prompts
# Check if usernames are resolved correctly
```

### Workflow 4: Send Supervisor Notifications Only
```bash
python3 scrape.py --interactive
# Email: y
# For each thesis:
#   - Supervisor: y
#   - Author: skip
```

## Tips

### ✅ Do's
- ✅ Use interactive mode for **first-time testing**
- ✅ Use it when **new supervisors** are added
- ✅ Use it to **verify message formatting**
- ✅ Use it to **check username generation**

### ❌ Don'ts
- ❌ Don't use interactive mode in **cronjobs** (use `--cron` instead)
- ❌ Don't use for **regular automated runs** (defeats the purpose)
- ❌ Don't commit if you answered `y` accidentally (check your DMs!)

## Safety Features

1. **No automatic sending**: Everything requires confirmation
2. **Granular control**: Approve email, supervisors, and authors separately
3. **Skip option**: Skip individual notifications without cancelling everything
4. **Preview before send**: See exact message before confirming
5. **Username verification**: See which usernames are being resolved

## Troubleshooting

### Issue: "No pending submissions found"
**Cause**: No theses in pending state  
**Solution**: Check repository manually, or submissions may already be approved

### Issue: Username not found for supervisor
**Cause**: Supervisor not in Mattermost or name mismatch  
**Solution**: Add manual override in `manual_overrides` dict

### Issue: Author username not found
**Cause**: Student not in Mattermost  
**Solution**: Normal - system will skip author notification gracefully

### Issue: Accidentally sent notification
**Cause**: Answered `y` when you meant `n`  
**Solution**: 
- Explain in Mattermost that it was a test
- Delete the message if possible
- Use more caution next time

## After Testing

Once you've verified everything works:

1. **Check Mattermost**: Verify messages were received correctly
2. **Check Email**: Verify email was sent (if you said yes)
3. **Review Usernames**: Note any that need manual overrides
4. **Update Overrides**: Add any needed entries to `manual_overrides`
5. **Ready for Production**: Set up cronjob with `--cron` flag

## Production Setup

After successful interactive testing:

```bash
# Add to crontab
crontab -e

# Run every 2 hours during business hours (no interaction required)
0 9-17/2 * * 1-5 cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging && /usr/bin/python3 scrape.py --cron
```

---

**Remember**: Interactive mode is for **testing and verification**. Use `--cron` for **automated production runs**.
