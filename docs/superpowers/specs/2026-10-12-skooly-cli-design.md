# Skooly CLI design

## Purpose

Build a private, single-user Python terminal app for finding books in the owner's existing collection and keeping timestamped learning notes. Building it should teach one concept at a time. The owner will write the initial code, with coaching when wanted.

## First release

Running `python src/init.py` from the project directory opens a numbered menu. It offers book search, book notes, standalone notes, and exit. Book search accepts any combination of a title keyword, category, and subcategory. Title matching ignores case and finds the keyword anywhere in the title. Category and subcategory are selected from the values present in the catalogue. Filled-in filters combine so a result must match all of them. Results display the stable `SK-...` book ID, title, category, and subcategory when present. An empty result says that no books matched.

Selecting a book by its ID shows its notes in creation order and allows adding, editing, or deleting one. A separate menu does the same for standalone notes. Each note contains text, a creation timestamp, and a last-edited timestamp. The first release accepts a single line of text per note. An edit changes the text and last-edited timestamp but preserves the creation timestamp. A delete shows the target note and asks for confirmation. Empty text, unknown IDs, and database connection failures get clear messages without losing existing data.

## Data and persistence

PostgreSQL is the store from the first release. `src/data/data.py` supplies the 60 inventoried book records. Setup inserts them using their existing IDs and can be run again without replacing notes or duplicating books. The app neither infers reading progress nor imports book contents or files.

Keep the owner's separate `books`, `book_notes`, and `standalone_notes` tables in `src/data/schema.sql`. All three tables are drafted, and the SQL syntax issue in `standalone_notes` has been corrected. Change each note table's current text `note_id` to a PostgreSQL-generated numeric identity key, so the owner does not have to invent IDs while adding notes. Keep the `book_notes.book_id` foreign key. Store `created_at` and `updated_at` as `TIMESTAMPTZ`; inserts use their defaults and edit queries explicitly set `updated_at` to the current time. Table names make numeric note IDs unambiguous in their respective menus.

The Python CLI connects directly to PostgreSQL through Psycopg, using parameterized queries for user text. A local database connection string is supplied through `SKOOLY_DATABASE_URL`; setup instructions explain how to set it in the terminal without committing a password. This CLI has no HTTP service. A web API can be a separate learning project if another client needs access later. The first release has no external data sharing or analytics.

## Code responsibilities

- `src/init.py`: menu, prompts, and user-facing messages.
- `src/data/data.py`: the existing book inventory; preserve its IDs and category names.
- `src/data/schema.sql`: the three PostgreSQL tables and constraints.
- A small database access module: connection, book search, note queries, and seed operations. Keep SQL apart from menu text so each can be read and changed independently.
- A setup guide: database creation, dependency installation, schema application, catalogue import, running the CLI, and backup and restore commands.

## Build sequence and checks

1. Change note IDs to database-generated numbers, configure the database connection, and display a working menu. Check that the schema applies and that the CLI gives a useful message when PostgreSQL is unavailable.
2. Load the catalogue once, then run setup again and check that there are still 60 books and no duplicate IDs.
3. Add combined book search. Check title keywords with mixed capitalization, category and subcategory selection, combined filters, and no matches.
4. Add book-note list, add, edit, and delete. Check that notes remain after restarting the CLI, `created_at` stays fixed on edit, `updated_at` changes, and a declined delete preserves the note.
5. Add the same actions for standalone notes. Check that the two note menus target the intended tables and unknown IDs change nothing.
6. Document and try a local PostgreSQL backup and restore before the database becomes the only copy of personal notes.

Each increment should be small enough for the owner to write and understand. Introduce lists and dictionaries through the real book records, then functions and SQL as the related features need them. Do not implement ahead of the owner unless asked.

## Outside the first release

Reading status, book editing, note search, multiline note editing, a graphical interface, Skooly mascot behavior, and an HTTP API are future possibilities, not first-release requirements.
