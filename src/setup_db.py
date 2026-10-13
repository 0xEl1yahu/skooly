"""Import the inventoried books into the existing Skooly database."""

import psycopg

from data.books import seed_books
from data.data import books
from data.db import connect


def main():
    try:
        with connect() as conn:
            inserted = seed_books(conn, books)
    except (ValueError, psycopg.Error):
        print("Could not import books. Check SKOOLY_DATABASE_URL and PostgreSQL.")
        return 1

    print(f"Imported {inserted} new books. Catalogue contains {len(books)} titles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
