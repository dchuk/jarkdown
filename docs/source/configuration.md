# Configuration

jarkdown uses environment variables for credentials and an optional TOML file for field selection. This keeps sensitive credentials out of your code and command history.

## Required Environment Variables

These three variables must be set for jarkdown to work:

### JIRA_DOMAIN

Your Atlassian instance domain, without the protocol:

```bash
JIRA_DOMAIN=yourcompany.atlassian.net
```

**Note:** Do not include `https://` - just the domain name.

### JIRA_EMAIL

The email address associated with your Atlassian account:

```bash
JIRA_EMAIL=your.email@company.com
```

This should be the email you use to log into Jira.

### JIRA_API_TOKEN

Your Atlassian API token (not your password):

```bash
JIRA_API_TOKEN=ATATT3xFfGF0A1B2C3D4E5F6G7H8I9J0
```

Generate this from your [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens).

## Setup Wizard

The easiest way to configure credentials:

```bash
jarkdown setup
```

This interactive wizard prompts for your domain, email, and API token (hidden input), then writes a `.env` file in the current directory. If a `.env` file already exists, you'll be asked to confirm before overwriting.

## Configuration Methods

### Method 1: .env File (Recommended)

Create a `.env` file in your project directory:

```bash
# .env
JIRA_DOMAIN=yourcompany.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_token_here
```

**Benefits:**
- Credentials stay in one place
- Easy to update
- Automatically loaded by the tool
- Already in `.gitignore`

### Method 2: Shell Export

Export variables in your current shell session:

```bash
export JIRA_DOMAIN=yourcompany.atlassian.net
export JIRA_EMAIL=your.email@company.com
export JIRA_API_TOKEN=your_token_here
```

**Benefits:**
- Quick for one-time use
- No files to manage

**Drawbacks:**
- Must re-export in each new terminal
- Variables visible in shell history

### Method 3: Shell Profile

Add exports to your shell profile for permanent configuration:

```bash
# ~/.bashrc, ~/.zshrc, or equivalent
export JIRA_DOMAIN=yourcompany.atlassian.net
export JIRA_EMAIL=your.email@company.com
export JIRA_API_TOKEN=your_token_here
```

Then reload your profile:

```bash
source ~/.bashrc  # or ~/.zshrc
```

**Benefits:**
- Always available
- Works across all projects

**Drawbacks:**
- Credentials in your profile
- Same credentials for all projects

### Method 4: direnv (Advanced)

