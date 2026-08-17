"""Regression checks for the Alembic revision graph.

These merge revisions have previously been lost during branch merges while
newer migrations still referenced them.  Alembic then failed before it could
run any command, including ``current`` and ``upgrade``.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[1]


def _script_directory() -> ScriptDirectory:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    return ScriptDirectory.from_config(config)


def test_alembic_revision_graph_is_complete_and_has_one_head() -> None:
    script = _script_directory()

    # Walking the graph resolves every down_revision and therefore catches a
    # deleted parent such as aedef0ff7743 instead of failing only at deploy.
    revision_ids = {revision.revision for revision in script.walk_revisions()}

    assert "aedef0ff7743" in revision_ids
    assert "c95f302a587e" in revision_ids
    assert len(script.get_heads()) == 1


def test_dishes_origin_roles_upgrade_skips_columns_already_reconciled(monkeypatch) -> None:
    """The shared DB received these columns before Alembic recorded revision a204.

    A later ``upgrade head`` must be able to advance its revision marker rather
    than failing with PostgreSQL ``DuplicateColumn``.
    """
    migration_path = ROOT / "alembic" / "versions" / "a204c4df9366_dishes_origin_roles.py"
    spec = spec_from_file_location("dishes_origin_roles_migration", migration_path)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    added_columns: list[str] = []

    class Inspector:
        def get_columns(self, table_name: str) -> list[dict[str, str]]:
            assert table_name == "dishes"
            return [{"name": "dish_id"}, {"name": "origin"}]

    monkeypatch.setattr(migration.op, "get_bind", lambda: object())
    monkeypatch.setattr(migration.sa, "inspect", lambda _bind: Inspector())
    monkeypatch.setattr(
        migration.op,
        "add_column",
        lambda _table_name, column: added_columns.append(column.name),
    )

    migration.upgrade()

    assert added_columns == ["roles"]
