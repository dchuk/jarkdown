# Getting Started for Beginners

Welcome! This guide will walk you through setting up and using Jarkdown, even if you're new to command-line tools. We'll explain everything step by step.

## What is Jarkdown?

Jarkdown is a tool that helps you export issues from Jira (a project management system) into Markdown files on your computer. This is useful for:
- Creating offline documentation
- Sharing issues with people who don't have Jira access
- Archiving completed projects
- Including Jira content in other documents

## Prerequisites

Before you begin, you'll need:
1. **Python installed on your computer** - Jarkdown requires Python 3.8 or newer
2. **A Jira Cloud account** - You need access to a Jira instance
3. **A Jira API token** - We'll show you how to get this

## Step 1: Install Python

If you don't have Python installed:

### On Windows:
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest Python 3 version (3.8 or newer)
3. Run the installer
4. **Important:** Check the box "Add Python to PATH" during installation
5. Click "Install Now"

### On macOS:
1. Open Terminal (find it in Applications > Utilities)
2. Check if Python is installed by typing: `python3 --version`
3. If not installed, go to [python.org/downloads](https://www.python.org/downloads/)
4. Download and run the macOS installer

### On Linux:
Python is usually pre-installed. Open a terminal and check with: `python3 --version`

## Step 2: Open a Terminal/Command Prompt

You'll need to use a terminal to run Jarkdown:

### On Windows:
1. Press `Windows + R`
2. Type `cmd` and press Enter
3. Or search for "Command Prompt" in the Start menu

### On macOS:
1. Press `Command + Space`
2. Type "Terminal" and press Enter
3. Or find Terminal in Applications > Utilities

### On Linux:
- Press `Ctrl + Alt + T` on most distributions
- Or look for "Terminal" in your applications menu

## Step 3: Install Jarkdown

In your terminal, type this command and press Enter:

```bash
pip install jarkdown
```

Wait for the installation to complete. You should see messages about downloading and installing packages.

To verify the installation worked, type:

```bash
jarkdown --version
```

You should see the version number displayed.

## Step 4: Get Your Jira API Token

1. Open your web browser and go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Log in with your Atlassian account (the same one you use for Jira)
3. Click the blue "Create API token" button
4. Give your token a name like "jarkdown"
5. Click "Create"
6. **Important:** Copy the token that appears - you won't be able to see it again!
7. Save it somewhere safe (like a password manager or secure note)

## Step 5: Configure Jarkdown

You need to tell Jarkdown how to connect to your Jira instance.

### Creating the Configuration File

1. In your terminal, navigate to where you want to work with Jira issues. For example:
   - Windows: `cd C:\Users\YourName\Documents`
   - Mac/Linux: `cd ~/Documents`

2. Create a new file called `.env` (note the dot at the beginning!)

### On Windows (using Notepad):
```cmd
notepad .env
```

### On macOS/Linux (using nano):
```bash
nano .env
```

3. In the file, add these three lines (replace with your actual information):
```
JIRA_DOMAIN=yourcompany.atlassian.net
JIRA_EMAIL=your.email@example.com
JIRA_API_TOKEN=paste-your-token-here
```

Where:
- `JIRA_DOMAIN`: The web address you use to access Jira (without https://)
- `JIRA_EMAIL`: The email you use to log into Jira
- `JIRA_API_TOKEN`: The token you created in Step 4

4. Save the file:
   - In Notepad: File > Save
   - In nano: Press `Ctrl+X`, then `Y`, then Enter

## Step 6: Use Jarkdown

Now you're ready to export your first Jira issue!

### Basic Usage

To export a Jira issue, you need its key (like "PROJ-123"). In your terminal, type:

```bash
jarkdown PROJ-123
```

Replace "PROJ-123" with your actual issue key.

This will:
1. Connect to Jira and fetch the issue
2. Download any attachments
3. Create a folder named after the issue
4. Save everything as markdown files

### Where Are My Files?

Jarkdown creates a new folder in your current directory. For example, if you run `jarkdown PROJ-123`, it creates:

```
PROJ-123/
├── PROJ-123.md       (the issue content)
├── image1.png        (any attachments)
├── document.pdf
└── ...
```

### Specifying an Output Directory

To save files in a specific location:

```bash
jarkdown PROJ-123 --output C:\Users\YourName\Desktop\JiraExports
```

Or on Mac/Linux:

```bash
jarkdown PROJ-123 --output ~/Desktop/JiraExports
```

## Troubleshooting

### "Command not found" error
- Make sure Python and pip are installed correctly
- On Windows, you may need to restart your terminal after installing Python
- Try `python -m pip install jarkdown` instead

### "Authentication failed" error
- Double-check your API token is correct
- Verify your email address is the one you use for Jira
- Make sure your `.env` file is in the current directory

### "Issue not found" error
- Check that the issue key is correct (including the project prefix)
- Verify you have permission to view the issue in Jira

### Can't see the .env file
Files starting with a dot are hidden by default:
- **Windows:** In File Explorer, click View > Show > Hidden items
- **macOS:** In Finder, press `Command + Shift + .`
- **Linux:** In your file manager, press `Ctrl + H`

## Getting Help

If you encounter issues:
1. Check the error message for clues
2. Visit the [documentation](https://jarkdown.readthedocs.io/)
3. Report issues at [GitHub](https://github.com/chrisbyboston/jarkdown/issues)

## Next Steps

Once you're comfortable with basic usage, explore:
- The [Usage Guide](usage.md) for advanced options
- The [Configuration Guide](configuration.md) for additional settings
- Using `jarkdown --help` to see all available options

Congratulations! You're now ready to export Jira issues to markdown.
