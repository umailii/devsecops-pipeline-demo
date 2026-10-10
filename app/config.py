"""Settings come from the environment. No secrets are kept in the source."""

import os

DB_PATH = os.environ.get("DB_PATH", "notes.db")
