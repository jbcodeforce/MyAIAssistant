"""
Normalize customer account index.md files to a canonical section template using Agno.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.models.openai.like import OpenAILike

from agent_service.agents.agent_config import get_llm_api_key, get_llm_base_url, get_llm_model

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt: section definitions, merge rules (B), English, no fabrication
# ---------------------------------------------------------------------------

CUSTOMER_INDEX_SYSTEM_PROMPT = """You are an editor for customer account notes in Markdown.

Your task: read the SOURCE document and fill a structured schema. Each schema field is the body
for one canonical section. Do NOT repeat ## headings inside the field values; only bullet lists,
paragraphs, ### subheadings, links, and images belong in the fields.

Rules:
1. Do not invent facts, names, numbers, dates, or URLs. Only use information present in SOURCE.
2. Fix English: grammar, spelling, and clarity. Keep technical terms and product names as in SOURCE unless clearly typoed.
3. Preserve every URL and every image path from SOURCE (e.g. ![](...), [text](url)) — verbatim hrefs and paths.
4. Every substantive bullet or paragraph from SOURCE must appear in exactly one section (no dropped content).
5. Normalize actionable checkboxes in next_steps to `- [ ]` when they are open tasks.
6. No supplementary or appendix ## section: merge extra material into the closest canonical section (merge strategy B):
   - Sizing, capacity, demo script, topology diagrams → Architecture (or Context if purely business sizing).
   - Issues, blockers, risks, challenges → Context.
   - Cost, questions, status-only updates → Context or Past Steps by tense.
   - EA asks, SE Flink goals, product asks → Confluent when Confluent-facing; else Context.
   - Account opportunity, meeting notes with dates: retrospective → Past Steps; forward-looking → Next Steps.
   - Milestones / project status → Context or Past Steps.
7. title_line must be a single Markdown H1 line like `# AccountName` matching the account in SOURCE.
8. preamble_after_title: optional lines after the H1 that are not a ## section (e.g. migration banner, date). Use empty string if none.
9. Field values use Markdown; empty string if there is nothing to place in that section.

Canonical section meanings:
- products_in_scope: Confluent/Flink/Kafka products and scope.
- champion_and_team: Customer champions and team names.
- confluent: AE, SE, and Confluent-side contacts (no trailing colon in section title when rendered).
- use_case: What they want to achieve with streaming/Flink.
- context: Background, constraints, links to docs, issues, blockers, opportunity narrative.
- architecture: Diagrams, data flow, clusters, technical topology, sizing numbers, demo flow.
- past_steps: History, completed work, past meetings.
- next_steps: Forward actions and follow-ups.
- sources_of_information: Reference links list.
"""


# ---------------------------------------------------------------------------
# Structured output schema (field bodies = markdown without leading ## for that section)
# ---------------------------------------------------------------------------


class CustomerIndexNormalized(BaseModel):
    title_line: str = Field(
        ...,
        description="Single H1 line, e.g. `# Highmark`",
    )
    preamble_after_title: str = Field(
        default="",
        description="Optional text after H1 before first section (banners, dates). No ## headers.",
    )
    products_in_scope: str = Field(default="", description="Body for ## Products in scope")
    champion_and_team: str = Field(default="", description="Body for ## Champion and team")
    confluent: str = Field(default="", description="Body for ## Confluent")
    use_case: str = Field(default="", description="Body for ## Use case")
    context: str = Field(default="", description="Body for ## Context")
    architecture: str = Field(default="", description="Body for ## Architecture")
    past_steps: str = Field(default="", description="Body for ## Past Steps")
    next_steps: str = Field(default="", description="Body for ## Next Steps")
    sources_of_information: str = Field(default="", description="Body for ## Sources of information")


SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("products_in_scope", "Products in scope"),
    ("champion_and_team", "Champion and team"),
    ("confluent", "Confluent"),
    ("use_case", "Use case"),
    ("context", "Context"),
    ("architecture", "Architecture"),
    ("past_steps", "Past Steps"),
    ("next_steps", "Next Steps"),
    ("sources_of_information", "Sources of information"),
)


def _strip_blank_lines(text: str) -> str:
    return text.strip()


def render_customer_index_markdown(data: CustomerIndexNormalized) -> str:
    """Build final markdown with fixed ## order. Omits empty section bodies."""
    parts: list[str] = []
    title = _strip_blank_lines(data.title_line)
    if not title.startswith("#"):
        title = f"# {title.lstrip('#').strip()}"
    parts.append(title)

    pre = _strip_blank_lines(data.preamble_after_title)
    if pre:
        parts.append("")
        parts.append(pre)

    for field_name, heading in SECTION_ORDER:
        body = getattr(data, field_name, "") or ""
        body = body.strip()
        if not body:
            continue
        parts.append("")
        parts.append(f"## {heading}")
        parts.append("")
        parts.append(body)

    return "\n".join(parts).rstrip() + "\n"


