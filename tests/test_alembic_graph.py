"""Regression checks for the Alembic revision graph.

These merge revisions have previously been lost during branch merges while
newer migrations still referenced them.  Alembic then failed before it could
run any command, including ``current`` and ``upgrade``.
"""

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
