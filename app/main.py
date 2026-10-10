"""A tiny notes API: create notes, search them, and resolve a hostname."""

import re
import socket
import sqlite3
from contextlib import contextmanager

from flask import Flask, jsonify, request

from app import config

HOSTNAME = re.compile(r"^[A-Za-z0-9.-]{1,253}$")


def create_app(db_path=None):
    app = Flask(__name__)
    path = db_path or config.DB_PATH

    @contextmanager
    def db():
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:  # commits on success, rolls back on error
                yield conn
        finally:
            conn.close()

    with db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL)"
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/notes")
    def add_note():
        data = request.get_json(silent=True) or {}
        title, body = data.get("title"), data.get("body")
        if not title or not body:
            return jsonify(error="title and body are required"), 400
        with db() as conn:
            cur = conn.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body))
        return jsonify(id=cur.lastrowid), 201

    @app.get("/notes")
    def search_notes():
        term = request.args.get("q", "")
        with db() as conn:
            rows = conn.execute(
                "SELECT id, title, body FROM notes WHERE title LIKE ?", (f"%{term}%",)
            ).fetchall()
        return jsonify([dict(row) for row in rows])

    @app.get("/resolve")
    def resolve():
        host = request.args.get("host", "")
        if not HOSTNAME.match(host):
            return jsonify(error="invalid hostname"), 400
        try:
            return jsonify(host=host, address=socket.gethostbyname(host))
        except socket.gaierror:
            return jsonify(error="could not resolve host"), 404

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
