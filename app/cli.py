import click
from flask.cli import with_appcontext
from app import db

@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
    click.echo("Database tables created.")
