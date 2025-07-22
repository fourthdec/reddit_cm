import json
import sys
from datetime import datetime
from pathlib import Path

import click
import praw
import yaml


def load_config(config_file):
    """Load configuration from YAML or JSON file."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise click.ClickException(f"Config file not found: {config_file}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config = json.load(f)
            else:
                # Try to detect format by content
                content = f.read()
                f.seek(0)
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    f.seek(0)
                    config = yaml.safe_load(f)
        
        return config or {}
    except Exception as e:
        raise click.ClickException(f"Failed to parse config file: {e}")


def authenticate_reddit(client_id, client_secret, username, password, user_agent):
    """Authenticate with Reddit using provided credentials."""
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        # Test authentication
        reddit.user.me()
        return reddit
    except Exception as e:
        raise click.ClickException(f"Authentication failed: {e}")


def export_communities(reddit, format_type, output_file):
    """Export user's joined communities to specified format."""
    try:
        communities = []
        
        click.echo("Fetching joined communities...")
        for subreddit in reddit.user.subreddits(limit=None):
            community_data = {
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.public_description or '',
                'subscribers': subreddit.subscribers,
                'created_utc': datetime.fromtimestamp(subreddit.created_utc).isoformat(),
                'url': f"https://reddit.com/r/{subreddit.display_name}"
            }
            communities.append(community_data)
            
        click.echo(f"Found {len(communities)} communities")
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_communities': len(communities),
            'communities': communities
        }
        
        if format_type == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        elif format_type == 'yaml':
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
                
        click.echo(f"Communities exported to {output_file}")
        
    except Exception as e:
        raise click.ClickException(f"Export failed: {e}")


def load_communities_file(file_path):
    """Load communities from exported JSON or YAML file."""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise click.ClickException(f"Import file not found: {file_path}")
        
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            if file_path_obj.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:  # Assume JSON for other extensions
                data = json.load(f)
        
        if not isinstance(data, dict) or 'communities' not in data:
            raise click.ClickException("Invalid file format: missing 'communities' field")
        
        communities = data['communities']
        if not isinstance(communities, list):
            raise click.ClickException("Invalid file format: 'communities' must be a list")
        
        return communities
    
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Failed to parse JSON file: {e}")
    except yaml.YAMLError as e:
        raise click.ClickException(f"Failed to parse YAML file: {e}")
    except Exception as e:
        raise click.ClickException(f"Failed to load import file: {e}")


def import_communities(reddit, import_file, dry_run=False):
    """Import communities from exported file."""
    try:
        communities = load_communities_file(import_file)
        
        click.echo(f"Found {len(communities)} communities to import")
        if dry_run:
            click.echo("DRY RUN MODE - No communities will actually be joined")
        
        successful_joins = []
        failed_joins = []
        already_joined = []
        
        with click.progressbar(communities, label="Importing communities") as community_list:
            for community in community_list:
                community_name = community.get('name')
                if not community_name:
                    failed_joins.append({'name': 'Unknown', 'error': 'Missing community name'})
                    continue
                
                try:
                    subreddit = reddit.subreddit(community_name)
                    
                    # Check if already subscribed
                    if hasattr(subreddit, 'user_is_subscriber') and subreddit.user_is_subscriber:
                        already_joined.append(community_name)
                        continue
                    
                    if not dry_run:
                        subreddit.subscribe()
                    
                    successful_joins.append(community_name)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'private' in error_msg or 'forbidden' in error_msg:
                        failed_joins.append({'name': community_name, 'error': 'Private/Restricted community'})
                    elif 'not found' in error_msg or '404' in error_msg:
                        failed_joins.append({'name': community_name, 'error': 'Community not found'})
                    elif 'banned' in error_msg:
                        failed_joins.append({'name': community_name, 'error': 'Banned from community'})
                    else:
                        failed_joins.append({'name': community_name, 'error': f"Unknown error: {e}"})
        
        # Print summary
        click.echo("\n" + "="*50)
        click.echo("IMPORT SUMMARY")
        click.echo("="*50)
        
        if dry_run:
            click.echo(f"Would join: {len(successful_joins)} communities")
        else:
            click.echo(f"Successfully joined: {len(successful_joins)} communities")
        
        if already_joined:
            click.echo(f"\nAlready joined: {len(already_joined)} communities")
            for name in already_joined:
                click.echo(f"  - r/{name}")
        
        if failed_joins:
            click.echo(f"\nFailed to join: {len(failed_joins)} communities")
            for failure in failed_joins:
                click.echo(f"  - r/{failure['name']}: {failure['error']}")
        
        click.echo(f"\nTotal processed: {len(communities)} communities")
        
    except Exception as e:
        raise click.ClickException(f"Import failed: {e}")


