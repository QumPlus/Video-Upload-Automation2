# Video Upload Automation

A Python GUI application for macOS that automatically uploads rendered video files to multiple platforms with configurable platform on/off switches.

## Features

- **Three-tab interface**: Main (Upload), Settings (API Config), Schedule (Automation)
- **Multi-platform support**: CloudFlare Stream, YouTube, Pinterest, Facebook
- **Platform toggles**: Enable/disable specific platforms
- **Concurrent uploads**: Configurable simultaneous uploads
- **Scheduling**: Automated daily/weekly uploads
- **Status tracking**: Upload progress and completion status
- **macOS optimized**: Native dark mode support

## Setup

1. **Install Python 3.8+**
   ```bash
   python3 --version
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

## Configuration

### Folder Structure
Create the following folder structure in your selected directory:
```
Rendered/
├── CloudFlare/          # Videos for CloudFlare + Facebook
├── Pinterest/           # Videos for Pinterest only  
└── YouTube Shorts/      # Videos for YouTube Shorts only
```

### Platform Setup

**CloudFlare Stream:**
- API Token from CloudFlare dashboard
- Account ID from CloudFlare dashboard

**YouTube:**
- Google Cloud Console project
- OAuth2 Client ID and Client Secret
- Enable YouTube Data API v3

**Pinterest:**
- Pinterest Developer account
- Access Token from Pinterest App
- Board ID (optional)

**Facebook:**
- Facebook App with Groups API access
- Page Access Token
- Private Group ID

## Usage

1. **Settings Tab**: Configure API credentials and enable platforms
2. **Main Tab**: Select folder and click RUN to start uploads
3. **Schedule Tab**: Set up automated runs (daily/weekly)

## Upload Logic

- **CloudFlare folder**: → CloudFlare + Facebook (+ YouTube if filename contains "001")
- **Pinterest folder**: → Pinterest only
- **YouTube Shorts folder**: → YouTube Shorts only
- **Facebook posts**: Scheduled 30 days in future

## File Requirements

Include text files for metadata:
- `TITLE.txt` - Video title
- `DESCRIPTION.txt` - Full description  
- `SHORT_DESCRIPTION.txt` - Brief description

## Status Files

The app creates status files to track progress:
- `filename_UPLOADING.txt` - Upload in progress
- `filename_COMPLETED.txt` - Upload successful
- `filename_ERROR.txt` - Upload failed

## Troubleshooting

- Check Settings tab for API connection tests
- Review log window for detailed error messages
- Ensure video files are valid and accessible
- Verify platform credentials and permissions 