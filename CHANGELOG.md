# Changelog

All notable changes to ETaPprover will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0]

### Added
- **Smart Username Lookup System**
  - Automatic username generation from supervisor names
  - Multiple pattern matching (firstname initial + lastname, lastname only, etc.)
  - Character normalization (umlauts, accents, special characters)
  - Live verification against Mattermost API
  - Manual override dictionary for special cases
  - Interactive username lookup tool (Option 4 in test mode)

- **Cronjob Support**
  - `--cron` flag for unattended execution
  - Automatic log capture system (`TeeOutput` class)
  - Log files attached to notification emails
  - Timestamped log filenames
  - Status emails even when no submissions found
  - Execution metrics (start time, end time, duration)

- **Command-Line Interface**
  - `--cron`: Run in cronjob mode with log capture
  - `--mode scraper`: Direct scraper mode
  - `--mode test`: Mattermost test mode
  - `--log`: Force log capture in non-cron mode
  - `--help`: Show usage information
  - Backward-compatible interactive mode

- **Error Handling**
  - Username validation with clear error messages
  - Graceful error handling in notification loop
  - Continues processing other submissions on error
  - Detailed error messages with attempted username variants

- **Documentation**
  - `CRONJOB_SETUP.md`: Complete cronjob configuration guide
  - `USERNAME_LOOKUP_GUIDE.md`: Smart username system documentation
  - `README.md`: Comprehensive project documentation
  - Inline code documentation and comments

- **Testing Tools**
  - `test_username_error.py`: Username error handling validation
  - `test_log_capture.py`: Log capture system verification
  - Standalone `test.py` for Mattermost testing

### Changed
- **Email Notifications**
  - Now accept optional log content parameter
  - Automatically attach execution logs
  - Enhanced email body with log reference
  - MIME encoding for text log attachments

- **Notification Logic**
  - Bachelor thesis filtering improved
  - Master/Doctoral theses explicitly skipped for Mattermost
  - Username resolution integrated into notification flow
  - Better error messages and status reporting

- **Code Organization**
  - Added logging system section
  - Clearer function separation
  - Better code comments
  - Consistent error handling patterns

### Fixed
- SSL warning suppression for self-signed certificates
- Character encoding in username generation
- Error propagation in username lookup
- Email sending for edge cases (no submissions)

## [1.0.0] 

### Added
- Initial release
- Thesis submission scraping from publish.etp.kit.edu
- Email notifications for pending submissions

### Features
- Web scraping with BeautifulSoup
- Session-based authentication
- API integration with thesis repository
- SMTP email notifications

### Technical
- Python 3.7+ support
- Requests library for HTTP
- BeautifulSoup4 for HTML parsing
- urllib3 for SSL handling
- smtplib for email

---

## Version Number Scheme

- **Major version** (X.0.0): Breaking changes, major features
- **Minor version** (1.X.0): New features, backward compatible
- **Patch version** (1.0.X): Bug fixes, minor improvements


**Note**: Version numbers and dates use the format YYYY-MM-DD.
