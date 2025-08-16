# Installation

This guide will walk you through installing jarkdown and setting up the required authentication.

## Prerequisites

- Python 3.8 or higher
- A Jira account with API access
- An Atlassian API token

## Install from PyPI

Once published to PyPI, you'll be able to install with:

```bash
pip install jarkdown
```

## Install from Source

For the latest development version or to contribute:

```bash
# Clone the repository
git clone https://github.com/yourusername/jarkdown.git
cd jarkdown

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Authentication Setup

jarkdown requires three environment variables for authentication:

### 1. Get Your Atlassian API Token

1. Log in to your Atlassian account
2. Go to [Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
3. Click "Create API token"
4. Give it a descriptive name (e.g., "jarkdown")
5. Copy the generated token - you won't be able to see it again!

### 2. Create Environment File

Create a `.env` file in your project directory:

```bash
# .env
JIRA_DOMAIN=yourcompany.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_api_token_here
```

**Security Note:** Never commit the `.env` file to version control! It's already included in `.gitignore`.

### 3. Alternative: Export Variables

You can also export the variables in your shell:

```bash
export JIRA_DOMAIN=yourcompany.atlassian.net
export JIRA_EMAIL=your.email@company.com
export JIRA_API_TOKEN=your_api_token_here
```

For permanent setup, add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.).

## Verify Installation

Test that everything is working:

```bash
# Check the installation
jarkdown --help

# Test with a known issue
jarkdown PROJ-123
```

If you see the issue downloaded successfully, you're all set!

## Troubleshooting

### Command not found

If `jarkdown` isn't recognized:

```bash
# Ensure you're in the virtual environment
which python

# Reinstall
pip install -e .
```

### Authentication errors

- **401 Unauthorized**: Check your email and API token are correct
- **Domain not found**: Verify JIRA_DOMAIN doesn't include `https://`
- **Missing variables**: Ensure all three environment variables are set

### Permission denied

On Unix-like systems, you might need to make the script executable:

```bash
chmod +x jarkdown
```

## Next Steps

- Read the [Usage Guide](usage.md) to learn all available options
- Check the [Configuration](configuration.md) page for advanced settings
- See [Architecture](architecture.md) if you want to understand how it works
