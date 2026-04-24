"""Unit tests for legacy customer index extraction schemas and CLI helpers (no LLM)."""

from __future__ import annotations

import json

import pytest

from agent_service.tools.legacy_customer_import.schemas import (
    ExtractedMeeting,
    ExtractedOrganization,
    ExtractedProject,
    ImportStep,
    LegacyCustomerIndexImport,
    MeetingImportStep,
)
from agent_service.tools.migrate_customer_index import (
    meeting_create_body,
    meeting_patch_steps_body,
    planned_payloads,
)


@pytest.fixture
def sample_import() -> LegacyCustomerIndexImport:
    return LegacyCustomerIndexImport(
        organization=ExtractedOrganization(
            name="ATT",
            stakeholders="John Radice (PM)",
            team="Murthy Kakarlamudi (SE)",
            related_products="Confluent Cloud for Kafka",
        ),
        project=ExtractedProject(
            name="ATT Flink migration",
            description="ksql to Flink migration program.",
            status="Active",
            past_steps=[ImportStep(what="Delivered demo", who="Team")],
            next_steps=[ImportStep(what="Dry run migration", who="unknown")],
        ),
        meetings=[
            ExtractedMeeting(
                meeting_id="att-2026-01-13",
                title_hint="Meeting 1/13",
                attendees="John Radice, Murthy",
                content="### Meeting 1/13\n\n- RBAC discussion\n",
                past_steps=[MeetingImportStep(what="Murthy to share doc", who="Murthy")],
            )
        ],
        source_hint="att",
        confidence_notes=None,
    )


def test_legacy_customer_index_import_roundtrip(sample_import: LegacyCustomerIndexImport) -> None:
    raw = sample_import.model_dump(mode="json")
    restored = LegacyCustomerIndexImport.model_validate(raw)
    assert restored.organization.name == "ATT"
    assert len(restored.meetings) == 1
    assert restored.meetings[0].meeting_id == "att-2026-01-13"


def test_planned_payloads_structure(sample_import: LegacyCustomerIndexImport) -> None:
    plan = planned_payloads(sample_import)
    assert plan["organization"]["name"] == "ATT"
    assert plan["project"]["name"] == "ATT Flink migration"
    assert len(plan["meetings"]) == 1
    create = plan["meetings"][0]["create"]
    assert create["meeting_id"] == "att-2026-01-13"
    assert "steps_patch_after_create" in plan["meetings"][0]


def test_meeting_create_body_null_ids(sample_import: LegacyCustomerIndexImport) -> None:
    m = sample_import.meetings[0]
    body = meeting_create_body(m, project_id=None, org_id=None)
    assert body["project_id"] is None
    assert body["org_id"] is None
    assert body["content"].startswith("###")


def test_meeting_patch_steps_body_empty_when_no_steps() -> None:
    m = ExtractedMeeting(meeting_id="x", content="# Hi")
    assert meeting_patch_steps_body(m) == {}


def test_fixture_json_snapshot_minimal() -> None:
    """Golden-style minimal blob: ensures schema accepts typical API-shaped dicts."""
    blob = {
        "organization": {
            "name": "Acme",
            "stakeholders": None,
            "team": None,
            "description": None,
            "related_products": None,
            "is_top_active": False,
        },
        "project": {
            "name": "Cloud rollout",
            "description": "Rollout",
            "status": "Draft",
            "tasks": None,
            "past_steps": [{"what": "Kickoff", "who": "Alice"}],
            "next_steps": None,
        },
        "meetings": [],
        "source_hint": "acme",
        "confidence_notes": None,
    }
    LegacyCustomerIndexImport.model_validate(blob)
    json.dumps(blob)
