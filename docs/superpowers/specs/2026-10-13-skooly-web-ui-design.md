# Skooly web UI design

Date: 2026-10-13. Branch: `web-ui`.

## Goal

Give Skooly a basic browser interface for what the CLI already does: search books, and list, add, edit, and delete book notes and standalone notes. The owner writes the code with coaching, and learning is as much the point as the result. The owner is starting from zero with HTTP, APIs, tests, error handling, HTML, CSS, React, Next.js, and TypeScript, so each step introduces one main idea and ends with something visible.

## What the owner asked for

- A Next.js front end that reaches the existing Python code through an API layer.
- One page to start, built first as plain HTML and CSS, then converted to React.
- API built before the page. TypeScript for the Next.js stage.
- Coaching rather than finished code. Small steps scoped for them, with the reasoning explained.

## Assumptions

- Single user, on this Mac only. No login, hosting, analytics, or external services.
- Same features as the CLI. Skooly the owl, reading status, note search, and book editing stay future ideas.
- The CLI keeps working, unchanged, against the same database.

## Architecture

```
person at keyboard  ->  src/init.py  -+
                                      +->  src/data/ (notes.py, books.py)  ->  PostgreSQL
browser -> Next.js  ->  src/api.py   -+
```

- `src/data/` does the real work (SQL and the "blank note" rule). It does not change.
- `src/api.py` is new: a thin FastAPI layer that turns HTTP requests into calls to `data/` and replies with JSON. It sits beside `init.py` so it imports `data.notes` the same way.
- `web/` is new: the Next.js project.
- `mockup/` is new: the plain HTML and CSS page, kept as a reference after the React conversion. It lives outside `web/` because `create-next-app` needs an empty folder.

Running it means three servers, all on this Mac: PostgreSQL (port 5432, already running), the FastAPI server (port 8000, started with `uvicorn`), and the Next.js dev server (port 3000, started with `npm run dev`). FastAPI and Next.js listen only on `127.0.0.1`. The browser only talks to port 3000. Next.js forwards any `/api/...` request to port 8000 using a rewrite in `web/next.config.ts`, so the browser sees one address and no CORS setup is needed.