def _build_model() -> OpenAILike:
    return OpenAILike(
        id=get_llm_model(),
        base_url=get_llm_base_url(),
        temperature=0.2,
        api_key=get_llm_api_key(),
    )


def build_normalizer_agent() -> Agent:
    """Single reusable Agent (create once per CLI run, not per file)."""
    return Agent(
        name="CustomerIndexNormalizer",
        model=_build_model(),
        instructions=CUSTOMER_INDEX_SYSTEM_PROMPT,
        output_schema=CustomerIndexNormalized,
        markdown=False,
        debug_mode=False,
    )


def normalize_source_with_agent(source_markdown: str, agent: Agent) -> CustomerIndexNormalized:
    user_msg = (
        "Normalize the following customer account markdown into the structured fields.\n\n"
        "---SOURCE---\n"
        f"{source_markdown}\n"
        "---END---"
    )
    run = agent.run(user_msg, stream=False)
    content = run.content
    if isinstance(content, CustomerIndexNormalized):
        return content
    if isinstance(content, BaseModel):
        return CustomerIndexNormalized.model_validate(content.model_dump())
    raise TypeError(f"Unexpected run.content type: {type(content)}")


def discover_index_files(customers_root: Path, only_slug: str | None) -> list[Path]:
    root = customers_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")
    paths: list[Path] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if only_slug is not None and p.name != only_slug:
            continue
        idx = p / "index.md"
        if idx.is_file():
            paths.append(idx)
    return paths


def _warn_if_suspiciously_short(source: str, rendered: str) -> None:
    s_len = len(re.sub(r"\s+", "", source))
    r_len = len(re.sub(r"\s+", "", rendered))
    if s_len > 500 and r_len < s_len * 0.4:
        logger.warning(
            "Normalized output is much shorter than source (%s vs %s non-ws chars); verify nothing was dropped",
            r_len,
            s_len,
        )


URL_OR_IMAGE = re.compile(r"https?://|\]\(\./images/")


def _count_refs(text: str) -> int:
    return len(URL_OR_IMAGE.findall(text))


def _warn_if_refs_lost(source: str, rendered: str) -> None:
    if _count_refs(source) > _count_refs(rendered):
        logger.warning(
            "Fewer URL/image references in output than in source; check for dropped links",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize customer index.md files using Agno + LLM. "
        "Default: print one file to stdout (use --only if several accounts exist). "
        "Otherwise use --write or --output-sibling.",
    )
    parser.add_argument(
        "--customers-root",
        type=Path,
        default=None,
        help="Directory containing one folder per customer, each with index.md. "
        "Default: CUSTOMERS_ROOT env var.",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        metavar="SLUG",
        help="Process only this customer folder name (e.g. Highmark).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite each index.md in place.",
    )
    parser.add_argument(
        "--output-sibling",
        action="store_true",
        help="Write index.md.normalized next to each index.md instead of overwriting.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="With --write, save index.md.bak before overwrite.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less logging.",
    )
    ns = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING if ns.quiet else logging.INFO, format="%(levelname)s %(message)s")

    env_root = os.environ.get("CUSTOMERS_ROOT", "").strip()
    root = ns.customers_root if ns.customers_root is not None else (Path(env_root) if env_root else Path())
    if not str(root).strip():
        parser.error("Set --customers-root or CUSTOMERS_ROOT to the customers directory.")

    if ns.write and ns.output_sibling:
        parser.error("Use only one of --write and --output-sibling.")

    dry_run_stdout = not ns.write and not ns.output_sibling

    files = discover_index_files(root, ns.only)
    if not files:
        logger.error("No index.md found under %s", root)
        return 1

    if dry_run_stdout and len(files) > 1:
        parser.error("Stdout mode prints one document; use --only SLUG, or use --write / --output-sibling.")

    agent = build_normalizer_agent()

    for idx_path in files:
        source = idx_path.read_text(encoding="utf-8")
        try:
            normalized = normalize_source_with_agent(source, agent)
        except Exception as e:
            logger.exception("Failed to normalize %s: %s", idx_path, e)
            return 1

        rendered = render_customer_index_markdown(normalized)
        _warn_if_suspiciously_short(source, rendered)
        _warn_if_refs_lost(source, rendered)

        if dry_run_stdout:
            print(f"===== {idx_path} =====", file=sys.stderr)
            sys.stdout.write(rendered)
            continue

        if ns.output_sibling:
            out = idx_path.with_name("index.md.normalized")
            out.write_text(rendered, encoding="utf-8")
            logger.info("Wrote %s", out)
            continue

        if ns.backup:
            bak = idx_path.with_suffix(idx_path.suffix + ".bak")
            bak.write_text(source, encoding="utf-8")
            logger.info("Backup %s", bak)

        idx_path.write_text(rendered, encoding="utf-8")
        logger.info("Overwrote %s", idx_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
