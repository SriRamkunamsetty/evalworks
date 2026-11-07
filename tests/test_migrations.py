from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session


def test_initial_migration_creates_expected_tables(tmp_path, monkeypatch):
    from evalworks.config import settings

    database = tmp_path / "migration.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database.as_posix()}")
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database.as_posix()}")
    names = set(inspect(engine).get_table_names())
    assert {"evaluation_runs", "review_feedback", "workspaces", "users", "alembic_version"} <= names
    columns = {column["name"] for column in inspect(engine).get_columns("evaluation_runs")}
    assert "metadata" in columns
    assert {"workspace_id", "created_by"} <= columns
    from evalworks.models import EvaluationRun

    with Session(engine) as session:
        session.add(
            EvaluationRun(
                project="judgebench",
                workspace_id="local",
                input_digest="a" * 64,
                result={"human_review_required": True},
                run_metadata={"model": "test-model"},
            )
        )
        session.commit()
        stored = session.query(EvaluationRun).one()
        assert stored.run_metadata == {"model": "test-model"}
    engine.dispose()