New Python dependencies: `fastapi`, `uvicorn` (runs the server), and `httpx` (needed by FastAPI's test client). They are added to `requirements.txt` with version ranges, like `psycopg`.

## API endpoints

Each endpoint calls one existing function.

| Method and path | Calls | Success reply |
|---|---|---|
| `GET /api/books?q=&category=&subcategory=` | `search_books` | `200`, list of books |
| `GET /api/books/{book_id}` | `get_book` | `200`, one book |
| `GET /api/categories` | `list_categories` | `200`, list of names |
| `GET /api/subcategories?category=` | `list_subcategories` | `200`, list of names |
| `GET /api/books/{book_id}/notes` | `list_book_notes` | `200`, list of notes |
| `POST /api/books/{book_id}/notes` | `add_book_note` | `201`, `{"note_id": 12}` |
| `PUT /api/books/{book_id}/notes/{note_id}` | `edit_book_note` | `200`, `{"note_id": 12}` |
| `DELETE /api/books/{book_id}/notes/{note_id}` | `delete_book_note` | `204`, no body |
| `GET /api/notes` | `list_standalone_notes` | `200`, list of notes |
| `POST /api/notes` | `add_standalone_note` | `201`, `{"note_id": 12}` |
| `PUT /api/notes/{note_id}` | `edit_standalone_note` | `200`, `{"note_id": 12}` |
| `DELETE /api/notes/{note_id}` | `delete_standalone_note` | `204`, no body |

`POST` and `PUT` take a JSON body of `{"note_text": "..."}`. A note is returned as:

```json
{"note_id": 12, "note_text": "Generators are lazy",
 "created_at": "2026-10-13T09:15:02+01:00", "updated_at": "2026-10-13T09:15:02+01:00"}
```

A book is `{"book_id": "SK-005", "title": "...", "category": "...", "subcategory": null}`. Book IDs in paths are uppercased, as the CLI does. After any change, the page fetches the note list again rather than patching its own copy; this mirrors the CLI, which re-lists notes on every loop.

## Database connections and saving

One shared helper in `api.py` opens a connection for each request (a FastAPI "dependency"). If the endpoint finishes without an error, the helper commits; if anything fails, it rolls back, so a half-finished change is never saved. Endpoints do not call `commit()` themselves. Tests replace this helper with one that always rolls back.

## Errors

The API replies with a status code and a `{"detail": "..."}` message. The page shows the message in a status line near the relevant form, announced to screen readers (`aria-live`).

| Situation | Code | Detail |
|---|---|---|
| Blank or whitespace-only note (the `ValueError` from `notes.py`) | `422` | `A note cannot be blank.` |
| Missing `note_text` in the request body | `422` | FastAPI's built-in message |
| Unknown book ID, on any `/api/books/{book_id}...` path | `404` | `No book has that ID.` |
| Unknown note ID, or a note that belongs to another book | `404` | `No note with that ID.` |
| `SKOOLY_DATABASE_URL` unset, or PostgreSQL unreachable | `503` | `Could not use the database. Check SKOOLY_DATABASE_URL and PostgreSQL.` |

For book notes, the API checks the book exists before adding a note, so an unknown book gives `404` rather than a database error. Deleting asks "Delete this note? Yes / No" inside the page, not in a browser pop-up.

## The page

One page with two columns on a wide window that stack into one on a narrow window.

- **Header:** "SKOOLY" in a pixel font, with an empty spot reserved for the owl.
- **Books column:** a title keyword box, category and subcategory dropdowns (each with "Any"), a Search button, a count ("3 books found"), and the result list. Choosing a book selects it, and the selection is visibly marked.
- **Notes column:** "Notes for: {title} ({book_id})" with that book's notes, then "My notes" with standalone notes. Each note shows its text, created and edited dates, and Edit and Delete buttons. Each section ends with a multi-line "Add a note" box and a Save button. With no book selected, the book section says to choose a book.

Style: a pixel font only for the title and section headings, a plain readable font for all other text, strong text contrast, visible focus outlines, and full keyboard use. Plain CSS, no Tailwind, so the stylesheet carries into Next.js.

Note text can now span several lines. The database already allows it. The CLI prints such notes across several lines, which is untidy but works.

## Testing

- **API:** `tests/test_api.py`, using `unittest` (like the existing tests) and FastAPI's `TestClient`, which sends pretend requests to `api.py` without starting a server. It covers every endpoint's success reply and every row of the error table. It runs with the existing test command, and it never changes real notes because of the rollback helper.
- **Existing tests:** all nine must still pass after each step.
- **Mockup:** checked by eye against a checklist: it reads well; every control is reachable with Tab and shows a visible outline; it stacks on a narrow window; text contrast meets WCAG AA (4.5:1 for body text).
- **Next.js:** a manual walkthrough of every action and error, with the CLI open to confirm both see the same notes. No automated front-end tests yet.

## Build order

Each step is one lesson: one main new idea, one visible result, one check. Commit after each step.

| # | Step | Main new idea | Visible result | Check |
|---|---|---|---|---|
| 1 | Install FastAPI; `GET /api/notes` | what a server, port, and endpoint are | your notes as JSON at `127.0.0.1:8000/api/notes`, and the `/docs` page | open both in the browser |
| 2 | First API test | what an automated test is and why | `OK` in the terminal | run the test command |
| 3 | Connection helper with commit and rollback; `POST /api/notes` | dependencies; request bodies | add a note through `/docs`, then see it in the CLI | test plus CLI |
| 4 | Errors for notes: `422`, `404`, `503` | `try` / `except` and status codes | friendly messages in `/docs` | tests for each error |
| 5 | `PUT` and `DELETE` for standalone notes | finishing a pattern on your own | edit and delete through `/docs` | tests |
| 6 | Book and book-note endpoints | reusing the pattern with path parameters | book search and book notes in `/docs` | tests |
| 7 | HTML structure with sample data | semantic HTML | a plain but complete page | open `mockup/index.html` |
| 8 | CSS | layout, type, focus, responsive design | the page looking like Skooly | mockup checklist |
| 9 | Next.js project in TypeScript; mockup pasted in as one page | what Next.js is; JSX; basic types | the same page at `localhost:3000` | open it |
| 10 | Split into components | components and props | identical page, with `NoteList` used twice | compare with the mockup |
| 11 | Load real data through the API | state, effects, and `fetch` | your real notes and books on the page | manual walkthrough |
| 12 | Add, edit, delete, and error messages | forms and events | full CRUD in the browser, matching the CLI | manual walkthrough plus CLI |

The implementation plan breaks each step into smaller coached tasks with hints.

## Out of scope

Skooly mascot behaviour, reading status, note search, book editing, login, deployment, automated front-end tests, and Tailwind. Any of these can be a later project.
