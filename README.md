# Skooly

Skooly is a private Python terminal app for finding books in your learning collection and keeping notes. It uses your local PostgreSQL database. The 60 book titles come from `src/data/data.py`; importing them says nothing about your reading progress.

## Run it on this Mac

Open Terminal in the `skooly.ai` project directory. Run each command there:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export SKOOLY_DATABASE_URL='dbname=skooly'
.venv/bin/python src/setup_db.py
.venv/bin/python src/init.py
```

The first command creates a project-only Python environment in `.venv`; the second installs the PostgreSQL driver into it. `export` gives this terminal session the database name the app needs. The import command adds any missing catalogued books and leaves existing book IDs and notes alone. On this Mac, where all 60 books have been imported, it should say `Imported 0 new books`. The last command shows the four-choice menu. Enter `4` to exit.

If the app says it cannot use the database, check `pg_isready` (successful output includes `accepting connections`) and confirm you can run `psql -d skooly -c 'SELECT COUNT(*) FROM books;'`. Set `SKOOLY_DATABASE_URL` again in each new Terminal session.

## A fresh PostgreSQL database

The existing `skooly` database has already had migration `001` applied. **Do not rerun `src/data/schema.sql` or migration `001` on it.**

For a genuinely new, empty database on another machine, create it and apply the current schema once:

```bash
createdb skooly
psql -X -v ON_ERROR_STOP=1 -1 -d skooly -f src/data/schema.sql
export SKOOLY_DATABASE_URL='dbname=skooly'
.venv/bin/python src/setup_db.py
```

The schema command should report three `CREATE TABLE` lines. The first import should report `Imported 60 new books`; a second import should report `Imported 0 new books`.

## Use the menu

- **Search books:** Enter part of a title, then optionally choose a category and subcategory by number. Press Enter at either list to use any value. Results show book IDs you can use to open book notes.
- **Book notes:** Enter a book ID such as `SK-005`, then list, add, edit, or delete its notes. A note is one line of text. Deletion asks for confirmation.
- **Standalone notes:** List, add, edit, or delete notes that are not linked to a book.

Each note shows when it was created and last edited. Empty notes and unknown IDs are rejected. Notes remain in PostgreSQL after the CLI exits.

## Check the app

From the project directory, after setting `SKOOLY_DATABASE_URL`:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Successful output ends with `OK`. The database tests roll back their temporary book and note rows; the CLI search test reads the real catalogue.

## Back up your notes

Keep backups outside this Git project. For example, run:

```bash
mkdir -p ~/Documents/SkoolyBackups
pg_dump -Fc -d skooly -f ~/Documents/SkoolyBackups/skooly.dump
pg_restore --list ~/Documents/SkoolyBackups/skooly.dump
```

`pg_dump` saves the database to a local file. `pg_restore --list` checks that PostgreSQL can read the backup's contents; it does not restore data. Protect this file like your private notes.

To practise a full restore, create a **new temporary database with a name that does not already exist**. This does not affect the app's `skooly` database:

```bash
createdb skooly_restore_check
pg_restore --exit-on-error --no-owner -d skooly_restore_check ~/Documents/SkoolyBackups/skooly.dump
psql -d skooly_restore_check -c 'SELECT COUNT(*) FROM books;'
```

The count should be 60 for this catalogue. Once you have checked the restored data, you can remove only that temporary database with `dropdb skooly_restore_check`. Never run `pg_restore` against `skooly` as a backup test; that is the working database.

## Project files

`src/init.py` is the menu. `src/data/books.py` and `src/data/notes.py` contain the database queries. `src/data/schema.sql` describes a fresh database; `src/data/migrations/` records changes to an existing one.
