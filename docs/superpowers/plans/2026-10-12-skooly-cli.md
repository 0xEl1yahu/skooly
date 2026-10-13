# Skooly Python CLI Execution Plan

**Goal:** A private terminal app that searches the 60-book catalogue and manages timestamped book and standalone notes.

**Architecture:** `src/init.py` handles prompts and display. Small files under `src/data/` connect to PostgreSQL and run the book and note queries. The existing `skooly` database has the migrated three-table schema but no rows yet.

**Tech stack:** Python 3, PostgreSQL 17, Psycopg 3. Use `python3` from the `skooly.ai` directory; the current `python` command points into an unrelated project's environment.

**Design:** [Skooly CLI design](../specs/2026-10-12-skooly-cli-design.md).

**Working style:** The owner writes the initial code. The assistant gives a plain-language hint, reviews each increment, and supplies more code when asked. Do not rerun `schema.sql` or migration `001` against the existing database.

**Git boundary:** Git currently resolves to the parent `GitHub` directory. Do not stage with `git add .` or push from this checkout; isolate Skooly as its own repository before using project-wide Git commands.

## File map

- `src/init.py` — numbered menu, prompts, and messages.
- `src/data/data.py` — existing book records; preserve all 60 IDs and categories.
- `src/data/db.py` — one PostgreSQL connection function, reading `SKOOLY_DATABASE_URL`.
- `src/data/books.py` — catalogue import, search, and category choices.
- `src/data/notes.py` — book-note and standalone-note queries.
- `src/setup_db.py` — one-time, repeat-safe catalogue import.
- `requirements.txt` — Psycopg dependency.
- `.gitignore` — keep the project virtual environment out of Git.
- `README.md` — setup, run, and backup instructions.

## Review focus

- A title keyword with different capitalization still finds the same books.
- Category and subcategory filters narrow results together; a missing subcategory does not hide a book from category-only search.
- Repeating catalogue import does not duplicate books or change notes.
- Unknown IDs and blank note text change nothing.
- A book-note ID from a different book cannot be edited or deleted through the selected book.
- Editing preserves `created_at`, changes `updated_at`, and a declined delete preserves the note.

## Milestone 1 — Menu you can run

**Visible result:** `python3 src/init.py` shows Search books, Book notes, Standalone notes, and Exit. Entering `4` ends the program; other choices show a temporary “coming next” message; an invalid choice asks again.

**Files:** Modify `src/init.py` only.

- [ ] Replace the one-time print with a `while` loop that displays four numbered choices and reads `input()`.
- [ ] Use `if` / `elif` / `else` to handle `1` through `4`; use `break` for Exit. Keep the existing welcome message.
- [ ] Run `python3 src/init.py` from the project directory. Check choices `1`, `4`, and an invalid value. Success means the menu repeats until Exit and never crashes.

**New concept:** None required yet; this uses loops and branches the owner already knows.

## Milestone 2 — Connect to PostgreSQL

**Visible result:** A database action connects to `skooly`; a missing or unavailable connection gives a useful message instead of a traceback.

**Files:** Create `requirements.txt`, `.gitignore`, `src/data/db.py`, `README.md`; modify `src/init.py`.

- [ ] Create a project virtual environment with `python3 -m venv .venv`, add `.venv/` to `.gitignore`, put `psycopg[binary]` in `requirements.txt`, and install it into the environment. Explain that the environment keeps this project's package separate from other Python projects.
- [ ] Define `connect()` in `src/data/db.py`; it reads `SKOOLY_DATABASE_URL` and returns a Psycopg connection configured to return dictionary rows. For local use, `dbname=skooly` is sufficient when the local PostgreSQL user already connects with `psql -d skooly`.
- [ ] Connect only when a menu action needs data; catch connection errors at the menu boundary and print a short recovery message.
- [ ] Run `export SKOOLY_DATABASE_URL='dbname=skooly'` in the terminal. This makes the connection setting available to Python. Run the CLI with `.venv/bin/python src/init.py`; a database action should connect. Try with an invalid database name and check the friendly error.

**New concept:** A function groups reusable steps; `connect()` is the first example.

## Milestone 3 — Import the real catalogue

**Visible result:** The existing 60 book records appear in PostgreSQL, each once. Running import again reports zero new records and leaves existing rows alone.

**Files:** Create `src/data/books.py`, `src/setup_db.py`; use existing `src/data/data.py`.