def get_reddit_credentials(config_file, client_id, client_secret, username, password, user_agent):
    """Helper function to get Reddit credentials from config file or CLI args."""
    # Load config file if provided
    config = {}
    if config_file:
        config = load_config(config_file)
    
    # Use command line args or fall back to config file values (credentials only)
    client_id = client_id or config.get('client_id')
    client_secret = client_secret or config.get('client_secret')
    username = username or config.get('username')
    password = password or config.get('password')
    user_agent = user_agent or config.get('user_agent', 'reddit-cm:v0.1.0')
    
    # Validate required parameters
    missing_params = []
    if not client_id:
        missing_params.append('client-id')
    if not client_secret:
        missing_params.append('client-secret')
    if not username:
        missing_params.append('username')
    if not password:
        missing_params.append('password')
    
    if missing_params:
        raise click.ClickException(
            f"Missing required parameters: {', '.join(missing_params)}. "
            f"Provide them via command line or config file."
        )
    
    return client_id, client_secret, username, password, user_agent


@click.group()
def cli():
    """Reddit Community Manager - Export and import your joined Reddit communities."""
    pass


@cli.command()
@click.option('--config', 'config_file', type=click.Path(exists=True), 
              help='Configuration file (JSON or YAML)')
@click.option('--client-id', help='Reddit API client ID')
@click.option('--client-secret', help='Reddit API client secret')
@click.option('--username', help='Reddit username')
@click.option('--password', help='Reddit password')
@click.option('--user-agent', help='User agent string')
@click.option('--format', 'format_type', type=click.Choice(['json', 'yaml']), 
              help='Export format (json or yaml)')
@click.option('--output', 'output_file', type=click.Path(), 
              help='Output file path')
def export(config_file, client_id, client_secret, username, password, user_agent, format_type, output_file):
    """Export your joined Reddit communities to JSON or YAML format."""
    
    client_id, client_secret, username, password, user_agent = get_reddit_credentials(
        config_file, client_id, client_secret, username, password, user_agent
    )
    
    # Set defaults for export-specific options
    format_type = format_type or 'json'
    output_file = output_file or 'communities.json'
    
    # Adjust output file extension if needed
    if format_type == 'yaml' and output_file == 'communities.json':
        output_file = 'communities.yaml'
    
    click.echo(f"Authenticating with Reddit as {username}...")
    reddit = authenticate_reddit(client_id, client_secret, username, password, user_agent)
    
    click.echo(f"Exporting communities to {format_type.upper()} format...")
    export_communities(reddit, format_type, output_file)


@cli.command('import')
@click.argument('import_file', type=click.Path(exists=True))
@click.option('--config', 'config_file', type=click.Path(exists=True), 
              help='Configuration file (JSON or YAML)')
@click.option('--client-id', help='Reddit API client ID')
@click.option('--client-secret', help='Reddit API client secret')
@click.option('--username', help='Reddit username')
@click.option('--password', help='Reddit password')
@click.option('--user-agent', help='User agent string')
@click.option('--dry-run', is_flag=True, default=False,
              help='Preview what would be imported without actually joining communities')
def import_cmd(import_file, config_file, client_id, client_secret, username, password, user_agent, dry_run):
    """Import communities from exported file to join them with a different account.
    
    IMPORT_FILE: Path to exported JSON or YAML file containing communities to import.
    """
    
    client_id, client_secret, username, password, user_agent = get_reddit_credentials(
        config_file, client_id, client_secret, username, password, user_agent
    )
    
    click.echo(f"Authenticating with Reddit as {username}...")
    reddit = authenticate_reddit(client_id, client_secret, username, password, user_agent)
    
    import_communities(reddit, import_file, dry_run)


if __name__ == "__main__":
    cli()
