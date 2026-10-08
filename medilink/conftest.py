"""Wird von pytest vor allen Tests geladen: Tests benutzen NIE die echte Datenbank (Neon/PostgreSQL)."""
import os

os.environ.pop("DATABASE_URL", None)
