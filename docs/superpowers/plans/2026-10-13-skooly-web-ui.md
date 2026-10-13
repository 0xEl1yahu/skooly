# Skooly Web UI Implementation Plan

> **For agents:** Do not implement these tasks. The owner writes the code. Follow the "Boilerplate, never the solution" rule in `AGENTS.md`: when asked, put a task's **Boilerplate** in place exactly as written, answer questions like Stack Overflow, explain errors, and review the owner's code. Write solution code only when the owner explicitly asks for that specific piece.

**Goal:** A one-page browser interface for Skooly's book search and notes, backed by a FastAPI layer over the existing `src/data/` code.

**Architecture:** `src/api.py` is a thin FastAPI app that calls the existing `data/` functions and replies with JSON. The page is first built as plain HTML and CSS in `mockup/`, then rebuilt as a TypeScript Next.js app in `web/` whose dev server forwards `/api/...` requests to FastAPI.

**Tech stack:** Python 3.14, FastAPI, Uvicorn, httpx (for tests), psycopg 3, PostgreSQL, `unittest`; HTML, CSS; Next.js 16.4 (App Router), React 19, TypeScript, npm.

**Spec:** `docs/superpowers/specs/2026-10-13-skooly-web-ui-design.md`

## How this plan is scoped

This is how the work was divided, so you can learn to scope by example:

1. **Split by layer.** API first (tasks 1 to 6), then the page as HTML/CSS (7 and 8), then Next.js (9 to 12). Each layer can be checked before the next one exists.
2. **One new idea per task.** If a task needed two big new ideas, it was split into two tasks.
3. **Every task ends with something you can see** and a command or checklist that proves it works.
4. **Patterns repeat on purpose.** Task 3 teaches the pattern for one endpoint. Task 5 has you repeat it with less help. Task 6 has you repeat it with almost none.

## How each task works

Each task has the same parts:

- **You'll see:** the visible result when the task is done.
- **New idea:** the main concept, with links to the official docs.
- **Boilerplate:** the scaffolding to copy in (or ask Claude to put in place). `TODO` comments mark your part.
- **Your part:** what to write.
- **Hints:** start here if you get stuck. Ask Claude for a smaller hint before asking for code.
- **Try to break it:** experiments that teach you how it fails.
- **Check:** how you know it works.
- **Commit:** save the step in Git.

Every task's commit runs from the `skooly.ai` folder:

```bash
git rev-parse --show-toplevel   # must end in skooly.ai
git add <the files listed in the task>
git commit -m "<message from the task>"
git push
```

## Global constraints

- Python packages: `fastapi>=0.143,<1`, `uvicorn>=0.54,<1`, `httpx>=0.28,<1`, added to `requirements.txt`.
- Next.js `16.4.0` with TypeScript, App Router, ESLint, plain CSS (no Tailwind), npm.
- The API listens on `127.0.0.1:8000` and Next.js on `127.0.0.1:3000`. Nothing listens on your Wi-Fi network.
- `src/data/` and `src/init.py` do not change. The CLI keeps working.
- Error `detail` messages are exactly: `A note cannot be blank.`, `No book has that ID.`, `No note with that ID.`, `Could not use the database. Check SKOOLY_DATABASE_URL and PostgreSQL.`
- The 9 existing tests must still pass after every task.
- API tests never change real notes (they roll back).
- No external services or analytics. `docs/book-catalogue.md` stays out of Git.

## Review focus

The five situations most likely to bite that the spec does not spell out, and the task that pins each down:

1. **A note that is only spaces** must be rejected with `422`, not saved. Test in Task 4.
2. **Editing or deleting a note through the wrong book's address** (for example, book A's note via `/api/books/B/notes/...`) must give `404` and leave the note untouched. Test in Task 6.
3. **A lowercase book ID** (`/api/books/sk-005`) must work the same as `SK-005`, as it does in the CLI. Test in Task 6.
4. **The API server not running** while the page is open must show a clear message on the page, not a blank page or a frozen button. Manual check in Task 12.
5. **A note with several lines** must keep its line breaks through the API and display them on the page. Test in Task 6, visual check in Tasks 8 and 12.

## Starting the servers (from Task 1 onward)

Open Terminal in the `skooly.ai` folder. In each new tab, set the database first:

```bash
export SKOOLY_DATABASE_URL='dbname=skooly'
```

**Tab 1, the API** (from Task 1):

```bash
.venv/bin/uvicorn api:app --app-dir src --reload
```

`--app-dir src` lets Python find `api.py` and `data/` inside `src`. `--reload` restarts the server whenever you save a Python file. Success looks like `Uvicorn running on http://127.0.0.1:8000`. Press `Ctrl+C` to stop it.

**Tab 2, the web page** (from Task 9):

```bash
cd web
npm run dev
```

Success looks like `Local: http://127.0.0.1:3000`.

**Run the tests:**

```bash
.venv/bin/python -m unittest discover -s tests -v                       # everything
.venv/bin/python -m unittest discover -s tests -p "test_api.py" -v      # just the API tests
```

---

## Part 1: the API

### Task 1: Install FastAPI and list notes over HTTP

**Files:**
- Modify: `requirements.txt`
- Create: `src/api.py`

**Interfaces:**
- Consumes: `connect()` from `data/db.py`; `list_standalone_notes(conn)` from `data/notes.py`
- Produces: `app` (the FastAPI object) and `GET /api/notes`

**You'll see:** your standalone notes as JSON at `http://127.0.0.1:8000/api/notes`, and an interactive page listing your endpoints at `http://127.0.0.1:8000/docs`.

**New idea: servers, ports, endpoints.** A server is a program that waits on a port for HTTP requests and replies. An endpoint is one method plus path it answers, like `GET /api/notes`. The line `@app.get("/api/notes")` above a function is a *decorator*. Read it as "when a GET request arrives at /api/notes, run the function below and send back what it returns." FastAPI turns returned lists and dictionaries into JSON.

Generic example (not Skooly):

```python
@app.get("/api/cats")
def list_cats():
    return [{"name": "Miso"}, {"name": "Tofu"}]
```