Use [direnv](https://direnv.net/) for directory-specific environment:

```bash
# .envrc
export JIRA_DOMAIN=yourcompany.atlassian.net
export JIRA_EMAIL=your.email@company.com
export JIRA_API_TOKEN=your_token_here
```

**Benefits:**
- Automatic loading when entering directory
- Automatic unloading when leaving
- Per-project configuration

## Field Selection Configuration

Control which custom fields appear in your exported Markdown using a `.jarkdown.toml` file or CLI flags.

### `.jarkdown.toml` File

Create a `.jarkdown.toml` file in your working directory:

#### Include specific fields only

```toml
[fields]
include = ["Story Points", "Sprint", "Team", "Epic Link"]
```

When `include` is set, only the listed custom fields will appear in the output.

#### Exclude specific fields

```toml
[fields]
exclude = ["Internal Notes", "Dev Notes", "Epic Color", "Rank"]
```

When `exclude` is set, the listed fields are hidden but all others are included.

### CLI Flags

CLI flags override `.jarkdown.toml` settings entirely:

```bash
# Include only these custom fields (overrides toml include)
jarkdown export PROJ-123 --include-fields "Story Points,Sprint"

# Exclude these custom fields (overrides toml exclude)
jarkdown export PROJ-123 --exclude-fields "Internal Notes,Dev Notes"

# Force refresh of cached field metadata
jarkdown export PROJ-123 --refresh-fields
```

### Priority Order

1. CLI `--include-fields` / `--exclude-fields` (highest priority)
2. `.jarkdown.toml` `[fields]` section
3. Default: include all custom fields with non-null values

### Field Metadata Cache

jarkdown caches Jira field definitions for 24 hours to avoid repeated API calls. The cache is stored in your platform's config directory:

- **Linux**: `~/.config/jarkdown/fields-{domain}.json`
- **macOS**: `~/Library/Application Support/jarkdown/fields-{domain}.json`
- **Windows**: `%APPDATA%\jarkdown\fields-{domain}.json`

To force a refresh:

```bash
jarkdown export PROJ-123 --refresh-fields
```

## Security Best Practices

### Protecting Your Credentials

1. **Never commit credentials to Git**
   - `.env` is in `.gitignore`
   - Don't commit `.envrc` files
   - Review commits before pushing

2. **Use appropriate file permissions**
   ```bash
   chmod 600 .env  # Only you can read/write
   ```

3. **Rotate tokens regularly**
   - Delete old tokens from Atlassian
   - Generate new tokens periodically
   - Update your configuration

4. **Use separate tokens for different purposes**
   - Development token
   - CI/CD token
   - Production token

### Secure Storage Options

For enhanced security, consider:

1. **Operating System Keychains**
   ```bash
   # macOS Keychain example
   security add-generic-password -s "jarkdown" -a "api-token" -w "your_token"
   ```

2. **Password Managers**
   - Store credentials in 1Password, LastPass, etc.
   - Copy to `.env` when needed

3. **Environment Management Tools**
   - [dotenv](https://github.com/motdotla/dotenv)
   - [direnv](https://direnv.net/)
   - [envchain](https://github.com/sorah/envchain)

## Validation and Testing

### Check Your Configuration

Verify all variables are set:

```bash
# Check if variables are set
echo "JIRA_DOMAIN: ${JIRA_DOMAIN:=NOT SET}"
echo "JIRA_EMAIL: ${JIRA_EMAIL:=NOT SET}"
echo "JIRA_API_TOKEN: ${JIRA_API_TOKEN:=NOT SET}"
```

### Test Connection

Test with a known accessible issue:

```bash
jarkdown export PROJ-1 --verbose
```

### Common Configuration Issues

#### Issue: "JIRA_DOMAIN not found"

**Solution:** Ensure the variable is exported:
```bash
export JIRA_DOMAIN=yourcompany.atlassian.net
```

Or run the setup wizard:
```bash
jarkdown setup
```

#### Issue: "401 Unauthorized"

**Causes and solutions:**
- Wrong email: Verify JIRA_EMAIL matches your account
- Wrong token: Regenerate token in Atlassian settings
- Token expired: Create a new token

#### Issue: "Connection refused"

**Check:**
- Domain doesn't include `https://`
- Domain spelling is correct
- Your network allows HTTPS connections

## Advanced Configuration

### Using Different Configurations

For multiple Jira instances:

```bash
# Create multiple .env files
.env.prod    # Production Jira
.env.dev     # Development Jira
.env.client  # Client's Jira

# Switch between them
cp .env.prod .env
jarkdown export PROD-123

cp .env.dev .env
jarkdown export DEV-456
```

### Configuration in CI/CD

For GitHub Actions:

```yaml
- name: Export Jira Issue
  env:
    JIRA_DOMAIN: ${{ secrets.JIRA_DOMAIN }}
    JIRA_EMAIL: ${{ secrets.JIRA_EMAIL }}
    JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
  run: |
    uv tool install jarkdown
    jarkdown export PROJ-123
```

### Proxy Configuration

If behind a corporate proxy:

```bash
# Set proxy for Python requests
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Run jarkdown
jarkdown export PROJ-123
```

## Troubleshooting Configuration

### Debug Mode

See exactly what's being sent:

```bash
jarkdown export PROJ-123 --verbose
```

### Reset Configuration

Start fresh if having issues:

```bash
# Clear environment variables
unset JIRA_DOMAIN JIRA_EMAIL JIRA_API_TOKEN

# Remove .env file
rm .env

# Start over with the setup wizard
jarkdown setup
```

## Next Steps

- Review the [Usage Guide](usage.md) for command options
- See [Architecture](architecture.md) to understand how configuration is used
- Check [Contributing](contributing.md) if you want to improve configuration handling
