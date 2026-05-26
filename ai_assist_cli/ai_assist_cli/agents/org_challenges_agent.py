"""Agno agent: synthesize org-wide challenges, next steps, and issues from DB + notes."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from agno.agent import Agent
from agno.tools.sql import SQLTools
from pydantic import BaseModel, Field

from ai_assist_cli.agents.workspace_notes_tools import WorkspaceNotesTools
from ai_assist_cli.services.llm_model import build_openai_like_model

ORG_CHALLENGES_INSTRUCTIONS = """You consolidate customer/account status across the MyAI Assistant database and workspace notes.

Use the SQL tools to inspect schema, then query relevant tables: organizations, projects, todos, meetings.
Join organization names when reporting. Meetings store file_ref paths; when needed, use read_markdown_file for those files if they fall under the notes root.
Use list_markdown_files to discover note files when the database is sparse.

Extract only what is supported by queried data or file contents. Do not invent issues.

Categories:
- challenge: current obstacles or risks called out in DB text fields or notes.
- next_step: planned actions from project/meeting next_steps JSON, todos not completed, or explicit next steps in notes.
- issue: bugs, blockers, open problems, or urgent todos.

Each row must name an account: use organizations.name when linked; otherwise use the top-level folder name under notes for that content.

Prefer selective reads: run SQL first, then open a small set of markdown files (meeting notes, index.md) rather than loading everything.

Respond using the required structured output schema only."""


class ChallengeRow(BaseModel):
    """One synthesized row for the report."""

    account: str = Field(..., description="Organization / account name")
    kind: Literal["challenge", "next_step", "issue"] = Field(
        ...,
        description="Row category",
    )
    summary: str = Field(..., description="Short description")
    source: str = Field(
        ...,
        description="Origin: table.column, meeting id, or note path",
    )


class ChallengeReport(BaseModel):
    """Structured org-wide challenges report."""

    rows: list[ChallengeRow] = Field(default_factory=list)


def build_org_challenges_agent(
    *,
    notes_root: Path,
    database_url: str | None,
    skip_db: bool = False,
) -> Agent:
    """Create an Agno agent with SQL + workspace notes tools and structured output."""
    tools: list = [WorkspaceNotesTools(notes_root=notes_root)]
    if not skip_db and database_url:
        tools.insert(
            0,
            SQLTools(
                db_url=database_url,
                enable_list_tables=True,
                enable_describe_table=True,
                enable_run_sql_query=True,
            ),
        )

    return Agent(
        name="OrgChallenges",
        model=build_openai_like_model(),
        instructions=ORG_CHALLENGES_INSTRUCTIONS,
        tools=tools,
        markdown=True,
        output_schema=ChallengeReport,
        structured_outputs=True,
    )