Docs: [FastAPI first steps](https://fastapi.tiangolo.com/tutorial/first-steps/).

**Boilerplate:**

- [ ] **Step 1: Add the new packages to `requirements.txt`** (below the existing `psycopg` line):

```text
fastapi>=0.143,<1
uvicorn>=0.54,<1
httpx>=0.28,<1
```

- [ ] **Step 2: Install them.** From the `skooly.ai` folder:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Success ends with `Successfully installed ... fastapi-... uvicorn-... httpx-...`.

- [ ] **Step 3: Create `src/api.py`:**

```python
"""Answer HTTP requests from the web page by calling data/."""

from fastapi import FastAPI

from data.db import connect
from data.notes import list_standalone_notes

app = FastAPI(title="Skooly API")


@app.get("/api/notes")
def list_notes():
    # TODO: open a database connection the way init.py does (look at main()),
    # get the standalone notes with list_standalone_notes(conn), and return them.
    pass
```

**Your part:**

- [ ] **Step 4:** Replace the `TODO` and `pass` with the body of `list_notes`.

**Hints:**
- `init.py` already opens a connection with a `with ... as conn:` block. The same shape works here.
- You do not need to convert anything to JSON yourself.

**Try to break it:**
- Return the notes *without* the `with` block's connection being open. What error do you get?
- Start the server in a tab where you forgot `export SKOOLY_DATABASE_URL=...`. What does the browser show? (You will fix this properly in Task 4.)

**Check:**
- [ ] **Step 5:** Start the API (see "Starting the servers"), open `http://127.0.0.1:8000/api/notes`. You see a list in square brackets, `[]` if you have no standalone notes. Add a note with the CLI and refresh: it appears.
- [ ] **Step 6:** Open `http://127.0.0.1:8000/docs`, expand `GET /api/notes`, click **Try it out**, then **Execute**. You see the same JSON and `200` as the response code.
- [ ] **Step 7:** Run all tests. The 9 existing tests still pass.

- [ ] **Step 8: Commit** `requirements.txt` and `src/api.py` with message `feat: list standalone notes over HTTP`.

---

### Task 2: Your first API test

**Files:**
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: `app` from `src/api.py`
- Produces: `tests/test_api.py` with `NoteApiTests`, which later tasks extend

**You'll see:** `OK` in the terminal, and then a deliberate `FAIL` that you learn to read.

**New idea: automated tests.** A test is a small piece of code that runs your code and checks the result, so you don't have to click through `/docs` after every change. In `unittest`:
- a test lives in a class that inherits from `unittest.TestCase`;
- every method whose name starts with `test_` is one test;
- checks such as `self.assertEqual(actual, expected)` fail the test when they're wrong.

FastAPI's `TestClient` sends pretend requests to `app` without starting a server.

Generic example (not Skooly):

```python
def test_cats_list_works(self):
    response = self.client.get("/api/cats")
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()[0]["name"], "Miso")
```

Docs: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Python unittest](https://docs.python.org/3/library/unittest.html).

**Boilerplate:**

- [ ] **Step 1: Create `tests/test_api.py`:**

```python
"""Check the HTTP API in src/api.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from api import app


class NoteApiTests(unittest.TestCase):
    def setUp(self):
        # setUp runs before every test method in this class.
        self.client = TestClient(app)

    def test_listing_notes_returns_a_list(self):
        response = self.client.get("/api/notes")
        # TODO: check the status code is 200.
        # TODO: check response.json() is a list (hint: isinstance).
```

The `sys.path.insert` line lets the test find `api.py` inside `src/`, exactly as `tests/test_data.py` does.

**Your part:**

- [ ] **Step 2:** Replace the two `TODO`s with checks.

**Try to break it:**
- [ ] **Step 3:** Change your expected status code from `200` to `201` and run the API tests. Read the `FAIL` output: it names the test, the line, and `AssertionError: 200 != 201`. That is what a failing test looks like. Change it back.

**Check:**
- [ ] **Step 4:** Run the API tests: `Ran 1 test ... OK`. Run all tests: `Ran 10 tests ... OK`.

- [ ] **Step 5: Commit** `tests/test_api.py` with message `test: check the notes list endpoint`.

---

### Task 3: A shared connection helper, and adding notes

**Files:**
- Modify: `src/api.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: `add_standalone_note(conn, text)` returns the new `note_id`
- Produces: `NoteIn` (request body with `note_text: str`), `get_conn()` (the connection dependency), `POST /api/notes` returning `201` and `{"note_id": <int>}`. Every later endpoint takes `conn=Depends(get_conn)`.

**You'll see:** a note you add through `/docs` showing up in the CLI menu.

**New idea: dependencies and request bodies.**
- A *dependency* is a helper FastAPI runs before your endpoint, handing its result in as a parameter. You write `get_conn` once, and every endpoint that says `conn=Depends(get_conn)` gets a fresh connection. A dependency that uses `yield` can also run code *after* the endpoint finishes, which is the right moment to commit or roll back.
- A *request body* is the JSON the page sends with a POST, such as `{"note_text": "..."}`. `NoteIn` describes its shape, and FastAPI rejects requests that don't match.

Generic example of a `yield` dependency (not Skooly):

```python
def get_cat_basket():
    basket = open_basket()
    yield basket          # the endpoint runs here
    basket.close()        # this runs after the endpoint finishes
```

Docs: [Request body](https://fastapi.tiangolo.com/tutorial/body/), [Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), [psycopg connection context](https://www.psycopg.org/psycopg3/docs/basic/usage.html#connection-context).

**Boilerplate:**

- [ ] **Step 1: Replace the test class setup in `tests/test_api.py`** so tests never change your real notes. Change the imports and the start of the file to:

```python
"""Check the HTTP API in src/api.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from api import app, get_conn
from data.db import connect


class ApiTestCase(unittest.TestCase):
    """Gives each test a client whose database changes are rolled back."""

    def setUp(self):
        self.conn = connect()

        def use_test_conn():
            yield self.conn

        # Swap the real get_conn (which commits) for one that never commits.
        app.dependency_overrides[get_conn] = use_test_conn
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.conn.rollback()
        self.conn.close()


class NoteApiTests(ApiTestCase):
    # Keep your test_listing_notes_returns_a_list method here, but delete
    # its old setUp: ApiTestCase now provides self.client.
    ...
```

- [ ] **Step 2: Add a failing test first** to `NoteApiTests`. Writing the test before the code is called *test-driven development*: you watch the test fail for the right reason, then make it pass.

```python
    def test_adding_a_note_returns_201_and_it_appears_in_the_list(self):
        response = self.client.post("/api/notes", json={"note_text": "Test note from the API"})
        # TODO: check the status code is 201.
        # TODO: check the reply has a "note_id".
        # TODO: GET /api/notes and check "Test note from the API" is one of the note texts.
```

- [ ] **Step 3: Run the API tests and watch them fail.** You'll see an `ImportError` about `get_conn`, because it doesn't exist yet. That's the right failure.

- [ ] **Step 4: Add this to `src/api.py`** (merge the imports with the ones already there):

```python
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from data.notes import add_standalone_note, list_standalone_notes


class NoteIn(BaseModel):
    """The JSON body the page sends to add or edit a note."""

    note_text: str


def get_conn():
    # TODO: open a connection, hand it to the endpoint with `yield conn`,
    # commit if the endpoint finished normally, roll back if it raised an error.
    pass


@app.post("/api/notes", status_code=201)
def create_note(note: NoteIn, conn=Depends(get_conn)):
    # TODO: add the note and return {"note_id": <the new id>}.
    # Do not call conn.commit() here: get_conn is responsible for that.
    pass
```

**Your part:**

- [ ] **Step 5:** Write the body of `get_conn`.
- [ ] **Step 6:** Write the body of `create_note`.
- [ ] **Step 7:** Change `list_notes` from Task 1 to take `conn=Depends(get_conn)` instead of opening its own connection.
- [ ] **Step 8:** Fill in the test's `TODO`s.

**Hints:**
- `get_conn` can be three lines. Read the psycopg "connection context" link: a `with` block around a connection already commits or rolls back when it ends.
- Inside `create_note`, the text is at `note.note_text`.
- For the last test check, build a list of the `note_text` values, or loop and compare.

**Try to break it:**
- Send `{"text": "hi"}` instead of `{"note_text": "hi"}` in `/docs`. What status code and message come back, and who wrote that message?
- Temporarily remove the dependency override lines from `setUp`, run the test, then look at your notes in the CLI. Did the test note stay? (Delete it with the CLI and put the lines back.) This is why the override exists.

**Check:**
- [ ] **Step 9:** Run all tests: `OK`.
- [ ] **Step 10:** Count standalone notes before and after a test run. The numbers must match:

```bash
psql -d skooly -c 'SELECT COUNT(*) FROM standalone_notes;'
```

- [ ] **Step 11:** In `/docs`, run `POST /api/notes` with a real note. You get `201` and a `note_id`. Open the CLI, choose standalone notes: it's there.

- [ ] **Step 12: Commit** `src/api.py` and `tests/test_api.py` with message `feat: add standalone notes over HTTP`.

---

### Task 4: Friendly errors: 422 and 503

**Files:**
- Modify: `src/api.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: the `ValueError("A note cannot be blank.")` raised by `add_standalone_note`; the `ValueError` raised by `connect()` when `SKOOLY_DATABASE_URL` is unset; `psycopg.OperationalError` when PostgreSQL is unreachable
- Produces: blank notes give `422` with `detail` `A note cannot be blank.`; database problems give `503` with `detail` `Could not use the database. Check SKOOLY_DATABASE_URL and PostgreSQL.` from every endpoint

**You'll see:** in `/docs`, a blank note gives a clear `422` message instead of `500 Internal Server Error`.

**New idea: exceptions and status codes.** When Python hits a problem it *raises* an exception, which travels up through the functions that called it until something *catches* it with `try` / `except`. If nothing catches it, FastAPI replies `500 Internal Server Error`. You catch the exceptions you expect, and *raise* `HTTPException(status_code, detail)` so the page gets a meaningful code and message. Status codes come in groups: `2xx` worked, `4xx` the request was wrong, `5xx` the server had a problem.

Generic example (not Skooly):

```python
from fastapi import HTTPException

@app.get("/api/cats/{name}")
def read_cat(name: str):
    try:
        return find_cat(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="No cat has that name.")
```

Docs: [Python errors and exceptions](https://docs.python.org/3/tutorial/errors.html), [FastAPI handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [HTTP status codes (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).

**Boilerplate:**

- [ ] **Step 1: Add these imports to `tests/test_api.py`** (with the others at the top):

```python
import os
from unittest.mock import patch
```

- [ ] **Step 2: Add failing tests.** In `NoteApiTests`:

```python
    def test_blank_note_is_rejected_with_422(self):
        response = self.client.post("/api/notes", json={"note_text": "   "})
        # TODO: check the status code is 422 and response.json()["detail"] is the spec's message.

    def test_missing_note_text_is_rejected_with_422(self):
        response = self.client.post("/api/notes", json={})
        # TODO: check the status code is 422.
```

And a new class at the bottom of the file. It does **not** inherit from `ApiTestCase`, because it must use the real `get_conn`:

```python
class DatabaseUnavailableTests(unittest.TestCase):
    def test_database_unavailable_gives_503(self):
        # Pretend SKOOLY_DATABASE_URL is empty, only inside this with block.
        with patch.dict(os.environ, {"SKOOLY_DATABASE_URL": ""}):
            response = TestClient(app).get("/api/notes")
        # TODO: check the status code is 503 and the detail is the spec's message.
```

- [ ] **Step 3: Run the API tests** and watch the new ones fail. Note which ones fail and with what status code.

- [ ] **Step 4: Add these imports to `src/api.py`:**

```python
import psycopg
from fastapi import Depends, FastAPI, HTTPException
```

**Your part:**

- [ ] **Step 5:** Make `create_note` turn the blank-note `ValueError` into a `422`.
- [ ] **Step 6:** Make `get_conn` turn a failed connection into a `503`.
- [ ] **Step 7:** Fill in the test `TODO`s.

**Hints:**
- Read the failing output from Step 3 first. Which tests already pass without any code? Why? (Look at what `NoteIn` does.)
- Use `str(error)` to reuse the message from `notes.py` instead of typing it again.
- In `get_conn`, put the `try` around the **connecting part only**, not around the `yield`. If the `try` also covered the `yield`, a blank-note `ValueError` from the endpoint would be caught there and wrongly reported as `503`.
- `except (ValueError, psycopg.OperationalError):` catches either one.

**Try to break it:**
- Wrap the whole of `get_conn`, including the `yield`, in your `try`. Run the tests. Which test fails and why? Put it back.
- Stop PostgreSQL (`brew services list` shows its name, then `brew services stop <name>`), call `/api/notes` in the browser, then `brew services start <name>`. You should see your `503` message.

**Check:**
- [ ] **Step 8:** Run all tests: `OK`.
- [ ] **Step 9:** In `/docs`, post `{"note_text": "   "}`. The reply is `422` with `"detail": "A note cannot be blank."`.

- [ ] **Step 10: Commit** `src/api.py` and `tests/test_api.py` with message `feat: report blank notes and database problems clearly`.

---

### Task 5: Edit and delete standalone notes

**Files:**
- Modify: `src/api.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: `edit_standalone_note(conn, note_id, text)` and `delete_standalone_note(conn, note_id)`, which return `True` if a note changed and `False` if no note had that ID
- Produces: `PUT /api/notes/{note_id}` returning `200` and `{"note_id": <int>}`; `DELETE /api/notes/{note_id}` returning `204` with no body; both return `404` with `No note with that ID.` for unknown IDs

**You'll see:** edit and delete working in `/docs`, and the CLI showing the changes.

**New idea: finishing a pattern on your own.** This task repeats Tasks 3 and 4 with one new piece: a *path parameter*. `{note_id}` in the path becomes a function argument. `note_id: int` tells FastAPI to convert it to a number and reject anything that isn't one.

Docs: [Path parameters](https://fastapi.tiangolo.com/tutorial/path-params/).

**Boilerplate:**

- [ ] **Step 1: Add test names to `NoteApiTests`** (you write each body; Task 3's test shows the shape):

```python
    def test_editing_a_note_changes_its_text(self):
        # TODO: add a note, PUT new text, check 200, then check the list shows the new text.
        pass

    def test_editing_a_note_to_blank_gives_422(self):
        pass

    def test_editing_a_missing_note_gives_404(self):
        pass

    def test_deleting_a_note_removes_it(self):
        # TODO: add a note, DELETE it, check 204, then check it is gone from the list.
        pass

    def test_deleting_a_missing_note_gives_404(self):
        pass

    def test_a_note_id_that_is_not_a_number_gives_422(self):
        # TODO: try DELETE /api/notes/abc.
        pass
```

- [ ] **Step 2: Run the API tests** and watch the new ones fail.

- [ ] **Step 3: Add the endpoint signatures to `src/api.py`:**

```python
@app.put("/api/notes/{note_id}")
def update_note(note_id: int, note: NoteIn, conn=Depends(get_conn)):
    # TODO: edit the note; 404 if it doesn't exist, 422 if the text is blank.
    pass


@app.delete("/api/notes/{note_id}", status_code=204)
def remove_note(note_id: int, conn=Depends(get_conn)):
    # TODO: delete the note; 404 if it doesn't exist. Return nothing.
    pass
```

**Your part:**

- [ ] **Step 4:** Write both endpoint bodies and all six test bodies.

**Hints:**
- `edit_standalone_note` and `delete_standalone_note` return `True` or `False`. A `False` means "no such note".
- For a "missing" ID that is guaranteed not to exist, add a note, delete it, then use its old ID.
- `self.client.put(url, json={...})` and `self.client.delete(url)` work like `.post`.

**Try to break it:**
- Delete the same note twice. Second time?
- Edit a note to a very long text (paste a paragraph). Does the CLI still show it?

**Check:**
- [ ] **Step 5:** Run all tests: `OK`.
- [ ] **Step 6:** In `/docs`, edit then delete a real test note. Confirm each change in the CLI.

- [ ] **Step 7: Commit** `src/api.py` and `tests/test_api.py` with message `feat: edit and delete standalone notes over HTTP`.

---

### Task 6: Books and book notes

**Files:**
- Modify: `src/api.py`
- Modify: `tests/test_api.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `search_books(conn, keyword, category, subcategory)`, `get_book(conn, book_id)` (returns `None` if missing), `list_categories(conn)`, `list_subcategories(conn, category)`, `list_book_notes(conn, book_id)`, `add_book_note(conn, book_id, text)`, `edit_book_note(conn, book_id, note_id, text)`, `delete_book_note(conn, book_id, note_id)`
- Produces: the eight book endpoints in the spec's table. Book IDs are uppercased. Unknown books give `404` with `No book has that ID.`

**You'll see:** book search and book notes working in `/docs`, matching the CLI's search results.

**New idea: query parameters and reusing a pattern.** The values after `?` in `/api/books?q=python&category=...` are *query parameters*. A function argument that isn't in the path becomes one, and giving it a default (`= ""` or `= None`) makes it optional. Everything else here is a pattern you already know.

Docs: [Query parameters](https://fastapi.tiangolo.com/tutorial/query-params/).

**Boilerplate:**

- [ ] **Step 1: Add a book test class to `tests/test_api.py`.** Its `setUp` creates two temporary books that are rolled back after each test:

```python
class BookApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.conn.execute(
            "INSERT INTO books (book_id, title, category, subcategory) VALUES "
            "('SK-TEST-A', 'Api Test Book Alpha', 'Api Test Category', 'Api Test Sub'), "
            "('SK-TEST-B', 'Api Test Book Beta', 'Api Test Category', NULL)"
        )

    def test_search_finds_a_book_by_title_keyword(self):
        pass

    def test_search_filters_by_category(self):
        pass

    def test_reading_an_unknown_book_gives_404(self):
        pass

    def test_categories_include_the_test_category(self):
        pass

    def test_book_note_lifecycle(self):
        # TODO: add, list, edit, and delete a note on SK-TEST-A, checking each status code.
        pass

    def test_lowercase_book_id_works(self):
        # TODO: add a note via /api/books/sk-test-a/notes and find it via SK-TEST-A.
        pass

    def test_note_cannot_be_changed_through_another_books_address(self):
        # TODO: add a note to SK-TEST-A, try to PUT and DELETE it via SK-TEST-B,
        # expect 404 both times, then check it is unchanged on SK-TEST-A.
        pass

    def test_multiline_note_keeps_its_line_breaks(self):
        # TODO: add "first line\nsecond line" and check the listed text is identical.
        pass

    def test_adding_a_note_to_an_unknown_book_gives_404(self):
        pass
```

- [ ] **Step 2: Run the API tests** and watch the new ones fail.

- [ ] **Step 3: Add the endpoint signatures to `src/api.py`** (and import the book functions from `data.books` and the book-note functions from `data.notes`):

```python
@app.get("/api/books")
def find_books(q: str = "", category: str | None = None, subcategory: str | None = None,
               conn=Depends(get_conn)):
    pass


@app.get("/api/books/{book_id}")
def read_book(book_id: str, conn=Depends(get_conn)):
    pass


@app.get("/api/categories")
def categories(conn=Depends(get_conn)):
    pass


@app.get("/api/subcategories")
def subcategories(category: str | None = None, conn=Depends(get_conn)):
    pass


@app.get("/api/books/{book_id}/notes")
def list_notes_for_book(book_id: str, conn=Depends(get_conn)):
    pass


@app.post("/api/books/{book_id}/notes", status_code=201)
def create_book_note(book_id: str, note: NoteIn, conn=Depends(get_conn)):
    pass


@app.put("/api/books/{book_id}/notes/{note_id}")
def update_book_note(book_id: str, note_id: int, note: NoteIn, conn=Depends(get_conn)):
    pass


@app.delete("/api/books/{book_id}/notes/{note_id}", status_code=204)
def remove_book_note(book_id: str, note_id: int, conn=Depends(get_conn)):
    pass
```

**Your part:**

- [ ] **Step 4:** Write all eight endpoint bodies and the test bodies.
- [ ] **Step 5:** Add a short "Run the API" section to `README.md`. Say where to run the command, what it does, what success looks like, and that `/docs` exists. Keep the existing README style.

**Hints:**
- Five endpoints need to check the book exists before doing anything else. When you notice yourself writing the same lines five times, that's the moment to write a small helper function of your own and call it from each one.
- The CLI uppercases book IDs with `.upper()`. Look at `book_notes_menu` in `init.py`.
- `get_book` returns `None` for an unknown book.

**Try to break it:**
- Search with every field empty. How many books come back? Compare with the CLI.
- Ask for `/api/books/SK-999`. Then `/api/books/SK-999/notes`. Same message both times?

**Check:**
- [ ] **Step 6:** Run all tests: `OK`.
- [ ] **Step 7:** Search for the same keyword in `/docs` and in the CLI. Same books.

- [ ] **Step 8: Commit** `src/api.py`, `tests/test_api.py`, and `README.md` with message `feat: books and book notes over HTTP`.

**The API is done.** Every action the CLI can take now has an HTTP door, and the tests prove it.

---

## Part 2: the page in HTML and CSS

### Task 7: The page's structure in HTML

**Files:**
- Create: `mockup/index.html`
- Create: `mockup/style.css` (empty for now)

**Interfaces:**
- Produces: the page markup that Task 9 pastes into Next.js. Its sections are the future components: header, book search form, book list, notes list (twice), note form.

**You'll see:** a plain, unstyled page in your browser with every part of the spec's layout: header, book search, results, the selected book's notes, and your standalone notes.

**New idea: semantic HTML.** HTML describes *what each part of a page is*, using elements such as `<header>`, `<main>`, `<section>`, `<h2>`, `<form>`, `<label>`, `<input>`, `<select>`, `<textarea>`, `<button>`, `<ul>`/`<li>`, and `<time>`. Choosing the element that matches the meaning is what lets keyboards, screen readers, and later your CSS work well. Every form control needs a `<label>` connected to it.

Generic example (not Skooly):

```html
<section>
  <h2>Cats</h2>
  <ul>
    <li>Miso <time datetime="2026-10-01">1 Oct</time></li>
  </ul>
  <form>
    <label for="cat-name">Cat name</label>
    <input id="cat-name" name="cat-name">
    <button type="submit">Add cat</button>
  </form>
</section>
```

Docs: [MDN: Structuring content with HTML](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content), [MDN: HTML forms](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms).

**Boilerplate:**

- [ ] **Step 1: Create `mockup/index.html`:**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Skooly</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- TODO header: "SKOOLY" and an empty spot reserved for the owl -->

  <!-- TODO main, with two columns of content: -->

  <!-- TODO Books section: title keyword box, category and subcategory
       dropdowns (each with "Any" first), Search button, "3 books found",
       and a list of results with one marked as selected -->

  <!-- TODO Notes section, part 1: "Notes for: <title> (<book id>)",
       a list of notes (text, created and edited dates, Edit and Delete
       buttons), one note shown in its editing state, one showing the
       "Delete this note? Yes / No" question, a status line message,
       then an "Add a note" text area and Save button -->

  <!-- TODO Notes section, part 2: "My notes" with the same parts -->
</body>
</html>
```

- [ ] **Step 2: Create `mockup/style.css`** containing only the comment `/* Skooly styles: Task 8 */`.

**Your part:**

- [ ] **Step 3:** Replace each `TODO` comment with real HTML, using sample data. Copy real titles and categories from `src/data/data.py`.

**Hints:**
- Sketch the boxes on paper first, then write one section at a time and refresh the browser after each.
- The two notes sections are almost identical. Copy and paste is fine here: Task 10 turns them into one component.
- Use `<button type="button">` for buttons that are not submitting a form.
- `<time datetime="2026-10-13T09:15">13 Oct</time>` gives a machine-readable date with friendly text.

**Try to break it:**
- Remove a `for` attribute from a label, then click the label text. What stops happening?
- Press Tab repeatedly from the top. Does focus visit every control in a sensible order?

**Check:**
- [ ] **Step 4:** Double-click `mockup/index.html` to open it. Every part listed in the boilerplate comments is there.
- [ ] **Step 5:** Optional: paste the HTML into the [W3C validator](https://validator.w3.org/nu/#textarea) and fix what it reports.

- [ ] **Step 6: Commit** `mockup/index.html` and `mockup/style.css` with message `feat: HTML structure for the Skooly page`.

---

### Task 8: Styling with CSS

**Files:**
- Modify: `mockup/style.css`
- Modify: `mockup/index.html` (only the font link in `<head>`, and class names if you add them)

**Interfaces:**
- Produces: the stylesheet that Task 9 moves into `web/app/globals.css`. Uses a CSS variable `--font-pixel` for the pixel font so Next.js can supply the same font differently.

**You'll see:** the page looking like Skooly: two columns on a wide window, one column on a narrow one, pixel headings, readable notes, and clear focus outlines.

**New idea: CSS layout and readable, accessible styling.** CSS selects elements and sets their properties. The main tools here:
- custom properties (variables) for colours and fonts;
- `display: grid` for the two columns;
- a `@media (max-width: ...)` rule to stack them on narrow screens;
- `:focus-visible` for keyboard outlines;
- `white-space: pre-wrap` so multi-line notes keep their line breaks.

Docs: [MDN: CSS styling basics](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics), [MDN: Grids](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Grids), [MDN: Media queries](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Media_queries), [WebAIM contrast checker](https://webaim.org/resources/contrastchecker/).

**Boilerplate:**

- [ ] **Step 1: Load the pixel font in the mockup.** Add to `<head>` in `mockup/index.html`, above the `style.css` link:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap">
```

This downloads only the font from Google; none of your notes are sent. In Next.js (Task 9) the font is bundled with the app instead, so the real app makes no request to Google.

- [ ] **Step 2: Start `mockup/style.css` with:**

```css
/* Skooly styles */

:root {
  --font-pixel: "Press Start 2P", monospace;
  /* TODO: colour variables: page background, text, muted text, the owl red accent, focus outline */
}

/* TODO: base: body font, size, line height, colours */
/* TODO: header and pixel headings (use var(--font-pixel) only here) */
/* TODO: two-column grid for main */
/* TODO: forms: labels, inputs, selects, textarea, buttons */
/* TODO: book list and the selected book */
/* TODO: note cards, dates, multi-line text, editing and delete-question states */
/* TODO: status line */
/* TODO: :focus-visible outlines */
/* TODO: @media rule to stack the columns on narrow windows */
```

**Your part:**

- [ ] **Step 3:** Fill in each `TODO` section, refreshing the browser as you go.

**Hints:**
- Get the layout right (grid and stacking) before colours and details.
- The pixel font is wide. Use it small and only for the title and headings. Body text at 16px or more, with a line height around 1.5, stays easy to read.
- Check your text and accent colours in the WebAIM checker. Body text needs a ratio of at least 4.5:1.

**Try to break it:**
- Make the window as narrow as a phone. Does anything overflow sideways?
- Zoom to 200% (`Cmd +`). Is everything still usable?
- Put a very long word or URL in a sample note. Does it break the layout? (`overflow-wrap: anywhere` is the usual fix.)

**Check:**
- [ ] **Step 4:** Mockup checklist:
  - reads comfortably;
  - every control can be reached with Tab and shows a visible outline;
  - columns stack on a narrow window with no sideways scrolling;
  - text contrast is 4.5:1 or more;
  - multi-line sample notes show their line breaks.

- [ ] **Step 5: Commit** `mockup/index.html` and `mockup/style.css` with message `feat: style the Skooly page`.

---

## Part 3: the page in Next.js

### Task 9: Create the Next.js app and show the mockup in it

**Files:**
- Create: `web/` (generated by `create-next-app`)
- Modify: `web/package.json`, `web/next.config.ts`, `web/app/layout.tsx`, `web/app/page.tsx`, `web/app/globals.css`
- Delete: `web/app/page.module.css`
- Modify: `README.md`

**Interfaces:**
- Consumes: the markup from `mockup/index.html` and the CSS from `mockup/style.css`
- Produces: a Next.js app at `127.0.0.1:3000` that forwards `/api/...` to `127.0.0.1:8000/api/...`; the font variable `--font-pixel` set by `layout.tsx`

**You'll see:** the same page as your mockup, now at `http://localhost:3000`. Also, `http://localhost:3000/api/notes` shows your notes JSON, passed through from the API.

**New idea: what Next.js is, JSX, and a first look at TypeScript.**
- Next.js is a React framework. Each folder under `web/app/` with a `page.tsx` becomes a page, and `layout.tsx` wraps every page.
- React components are functions that return *JSX*: HTML-like markup inside TypeScript. It's almost HTML, with a few differences: `class` becomes `className`, `for` becomes `htmlFor`, every tag must be closed (`<input />`), and comments are `{/* ... */}`.
- TypeScript is JavaScript plus *types*: labels that say what kind of value something is, checked before your code runs. `.tsx` files are TypeScript with JSX.

Docs: [Next.js getting started](https://nextjs.org/docs/app/getting-started), [React: Writing markup with JSX](https://react.dev/learn/writing-markup-with-jsx), [TypeScript in 5 minutes](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html), [Next.js rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites).

**Boilerplate:**

- [ ] **Step 1: Create the app.** From the `skooly.ai` folder (Node.js 22 is already installed):

```bash
npx create-next-app@16.4.0 web --ts --app --eslint --no-tailwind --no-src-dir --no-react-compiler --no-agents-md --no-agent-feedback --import-alias "@/*" --use-npm --disable-git --yes
```

This creates `web/` and installs its packages into `web/node_modules`, which `web/.gitignore` keeps out of Git. `--disable-git` matters: `skooly.ai` is already a Git repository. Success ends with `Success! Created web at ...`.

- [ ] **Step 2: Keep the dev server on this Mac only.** In `web/package.json`, change the `dev` script to:

```json
"dev": "next dev --hostname 127.0.0.1",
```

- [ ] **Step 3: Forward `/api` requests to FastAPI.** Replace `web/next.config.ts` with:

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // These two lines came from create-next-app; leave them as they are.
  cacheComponents: true,
  partialPrefetching: true,

  // Send any request for /api/... to the FastAPI server on port 8000.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 4: Set up the layout and font.** Replace `web/app/layout.tsx` with:

```tsx
import type { Metadata } from "next";
import { Press_Start_2P } from "next/font/google";
import "./globals.css";

// Next.js downloads this font when it builds, and serves it from the app itself.
const pixelFont = Press_Start_2P({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-pixel",
});

export const metadata: Metadata = {
  title: "Skooly",
  description: "Your learning notes and books",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={pixelFont.variable}>
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 5: Bring the styles across.**
  - Delete `web/app/page.module.css`.
  - Replace everything in `web/app/globals.css` with the contents of `mockup/style.css`.
  - In `globals.css`, delete the `--font-pixel` line inside `:root`, because `layout.tsx` now sets it.

- [ ] **Step 6: Replace `web/app/page.tsx` with:**

```tsx
export default function Home() {
  return (
    <>
      {/* TODO: paste everything inside <body> from mockup/index.html here,
          then fix the JSX differences until the page shows without errors. */}
    </>
  );
}
```

**Your part:**

- [ ] **Step 7:** Paste the mockup markup and convert it to valid JSX.

**Hints:**
- The terminal running `npm run dev` and the browser page both show errors with line numbers. Fix one at a time.
- HTML comments `<!-- -->` are not allowed in JSX.
- Search the pasted markup for `class=` and `for=`.

**Try to break it:**
- Leave one `class=` unconverted. What does the browser console say? (`Cmd+Option+J` opens it in Chrome.)
- Stop the API server and open `http://localhost:3000/api/notes`. What happens? You'll handle this on the page in Task 12.

**Check:**
- [ ] **Step 8:** With both servers running, `http://localhost:3000` looks the same as the mockup, and `http://localhost:3000/api/notes` shows your notes JSON.
- [ ] **Step 9:** Run, from `web/`:

```bash
npm run lint
npx tsc --noEmit
```

Both finish without errors. `npx tsc --noEmit` runs the TypeScript checker on its own.

- [ ] **Step 10:** Add a "Run the web page" section to `README.md`: first-time `npm install` inside `web/`, the two-tab startup, and the address to open.

- [ ] **Step 11: Commit** `web/` (Git skips `node_modules` and `.next` thanks to `web/.gitignore`) and `README.md` with message `feat: Next.js app showing the Skooly mockup`. Before committing, run `git status` and make sure no `node_modules` files are listed.

---

### Task 10: Split the page into components

**Files:**
- Create: `web/app/types.ts`
- Create: `web/app/components/Header.tsx`, `BookSearch.tsx`, `BookList.tsx`, `NoteList.tsx`, `NoteForm.tsx`
- Modify: `web/app/page.tsx`

**Interfaces:**
- Produces: `Book` and `Note` types in `web/app/types.ts` matching the API's JSON; the components below with these props. Tasks 11 and 12 add props to them.

**You'll see:** an identical page, but `page.tsx` is short and the notes markup exists once, in `NoteList`, used twice.

**New idea: components and props.** A component is a function that returns a piece of the page. *Props* are the inputs you pass to it, like arguments to a function: `<NoteList heading="My notes" notes={myNotes} />`. To show a list of things, you turn an array of data into an array of JSX with `.map()`, giving each item a unique `key`.

Generic example (not Skooly):

```tsx
type Cat = { id: number; name: string };

function CatList({ cats }: { cats: Cat[] }) {
  return (
    <ul>
      {cats.map((cat) => (
        <li key={cat.id}>{cat.name}</li>
      ))}
    </ul>
  );
}
```

Docs: [React: Your first component](https://react.dev/learn/your-first-component), [Passing props](https://react.dev/learn/passing-props-to-a-component), [Rendering lists](https://react.dev/learn/rendering-lists), [TypeScript object types](https://www.typescriptlang.org/docs/handbook/2/objects.html).

**Boilerplate:**

- [ ] **Step 1: Create `web/app/types.ts`:**

```ts
// TODO: export a Book type matching the API's book JSON
// (book_id, title, category, subcategory, and subcategory can be null).

// TODO: export a Note type matching the API's note JSON
// (note_id, note_text, created_at, updated_at; the dates arrive as strings).
```

- [ ] **Step 2: Create the component files.** Each starts like this; change the names and props for each:

`web/app/components/NoteList.tsx`:

```tsx
import type { Note } from "../types";

type NoteListProps = {
  heading: string;
  notes: Note[];
};

export default function NoteList({ heading, notes }: NoteListProps) {
  // TODO: return the notes section markup from page.tsx, using heading and notes.map(...)
  return null;
}
```

The others, with their props:

```tsx
// Header.tsx       export default function Header()                        (no props)
// BookSearch.tsx   export default function BookSearch({ categories, subcategories }: { categories: string[]; subcategories: string[] })
// BookList.tsx     export default function BookList({ books, selectedBookId }: { books: Book[]; selectedBookId: string | null })
// NoteForm.tsx     export default function NoteForm({ label }: { label: string })
```

- [ ] **Step 3: Use them in `page.tsx`.** At the top, import each one:

```tsx
import Header from "./components/Header";
import NoteList from "./components/NoteList";
// ...and the rest
```

**Your part:**

- [ ] **Step 4:** Write `types.ts`.
- [ ] **Step 5:** Move each part of `page.tsx` into its component.
- [ ] **Step 6:** In `page.tsx`, keep the sample data as typed arrays (for example, a `Note[]` for your standalone notes) and pass them in as props.

**Hints:**
- Move one component at a time, and check the page still looks the same after each.
- Decide where `NoteForm` goes: inside `NoteList`, or next to it in `page.tsx`. Either is fine; pick one and be consistent.
- The editing state and delete question from the mockup can stay as fixed sample markup for now. Task 12 makes them real.

**Try to break it:**
- Remove the `key` from a `.map()`. Read the warning in the browser console.
- Pass `notes={"oops"}` to `NoteList`. What does `npx tsc --noEmit` say? That's TypeScript catching the mistake before the browser does.

**Check:**
- [ ] **Step 7:** The page at `localhost:3000` looks exactly like the mockup. `npm run lint` and `npx tsc --noEmit` pass.

- [ ] **Step 8: Commit** `web/app` with message `refactor: split the page into components`.

---

### Task 11: Show real data from the API

**Files:**
- Modify: `web/app/page.tsx`
- Modify: components that need new props (`BookSearch`, `BookList`)

**Interfaces:**
- Consumes: `GET /api/notes`, `GET /api/categories`, `GET /api/subcategories?category=`, `GET /api/books?q=&category=&subcategory=`, `GET /api/books/{book_id}/notes`
- Produces: `page.tsx` as a client component holding state: `books`, `selectedBook`, `bookNotes`, `standaloneNotes`, `categories`, `subcategories`

**You'll see:** your real standalone notes, a working search that matches the CLI's results, and a book's real notes when you choose it.

**New idea: state, effects, and fetch.**
- *State* (`useState`) is data a component remembers that can change. Changing it redraws the page.
- An *effect* (`useEffect`) runs code after the page appears, such as loading data.
- `fetch(url)` sends an HTTP request from the browser. Because of the rewrite, `/api/notes` reaches FastAPI.
- `"use client"` at the top of a file tells Next.js the component runs in the browser, which is needed for state and effects.

Generic example (not Skooly):

```tsx
"use client";
import { useEffect, useState } from "react";

export default function Cats() {
  const [cats, setCats] = useState<Cat[]>([]);

  useEffect(() => {
    fetch("/api/cats")
      .then((response) => response.json())
      .then((data: Cat[]) => setCats(data));
  }, []); // the empty [] means: run once, when the page first appears

  return <CatList cats={cats} />;
}
```

Docs: [React: State](https://react.dev/learn/state-a-components-memory), [Synchronizing with effects](https://react.dev/learn/synchronizing-with-effects), [Responding to events](https://react.dev/learn/responding-to-events), [MDN: Using fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch), [MDN: URLSearchParams](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams).

**Boilerplate:**

- [ ] **Step 1: Make `page.tsx` a client component.** Its first lines become:

```tsx
"use client";

import { useEffect, useState } from "react";
import type { Book, Note } from "./types";
// ...your component imports

export default function Home() {
  // TODO: useState for books, selectedBook, bookNotes, standaloneNotes,
  //       categories, and subcategories.
  // TODO: useEffect that loads standalone notes and categories when the page opens.
  // TODO: a function that runs a search and stores the books.
  // TODO: a function that selects a book and loads its notes.

  return (
    <>
      {/* your components, now given state instead of sample data */}
    </>
  );
}
```

**Your part:**

- [ ] **Step 2:** Replace the sample data with state loaded from the API.
- [ ] **Step 3:** Make the search form submit to `/api/books` with the keyword, category, and subcategory.
- [ ] **Step 4:** Load subcategories again when the category changes.
- [ ] **Step 5:** Make choosing a book load its notes and mark it as selected.
- [ ] **Step 6:** Show the "choose a book" message when no book is selected.

**Hints:**
- Build it in this order, checking the page after each: standalone notes, then categories, then search, then book selection.
- A form's submit handler needs `event.preventDefault()`, or the browser reloads the page.
- `new URLSearchParams({ q: keyword })` builds `q=...` safely, including spaces and special characters.
- Pass functions as props, for example `onSearch` or `onSelectBook`, so the components can tell `page.tsx` what happened. Add these props to the component types.
- Dates arrive as strings. `new Date(note.created_at).toLocaleString()` turns one into something friendly.

**Try to break it:**
- Search for a keyword with no matches. What does the page show? Make it say so clearly.
- Click between books quickly. Does the right book's notes always end up showing?

**Check:**
- [ ] **Step 7:** Manual walkthrough with the CLI open beside it:
  - your standalone notes match the CLI's list;
  - searching "python" finds the same books as the CLI;
  - choosing a book shows the notes the CLI shows for it.
- [ ] **Step 8:** `npm run lint` and `npx tsc --noEmit` pass.

- [ ] **Step 9: Commit** `web/app` with message `feat: load books and notes from the API`.

---

### Task 12: Add, edit, delete, and show errors

**Files:**
- Modify: `web/app/page.tsx`, `NoteList.tsx`, `NoteForm.tsx`
- Modify: `README.md`

**Interfaces:**
- Consumes: `POST`, `PUT`, and `DELETE` on `/api/notes...` and `/api/books/{book_id}/notes...`; error replies shaped `{"detail": "..."}`
- Produces: the finished page

**You'll see:** everything the CLI can do, in the browser. Clear messages appear when something goes wrong.

**New idea: forms, events, and sending data.**
- A *controlled input* keeps its text in state (`value` plus `onChange`), so React always knows what's typed.
- To send data, `fetch` takes a method, a header saying the body is JSON, and the body itself turned into a JSON string.
- `response.ok` is `true` for `2xx` codes. For anything else, read `detail` from the JSON and show it.
- If the API server isn't running at all, `fetch` itself fails or the rewrite returns an error. Catch that too and show a message.

Generic example (not Skooly):

```tsx
const response = await fetch("/api/cats", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "Miso" }),
});
if (!response.ok) {
  const error = await response.json();
  setMessage(error.detail);
}
```

Docs: [React: Reacting to input with state](https://react.dev/learn/reacting-to-input-with-state), [MDN: fetch with a body](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#setting_a_body), [MDN: ARIA live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions), [MDN: async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function).

**Boilerplate:**

- [ ] **Step 1: Give the status line its accessibility attribute.** Wherever you show messages, use:

```tsx
<p className="status" role="status" aria-live="polite">{message}</p>
```

`aria-live` makes screen readers announce new messages without moving focus.

**Your part:**

- [ ] **Step 2:** Adding a note: a controlled text area, POST, clear the box on success, then fetch the list again.
- [ ] **Step 3:** Editing: Edit swaps the note text for a text area with Save and Cancel; PUT on save, then fetch the list again.
- [ ] **Step 4:** Deleting: Delete shows "Delete this note? Yes / No" on that note; Yes sends DELETE, then fetches the list again; No hides the question.
- [ ] **Step 5:** Errors: show the API's `detail` for `4xx` and `5xx` replies, and a message such as "Could not reach Skooly's API. Is it running?" when the request fails entirely.
- [ ] **Step 6:** Make all of the above work for both book notes and standalone notes without writing the logic twice.
- [ ] **Step 7:** Update `README.md` so the "Use the menu" section mentions the web page alongside the CLI.

**Hints:**
- Do add, edit, delete, then errors, one at a time, for standalone notes first. Then make book notes reuse the same code by passing the right URL into it.
- Which note is being edited, and which is showing the delete question, are both state: the `note_id`, or `null` for none.
- After a delete question appears, move keyboard focus to its "No" button, so a stray Enter doesn't delete anything.
- Disable the Save button while a request is in progress, so a double click doesn't add two notes.

**Try to break it:**
- Save a note that is only spaces.
- Stop the API server (`Ctrl+C` in tab 1) and try to add a note. Start it again and retry.
- Stop PostgreSQL and try to load the page.
- Add a note with three lines. Then look at it in the CLI.
- Do everything using only the keyboard.

**Check:**
- [ ] **Step 8:** Manual walkthrough with the CLI open. Each must work:
  - add, edit, and delete a standalone note, with the CLI agreeing each time;
  - the same for a book note;
  - a blank note shows `A note cannot be blank.`;
  - the API stopped shows your "Could not reach" message;
  - PostgreSQL stopped shows the database message;
  - a multi-line note keeps its lines;
  - everything works by keyboard alone, with visible focus.
- [ ] **Step 9:** `npm run lint`, `npx tsc --noEmit`, and all Python tests pass.

- [ ] **Step 10: Commit** `web/app` and `README.md` with message `feat: add, edit, and delete notes from the page`.

**Done.** Skooly has a working web page. When you're ready, the branch can be merged into `main`. Ask Claude to walk you through a pull request on GitHub.
