"""
Alembic migrations environment configuration.

This file configures Alembic to work with the AIRS database,
supporting both SQLite (local) and PostgreSQL (Cloud SQL).
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app configuration and models
from app.core.config import settings
from app.db.database import Base
from app.models import (
    Organization,
    Assessment,
    Answer,
    Score,
    Finding,
)

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the app's DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    useful for generating SQL scripts without a database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render as batch for SQLite ALTER TABLE support
        render_as_batch=url.startswith("sqlite"),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Detect SQLite for batch mode
        is_sqlite = connection.dialect.name == "sqlite"
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Render as batch for SQLite ALTER TABLE support
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
