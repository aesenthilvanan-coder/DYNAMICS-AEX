"""CALY360 PDF §7: apply initial SQL schema (same DDL as ``001_initial.sql``).

Revision ID: pdf_schema_001
Revises:
Create Date: 2026-04-10
"""

from pathlib import Path

from alembic import op

revision = "pdf_schema_001"
down_revision = None
branch_labels = None
depends_on = None


def _split_sql(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    stmts: list[str] = []
    buf: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        buf.append(line)
        if s.endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    return stmts


def upgrade() -> None:
    sql_file = Path(__file__).resolve().parent / "001_initial.sql"
    for stmt in _split_sql(sql_file):
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dynamics_results CASCADE")
    op.execute("DROP TABLE IF EXISTS jobs CASCADE")
