## init talks to users. imported files are modules that we bring to interact with the DB
## conn = connect to link up to DB

import psycopg

from data.books import get_book, list_categories, list_subcategories, search_books
from data.db import connect
from data.notes import (
    add_book_note,
    add_standalone_note,
    delete_book_note,
    delete_standalone_note,
    edit_book_note,
    edit_standalone_note,
    list_book_notes,
    list_standalone_notes,
)


def choose_filter(options, label):
    if not options:
        return None

    print(f"\n{label} (press Enter for any):")
    for number, option in enumerate(options, start=1):
        print(f"{number}. {option}")

    while True:
        choice = input("Choose a number: ").strip()
        if not choice:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print(f"Please choose a number from 1 to {len(options)}, or press Enter.")


def search_menu(conn):
    keyword = input("Title keyword (press Enter for any): ").strip()
    category = choose_filter(list_categories(conn), "Categories")
    subcategory = choose_filter(list_subcategories(conn, category), "Subcategories")
    matches = search_books(conn, keyword, category, subcategory)

    if not matches:
        print("No books matched.")
        return

    print(f"\n{len(matches)} book(s) found:")
    for book in matches:
        location = book["category"]
        if book["subcategory"]:
            location += f" / {book['subcategory']}"
        print(f"{book['book_id']} — {book['title']} ({location})")

    selected = input("Book ID for notes, or Enter to return: ").strip().upper()
    if selected:
        book_notes_menu(conn, selected)


def show_note(note):
    created = note["created_at"].astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    updated = note["updated_at"].astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"#{note['note_id']} — created {created}, updated {updated}")
    print(f"  {note['note_text']}")


def ask_note_id():
    answer = input("Note ID: ").strip()
    if not answer.isdigit():
        print("Enter a numeric note ID.")
        return None
    return int(answer)


def book_notes_menu(conn, book_id=None):
    if book_id is None:
        book_id = input("Book ID (for example SK-001): ").strip().upper()

    book = get_book(conn, book_id)
    if book is None:
        print("No book has that ID. Search books to find its ID.")
        return

    while True:
        notes = list_book_notes(conn, book_id)
        print(f"\nNotes for {book['title']} ({book_id})")
        if notes:
            for note in notes:
                show_note(note)
        else:
            print("No notes yet.")

        print("1. Add note  2. Edit note  3. Delete note  4. Back")
        choice = input("Choose 1-4: ").strip()

        if choice == "1":
            text = input("Your note (one line): ")
            try:
                note_id = add_book_note(conn, book_id, text)
                conn.commit()
                print(f"Saved book note #{note_id}.")
            except ValueError as error:
                print(error)
        elif choice == "2":
            note_id = ask_note_id()
            if note_id is None:
                continue
            text = input("Revised note (one line): ")
            try:
                changed = edit_book_note(conn, book_id, note_id, text)
            except ValueError as error:
                print(error)
                continue
            if changed:
                conn.commit()
                print("Note updated.")
            else:
                print("No note with that ID belongs to this book.")
        elif choice == "3":
            note_id = ask_note_id()
            if note_id is None:
                continue
            note = next((item for item in notes if item["note_id"] == note_id), None)
            if note is None:
                print("No note with that ID belongs to this book.")
                continue
            show_note(note)
            confirm = input("Delete this note? (y/N): ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Deletion cancelled.")
                continue
            if delete_book_note(conn, book_id, note_id):
                conn.commit()
                print("Note deleted.")
        elif choice == "4":
            return
        else:
            print("Please choose 1, 2, 3, or 4.")


def standalone_notes_menu(conn):
    while True:
        notes = list_standalone_notes(conn)
        print("\nStandalone notes")
        if notes:
            for note in notes:
                show_note(note)
        else:
            print("No notes yet.")

        print("1. Add note  2. Edit note  3. Delete note  4. Back")
        choice = input("Choose 1-4: ").strip()

        if choice == "1":
            text = input("Your note (one line): ")
            try:
                note_id = add_standalone_note(conn, text)
                conn.commit()
                print(f"Saved standalone note #{note_id}.")
            except ValueError as error:
                print(error)
        elif choice == "2":
            note_id = ask_note_id()
            if note_id is None:
                continue
            text = input("Revised note (one line): ")
            try:
                changed = edit_standalone_note(conn, note_id, text)
            except ValueError as error:
                print(error)
                continue
            if changed:
                conn.commit()
                print("Note updated.")
            else:
                print("No standalone note has that ID.")
        elif choice == "3":
            note_id = ask_note_id()
            if note_id is None:
                continue
            note = next((item for item in notes if item["note_id"] == note_id), None)
            if note is None:
                print("No standalone note has that ID.")
                continue
            show_note(note)
            confirm = input("Delete this note? (y/N): ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Deletion cancelled.")
                continue
            if delete_standalone_note(conn, note_id):
                conn.commit()
                print("Note deleted.")
        elif choice == "4":
            return
        else:
            print("Please choose 1, 2, 3, or 4.")


def main():
    print("Welcome to Skooly user!")

    while True:
        print("\n1. Search books")
        print("2. Book notes")
        print("3. Standalone notes")
        print("4. Exit")
        try:
            choice = input("Choose 1-4: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice in ("1", "2", "3"):
            try:
                with connect() as conn:
                    if choice == "1":
                        search_menu(conn)
                    elif choice == "2":
                        book_notes_menu(conn)
                    else:
                        standalone_notes_menu(conn)
            except (ValueError, psycopg.Error):
                print("Could not use the database. Check SKOOLY_DATABASE_URL and PostgreSQL.")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Please choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
