-- Upgrade the existing skooly database to match src/data/schema.sql.
-- Run once with: psql -X -v ON_ERROR_STOP=1 -d skooly -f src/data/migrations/001_align_notes_schema.sql
-- Existing book records are left untouched. Stop if book notes have been added.

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM book_notes) THEN
        RAISE EXCEPTION 'book_notes is not empty; review its IDs before this migration';
    END IF;
END;
$$;

ALTER TABLE book_notes
    ALTER COLUMN note_id TYPE BIGINT USING note_id::BIGINT;

ALTER TABLE book_notes
    ALTER COLUMN note_id ADD GENERATED ALWAYS AS IDENTITY;

ALTER TABLE book_notes
    ALTER COLUMN created_at DROP DEFAULT;

ALTER TABLE book_notes
    ALTER COLUMN created_at TYPE TIMESTAMPTZ
    USING created_at AT TIME ZONE 'UTC';

ALTER TABLE book_notes
    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE book_notes
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE standalone_notes (
    note_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMIT;

/* - schema.sql describes how to create tables from scratch. A migration changes tables that already exist. Save migrations in order and normally run each one once.
- BEGIN; starts a transaction. COMMIT; saves all its changes together. ROLLBACK; cancels them. This is different from the BEGIN inside a DO block.
- DO $$ ... $$; runs a short SQL program. Our migration uses IF inside it to stop if book_notes contains notes. Most migrations do not need DO.
- ALTER TABLE changes an existing table. For example, ADD COLUMN updated_at ... adds a new field.
- USING says how to convert old values when a column’s type changes. note_id::BIGINT means “convert this value to a large whole number.”
- GENERATED ALWAYS AS IDENTITY lets PostgreSQL assign a new numeric ID when a note is added.
- TIMESTAMPTZ stores a timestamp with time-zone handling. DEFAULT CURRENT_TIMESTAMP fills it when a row is created; it does not update updated_at when you edit a note.
*/
