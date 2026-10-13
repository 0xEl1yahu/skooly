"""Store and find books in the owner's catalogue."""


def seed_books(conn, books):
    inserted = 0

    for book in books:
        result = conn.execute(
            """
            INSERT INTO books (book_id, title, category, subcategory)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (book_id) DO NOTHING
            RETURNING book_id
            """,
            (
                book["book_id"],
                book["title"],
                book["category"],
                book["subcategory"],
            ),
        )
        if result.fetchone() is not None:
            inserted += 1

    return inserted


def get_book(conn, book_id):
    return conn.execute(
        """
        SELECT book_id, title, category, subcategory
        FROM books
        WHERE book_id = %s
        """,
        (book_id,),
    ).fetchone()


def list_categories(conn):
    rows = conn.execute(
        "SELECT DISTINCT category FROM books ORDER BY category"
    ).fetchall()
    return [row["category"] for row in rows]


def list_subcategories(conn, category=None):
    if category is None:
        rows = conn.execute(
            """
            SELECT DISTINCT subcategory FROM books
            WHERE subcategory IS NOT NULL
            ORDER BY subcategory
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT DISTINCT subcategory FROM books
            WHERE category = %s AND subcategory IS NOT NULL
            ORDER BY subcategory
            """,
            (category,),
        ).fetchall()

    return [row["subcategory"] for row in rows]


def search_books(conn, keyword="", category=None, subcategory=None):
    query = "SELECT book_id, title, category, subcategory FROM books"
    conditions = []
    values = []

    keyword = keyword.strip()
    if keyword:
        conditions.append("STRPOS(LOWER(title), LOWER(%s)) > 0")
        values.append(keyword)
    if category is not None:
        conditions.append("category = %s")
        values.append(category)
    if subcategory is not None:
        conditions.append("subcategory = %s")
        values.append(subcategory)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY title, book_id"

    return conn.execute(query, values).fetchall()
