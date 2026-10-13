import io
import os
import sys
import time
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ConnectionTests(unittest.TestCase):
    def test_connection_returns_dictionary_rows(self):
        self.assertIn("SKOOLY_DATABASE_URL", os.environ)

        from data.db import connect

        conn = connect()
        try:
            row = conn.execute("SELECT 1 AS value").fetchone()
            self.assertEqual(row["value"], 1)
        finally:
            conn.close()


class BookTests(unittest.TestCase):
    def setUp(self):
        from data.db import connect

        self.conn = connect()
        self.category = f"Test {uuid.uuid4().hex}"

    def tearDown(self):
        self.conn.rollback()
        self.conn.close()

    def test_seed_does_not_replace_an_existing_book(self):
        from data.books import get_book, seed_books

        book = {
            "book_id": f"TEST-{uuid.uuid4().hex[:12]}",
            "title": "Original title",
            "category": self.category,
            "subcategory": None,
        }
        self.assertEqual(seed_books(self.conn, [book]), 1)

        changed_book = {**book, "title": "Replacement title"}
        self.assertEqual(seed_books(self.conn, [changed_book]), 0)
        self.assertEqual(get_book(self.conn, book["book_id"])["title"], "Original title")

    def test_search_combines_filters_and_treats_percent_literally(self):
        from data.books import (
            list_categories,
            list_subcategories,
            search_books,
            seed_books,
        )

        books = [
            {
                "book_id": f"TEST-{uuid.uuid4().hex[:12]}",
                "title": "Python 100% Patterns",
                "category": self.category,
                "subcategory": "Python",
            },
            {
                "book_id": f"TEST-{uuid.uuid4().hex[:12]}",
                "title": "Python Basics",
                "category": self.category,
                "subcategory": None,
            },
            {
                "book_id": f"TEST-{uuid.uuid4().hex[:12]}",
                "title": "Java 100% Patterns",
                "category": self.category,
                "subcategory": "Java",
            },
        ]
        seed_books(self.conn, books)

        self.assertIn(self.category, list_categories(self.conn))
        self.assertIn("Python", list_subcategories(self.conn, None))
        self.assertIn("Python", list_subcategories(self.conn, self.category))
        self.assertEqual(
            [book["title"] for book in search_books(self.conn, "pYtHoN", self.category, None)],
            ["Python 100% Patterns", "Python Basics"],
        )
        self.assertEqual(
            [book["title"] for book in search_books(self.conn, "%", self.category, "Python")],
            ["Python 100% Patterns"],
        )
        self.assertEqual(
            [book["title"] for book in search_books(self.conn, "", self.category, None)],
            ["Java 100% Patterns", "Python 100% Patterns", "Python Basics"],
        )


class NoteTests(unittest.TestCase):
    def setUp(self):
        from data.db import connect

        self.conn = connect()

    def tearDown(self):
        self.conn.rollback()
        self.conn.close()

    def test_book_note_lifecycle_stays_with_its_book(self):
        from data.books import seed_books
        from data.notes import (
            add_book_note,
            delete_book_note,
            edit_book_note,
            list_book_notes,
        )

        book_ids = [f"TEST-{uuid.uuid4().hex[:12]}" for _ in range(2)]
        seed_books(
            self.conn,
            [
                {
                    "book_id": book_id,
                    "title": f"Test book {number}",
                    "category": "Test category",
                    "subcategory": None,
                }
                for number, book_id in enumerate(book_ids)
            ],
        )

        with self.assertRaises(ValueError):
            add_book_note(self.conn, book_ids[0], "  ")

        note_id = add_book_note(self.conn, book_ids[0], "First thought")
        first = list_book_notes(self.conn, book_ids[0])[0]
        self.assertEqual(first["note_id"], note_id)
        self.assertEqual(first["note_text"], "First thought")
        self.assertFalse(edit_book_note(self.conn, book_ids[1], note_id, "Wrong book"))
        self.assertFalse(delete_book_note(self.conn, book_ids[1], note_id))
        time.sleep(0.02)
        self.assertTrue(edit_book_note(self.conn, book_ids[0], note_id, "Better thought"))

        edited = list_book_notes(self.conn, book_ids[0])[0]
        self.assertEqual(edited["note_text"], "Better thought")
        self.assertEqual(edited["created_at"], first["created_at"])
        self.assertGreater(edited["updated_at"], first["updated_at"])
        self.assertTrue(delete_book_note(self.conn, book_ids[0], note_id))
        self.assertEqual(list_book_notes(self.conn, book_ids[0]), [])

    def test_standalone_note_lifecycle(self):
        from data.notes import (
            add_standalone_note,
            delete_standalone_note,
            edit_standalone_note,
            list_standalone_notes,
        )

        with self.assertRaises(ValueError):
            add_standalone_note(self.conn, "  ")

        note_id = add_standalone_note(self.conn, "A useful idea")
        first = next(
            note for note in list_standalone_notes(self.conn) if note["note_id"] == note_id
        )
        time.sleep(0.02)
        self.assertTrue(edit_standalone_note(self.conn, note_id, "A clearer idea"))
        edited = next(
            note for note in list_standalone_notes(self.conn) if note["note_id"] == note_id
        )
        self.assertEqual(edited["note_text"], "A clearer idea")
        self.assertEqual(edited["created_at"], first["created_at"])
        self.assertGreater(edited["updated_at"], first["updated_at"])
        self.assertTrue(delete_standalone_note(self.conn, note_id))
        self.assertFalse(delete_standalone_note(self.conn, note_id))

    def test_book_menu_keeps_note_when_delete_is_declined(self):
        from data.books import seed_books
        from data.notes import add_book_note, list_book_notes
        from init import book_notes_menu

        book_id = f"TEST-{uuid.uuid4().hex[:12]}"
        seed_books(
            self.conn,
            [{
                "book_id": book_id,
                "title": "Menu test book",
                "category": "Test category",
                "subcategory": None,
            }],
        )
        note_id = add_book_note(self.conn, book_id, "Keep this thought")

        output = io.StringIO()
        with patch("builtins.input", side_effect=["3", str(note_id), "n", "4"]):
            with redirect_stdout(output):
                book_notes_menu(self.conn, book_id)

        self.assertIn("Deletion cancelled", output.getvalue())
        self.assertEqual(list_book_notes(self.conn, book_id)[0]["note_text"], "Keep this thought")

    def test_standalone_menu_keeps_note_when_delete_is_declined(self):
        from data.notes import add_standalone_note, list_standalone_notes
        from init import standalone_notes_menu

        note_id = add_standalone_note(self.conn, "Keep this idea")
        output = io.StringIO()
        with patch("builtins.input", side_effect=["3", str(note_id), "n", "4"]):
            with redirect_stdout(output):
                standalone_notes_menu(self.conn)

        self.assertIn("Deletion cancelled", output.getvalue())
        self.assertTrue(
            any(note["note_id"] == note_id for note in list_standalone_notes(self.conn))
        )


if __name__ == "__main__":
    unittest.main()
