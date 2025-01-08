"""
manage.py

@author: Emotu Balogun
@created: December 4, 2024

Management script for executing database and application maintenance tasks.

This module provides command-line utilities for managing the application,
including database operations, migrations, and test execution.

Key Features:
    - Application setup and initialization
    - Schema migrations
    - Test runner integration
    - Development server controls
    - Data seeding and fixtures

Usage:
    python manage.py <command> [options]

Available Commands:
    createdb     Create and initialize the database
    migrate      Run database migrations
    test         Execute test suite
    seed         Populate database with sample data
    runserver    Start development server

Example:
    >>> python manage.py createdb
    >>> python manage.py migrate
    >>> python manage.py test

:module: manage
:requires: app.models, app.config
"""

import asyncio

import typer
from rich import print

from app.config import settings
from app.llm.classifier import Classifier
from app.models import drop_db, init_db
from app.schemas.public import CompanyRequest
from app.tools.setup import initialize_app

manager = typer.Typer()


@manager.command()
def createdb():
    """
    Create and initialize the database.

    This command creates database tables based on SQLModel definitions
    in the application models.

    Example:
        >>> python manage.py createdb
    """
    print("Stubs for management commands to be run across the application a db")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())


@manager.command()
def dropdb():
    """
    Drop all database tables.

    This command removes all database tables and their data.
    Use with caution as this operation cannot be undone.

    Example:
        >>> python manage.py dropdb
    """
    print("Dropping the db")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(drop_db())


@manager.command()
def initialize():
    """
    Initialize the application with core data and assets.

    This command performs first-time setup by creating database tables and installing
    default reference data like industry categories.

    Example:
        >>> python manage.py initialize
    """
    print("Installing application assets...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize_app())


@manager.command()
def classify():
    classifier = Classifier("data/nace-v2-activities.md")
    company = CompanyRequest(
        name="Alec Engineering & Contracting LLC",
        description="""
        ALEC, part of the Investment Corporation of Dubai, 
        is a prominent construction company specializing in complex and iconic projects. T
        heir portfolio includes airports, retail, hotels, high-rise buildings, and themed developments, 
        with a focus on quality, safety, functionality and sustainability.""",
        industry="construction",
        location="United Arab Emirates",
    )

    result = classifier.classify(company)
    print(result)


if __name__ == "__main__":
    print("===" * 10)
    print(f"[green]{settings.API_NAME} | Version {settings.API_VERSION}[/green]")
    print("===" * 10)
    manager()
