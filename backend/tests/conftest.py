"""Pytest defaults: keep DB persistence off unless a test opts in."""

import os

os.environ.setdefault("ENABLE_DATABASE", "false")
