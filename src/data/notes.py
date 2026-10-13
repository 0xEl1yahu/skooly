"""Read and change book notes and standalone notes."""


def _note_text(text):
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("A note cannot be blank.")
    return cleaned


def list_book_notes(conn, book_id):
    return conn.execute(
        """
        SELECT note_id, note_text, created_at, updated_at
        FROM book_notes
        WHERE book_id = %s
        ORDER BY created_at, note_id
        """,
        (book_id,),
    ).fetchall()


def add_book_note(conn, book_id, text):
    row = conn.execute(
        """
        INSERT INTO book_notes (book_id, note_text, created_at, updated_at)
        VALUES (%s, %s, clock_timestamp(), clock_timestamp())
        RETURNING note_id
        """,
        (book_id, _note_text(text)),
    ).fetchone()
    return row["note_id"]


def edit_book_note(conn, book_id, note_id, text):
    result = conn.execute(
        """
        UPDATE book_notes
        SET note_text = %s, updated_at = clock_timestamp()
        WHERE book_id = %s AND note_id = %s
        """,
        (_note_text(text), book_id, note_id),
    )
    return result.rowcount > 0


def delete_book_note(conn, book_id, note_id):
    result = conn.execute(
        "DELETE FROM book_notes WHERE book_id = %s AND note_id = %s",
        (book_id, note_id),
    )
    return result.rowcount > 0


def list_standalone_notes(conn):
    return conn.execute(
        """
        SELECT note_id, note_text, created_at, updated_at
        FROM standalone_notes
        ORDER BY created_at, note_id
        """
    ).fetchall()


def add_standalone_note(conn, text):
    row = conn.execute(
        """
        INSERT INTO standalone_notes (note_text, created_at, updated_at)
        VALUES (%s, clock_timestamp(), clock_timestamp())
        RETURNING note_id
        """,
        (_note_text(text),),
    ).fetchone()
    return row["note_id"]


def edit_standalone_note(conn, note_id, text):
    result = conn.execute(
        """
        UPDATE standalone_notes
        SET note_text = %s, updated_at = clock_timestamp()
        WHERE note_id = %s
        """,
        (_note_text(text), note_id),
    )
    return result.rowcount > 0


def delete_standalone_note(conn, note_id):
    result = conn.execute(
        "DELETE FROM standalone_notes WHERE note_id = %s",
        (note_id,),
    )
    return result.rowcount > 0
