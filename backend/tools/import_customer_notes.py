#!/usr/bin/env python3
"""
Tool to import customer and project data from markdown files using local LLM.

This script scans a folder containing customer markdown files, uses Ollama
to extract structured data (stakeholders, team, description, products),
and creates/updates customer and project records via the backend REST API.

The folder name containing the index.md file is used as the customer name.

Usage:
    python -m tools.import_customer_notes /path/to/customers/folder
    python -m tools.import_customer_notes /path/to/customers/folder --model llama3.1
    python -m tools.import_customer_notes /path/to/customers/folder --dry-run
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


class ExtractedCustomerData(BaseModel):
    """Pydantic model for LLM-extracted customer data."""
    stakeholders: Optional[str] = Field(
        None,
        description="Key stakeholders at the customer company (names, roles, emails if available)"
    )
    team: Optional[str] = Field(
        None,
        description="Internal team members working with this customer (from 'Confluent' section)"
    )
    description: Optional[str] = Field(
        None,
        description="Brief description of the customer's business context and main challenges"
    )
    related_products: Optional[str] = Field(
        None,
        description="Products or technologies being used or discussed (e.g., 'CC Flink', 'Kafka', etc.)"
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


class ExtractedData(BaseModel):
    """Combined extraction result."""
    customer: ExtractedCustomerData
    project: Optional[ExtractedProjectData] = None


class CustomerNotesImporter:
    """Imports customer notes from markdown files into the database via REST API."""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        backend_base_url: str = "http://localhost:8000",
        model: str = "llama3.1",
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
                return response.status_code == 200
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

    async def _get_customer_by_name(self, client: httpx.AsyncClient, name: str) -> Optional[dict]:
        """Get customer by name via API."""
        try:
            response = await client.get(
                f"{self.backend_base_url}/api/customers/search/by-name",
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

    async def _create_customer(self, client: httpx.AsyncClient, data: dict) -> dict:
        """Create a new customer via API."""
        response = await client.post(
            f"{self.backend_base_url}/api/customers/",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def _update_customer(self, client: httpx.AsyncClient, customer_id: int, data: dict) -> dict:
        """Update an existing customer via API."""
        response = await client.put(
            f"{self.backend_base_url}/api/customers/{customer_id}",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def _get_project_by_name(
        self,
        client: httpx.AsyncClient,
        name: str,
        customer_id: int
    ) -> Optional[dict]:
        """Get project by name and customer ID via API."""
        try:
            response = await client.get(
                f"{self.backend_base_url}/api/projects/search/by-name",
                params={"name": name, "customer_id": customer_id}
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

    async def extract_data_from_markdown(self, content: str, customer_name: str) -> ExtractedData:
        """Use LLM to extract structured data from markdown content."""
        system_prompt = """You are a data extraction assistant. Your task is to extract structured information from customer project notes written in markdown format.

Extract the following information:

1. **Customer Information:**
   - stakeholders: Key contacts at the customer company (names, roles, emails). Look for sections like "Customer", "Champion and team", "Champion".
   - team: Internal team members (from "Confluent" section or similar). Include names and roles.
   - description: A brief summary of the customer's business, context, and main challenges/goals.
   - related_products: Technologies and products mentioned (e.g., "CC Flink", "Kafka", "ksqlDB", etc.)

2. **Project Information** (if identifiable):
   - name: Derive a project name from the main use case or initiative
   - description: Project goals and scope
   - status: Infer status from context (Active if ongoing work, Completed if finished, etc.)
   - tasks: Extract "Next Steps" or action items as a bullet list
   - past_steps: Extract "Past Steps" or steps taken to address the project's challenges

Be concise. If information is not found, return null for that field.
Return valid JSON matching the schema."""

        user_prompt = f"""Extract customer and project data from these notes for customer "{customer_name}":

---
{content}
---

