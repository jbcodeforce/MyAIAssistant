#!/usr/bin/env python3
"""CLI: extract legacy customer index.md via Agno and persist to MyAIAssistant REST API."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx

from agent_service.tools.legacy_customer_import.extractor import (
    default_folder_slug_from_path,
    extract_legacy_customer_index,
)
from agent_service.tools.legacy_customer_import.schemas import ExtractedMeeting, LegacyCustomerIndexImport

logger = logging.getLogger(__name__)


def default_backend_url() -> str:
    return os.environ.get("MYAI_BACKEND_URL", "http://localhost:8000").rstrip("/")


def get_or_create_organization(client: httpx.Client, backend: str, org_body: dict[str, Any]) -> dict[str, Any]:
    """GET search by name; POST if 404."""
    name = org_body["name"]
    r = client.get(f"{backend}/api/organizations/search/by-name", params={"name": name})
    if r.status_code == 200:
        logger.info("Organization exists: %s (id=%s)", name, r.json().get("id"))
        return r.json()
    if r.status_code != 404:
        r.raise_for_status()
    r = client.post(f"{backend}/api/organizations/", json=org_body)
    r.raise_for_status()
    logger.info("Created organization: %s (id=%s)", name, r.json().get("id"))
    return r.json()


def get_or_create_project(
    client: httpx.Client,
    backend: str,
    organization_id: int,
    project_body: dict[str, Any],
) -> dict[str, Any]:
    """GET search by name + org; POST if 404."""
    name = project_body["name"]
    r = client.get(
        f"{backend}/api/projects/search/by-name",
        params={"name": name, "organization_id": organization_id},
    )
    if r.status_code == 200:
        logger.info("Project exists: %s (id=%s)", name, r.json().get("id"))
        return r.json()
    if r.status_code != 404:
        r.raise_for_status()
    body = {**project_body, "organization_id": organization_id}
    r = client.post(f"{backend}/api/projects/", json=body)
    r.raise_for_status()
    logger.info("Created project: %s (id=%s)", name, r.json().get("id"))
    return r.json()


def meeting_create_body(
    m: ExtractedMeeting,
    *,
    project_id: int | None,
    org_id: int | None,
) -> dict[str, Any]:
    return {
        "meeting_id": m.meeting_id,
        "project_id": project_id,
        "org_id": org_id,
        "attendees": m.attendees,
        "content": m.content,
    }


def meeting_patch_steps_body(m: ExtractedMeeting) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    if m.past_steps is not None:
        patch["past_steps"] = [s.model_dump(exclude_none=True) for s in m.past_steps]
    if m.next_steps is not None:
        patch["next_steps"] = [s.model_dump(exclude_none=True) for s in m.next_steps]
    return patch


def planned_payloads(data: LegacyCustomerIndexImport) -> dict[str, Any]:
    """Serializable preview of what would be POSTed (project/org without resolved IDs)."""
    org_payload = data.organization.model_dump(mode="json", exclude_none=True)
    proj_payload = data.project.model_dump(mode="json", exclude_none=True)
    meetings_out: list[dict[str, Any]] = []
    for m in data.meetings:
        entry: dict[str, Any] = {
            "create": meeting_create_body(m, project_id=None, org_id=None),
        }
        patch = meeting_patch_steps_body(m)
        if patch:
            entry["steps_patch_after_create"] = patch
        meetings_out.append(entry)
    return {
        "organization": org_payload,
        "project": proj_payload,
        "meetings": meetings_out,
        "source_hint": data.source_hint,
        "confidence_notes": data.confidence_notes,
    }


def migrate_to_backend(
    client: httpx.Client,
    backend: str,
    data: LegacyCustomerIndexImport,
) -> None:
    org_payload = data.organization.model_dump(mode="json", exclude_none=True)
    proj_payload = data.project.model_dump(mode="json", exclude_none=True)

    org = get_or_create_organization(client, backend, org_payload)
    org_id = org["id"]

    proj = get_or_create_project(client, backend, org_id, proj_payload)
    project_id = proj["id"]

    for m in data.meetings:
        body = meeting_create_body(m, project_id=project_id, org_id=org_id)
        r = client.post(f"{backend}/api/meeting-refs/", json=body)
        if r.status_code == 409:
            logger.warning("Skipping duplicate meeting_id=%s (already exists)", m.meeting_id)
            continue
        r.raise_for_status()
        created = r.json()
        mr_id = created["id"]
        patch = meeting_patch_steps_body(m)
        if patch:
            pr = client.put(f"{backend}/api/meeting-refs/{mr_id}", json=patch)
            pr.raise_for_status()
            logger.info("Updated meeting_ref id=%s with structured steps", mr_id)
        else:
            logger.info("Created meeting_ref id=%s meeting_id=%s", mr_id, m.meeting_id)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Migrate a legacy customer index.md into MyAIAssistant via Agno extraction + REST API.",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        required=True,
        help="Path to index.md (or any legacy customer markdown file)",
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default=default_backend_url(),
        help="MyAIAssistant backend base URL (default MYAI_BACKEND_URL or http://localhost:8000)",
    )
    parser.add_argument(
        "--folder-slug",
        type=str,
        default=None,
        help="Account folder name hint for naming (default: parent dir if file is index.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run extraction and print planned REST payloads as JSON; do not call backend",
    )
    parser.add_argument(
        "--only-extract",
        action="store_true",
        help="Print extraction JSON only; no HTTP persistence",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write extraction JSON to this path",
    )
    args = parser.parse_args(argv)

    path = args.file.expanduser().resolve()
    if not path.is_file():
        print(f"Not a file: {path}", file=sys.stderr)
        return 2

    slug = args.folder_slug or default_folder_slug_from_path(path)

    markdown = path.read_text(encoding="utf-8")
    logger.info("Extracting structured data (Agno)...")
    extracted = extract_legacy_customer_index(markdown, folder_slug=slug)

    if args.json_out:
        args.json_out.write_text(extracted.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Wrote extraction to %s", args.json_out)

    if args.only_extract:
        print(extracted.model_dump_json(indent=2))
        return 0

    if args.dry_run:
        print(json.dumps(planned_payloads(extracted), indent=2, default=str))
        return 0

    backend = args.backend_url.rstrip("/")
    timeout = httpx.Timeout(60.0, connect=10.0)
    with httpx.Client(timeout=timeout) as client:
        migrate_to_backend(client, backend, extracted)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