- [ ] Define `seed_books(conn, books) -> int` in `src/data/books.py`. Insert `book_id`, `title`, `category`, and `subcategory` with query parameters and `ON CONFLICT (book_id) DO NOTHING`; return the number newly inserted.
- [ ] In `src/setup_db.py`, import `books` from `data.data`, connect, call `seed_books`, and print the inserted count. Do not copy book data into another file.
- [ ] Run `.venv/bin/python src/setup_db.py` twice. Expect 60 inserted first, 0 second. Confirm `psql -d skooly -c 'SELECT COUNT(*) FROM books;'` reports 60.

**New concept:** A list holds the catalogue; each dictionary holds named facts for one book. SQL sends those facts to the matching table columns.

## Milestone 4 — Search books

**Visible result:** Search by part of a title, by category, by subcategory, or by their combination. Show book ID, title, category, and subcategory; say when there are no matches.

**Files:** Modify `src/data/books.py`, `src/init.py`.

- [ ] Define `list_categories(conn) -> list[str]` and `list_subcategories(conn, category: str | None) -> list[str]` from distinct stored values. If category is omitted, list all subcategories. Present numbered choices so category names are not retyped.
- [ ] Define `search_books(conn, keyword: str, category: str | None, subcategory: str | None) -> list[dict]`. Trim keyword whitespace; compare title text without regard to case, treat `%` and `_` as ordinary keyword characters, and combine supplied filters with AND. Category and subcategory match their selected values exactly.
- [ ] Connect menu choice `1` to the prompts and results. Check keyword `pYtHoN`, category `02 Code Craft`, subcategory `Python`, their combination, an empty keyword, and a nonsense keyword. Check that `04 Machine Learning` appears in category-only search even though its books have no subcategory.

**New concept:** A query selects rows; a result list lets the menu print each matching book with a `for` loop.

## Milestone 5 — Book notes

**Visible result:** Choose a book by ID, list its notes, add a one-line note, edit it, or delete it after confirmation.

**Files:** Create `src/data/notes.py`; modify `src/data/books.py`, `src/init.py`.

- [ ] Define `get_book(conn, book_id: str) -> dict | None` in `src/data/books.py`, plus `list_book_notes(conn, book_id: str) -> list[dict]` and `add_book_note(conn, book_id: str, text: str) -> int` in `src/data/notes.py`. Reject text that is blank after trimming and show an unknown-book message if the ID is absent. Let PostgreSQL generate the note ID and timestamps; list notes by creation time and ID.
- [ ] Define `edit_book_note(conn, book_id: str, note_id: int, text: str) -> bool` and `delete_book_note(conn, book_id: str, note_id: int) -> bool`. Match both IDs so a note from another book is untouched. Set `updated_at = CURRENT_TIMESTAMP` on edit; never change `created_at`. Return false for an unknown note ID.
- [ ] In the menu, display the note before delete and require explicit confirmation. Show local-readable timestamps alongside note IDs.
- [ ] Add a note, exit, restart, and confirm it remains. Edit it and check that only `updated_at` changed. Decline a deletion and confirm it remains; then confirm a deletion and check it disappears. Check blank text, unknown IDs, nonnumeric IDs, and a note ID belonging to a different book.

**New concept:** A foreign key links a note's `book_id` to an existing book, so a note belongs to the selected title.

## Milestone 6 — Standalone notes

**Visible result:** The standalone-note menu lists, adds, edits, and deletes notes without selecting a book.

**Files:** Modify `src/data/notes.py`, `src/init.py`.

- [ ] Define `list_standalone_notes(conn) -> list[dict]`, `add_standalone_note(conn, text: str) -> int`, `edit_standalone_note(conn, note_id: int, text: str) -> bool`, and `delete_standalone_note(conn, note_id: int) -> bool`. List notes by creation time and ID.
- [ ] Reuse the same blank-text, timestamp, unknown-ID, and delete-confirmation behavior as book notes. Keep SQL aimed at `standalone_notes` so equal numeric IDs in the two note tables cannot cross-edit each other.
- [ ] Add, restart, edit, decline delete, and then delete a standalone note. Confirm book notes are unchanged.

**New concept:** The two note tables have similar columns but different purposes; menu context chooses the correct table.

## Milestone 7 — Preserve and document the data

**Visible result:** The README tells the owner how to start the CLI and create and restore a local PostgreSQL backup.

**Files:** Complete `README.md`.

- [ ] Document where to run each command, what it does, and expected output. Include the existing migration as history, not as a command to rerun.
- [ ] Document `pg_dump` to a local file outside the repository and a restore procedure into a separate recovery database; do not overwrite `skooly` while testing recovery.
- [ ] Run the full menu journey: search, book note, standalone note, restart, and backup/recovery check. Record what actually passed and any remaining limitation.

**Finish condition:** The owner can find a real book and manage both kinds of notes across CLI restarts, with database data backed up and no unrelated Git project affected.
