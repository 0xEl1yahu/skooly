CREATE TABLE books (
    book_id VARCHAR(20) PRIMARY KEY,
    title VARCHAR(225) NOT NULL,
    category VARCHAR(225) NOT NULL,
    subcategory VARCHAR(100)
);

CREATE TABLE book_notes (
    note_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id VARCHAR(20) NOT NULL,
    note_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

CREATE TABLE standalone_notes (
    note_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

/* 
create table: create a table
varchar (no) how many character
timestampz for time stamp
primary key: gives note unique id 
null: no value recorded/""
not null: field must have value!
*/

/*
insert: add
select: find/read
update: change
delete: remove
*/ 