Return a JSON object with "customer" and "project" fields."""

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

    async def import_customer_folder(
        self,
        folder_path: Path,
        client: httpx.AsyncClient,
        dry_run: bool = False
    ) -> dict:
        """
        Import a single customer folder.

        Args:
            folder_path: Path to the customer folder (folder name = customer name)
            client: HTTP client for API calls
            dry_run: If True, don't actually create/update records

        Returns:
            Dict with import results
        """
        customer_name = folder_path.name
        index_file = folder_path / "index.md"

        if not index_file.exists():
            return {
                "customer": customer_name,
                "status": "skipped",
                "reason": "no index.md file found",
                "action": "none"
            }

        try:
            content = index_file.read_text(encoding="utf-8")
            if not content.strip():
                return {
                    "customer": customer_name,
                    "status": "skipped",
                    "reason": "empty file",
                    "action": "none"
                }

            logger.info(f"Extracting data for customer: {customer_name}")
            extracted = await self.extract_data_from_markdown(content, customer_name)

            result = {
                "customer": customer_name,
                "status": "success",
                "extracted": {
                    "stakeholders": extracted.customer.stakeholders[:100] + "..." if extracted.customer.stakeholders and len(extracted.customer.stakeholders) > 100 else extracted.customer.stakeholders,
                    "team": extracted.customer.team[:100] + "..." if extracted.customer.team and len(extracted.customer.team) > 100 else extracted.customer.team,
                    "description": extracted.customer.description[:200] + "..." if extracted.customer.description and len(extracted.customer.description) > 200 else extracted.customer.description,
                    "products": extracted.customer.related_products[:100] + "..." if extracted.customer.related_products and len(extracted.customer.related_products) > 100 else extracted.customer.related_products,
                    "project_name": extracted.project.name if extracted.project else None,
                },
                "customer_action": "none",
                "project_action": "none"
            }

            if dry_run:
                result["dry_run"] = True
                return result

            # Check if customer exists via API
            existing_customer = await self._get_customer_by_name(client, customer_name)

            if existing_customer:
                # Update existing customer
                customer_update = {
                    "stakeholders": extracted.customer.stakeholders,
                    "team": extracted.customer.team,
                    "description": extracted.customer.description,
                    "related_products": extracted.customer.related_products
                }
                # Remove None values
                customer_update = {k: v for k, v in customer_update.items() if v is not None}
                
                await self._update_customer(client, existing_customer["id"], customer_update)
                result["customer_action"] = "updated"
                result["customer_id"] = existing_customer["id"]
            else:
                # Create new customer
                customer_create = {
                    "name": customer_name,
                    "stakeholders": extracted.customer.stakeholders,
                    "team": extracted.customer.team,
                    "description": extracted.customer.description,
                    "related_products": extracted.customer.related_products
                }
                # Remove None values
                customer_create = {k: v for k, v in customer_create.items() if v is not None}
                
                new_customer = await self._create_customer(client, customer_create)
                result["customer_action"] = "created"
                result["customer_id"] = new_customer["id"]

            # Handle project if extracted
            if extracted.project and extracted.project.name:
                customer_id = result["customer_id"]
                existing_project = await self._get_project_by_name(
                    client, extracted.project.name, customer_id
                )

                if existing_project:
                    project_update = {
                        "description": extracted.project.description,
                        "status": extracted.project.status,
                        "tasks": extracted.project.tasks,
                        "past_steps": extracted.project.past_steps
                    }
                    # Remove None values
                    project_update = {k: v for k, v in project_update.items() if v is not None}
                    
                    await self._update_project(client, existing_project["id"], project_update)
                    result["project_action"] = "updated"
                    result["project_id"] = existing_project["id"]
                    result["project_name"] = extracted.project.name
                else:
                    project_create = {
                        "name": extracted.project.name,
                        "description": extracted.project.description,
                        "customer_id": customer_id,
                        "status": extracted.project.status or "Active",
                        "tasks": extracted.project.tasks,
                        "past_steps": extracted.project.past_steps
                    }
                    # Remove None values (except customer_id and status which are required)
                    project_create = {
                        k: v for k, v in project_create.items() 
                        if v is not None or k in ("customer_id", "status")
                    }
                    
                    new_project = await self._create_project(client, project_create)
                    result["project_action"] = "created"
                    result["project_id"] = new_project["id"]
                    result["project_name"] = extracted.project.name

            return result

        except Exception as e:
            logger.error(f"Error processing {customer_name}: {e}")
            return {
                "customer": customer_name,
                "status": "error",
                "error": str(e),
                "action": "none"
            }

    async def import_all_customers(
        self,
        base_folder: Path,
        dry_run: bool = False,
        filter_customers: list[str] = None
    ) -> dict:
        """
        Import all customer folders from a base directory.

        Args:
            base_folder: Path to the folder containing customer subfolders
            dry_run: If True, don't actually create/update records
            filter_customers: Optional list of customer names to process

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
            logger.info("Checking backend API connectivity...")
            if not await self._check_backend_health():
                raise ConnectionError(
                    f"Cannot connect to backend API at {self.backend_base_url}. "
                    "Make sure the backend server is running."
                )
            logger.info("Backend API is reachable")

        # Find all customer folders (directories with index.md)
        customer_folders = [
            d for d in sorted(base_folder.iterdir())
            if d.is_dir() and (d / "index.md").exists()
        ]

        # Apply filter if provided
        if filter_customers:
            filter_set = {name.lower() for name in filter_customers}
            customer_folders = [
                d for d in customer_folders
                if d.name.lower() in filter_set
            ]

        logger.info(f"Found {len(customer_folders)} customer folders to process")

        results = {
            "base_folder": str(base_folder),
            "total_folders": len(customer_folders),
            "customers_created": 0,
            "customers_updated": 0,
            "projects_created": 0,
            "projects_updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, folder in enumerate(customer_folders, 1):
                logger.info(f"[{i}/{len(customer_folders)}] Processing: {folder.name}")

                result = await self.import_customer_folder(folder, client, dry_run=dry_run)
                results["details"].append(result)

                if result["status"] == "success":
                    if result.get("customer_action") == "created":
                        results["customers_created"] += 1
                    elif result.get("customer_action") == "updated":
                        results["customers_updated"] += 1

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
        description="Import customer and project data from markdown files using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Import all customers from a folder
    python -m tools.import_customer_notes /path/to/customers

    # Import specific customers only
    python -m tools.import_customer_notes /path/to/customers --customers att stryker

    # Dry run (show what would be imported without making changes)
    python -m tools.import_customer_notes /path/to/customers --dry-run

    # Use a specific Ollama model
    python -m tools.import_customer_notes /path/to/customers --model llama3.1:8b

    # Use a different backend URL
    python -m tools.import_customer_notes /path/to/customers --backend-url http://localhost:8080
        """
    )

    parser.add_argument(
        "folder",
        type=Path,
        help="Path to folder containing customer subfolders with index.md files"
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-oss:20b",
        help="Ollama model to use (default: gpt-oss:20b)"
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
        "--customers", "-c",
        nargs="+",
        help="Process only specified customers (folder names)"
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
    importer = CustomerNotesImporter(
        ollama_base_url=args.ollama_url,
        backend_base_url=args.backend_url,
        model=args.model
    )

    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made to the database")

    logger.info(f"Processing folder: {args.folder}")
    logger.info(f"Using model: {importer.model}")
    logger.info(f"Backend URL: {importer.backend_base_url}")

    results = await importer.import_all_customers(
        args.folder,
        dry_run=args.dry_run,
        filter_customers=args.customers
    )

    # Print summary
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"Folder: {results['base_folder']}")
    print(f"Total customer folders: {results['total_folders']}")
    print(f"Customers created: {results['customers_created']}")
    print(f"Customers updated: {results['customers_updated']}")
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

            print(f"  {status_icon} {detail['customer']}: {detail['status']}", end="")

            if detail.get("customer_action") and detail["customer_action"] != "none":
                print(f" (customer {detail['customer_action']}", end="")
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
                    stakeholders_preview = ext['stakeholders'][:100] + "..." if len(ext['stakeholders']) > 100 else ext['stakeholders']
                    print(f"      Stakeholders: {stakeholders_preview}")
                if ext.get("team"):
                    team_preview = ext['team'][:100] + "..." if len(ext['team']) > 100 else ext['team']
                    print(f"      Team: {team_preview}")
                if ext.get("products"):
                    products_preview = ext['products'][:100] + "..." if len(ext['products']) > 100 else ext['products']
                    print(f"      Products: {products_preview}")
                if ext.get("project_name"):
                    print(f"      Project: {ext['project_name']}")


if __name__ == "__main__":
    asyncio.run(main())
