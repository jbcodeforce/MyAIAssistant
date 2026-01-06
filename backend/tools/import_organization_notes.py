#!/usr/bin/env python3
"""
Tool to import organization and project data from markdown files using local LLM.

This script scans a folder containing organization markdown files, uses Ollama
to extract structured data (stakeholders, team, description, products),
and creates/updates organization and project records via the backend REST API.

The folder name containing the index.md file is used as the organization name.

Usage:
    python -m tools.import_organization_notes /path/to/organizations/folder
    python -m tools.import_organization_notes /path/to/organizations/folder --model llama3.1
    python -m tools.import_organization_notes /path/to/organizations/folder --dry-run
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class ExtractedOrganizationData(BaseModel):
    """Pydantic model for LLM-extracted organization data."""
    stakeholders: Optional[str] = Field(
        None,
        description="Key stakeholders at the organization company (names, roles, emails if available)"
    )
    team: Optional[str] = Field(
        None,
        description="Internal team members working with this organization (from 'Confluent' section)"
    )
    description: Optional[str] = Field(
        None,
        description="Brief description of the organization's business context and main challenges"
    )
    related_products: Optional[str] = Field(
        None,
        description="Products or technologies being used or discussed (e.g., 'CC Flink', 'Kafka', etc.)"
    )
    use_case_information: Optional[str] = Field(
        None,
        description="Use case information"
    )
    context_information: Optional[str] = Field(
        None,
        description="Context information"
    )
    architecture_information: Optional[str] = Field(
        None,
        description="Architecture information"
    )
    sources_of_information: Optional[str] = Field(
        None,
        description="Sources of information"
    )


class ExtractedProjectData(BaseModel):
    """Pydantic model for LLM-extracted project data."""
    name: str = Field(
        ...,
        description="Project name derived from the main use case or initiative"
    )
    description: Optional[str] = Field(
        None,
        description="Project description including goals and scope"
    )
    status: str = Field(
        default="Active",
        description="Project status: Draft, Active, On Hold, Completed, Cancelled"
    )
    tasks: Optional[str] = Field(
        None,
        description="Key tasks or next steps as a bullet list to address the project's challenges"
    )
    past_steps: Optional[str] = Field(
        None,
        description="Past steps taken to address the project's challenges"
    )
    next_steps: Optional[str] = Field(
        None,
        description="Next steps planned to move the project forward"
    )


class ExtractedData(BaseModel):
    """Combined extraction result."""
    organization: ExtractedOrganizationData
    project: Optional[ExtractedProjectData] = None


class OrganizationNotesImporter:
    """Imports organization notes from markdown files into the database via REST API."""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        backend_base_url: str = "http://localhost:8000",
        model: str = "gpt-oss:20b",
        temperature: float = 0.1
    ):
        self.ollama_base_url = ollama_base_url
        self.backend_base_url = backend_base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    async def _check_backend_health(self) -> bool:
        """Check if the backend API is reachable."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backend_base_url}/")
                if response.status_code == 200:
                    print(f"  [OK] Backend API connected at {self.backend_base_url}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            return False

    async def _call_ollama(self, messages: list[dict], response_format: dict = None) -> str:
        """Call Ollama API for LLM inference."""
        request_body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }

        if response_format:
            request_body["format"] = response_format

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.ollama_base_url}/api/chat",
                json=request_body
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def _get_organization_by_name(self, client: httpx.AsyncClient, name: str) -> Optional[dict]:
        """Get organization by name via API."""
        try:
            response = await client.get(
                f"{self.backend_base_url}/api/organizations/search/by-name",
                params={"name": name}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def _create_organization(self, client: httpx.AsyncClient, data: dict) -> dict:
        """Create a new organization via API."""
        response = await client.post(
            f"{self.backend_base_url}/api/organizations/",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def _update_organization(self, client: httpx.AsyncClient, organization_id: int, data: dict) -> dict:
        """Update an existing organization via API."""
        response = await client.put(
            f"{self.backend_base_url}/api/organizations/{organization_id}",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def _get_project_by_name(
        self,
        client: httpx.AsyncClient,
        name: str,
        organization_id: int
    ) -> Optional[dict]:
        """Get project by name and organization ID via API."""
        try:
            response = await client.get(
                f"{self.backend_base_url}/api/projects/search/by-name",
                params={"name": name, "organization_id": organization_id}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def _create_project(self, client: httpx.AsyncClient, data: dict) -> dict:
        """Create a new project via API."""
        response = await client.post(
            f"{self.backend_base_url}/api/projects/",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def _update_project(self, client: httpx.AsyncClient, project_id: int, data: dict) -> dict:
        """Update an existing project via API."""
        response = await client.put(
            f"{self.backend_base_url}/api/projects/{project_id}",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def extract_data_from_markdown(self, content: str, organization_name: str) -> ExtractedData:
        """Use LLM to extract structured data from markdown content."""
        system_prompt = """You are a data extraction assistant. Your task is to extract structured information from organization project notes written in markdown format.

Extract the following information:

1. **Organization Information:**
   - stakeholders: Key contacts at the organization company (names, roles, emails). Look for sections like "Customer", "Champion and team", "Champion".
   - team: Internal team members (from "Confluent" section or similar). Include names and roles.
   - description: A brief summary of the organization's business, context, and main challenges/goals.
   - related_products: Technologies and products mentioned (e.g., "CC Flink", "Kafka", "ksqlDB", etc.)

2. **Project Information** (if identifiable):
   - name: Derive a project name from the main use case or initiative
   - description: Project goals and scope
   - status: Infer status from context (Active if ongoing work, Completed if finished, etc.)
   - tasks: Extract action items or current tasks as a bullet list
   - past_steps: Extract "Past Steps" or steps already taken to address the project's challenges
   - next_steps: Extract "Next Steps" or planned actions to move the project forward

3. **Use case information**
   - why it is important?
   - business unit?
   - what prior discussions regarding this use-case have happened in the account in the past?

4. **Context information**
   - what is the context of the use case?
   - what is the business context of the use case?
   - what is the technical context of the use case?

5. **Architecture information**

   - what is the architecture of the use case?
   - what are the upstream sources and the downstream destinations?
   - who is consuming the data and how (application, dashboards, etc.)?
   - do they need exactly-once semantics or is at-least once semantics acceptable?
   - what is the expected throughput (messages/sec and bytes/sec)?
   - average message size?
   - how many Flink statement forcasted?
   - what are their expectations around processing lag during deployments and failure recovery?

6. **Sources of information**
   - what are the sources of information?

Be concise. If information is not found, return null for that field.
Return valid JSON matching the schema."""

        user_prompt = f"""Extract organization and project data from these notes for organization "{organization_name}":

---
{content}
---

Return a JSON object with "organization" and "project" fields."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response_text = await self._call_ollama(
                messages,
                response_format=ExtractedData.model_json_schema()
            )
            return ExtractedData.model_validate_json(response_text)
        except Exception as e:
            logger.warning(f"Failed to parse structured response, trying without schema: {e}")
            # Fallback: try without strict schema
            response_text = await self._call_ollama(messages)
            # Try to extract JSON from the response
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return ExtractedData.model_validate(data)
            raise ValueError(f"Could not extract JSON from response: {response_text[:500]}")

    async def import_organization_folder(
        self,
        folder_path: Path,
        client: httpx.AsyncClient,
        dry_run: bool = False
    ) -> dict:
        """
        Import a single organization folder.

        Args:
            folder_path: Path to the organization folder (folder name = organization name)
            client: HTTP client for API calls
            dry_run: If True, don't actually create/update records

        Returns:
            Dict with import results
        """
        organization_name = folder_path.name
        index_file = folder_path / "index.md"

        if not index_file.exists():
            print(f"  [SKIP] No index.md file found")
            return {
                "organization": organization_name,
                "status": "skipped",
                "reason": "no index.md file found",
                "action": "none"
            }

        try:
            print(f"  [PARSE] Reading {index_file.name}...")
            content = index_file.read_text(encoding="utf-8")
            if not content.strip():
                print(f"  [SKIP] Empty file")
                return {
                    "organization": organization_name,
                    "status": "skipped",
                    "reason": "empty file",
                    "action": "none"
                }

            print(f"  [LLM] Extracting structured data using {self.model}...")
            logger.info(f"Extracting data for organization: {organization_name}")
            extracted = await self.extract_data_from_markdown(content, organization_name)
            print(f"  [LLM] Extraction complete")

            def truncate(text: Optional[str], max_len: int = 100) -> Optional[str]:
                """Truncate text to max_len characters with ellipsis."""
                if text and len(text) > max_len:
                    return text[:max_len] + "..."
                return text

            # Count how many sections were extracted
            sections_count = sum(1 for x in [
                extracted.organization.description,
                extracted.organization.use_case_information,
                extracted.organization.context_information,
                extracted.organization.architecture_information,
                extracted.organization.sources_of_information,
            ] if x)

            result = {
                "organization": organization_name,
                "status": "success",
                "extracted": {
                    "stakeholders": truncate(extracted.organization.stakeholders),
                    "team": truncate(extracted.organization.team),
                    "products": truncate(extracted.organization.related_products),
                    "sections_extracted": sections_count,
                    "has_description": bool(extracted.organization.description),
                    "has_use_case": bool(extracted.organization.use_case_information),
                    "has_context": bool(extracted.organization.context_information),
                    "has_architecture": bool(extracted.organization.architecture_information),
                    "has_sources": bool(extracted.organization.sources_of_information),
                    "project_name": extracted.project.name if extracted.project else None,
                },
                "organization_action": "none",
                "project_action": "none"
            }

            if dry_run:
                result["dry_run"] = True
                return result

            # Check if organization exists via API
            print(f"  [DB] Checking if organization '{organization_name}' exists...")
            existing_organization = await self._get_organization_by_name(client, organization_name)

            # Build combined description from all extracted sections
            def build_combined_description(org_data: ExtractedOrganizationData) -> str:
                """Combine all extracted sections into a single markdown description."""
                sections = []
                
                if org_data.description:
                    sections.append(f"## Description\n\n{org_data.description}")
                
                if org_data.use_case_information:
                    sections.append(f"## Use Cases\n\n{org_data.use_case_information}")
                
                if org_data.context_information:
                    sections.append(f"## Context\n\n{org_data.context_information}")
                
                if org_data.architecture_information:
                    sections.append(f"## Architecture\n\n{org_data.architecture_information}")
                
                if org_data.sources_of_information:
                    sections.append(f"## Sources of Information\n\n{org_data.sources_of_information}")
                
                return "\n\n".join(sections) if sections else None

            combined_description = build_combined_description(extracted.organization)

            if existing_organization:
                # Update existing organization
                print(f"  [DB] Updating organization (id={existing_organization['id']})...")
                organization_update = {
                    "stakeholders": extracted.organization.stakeholders,
                    "team": extracted.organization.team,
                    "description": combined_description,
                    "related_products": extracted.organization.related_products,
                }
                # Remove None values
                organization_update = {k: v for k, v in organization_update.items() if v is not None}
                
                await self._update_organization(client, existing_organization["id"], organization_update)
                result["organization_action"] = "updated"
                result["organization_id"] = existing_organization["id"]
                print(f"  [DB] Organization updated successfully")
            else:
                # Create new organization
                print(f"  [DB] Creating new organization '{organization_name}'...")
                organization_create = {
                    "name": organization_name,
                    "stakeholders": extracted.organization.stakeholders,
                    "team": extracted.organization.team,
                    "description": combined_description,
                    "related_products": extracted.organization.related_products,
                }
                # Remove None values
                organization_create = {k: v for k, v in organization_create.items() if v is not None}
                
                new_organization = await self._create_organization(client, organization_create)
                result["organization_action"] = "created"
                result["organization_id"] = new_organization["id"]
                print(f"  [DB] Organization created (id={new_organization['id']})")

            # Handle project if extracted
            if extracted.project and extracted.project.name:
                organization_id = result["organization_id"]
                print(f"  [DB] Checking if project '{extracted.project.name}' exists...")
                existing_project = await self._get_project_by_name(
                    client, extracted.project.name, organization_id
                )

                if existing_project:
                    print(f"  [DB] Updating project (id={existing_project['id']})...")
                    project_update = {
                        "description": extracted.project.description,
                        "status": extracted.project.status,
                        "tasks": extracted.project.tasks,
                        "past_steps": extracted.project.past_steps,
                        "next_steps": extracted.project.next_steps
                    }
                    # Remove None values
                    project_update = {k: v for k, v in project_update.items() if v is not None}
                    
                    await self._update_project(client, existing_project["id"], project_update)
                    result["project_action"] = "updated"
                    result["project_id"] = existing_project["id"]
                    result["project_name"] = extracted.project.name
                    print(f"  [DB] Project updated successfully")
                else:
                    print(f"  [DB] Creating new project '{extracted.project.name}'...")
                    project_create = {
                        "name": extracted.project.name,
                        "description": extracted.project.description,
                        "organization_id": organization_id,
                        "status": extracted.project.status or "Active",
                        "tasks": extracted.project.tasks,
                        "past_steps": extracted.project.past_steps,
                        "next_steps": extracted.project.next_steps
                    }
                    # Remove None values (except organization_id and status which are required)
                    project_create = {
                        k: v for k, v in project_create.items() 
                        if v is not None or k in ("organization_id", "status")
                    }
                    
                    new_project = await self._create_project(client, project_create)
                    result["project_action"] = "created"
                    result["project_id"] = new_project["id"]
                    result["project_name"] = extracted.project.name
                    print(f"  [DB] Project created (id={new_project['id']})")

            print(f"  [DONE] Successfully processed {organization_name}")
            return result

        except Exception as e:
            print(f"  [ERROR] {e}")
            logger.error(f"Error processing {organization_name}: {e}")
            return {
                "organization": organization_name,
                "status": "error",
                "error": str(e),
                "action": "none"
            }

    async def import_all_organizations(
        self,
        base_folder: Path,
        dry_run: bool = False,
        filter_organizations: list[str] = None
    ) -> dict:
        """
        Import all organization folders from a base directory.

        Args:
            base_folder: Path to the folder containing organization subfolders
            dry_run: If True, don't actually create/update records
            filter_organizations: Optional list of organization names to process

        Returns:
            Summary dict with processing results
        """
        base_folder = base_folder.resolve()

        if not base_folder.exists():
            raise FileNotFoundError(f"Folder not found: {base_folder}")

        if not base_folder.is_dir():
            raise ValueError(f"Not a directory: {base_folder}")

        # Check backend health first (skip in dry-run mode)
        if not dry_run:
            print("Checking backend API connectivity...")
            logger.info("Checking backend API connectivity...")
            if not await self._check_backend_health():
                raise ConnectionError(
                    f"Cannot connect to backend API at {self.backend_base_url}. "
                    "Make sure the backend server is running."
                )
            logger.info("Backend API is reachable")
        else:
            print("Dry run mode - skipping backend connectivity check")

        # Find all organization folders (directories with index.md)
        organization_folders = [
            d for d in sorted(base_folder.iterdir())
            if d.is_dir() and (d / "index.md").exists()
        ]

        # Apply filter if provided
        if filter_organizations:
            filter_set = {name.lower() for name in filter_organizations}
            organization_folders = [
                d for d in organization_folders
                if d.name.lower() in filter_set
            ]

        logger.info(f"Found {len(organization_folders)} organization folders to process")

        results = {
            "base_folder": str(base_folder),
            "total_folders": len(organization_folders),
            "organizations_created": 0,
            "organizations_updated": 0,
            "projects_created": 0,
            "projects_updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        print(f"\nProcessing {len(organization_folders)} organization(s)...\n")
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, folder in enumerate(organization_folders, 1):
                print(f"\n[{i}/{len(organization_folders)}] === {folder.name} ===")
                logger.info(f"[{i}/{len(organization_folders)}] Processing: {folder.name}")

                result = await self.import_organization_folder(folder, client, dry_run=dry_run)
                results["details"].append(result)

                if result["status"] == "success":
                    if result.get("organization_action") == "created":
                        results["organizations_created"] += 1
                    elif result.get("organization_action") == "updated":
                        results["organizations_updated"] += 1

                    if result.get("project_action") == "created":
                        results["projects_created"] += 1
                    elif result.get("project_action") == "updated":
                        results["projects_updated"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["errors"] += 1

        return results


async def main():
    parser = argparse.ArgumentParser(
        description="Import organization and project data from markdown files using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Import all organizations from a folder
    python -m tools.import_organization_notes /path/to/organizations

    # Import specific organizations only
    python -m tools.import_organization_notes /path/to/organizations --organizations att stryker

    # Dry run (show what would be imported without making changes)
    python -m tools.import_organization_notes /path/to/organizations --dry-run

    # Use a specific Ollama model
    python -m tools.import_organization_notes /path/to/organizations --model llama3.1:8b

    # Use a different backend URL
    python -m tools.import_organization_notes /path/to/organizations --backend-url http://localhost:8080
        """
    )

    parser.add_argument(
        "folder",
        type=Path,
        help="Path to folder containing organization subfolders with index.md files"
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="mistral:7b-instruct",
        help="Ollama model to use (default: mistral:7b-instruct)"
    )

    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API base URL (default: http://localhost:11434)"
    )

    parser.add_argument(
        "--backend-url",
        type=str,
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract data and show results without creating/updating records"
    )

    parser.add_argument(
        "--organizations", "-o",
        nargs="+",
        help="Process only specified organizations (folder names)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Initializing importer...")
    importer = OrganizationNotesImporter(
        ollama_base_url=args.ollama_url,
        backend_base_url=args.backend_url,
        model=args.model
    )

    # Print configuration summary
    print("\n" + "=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    print(f"Source folder:  {args.folder}")
    print(f"LLM model:      {importer.model}")
    print(f"Ollama URL:     {importer.ollama_base_url}")
    print(f"Backend API:    {importer.backend_base_url}")
    if args.dry_run:
        print("Mode:           DRY RUN (no database changes)")
        logger.info("DRY RUN MODE - no changes will be made to the database")
    else:
        print("Mode:           LIVE (changes will be persisted)")
    print("=" * 60 + "\n")

    logger.info(f"Processing folder: {args.folder}")
    logger.info(f"Using model: {importer.model}")
    logger.info(f"Backend URL: {importer.backend_base_url}")

    results = await importer.import_all_organizations(
        args.folder,
        dry_run=args.dry_run,
        filter_organizations=args.organizations
    )

    # Print summary
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"Folder: {results['base_folder']}")
    print(f"Total organization folders: {results['total_folders']}")
    print(f"Organizations created: {results['organizations_created']}")
    print(f"Organizations updated: {results['organizations_updated']}")
    print(f"Projects created: {results['projects_created']}")
    print(f"Projects updated: {results['projects_updated']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Errors: {results['errors']}")

    if args.verbose or args.dry_run:
        print("\nDetails:")
        for detail in results["details"]:
            status_icon = {
                "success": "+",
                "skipped": "-",
                "error": "!"
            }.get(detail["status"], "?")

            print(f"  {status_icon} {detail['organization']}: {detail['status']}", end="")

            if detail.get("organization_action") and detail["organization_action"] != "none":
                print(f" (organization {detail['organization_action']}", end="")
                if detail.get("project_action") and detail["project_action"] != "none":
                    print(f", project {detail['project_action']}", end="")
                print(")", end="")

            if detail.get("error"):
                print(f" - {detail['error']}")
            elif detail.get("reason"):
                print(f" - {detail['reason']}")
            else:
                print()

            # Show extracted data in dry run or verbose mode
            if detail.get("extracted"):
                ext = detail["extracted"]
                if ext.get("stakeholders"):
                    print(f"      Stakeholders: {ext['stakeholders']}")
                if ext.get("team"):
                    print(f"      Team: {ext['team']}")
                if ext.get("products"):
                    print(f"      Products: {ext['products']}")
                # Show description sections summary
                sections = []
                if ext.get("has_description"):
                    sections.append("Description")
                if ext.get("has_use_case"):
                    sections.append("Use Cases")
                if ext.get("has_context"):
                    sections.append("Context")
                if ext.get("has_architecture"):
                    sections.append("Architecture")
                if ext.get("has_sources"):
                    sections.append("Sources")
                if sections:
                    print(f"      Description sections: {', '.join(sections)} ({ext.get('sections_extracted', 0)} total)")
                if ext.get("project_name"):
                    print(f"      Project: {ext['project_name']}")


if __name__ == "__main__":
    asyncio.run(main())

