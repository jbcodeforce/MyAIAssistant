"""Agno Agent with structured output to parse legacy customer index.md files."""

from __future__ import annotations

import logging
from pathlib import Path

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from pydantic import BaseModel

from agent_service.agents.agent_config import get_llm_api_key, get_llm_base_url, get_llm_model
from agent_service.tools.legacy_customer_import.schemas import LegacyCustomerIndexImport

logger = logging.getLogger(__name__)

LEGACY_IMPORT_SYSTEM_PROMPT = """You extract structured CRM data from a legacy Markdown customer engagement note (often index.md).

Rules:
1. Do NOT invent facts. Use only names, dates, products, and statements present in the document.
2. Organization name: prefer the main H1 title (strip "Project notes" etc.) or the account folder context if given; keep it short (e.g. "ATT").
3. Map sections sensibly:
   - Customer / **Customer:** bullets → organization.stakeholders (names, roles if listed).
   - Confluent / SE / AE / account manager lines → organization.team.
   - Product / products in scope → organization.related_products and/or project.description as appropriate.
   - Narrative blocks (project status, architecture, issues) → project.description or leave in organization.description when org-level.
4. Project name: derive from primary initiative (e.g. product + migration theme). Must be distinct and concrete.
5. Meetings: Identify sections titled like "### Meeting …", "### Meeting MM/DD", "### Meeting DD/MM", or similar dated meeting headings.
   Each becomes one meeting with:
   - meeting_id: stable ASCII slug: lowercase, use source_hint prefix when helpful, include year if inferable (e.g. att-2026-01-13). If only month/day given, infer year from document context when explicit; otherwise use att-mtg-MM-DD with the year from the doc title or leave year as stated.
   - content: ONLY the markdown for that meeting (heading + bullets under it until the next ### Meeting or end of meetings area). Include attendee line if present under the heading.
   - attendees: comma-separated names if stated on the line after the heading or in the meeting body.
   - Optional past_steps / next_steps for bullets that are clearly actions inside that meeting block (use who unknown when missing).
6. Account-level bullets (not inside a specific ### Meeting block), including "## Past Steps", "## Last Steps", "## Next Steps" global lists → project.past_steps / project.next_steps as {what, who}. Use who "unknown" or "to_be_decided" when assignee is unclear.
7. If there are no dated meeting headings, set meetings to [] and keep narrative in project.description.
8. confidence_notes: briefly list ambiguities (e.g. inferred year) or leave null.
"""


def _build_model() -> OpenAILike:
    return OpenAILike(
        id=get_llm_model(),
        base_url=get_llm_base_url(),
        temperature=0.2,
        api_key=get_llm_api_key(),
    )


def build_legacy_import_agent() -> Agent:
    return Agent(
        name="LegacyCustomerIndexImporter",
        model=_build_model(),
        instructions=LEGACY_IMPORT_SYSTEM_PROMPT,
        output_schema=LegacyCustomerIndexImport,
        markdown=False,
        debug_mode=False,
    )


def extract_legacy_customer_index(
    markdown: str,
    *,
    folder_slug: str | None = None,
    agent: Agent | None = None,
) -> LegacyCustomerIndexImport:
    """Run structured extraction on full markdown source."""
    run_agent = agent or build_legacy_import_agent()
    hint = folder_slug or ""
    user_msg = (
        "Extract organization, project, and meetings from this legacy customer note.\n"
        + (f"Folder / account slug (hint for naming): {hint}\n" if hint else "")
        + "\n---SOURCE---\n"
        f"{markdown}\n"
        "---END---"
    )
    run = run_agent.run(user_msg, stream=False)
    content = run.content
    if isinstance(content, LegacyCustomerIndexImport):
        out = content
    elif isinstance(content, BaseModel):
        out = LegacyCustomerIndexImport.model_validate(content.model_dump())
    else:
        raise TypeError(f"Unexpected run.content type: {type(content)}")
    if folder_slug:
        out = out.model_copy(update={"source_hint": folder_slug})
    return out


def default_folder_slug_from_path(path: Path) -> str | None:
    """Use parent directory name when path is .../customer_slug/index.md."""
    name = path.name.lower()
    if name == "index.md":
        return path.parent.name or None
    return path.stem or None
