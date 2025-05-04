# app/cli.py

import click
from flask.cli import with_appcontext
from datetime import datetime

from . import db
from .models import User, UserPreference, Podcast, GenerationTask

@click.group()
def cli():
    """CLI commands for database management and administration."""
    pass

@cli.command()
@with_appcontext
def create_admin():
    """Create an admin user."""
    email = click.prompt('Admin email')
    name = click.prompt('Admin name', default='Admin User')
    google_id = click.prompt('Google ID')
    
    admin = User(
        email=email,
        name=name,
        google_id=google_id,
        role='admin',
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'Created admin user: {email}')

@cli.command()
@with_appcontext
def cleanup_old_tasks():
    """Clean up old completed and failed tasks."""
    cutoff_days = click.prompt('Delete tasks older than (days)', type=int, default=7)
    cutoff_date = datetime.utcnow() - timedelta(days=cutoff_days)
    
    deleted = GenerationTask.query.filter(
        GenerationTask.completed_at < cutoff_date,
        GenerationTask.status.in_(['completed', 'failed', 'cancelled'])
    ).delete()
    
    db.session.commit()
    click.echo(f'Deleted {deleted} old tasks')

@cli.command()
@with_appcontext
def stats():
    """Show application statistics."""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_podcasts = Podcast.query.count()
    completed_podcasts = Podcast.query.filter_by(status='completed').count()
    
    click.echo('Application Statistics:')
    click.echo(f'Total Users: {total_users}')
    click.echo(f'Active Users: {active_users}')
    click.echo(f'Total Podcasts: {total_podcasts}')
    click.echo(f'Completed Podcasts: {completed_podcasts}')

def register_commands(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(cli)