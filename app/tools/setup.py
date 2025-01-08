"""
setup.py

@author: Emotu Balogun
@created: December 5, 2024

Initial application setup and configuration utilities.

This module contains setup functions that initialize the application for first-time use.
These utilities help establish the initial state of the application, including database
setup and core asset installation.

Key Features:
    - First-time application initialization
    - Core data asset installation
    - Database setup and configuration

Note:
    These functions should typically only be run once during initial setup or when
    resetting the application to its default state.

Usage:
    Run these utilities during application deployment or initial setup.
    These are typically executed via deployment scripts or CLI commands.

Example:
    >>> from app.scripts.setup import initialize_application
    >>> await initialize_application()

:module: app.scripts.setup
:requires: sqlmodel, sqlalchemy, app.models
"""

import json
import pathlib

from slugify import slugify

from app.models import drop_db, get_session, init_db
from app.models.assets import Industry, Scope
from app.llm.classifier import create_classifier_dependency

async def initialize_app():
    """
    Initialize the application with core data and configuration.

    This async function sets up the initial database and installs core reference data
    including industry classifications. It should be run during first-time setup of
    the application.

    Note:
        This operation will initialize a fresh database and install default data.
        Only run this during initial setup or when intentionally resetting to defaults.

    Example:
        >>> await initialize_app()  # Performs complete initial setup
    """
    await drop_db()
    await init_db()

    # Load data for industry categories
    industry_categories = json.loads(pathlib.Path("data/industries.json").read_text())
    scopes = json.loads(pathlib.Path("data/scopes.json").read_text())

    # Generate industry categories for Industry model
    async for session in get_session():
        # Industries
        industries = [
            Industry(id=slugify(name, separator="_", lowercase=True), name=name)
            for name in industry_categories
        ]
        session.add_all(industries)

        # NACE Scopes
        nace_scopes = [Scope.model_validate(scope) for scope in scopes]
        session.add_all(nace_scopes)

        await session.commit()
        
        # Classifier
        get_classifier = create_classifier_dependency(document_path="data/nace-structure.md")
        classifier = get_classifier()
        await classifier.initialize(session)
