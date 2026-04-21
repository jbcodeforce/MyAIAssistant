"""Unit tests for customer index normalization (renderer + discovery; no LLM)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent_service.tools.customer_index_normalize import (
    CustomerIndexNormalized,
    discover_index_files,
    normalize_source_with_agent,
    render_customer_index_markdown,
)


def test_render_customer_index_markdown_order_and_headings():
    data = CustomerIndexNormalized(
        title_line="# TestCo",
        preamble_after_title="Status line.",
        products_in_scope="* Flink",
        champion_and_team="* Alice",
        confluent="* AE: Bob",
        use_case="* Stream events",
        context="* Pain: latency",
        architecture="* Kafka",
        past_steps="* Met once",
        next_steps="- [ ] Follow up",
        sources_of_information="* [Doc](https://example.com)",
    )
    md = render_customer_index_markdown(data)
    assert md.startswith("# TestCo\n\nStatus line.\n")
    assert md.index("## Products in scope") < md.index("## Champion and team")
    assert md.index("## Champion and team") < md.index("## Confluent")
    assert md.index("## Confluent") < md.index("## Use case")
    assert md.index("## Use case") < md.index("## Context")
    assert md.index("## Context") < md.index("## Architecture")
    assert md.index("## Architecture") < md.index("## Past Steps")
    assert md.index("## Past Steps") < md.index("## Next Steps")
    assert md.index("## Next Steps") < md.index("## Sources of information")


def test_render_omits_empty_sections():
    data = CustomerIndexNormalized(
        title_line="# Solo",
        products_in_scope="* Only",
    )
    md = render_customer_index_markdown(data)
    assert "## Champion and team" not in md
    assert "## Products in scope" in md


def test_render_title_prefixes_hash_if_missing():
    data = CustomerIndexNormalized(title_line="Bare")
    md = render_customer_index_markdown(data)
    assert md.startswith("# Bare\n")


def test_discover_index_files_filters_slug(tmp_path: Path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "index.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "index.md").write_text("# B\n", encoding="utf-8")
    found = discover_index_files(tmp_path, only_slug="b")
    assert len(found) == 1
    assert found[0].parent.name == "b"


def test_discover_index_files_empty_dir(tmp_path: Path):
    assert discover_index_files(tmp_path, only_slug=None) == []


def test_normalize_source_with_agent_uses_run_content():
    agent = MagicMock()
    agent.run.return_value = SimpleNamespace(
        content=CustomerIndexNormalized(title_line="# Acme", products_in_scope="* Item"),
    )
    out = normalize_source_with_agent("ignored body", agent)
    assert out.title_line == "# Acme"
    assert "Item" in out.products_in_scope
    agent.run.assert_called_once()
