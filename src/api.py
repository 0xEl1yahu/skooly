from fastapi import FastAPI

from data.db import connect
from data.notes import list_standalone_notes

app = FastAPI(title="Skooly API")


@app.get("/api/notes")
def listnotes():
    with connect() as conn:
        return list_standalone_notes(conn)