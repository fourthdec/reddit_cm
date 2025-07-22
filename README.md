# Reddit Community Manager

A CLI tool to export and import your joined Reddit communities. Perfect for migrating between Reddit accounts or backing up your community subscriptions.

## Installation

Install the dependencies:

```bash
pip install -e .
```

## Reddit API Setup

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill out the form:
   - **name**: Give your app a name (e.g., "reddit-cm-tool")
   - **App type**: Select "script"
   - **description**: Optional description
   - **about url**: Leave blank or enter any URL (e.g., https://github.com/yourusername/reddit-cm)
   - **redirect uri**: Enter `http://localhost:8080` (required for script apps, even though we don't use it)
4. Click "Create app"
5. Note down your credentials:
   - `client_id`: The string under your app name (looks random, e.g., "abc123def456")
   - `client_secret`: The "secret" field (longer string)

## Usage

### Using Configuration File

Create a configuration file with your Reddit credentials (credentials only):

**config.yaml:**
```yaml
client_id: "your_client_id"
client_secret: "your_client_secret"
username: "your_username"
password: "your_password"
user_agent: "my-reddit-tool:v1.0"  # optional
```

**config.json:**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "username": "your_username", 
  "password": "your_password",
  "user_agent": "my-reddit-tool:v1.0"
}
```

**Note:** Config files are for credentials only. Output file and format are specified as CLI parameters.

## Commands

The tool has two main commands: `export` and `import`.

### Export Communities

Export your current Reddit account's joined communities:

```bash
reddit-cm export --config config.yaml
```

### Import Communities  

Import communities from an exported file to join them with a different account:

```bash
reddit-cm import my_communities.yaml --config new_account_config.yaml
```

## Export Usage

### Using Configuration File

```bash
reddit-cm export --config config.yaml
```

### Command Line Only

Export communities to JSON (default):

```bash
reddit-cm export --client-id YOUR_ID --client-secret YOUR_SECRET --username YOUR_USER --password YOUR_PASS
```

Export communities to YAML:

```bash
reddit-cm export --client-id YOUR_ID --client-secret YOUR_SECRET --username YOUR_USER --password YOUR_PASS --format yaml
```

### Export Options

- `--config`: Configuration file path (JSON or YAML)
- `--client-id`: Reddit API client ID
- `--client-secret`: Reddit API client secret  
- `--username`: Your Reddit username
- `--password`: Your Reddit password
- `--user-agent`: User agent string (optional, defaults to "reddit-cm:v0.1.0")
- `--format`: Export format - "json" or "yaml" (optional, defaults to "json")
- `--output`: Output file path (optional, defaults to "communities.json" or "communities.yaml")

## Import Usage

### Basic Import

Import all communities from an exported file:

```bash
reddit-cm import communities.yaml --config new_account_config.yaml
```

### Dry Run Mode

Preview what would be imported without actually joining communities:

```bash
reddit-cm import communities.yaml --config new_account_config.yaml --dry-run
```

### Command Line Credentials

```bash
reddit-cm import communities.json --client-id YOUR_ID --client-secret YOUR_SECRET --username NEW_USER --password NEW_PASS
```

### Import Options

- `--config`: Configuration file path (JSON or YAML) 
- `--client-id`: Reddit API client ID
- `--client-secret`: Reddit API client secret
- `--username`: Your Reddit username (for the target account)
- `--password`: Your Reddit password (for the target account)
- `--user-agent`: User agent string (optional)
- `--dry-run`: Preview mode - shows what would be imported without actually joining

### Import Results

The import process will show:
- ✅ **Successfully joined**: Communities that were joined successfully
- ⚠️  **Already joined**: Communities you're already subscribed to
- ❌ **Failed to join**: Communities that couldn't be joined (private, banned, not found)

### Migration Workflow

1. **Export from old account:**
   ```bash
   reddit-cm export --config old_account.yaml --format yaml --output my_communities.yaml
   ```

2. **Preview import to new account (recommended):**
   ```bash
   reddit-cm import my_communities.yaml --config new_account.yaml --dry-run
   ```

3. **Actually import to new account:**
   ```bash
   reddit-cm import my_communities.yaml --config new_account.yaml
   ```

**Full status is always shown:** No prompts - you'll always see successful joins, already joined communities, and failed joins with reasons.

**Note:** Command line options take precedence over config file values. You can mix both approaches.

## Output Format

The exported file contains:

- `exported_at`: Timestamp of export
- `total_communities`: Number of communities found
- `communities`: Array of community objects with:
  - `name`: Community name (without r/ prefix)
  - `title`: Full community title
  - `description`: Community description
  - `subscribers`: Number of subscribers
  - `created_utc`: Community creation date (ISO format)
  - `url`: Full Reddit URL

### Example JSON Output

```json
{
  "exported_at": "2024-01-15T10:30:00.123456",
  "total_communities": 2,
  "communities": [
    {
      "name": "python",
      "title": "Python",
      "description": "News about the Python programming language",
      "subscribers": 1000000,
      "created_utc": "2008-01-25T05:06:22",
      "url": "https://reddit.com/r/python"
    }
  ]
}
```

## Security Notes

- Never commit your Reddit credentials to version control
- Consider using environment variables for credentials
- The tool requires your Reddit password - use at your own discretion
- Consider creating a dedicated Reddit account for API access

## Development

### Setup

Install development dependencies:

```bash
pip install -r dev-requirements.txt
```

Or with uv:

```bash
uv pip install -r dev-requirements.txt
```

### Running Tests

Run the full test suite:

```bash
pytest
```

Run tests with coverage:

```bash
coverage run -m pytest
coverage report
coverage html  # Generate HTML coverage report
```

Run specific test files:

```bash
pytest tests/test_config.py
pytest tests/test_cli.py
pytest tests/test_reddit_api.py
```

### Code Quality

Format code with Black:

```bash
black main.py tests/
```

Check code style with flake8:

```bash
flake8 main.py tests/
```

### Running the Application

Run directly with Python:

```bash
python main.py --help
```

### Test Structure

- `tests/test_config.py` - Tests for configuration file loading
- `tests/test_cli.py` - Tests for CLI argument parsing and command execution
- `tests/test_reddit_api.py` - Tests for Reddit API integration (with mocks)