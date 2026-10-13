"""Connect the CLI to its local PostgreSQL database."""

import os

import psycopg
from psycopg.rows import dict_row


def connect():
    database_url = os.environ.get("SKOOLY_DATABASE_URL")
    if not database_url:
        raise ValueError("Set SKOOLY_DATABASE_URL before running Skooly.")

    return psycopg.connect(database_url, row_factory=dict_row)
